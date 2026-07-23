"""
tracker/engine.py
─────────────────
Accumulates power samples and exposes environmental metrics.

Power sources considered:
  • CPU  – psutil.cpu_percent()  (always available); optionally real
           measured energy via Linux intel-rapl if the user grants permission
  • GPU  – GPUtil                (optional; auto-detected); optionally real
           measured power via NVIDIA pynvml if the user grants permission
  • RAM  – installed capacity (psutil.virtual_memory().total) × W/GB
  • TDP auto-detect              – Windows (WMI) / Linux (/proc/cpuinfo) /
                                    macOS (sysctl) → naming-convention heuristic

CPU power model: linear interpolation between idle and TDP wattage as a
function of utilization, following the SPECpower_ssj2008-based methodology
used by Cloud Carbon Footprint (Average Watts = Min Watts + Utilization ×
(Max Watts − Min Watts)) — see https://www.cloudcarbonfootprint.org/docs/methodology/
and the energy-proportionality model in Barroso & Hölzle,
"The Case for Energy-Proportional Computing", IEEE Computer, 2007
(https://www.barroso.org/publications/ieee_computer07.pdf).

Permission-gated real measurement:
  CPU and GPU power are *modeled* by default. If the user explicitly opts in
  (see set_permission()), the engine attempts to read real hardware counters
  instead of modeling them, and reports which metrics are actually measured
  vs. estimated via accuracy_report().

Boot-to-launch backfill (see backfill_report()):
  Energy consumed between boot and the moment this app was launched is
  frozen once at startup, from real signals only: CPU uses the OS's real
  cumulative busy/idle counters (psutil.cpu_times(), not an assumed load
  percentage), RAM uses real installed capacity. GPU is excluded (0) rather
  than guessed, since GPU permission cannot have been granted before launch.
  The user can toggle whether this frozen estimate counts toward totals via
  set_include_backfill(). Energy accumulated after launch is tracked
  separately via tick() and is unaffected by this toggle.

Network energy:
  • psutil.net_io_counters() gives cumulative bytes since boot
  • Converted to kWh via IEA estimate (0.06 kWh / GB)
  • Added to total for cost / water / waste calculations
"""

from __future__ import annotations

import platform
import re
import subprocess
import time
import json
from pathlib import Path
import psutil

import config

# Load global utility rates database
_RATES_FILE = Path(__file__).parent / "rates.json"
try:
    with open(_RATES_FILE, "r", encoding="utf-8") as _f:
        RATES_DB = json.load(_f)
except Exception:
    RATES_DB = {}


# ──────────────────────────────────────────────────────────────────────────────
#  GPU detection (optional dependency)
# ──────────────────────────────────────────────────────────────────────────────

def _try_import_gputil():
    try:
        import GPUtil
        return GPUtil
    except ImportError:
        return None


# ──────────────────────────────────────────────────────────────────────────────
#  Real hardware measurement probes (optional, permission-gated)
# ──────────────────────────────────────────────────────────────────────────────

def _try_import_pynvml():
    """pynvml gives real NVIDIA GPU power readback (nvidia-ml-py package)."""
    try:
        import pynvml
        pynvml.nvmlInit()
        return pynvml
    except Exception:
        return None


def _find_rapl_energy_path() -> Path | None:
    """
    Locate the Linux intel-rapl 'package' energy counter (microjoules,
    monotonically increasing since boot, wraps at max_energy_range_uj).
    Only present on Linux with a supported Intel/AMD CPU, and may require
    read permission the current user doesn't have.
    """
    base = Path("/sys/class/powercap")
    if not base.exists():
        return None
    try:
        for entry in sorted(base.glob("intel-rapl:*")):
            name_file = entry / "name"
            energy_file = entry / "energy_uj"
            if name_file.exists() and energy_file.exists() and ":" not in entry.name[len("intel-rapl:"):]:
                try:
                    if name_file.read_text().strip() == "package-0" and energy_file.read_text():
                        return energy_file
                except Exception:
                    continue
        # Fall back to the first readable energy_uj file found
        for energy_file in sorted(base.glob("intel-rapl:*/energy_uj")):
            try:
                energy_file.read_text()
                return energy_file
            except Exception:
                continue
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
#  CPU TDP auto-detection — Windows (WMI) / Linux (/proc/cpuinfo) / macOS (sysctl)
# ──────────────────────────────────────────────────────────────────────────────

def _infer_intel_amd_tdp(name_lower: str) -> float | None:
    """
    Infer TDP from an Intel/AMD model-name string using naming conventions.

    Intel suffixes:
      U / UP  → ultra-low-power mobile   ~15 W
      P       → performance mobile       ~28 W
      H / HK  → high-performance mobile  ~45 W
      K / KF  → desktop unlocked         ~125 W
      (none)  → mainstream desktop        ~65 W

    AMD suffixes:
      U       → ultra-low-power mobile   ~15 W
      H / HS  → high-performance mobile  ~45 W
      X       → desktop enthusiast       ~105 W
      (none)  → mainstream desktop        ~65 W
    """
    n = name_lower
    # ── Intel ────────────────────────────────────────────────────────────
    if re.search(r'(i[3579]-\d{4,5}u|125u|135u|165u|ultra.*\du)', n):
        return 15.0
    if re.search(r'i[3579]-\d{4,5}p\b', n):
        return 28.0
    if re.search(r'i[3579]-\d{4,5}h[kqx]?\b', n):
        return 45.0
    if re.search(r'i[3579]-\d{4,5}k[fs]?\b', n):
        return 125.0
    if re.search(r'i[3579]-\d{4,5}\b', n):
        return 65.0
    # ── AMD Ryzen ────────────────────────────────────────────────────────
    if re.search(r'ryzen.*\d{4}u\b', n):
        return 15.0
    if re.search(r'ryzen.*\d{4}h[sx]?\b', n):
        return 45.0
    if re.search(r'ryzen.*\d{4}x\b', n):
        return 105.0
    if re.search(r'ryzen.*\d{4}\b', n):
        return 65.0
    return None


def _infer_apple_silicon_tdp(name_lower: str) -> float | None:
    """
    Rough tier-based estimate for Apple M-series chips.

    Apple never publishes an official TDP, and independent power
    measurements are inconsistent across sources/methodologies, so these
    are coarse per-tier ballparks (not a precise, single-source citation):
    base M-series ≈ 20 W under sustained CPU load is the figure most
    third-party measurements converge on; Pro/Max/Ultra are scaled up
    roughly in line with their core counts relative to the base tier.
    """
    if not re.search(r'apple\s+m\d', name_lower):
        return None
    if "ultra" in name_lower:
        return 60.0
    if "max" in name_lower:
        return 45.0
    if "pro" in name_lower:
        return 30.0
    return 20.0


def _detect_cpu_tdp_windows() -> tuple[str, float | None] | tuple[None, None]:
    """Read CPU model name via WMI (Windows only)."""
    try:
        import wmi  # pip install wmi
        c = wmi.WMI()
        cpu_name: str = c.Win32_Processor()[0].Name
        return cpu_name, _infer_intel_amd_tdp(cpu_name.lower())
    except Exception:
        return None, None


def _detect_cpu_tdp_linux() -> tuple[str, float | None] | tuple[None, None]:
    """Read CPU model name from /proc/cpuinfo's 'model name' field (Linux only)."""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                cpu_name = line.split(":", 1)[1].strip()
                return cpu_name, _infer_intel_amd_tdp(cpu_name.lower())
    except Exception:
        pass
    return None, None


def _detect_cpu_tdp_macos() -> tuple[str, float | None] | tuple[None, None]:
    """Read CPU model name via `sysctl machdep.cpu.brand_string` (macOS only)."""
    try:
        cpu_name = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            text=True, timeout=2,
        ).strip()
        n = cpu_name.lower()
        tdp = _infer_apple_silicon_tdp(n)
        if tdp is None:
            tdp = _infer_intel_amd_tdp(n)  # Intel-based Macs
        return cpu_name, tdp
    except Exception:
        return None, None


def _detect_cpu_tdp() -> tuple[str, float | None] | tuple[None, None]:
    """Dispatch to the right detection method for the current OS."""
    system = platform.system()
    if system == "Windows":
        return _detect_cpu_tdp_windows()
    if system == "Linux":
        return _detect_cpu_tdp_linux()
    if system == "Darwin":
        return _detect_cpu_tdp_macos()
    return None, None


# ──────────────────────────────────────────────────────────────────────────────
#  Device profile (laptop vs. desktop) — for e-waste amortization
# ──────────────────────────────────────────────────────────────────────────────

def _detect_device_profile() -> str | None:
    """
    'laptop' if a battery is present, 'desktop' if not, None if undetermined.
    psutil.sensors_battery() returns None on desktops (no battery) and a
    real reading on laptops — no elevated permissions required.
    """
    try:
        battery = psutil.sensors_battery()
        return "laptop" if battery is not None else "desktop"
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
#  Network helpers
# ──────────────────────────────────────────────────────────────────────────────

def _net_bytes_total() -> int:
    """Total bytes sent + received since OS boot."""
    c = psutil.net_io_counters()
    return c.bytes_sent + c.bytes_recv


def _boot_cpu_busy_fraction() -> float | None:
    """
    Real average CPU utilization since boot (0.0-1.0), derived from the
    OS's cumulative busy/idle time counters (psutil.cpu_times()). Unlike
    cpu_percent(), these counters have been accumulating since boot
    regardless of whether this app was running, so this is a genuine
    measurement of boot-to-launch usage, not a guess.
    """
    try:
        t = psutil.cpu_times()
        total = sum(t)
        if total <= 0:
            return None
        return 1.0 - (t.idle / total)
    except Exception:
        return None


def _net_connection_status() -> str:
    """
    Best-effort description of the active network connection, based on
    interface-name conventions (no elevated permissions required).
    """
    _WIFI_HINTS = ("wi-fi", "wifi", "wlan", "wireless", "airport")
    _ETH_HINTS = ("ethernet", "eth", "local area connection")
    try:
        stats = psutil.net_if_stats()
        up = [name for name, st in stats.items() if st.isup]
        for name in up:
            if any(h in name.lower() for h in _WIFI_HINTS):
                return "Wi-Fi connected"
        for name in up:
            if any(h in name.lower() for h in _ETH_HINTS):
                return "Ethernet connected"
        for name in up:
            if name.lower() not in ("lo", "loopback", "loopback pseudo-interface 1"):
                return "Connected"
        return "Offline"
    except Exception:
        return "Unknown"


# ──────────────────────────────────────────────────────────────────────────────
#  Engine
# ──────────────────────────────────────────────────────────────────────────────

class Engine:
    """
    Tracks energy and computes environmental metrics.

    Call  .tick()    every second to accumulate hardware energy.
    Call  .metrics() to get the latest snapshot (includes network).
    """

    def __init__(self, backfill_from_boot: bool = True) -> None:
        self._last_tick: float = time.monotonic()
        self._boot_ts: float = psutil.boot_time()
        
        # Currency settings
        self._currency: str = "EUR"  # active currency
        self._use_auto: bool = True  # whether to follow detected currency
        self._detected_currency: str | None = None

        # GPU: detect presence and cache the model name in one call — the
        # name never changes mid-session, so there's no reason to re-invoke
        # GPUtil (which shells out to nvidia-smi) every time it's requested.
        self._gputil = _try_import_gputil()
        self._has_gpu: bool = False
        self._gpu_name_cached: str | None = None
        if self._gputil is not None:
            try:
                gpus = self._gputil.getGPUs()
                if gpus:
                    self._has_gpu = True
                    self._gpu_name_cached = gpus[0].name
            except Exception:
                pass

        # TDP: try OS-native auto-detect (WMI/procfs/sysctl), fall back to config value
        cpu_name, detected_tdp = _detect_cpu_tdp()
        self._cpu_name: str = cpu_name or "unknown"
        self._tdp: float = detected_tdp if detected_tdp is not None else config.TDP_WATTS
        self._tdp_auto: bool = detected_tdp is not None

        # RAM: real installed capacity, cached (doesn't change at runtime)
        try:
            self._ram_gb: float = psutil.virtual_memory().total / (1024 ** 3)
        except Exception:
            self._ram_gb = None

        # Device profile (laptop/desktop), for e-waste amortization
        self._device_profile: str | None = _detect_device_profile()

        # ── Permission-gated real measurement (opt-in; off by default) ────────
        self._perm_cpu_measure: bool = False
        self._perm_gpu_measure: bool = False

        self._pynvml = _try_import_pynvml()
        self._nvml_handle = None
        if self._pynvml is not None and self._has_gpu:
            try:
                self._nvml_handle = self._pynvml.nvmlDeviceGetHandleByIndex(0)
            except Exception:
                self._nvml_handle = None

        self._rapl_path = _find_rapl_energy_path()
        self._rapl_last_uj: int | None = None
        self._rapl_last_t: float | None = None

        # Whether the most recent tick used a real reading vs. the model
        self._last_cpu_measured: bool = False
        self._last_gpu_measured: bool = False

        # Seed current_watts with an idle estimate
        self._current_watts: float = config.IDLE_POWER_W

        # ── Boot-to-launch backfill (frozen once at startup, real signals only) ──
        # CPU: psutil.cpu_times() gives the OS's real cumulative busy/idle time
        #      since boot, so the backfilled CPU contribution is measured, not
        #      assumed.
        # RAM: real installed capacity, so its contribution is measured too.
        # GPU: excluded (0). Real GPU history requires the user's permission,
        #      which by definition cannot have been granted before this app
        #      was even open — rather than guess a load percentage, we simply
        #      don't count it.
        self._backfill_duration_h: float = (
            (time.time() - self._boot_ts) / 3600.0 if backfill_from_boot else 0.0
        )
        self._backfill_cpu_busy_frac: float | None = (
            _boot_cpu_busy_fraction() if backfill_from_boot else None
        )
        self._include_backfill: bool = True

        if backfill_from_boot and self._backfill_cpu_busy_frac is not None:
            backfill_cpu_w = config.IDLE_POWER_W + (self._tdp - config.IDLE_POWER_W) * self._backfill_cpu_busy_frac
            self._kwh_backfill: float = (backfill_cpu_w + self._ram_watts()) * self._backfill_duration_h / 1000.0
        else:
            self._kwh_backfill = 0.0

        # Energy accumulated via tick() since this Engine was constructed.
        self._kwh_ticked: float = 0.0

    # ── GPU helpers ───────────────────────────────────────────────────────────

    def _gpu_load_pct(self) -> float:
        if not self._has_gpu:
            return 0.0
        try:
            gpus = self._gputil.getGPUs()
            return (gpus[0].load * 100.0) if gpus else 0.0
        except Exception:
            return 0.0

    def _gpu_name(self) -> str | None:
        return self._gpu_name_cached

    # ── Power estimation ──────────────────────────────────────────────────────

    def _ram_watts(self) -> float:
        if self._ram_gb is not None:
            return self._ram_gb * config.RAM_POWER_W_PER_GB
        return config.RAM_POWER_W

    def ram_watts(self) -> float:
        """Public accessor for the current RAM power estimate (W)."""
        return self._ram_watts()

    def _ewaste_g_per_hour(self) -> float:
        if self._device_profile == "laptop":
            return config.WASTE_EWASTE_LAPTOP_G_PER_HOUR
        if self._device_profile == "desktop":
            return config.WASTE_EWASTE_DESKTOP_G_PER_HOUR
        return config.WASTE_EWASTE_G_PER_HOUR

    # ── Real hardware measurement (permission-gated) ────────────────────────────

    def _read_gpu_power_measured(self) -> float | None:
        """Real NVIDIA GPU power draw in watts via pynvml, or None if unavailable."""
        if not self._perm_gpu_measure or self._nvml_handle is None:
            return None
        try:
            milliwatts = self._pynvml.nvmlDeviceGetPowerUsage(self._nvml_handle)
            return milliwatts / 1000.0
        except Exception:
            return None

    def _read_cpu_power_measured(self, now: float) -> float | None:
        """
        Real CPU package power in watts, derived from the energy delta (J)
        read from Linux intel-rapl over the elapsed wall-clock time.
        Returns None on the first call (no prior sample) or when unavailable.
        """
        if not self._perm_cpu_measure or self._rapl_path is None:
            return None
        try:
            uj = int(self._rapl_path.read_text())
        except Exception:
            return None

        watts = None
        if self._rapl_last_uj is not None and self._rapl_last_t is not None:
            dt = now - self._rapl_last_t
            duj = uj - self._rapl_last_uj
            if dt > 0 and duj >= 0:  # negative delta = counter wrapped; skip this sample
                watts = (duj / 1_000_000.0) / dt
        self._rapl_last_uj = uj
        self._rapl_last_t = now
        return watts

    # Public API

    def set_permission(self, metric: str, granted: bool) -> None:
        """Grant/revoke user permission to read real hardware counters for 'cpu' or 'gpu'."""
        if metric == "cpu":
            self._perm_cpu_measure = granted
            if granted and self._rapl_path is not None:
                # Prime the baseline reading immediately so the very next
                # tick() already has a delta to compute wattage from,
                # instead of requiring two refreshes before anything shows.
                try:
                    self._rapl_last_uj = int(self._rapl_path.read_text())
                    self._rapl_last_t = time.monotonic()
                except Exception:
                    self._rapl_last_uj = None
                    self._rapl_last_t = None
            else:
                self._rapl_last_uj = None
                self._rapl_last_t = None
        elif metric == "gpu":
            self._perm_gpu_measure = granted

    def set_include_backfill(self, include: bool) -> None:
        """Whether the frozen boot-to-launch backfill estimate counts toward totals."""
        self._include_backfill = include

    @property
    def include_backfill(self) -> bool:
        return self._include_backfill

    def backfill_report(self) -> dict:
        """Detail for the Accuracy window's expandable 'Boot backfill' row."""
        return {
            "kwh": self._kwh_backfill,
            "duration_h": self._backfill_duration_h,
            "cpu_busy_pct": (
                self._backfill_cpu_busy_frac * 100.0
                if self._backfill_cpu_busy_frac is not None else None
            ),
            "include": self._include_backfill,
        }

    def tick(self) -> None:
        now_mono = time.monotonic()
        dt_h = (now_mono - self._last_tick) / 3600.0
        self._last_tick = now_mono
        cpu_pct = psutil.cpu_percent(interval=None)
        gpu_pct = self._gpu_load_pct()

        measured_cpu_w = self._read_cpu_power_measured(now_mono)
        measured_gpu_w = self._read_gpu_power_measured()
        self._last_cpu_measured = measured_cpu_w is not None
        self._last_gpu_measured = measured_gpu_w is not None

        modeled_cpu_f = max(0.0, min(cpu_pct / 100.0, 1.0))
        modeled_gpu_f = max(0.0, min(gpu_pct / 100.0, 1.0))
        cpu_w = measured_cpu_w if measured_cpu_w is not None else (
            config.IDLE_POWER_W + (self._tdp - config.IDLE_POWER_W) * modeled_cpu_f
        )
        gpu_w = measured_gpu_w if measured_gpu_w is not None else (
            config.GPU_IDLE_W + (config.GPU_TDP_W - config.GPU_IDLE_W) * modeled_gpu_f
            if self._has_gpu else 0.0
        )
        watts = cpu_w + gpu_w + self._ram_watts()
        self._current_watts = watts
        self._kwh_ticked += (watts * dt_h) / 1000.0

    @property
    def uptime_hours(self) -> float:
        return (time.time() - self._boot_ts) / 3600.0

    def accuracy_report(self) -> list[dict]:
        """
        Per-metric transparency report for the accuracy table UI: whether
        each figure is a real hardware/OS reading or a modeled estimate,
        whether the user can opt in to real measurement for it, and a plain
        factual info string (detected hardware, active setting, or the
        fixed coefficient in use) for the Info column.
        """
        gpu_supported = self._pynvml is not None and self._nvml_handle is not None
        cpu_supported = self._rapl_path is not None
        gpu_name = self._gpu_name()
        rate = self._resolve_rate()
        symbol = config.CURRENCY_SYMBOLS.get(self._currency, self._currency)

        if self._tdp_auto:
            cpu_info = f"{self._cpu_name} — {self._tdp:.0f}W TDP (auto-detected)"
        else:
            cpu_info = f"{self._tdp:.0f}W TDP (default, model detection failed)"

        if not self._has_gpu:
            gpu_info = "No discrete GPU detected"
        elif gpu_name is not None:
            gpu_info = gpu_name
        else:
            gpu_info = "GPU detected (name unavailable)"

        ram_info = (
            f"{self._ram_gb:.1f}GB installed" if self._ram_gb is not None
            else "Capacity read failed"
        )

        cost_info = f"{self._currency} — {symbol}{rate:g}/kWh"

        return [
            {
                "metric": "cpu",
                "measured": self._last_cpu_measured,
                "permission_supported": cpu_supported,
                "permission_granted": self._perm_cpu_measure,
                "reason": cpu_info,
            },
            {
                "metric": "gpu",
                "measured": self._last_gpu_measured,
                "permission_supported": gpu_supported,
                "permission_granted": self._perm_gpu_measure,
                "reason": gpu_info,
            },
            {
                "metric": "ram",
                "measured": self._ram_gb is not None,
                "permission_supported": False,
                "permission_granted": False,
                "reason": ram_info,
            },
            {
                "metric": "network",
                "measured": True,
                "permission_supported": False,
                "permission_granted": False,
                "reason": _net_connection_status(),
            },
            {
                "metric": "cost",
                "measured": False,
                "permission_supported": False,
                "permission_granted": False,
                "reason": cost_info,
            },
            {
                "metric": "water",
                "measured": False,
                "permission_supported": False,
                "permission_granted": False,
                "reason": f"{config.WATER_FACTOR_L_PER_KWH:g} L per kWh",
            },
            {
                "metric": "waste",
                "measured": False,
                "permission_supported": False,
                "permission_granted": False,
                "reason": (
                    f"{config.WASTE_POWER_G_PER_KWH:g} g per kWh + "
                    f"{self._ewaste_g_per_hour():g} g per hour e-waste "
                    f"({self._device_profile or 'unknown'} profile)"
                ),
            },
        ]

    @property
    def currency(self) -> str:
        return self._currency

    @currency.setter
    def currency(self, val: str) -> None:
        self._currency = val

    @property
    def use_auto(self) -> bool:
        return self._use_auto

    @use_auto.setter
    def use_auto(self, val: bool) -> None:
        self._use_auto = val

    @property
    def detected_currency(self) -> str | None:
        return self._detected_currency

    def apply_detected_location(self, currency_code: str) -> None:
        """Called when Geo-IP detection resolves the user's currency."""
        self._detected_currency = currency_code
        # If in auto mode, update active currency immediately
        if self._use_auto:
            self._currency = currency_code

    def _resolve_rate(self) -> float:
        """
        Return the rate per kWh for the active currency. rates.json is
        keyed by currency (not country), so this is a direct, unambiguous
        lookup — no arbitrary country needs to be picked for currencies
        shared by multiple countries (e.g. EUR). Every currency the tray
        menu can select is present in rates.json, so the flat fallback
        below only matters if rates.json itself failed to load.
        """
        entry = RATES_DB.get(self._currency)
        if entry is not None:
            return entry.get("rate", config.FALLBACK_RATE)
        return config.FALLBACK_RATE

    def metrics(self) -> dict:
        net_gb  = _net_bytes_total() / (1024 ** 3)
        net_kwh = net_gb * config.NETWORK_KWH_PER_GB
        hw_kwh    = self._kwh_ticked + (self._kwh_backfill if self._include_backfill else 0.0)
        total_kwh = hw_kwh + net_kwh
        uptime_h  = self.uptime_hours

        rate = self._resolve_rate()
        cost = total_kwh * rate

        return {
            "kwh_hw":    hw_kwh,
            "kwh_net":   net_kwh,
            "kwh_total": total_kwh,
            "watts":     self._current_watts,
            "cost":      cost,
            "water_l":   total_kwh * config.WATER_FACTOR_L_PER_KWH,
            "waste_g":   (total_kwh * config.WASTE_POWER_G_PER_KWH)
                         + (uptime_h * self._ewaste_g_per_hour()),
            "net_gb":    net_gb,
            "has_gpu":   self._has_gpu,
        }


def fmt_kwh(kwh: float) -> str:
    if kwh < 0.001:
        return f"{kwh * 1000:.2f} Wh"
    return f"{kwh:.4f} kWh"

def fmt_cost(amount: float, currency: str = "EUR") -> str:
    symbol = config.CURRENCY_SYMBOLS.get(currency, currency)
    # Check if currency is zero-decimal or large-unit
    if currency in ("KRW", "JPY", "VND", "INR", "SEK", "NOK", "DKK", "ZAR"):
        if amount < 1.0:
            return f"{symbol}{amount:.2f}"
        if amount < 10.0:
            return f"{symbol}{amount:.1f}"
        return f"{symbol}{amount:.0f}"
    else:
        if amount < 0.01:
            cents_symbol = "¢"
            return f"{amount * 100:.3f}{cents_symbol}"
        return f"{symbol}{amount:.4f}"

def fmt_water(litres: float) -> str:
    if litres < 1.0:
        return f"{litres * 1000:.1f} mL"
    return f"{litres:.3f} L"

def fmt_waste(grams: float) -> str:
    if grams < 1.0:
        return f"{grams * 1000:.1f} mg"
    if grams < 1000.0:
        return f"{grams:.2f} g"
    return f"{grams / 1000.0:.3f} kg"

def fmt_net(gb: float) -> str:
    if gb < 0.001:
        return f"{gb * 1000:.1f} MB"
    return f"{gb:.3f} GB"
