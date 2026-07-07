"""
tracker/engine.py
─────────────────
Accumulates power samples and exposes environmental metrics.

Power sources considered:
  • CPU  – psutil.cpu_percent()  (always available)
  • GPU  – GPUtil                (optional; auto-detected)
  • RAM  – fixed estimate        (DDR4/5 average)
  • CPU freq scaling             – psutil.cpu_freq() scales TDP by current/max ratio
  • TDP auto-detect              – WMI CPU name → naming-convention heuristic (Windows)
Network energy:
  • psutil.net_io_counters() gives cumulative bytes since boot
  • Converted to kWh via IEA estimate (0.06 kWh / GB)
  • Added to total for cost / water / waste calculations
"""

from __future__ import annotations

import re
import time
import psutil

import config


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
#  CPU TDP auto-detection via WMI (Windows only)
# ──────────────────────────────────────────────────────────────────────────────

def _detect_cpu_tdp_wmi() -> tuple[str, float] | tuple[None, None]:
    """
    Read CPU model name from WMI and infer TDP from naming conventions.

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

    Returns (cpu_name_string, tdp_float) or (None, None) on failure.
    """
    try:
        import wmi  # pip install wmi
        c = wmi.WMI()
        cpu_name: str = c.Win32_Processor()[0].Name
        n = cpu_name.lower()

        # ── Intel ────────────────────────────────────────────────────────────
        # Mobile low-power U-series  (e.g. "i7-1355U", "Core Ultra 5 125U")
        if re.search(r'(i[3579]-\d{4,5}u|125u|135u|165u|ultra.*\du)', n):
            return cpu_name, 15.0
        # Mobile performance P-series  (e.g. "i7-1260P")
        if re.search(r'i[3579]-\d{4,5}p\b', n):
            return cpu_name, 28.0
        # Mobile high-performance H-series  (e.g. "i7-13700H", "i9-13980HX")
        if re.search(r'i[3579]-\d{4,5}h[kqx]?\b', n):
            return cpu_name, 45.0
        # Desktop K-series unlocked  (e.g. "i7-13700K")
        if re.search(r'i[3579]-\d{4,5}k[fs]?\b', n):
            return cpu_name, 125.0
        # Desktop mainstream  (e.g. "i7-13700", "i5-12400")
        if re.search(r'i[3579]-\d{4,5}\b', n):
            return cpu_name, 65.0

        # ── AMD Ryzen ────────────────────────────────────────────────────────
        # Mobile ultra-low U  (e.g. "Ryzen 5 7530U")
        if re.search(r'ryzen.*\d{4}u\b', n):
            return cpu_name, 15.0
        # Mobile high-perf H / HS  (e.g. "Ryzen 9 7945HX", "Ryzen 7 6800HS")
        if re.search(r'ryzen.*\d{4}h[sx]?\b', n):
            return cpu_name, 45.0
        # Desktop enthusiast X  (e.g. "Ryzen 9 7950X")
        if re.search(r'ryzen.*\d{4}x\b', n):
            return cpu_name, 105.0
        # Desktop mainstream  (e.g. "Ryzen 5 5600")
        if re.search(r'ryzen.*\d{4}\b', n):
            return cpu_name, 65.0

    except Exception:
        pass
    return None, None


# ──────────────────────────────────────────────────────────────────────────────
#  Network helpers
# ──────────────────────────────────────────────────────────────────────────────

def _net_bytes_total() -> int:
    """Total bytes sent + received since OS boot."""
    c = psutil.net_io_counters()
    return c.bytes_sent + c.bytes_recv


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
        self._kwh: float = 0.0
        self._last_tick: float = time.monotonic()
        self._boot_ts: float = psutil.boot_time()
        self._currency: str = "EUR"  # default currency

        # GPU
        self._gputil = _try_import_gputil()
        self._has_gpu: bool = self._detect_gpu()

        # TDP: try WMI auto-detect, fall back to config value
        cpu_name, detected_tdp = _detect_cpu_tdp_wmi()
        self._cpu_name: str = cpu_name or "unknown"
        self._tdp: float = detected_tdp if detected_tdp is not None else config.TDP_WATTS
        self._tdp_auto: bool = detected_tdp is not None

        # Seed current_watts with an idle estimate
        self._current_watts: float = config.IDLE_POWER_W

        # Back-fill hardware energy from boot with 40 % CPU assumption
        if backfill_from_boot:
            uptime_h = (time.time() - self._boot_ts) / 3600.0
            avg_w = self._estimate_watts(cpu_pct=40.0, gpu_pct=20.0 if self._has_gpu else 0.0)
            self._kwh = (avg_w * uptime_h) / 1000.0

    # ── GPU helpers ───────────────────────────────────────────────────────────

    def _detect_gpu(self) -> bool:
        if self._gputil is None:
            return False
        try:
            return len(self._gputil.getGPUs()) > 0
        except Exception:
            return False

    def _gpu_load_pct(self) -> float:
        if not self._has_gpu:
            return 0.0
        try:
            gpus = self._gputil.getGPUs()
            return (gpus[0].load * 100.0) if gpus else 0.0
        except Exception:
            return 0.0

    # ── CPU frequency scaling ─────────────────────────────────────────────────

    def _get_freq_factor(self) -> float:
        """
        Returns current_freq / max_freq (clamped 0.1–1.0).
        When the CPU is throttled (idle, power-saving), this scales TDP down
        proportionally, giving a more accurate low-load estimate.
        Falls back to 1.0 if psutil can't read frequency.
        """
        try:
            freq = psutil.cpu_freq()
            if freq and freq.max > 0:
                return max(0.1, min(freq.current / freq.max, 1.0))
        except Exception:
            pass
        return 1.0

    # ── Power estimation ──────────────────────────────────────────────────────

    def _estimate_watts(self, cpu_pct: float, gpu_pct: float) -> float:
        """
        Estimate total device wattage:
          CPU  = IDLE + (TDP - IDLE) × freq_factor × (0.3 + 0.7 × load)
          GPU  = GPU_IDLE + (GPU_TDP - GPU_IDLE) × load    [if discrete GPU]
          RAM  = fixed constant

        freq_factor scales CPU power by the current/max clock ratio,
        so idle or power-saving states reduce the estimate below full TDP.
        """
        cpu_f = max(0.0, min(cpu_pct / 100.0, 1.0))
        gpu_f = max(0.0, min(gpu_pct / 100.0, 1.0))
        freq_factor = self._get_freq_factor()

        cpu_w = config.IDLE_POWER_W + (self._tdp - config.IDLE_POWER_W) * freq_factor * (
            0.3 + 0.7 * cpu_f
        )
        gpu_w = (
            config.GPU_IDLE_W + (config.GPU_TDP_W - config.GPU_IDLE_W) * gpu_f
            if self._has_gpu else 0.0
        )
        return cpu_w + gpu_w + config.RAM_POWER_W

    # Public API

    def tick(self) -> None:
        now = time.monotonic()
        dt_h = (now - self._last_tick) / 3600.0
        self._last_tick = now
        cpu_pct = psutil.cpu_percent(interval=None)
        gpu_pct = self._gpu_load_pct()
        watts = self._estimate_watts(cpu_pct, gpu_pct)
        self._current_watts = watts
        self._kwh += (watts * dt_h) / 1000.0

    @property
    def uptime_hours(self) -> float:
        return (time.time() - self._boot_ts) / 3600.0

    @property
    def cpu_info(self) -> dict:
        return {
            "cpu_name": self._cpu_name,
            "tdp_w":    self._tdp,
            "tdp_auto": self._tdp_auto,
        }

    @property
    def currency(self) -> str:
        return self._currency

    @currency.setter
    def currency(self, val: str) -> None:
        if val in config.CURRENCY_RATES:
            self._currency = val

    def metrics(self) -> dict:
        net_gb  = _net_bytes_total() / (1024 ** 3)
        net_kwh = net_gb * config.NETWORK_KWH_PER_GB
        hw_kwh    = self._kwh
        total_kwh = hw_kwh + net_kwh
        uptime_h  = self.uptime_hours

        rate = config.CURRENCY_RATES.get(self._currency, 0.28)
        cost = total_kwh * rate

        return {
            "kwh_hw":    hw_kwh,
            "kwh_net":   net_kwh,
            "kwh_total": total_kwh,
            "watts":     self._current_watts,
            "cost":      cost,
            "water_l":   total_kwh * config.WATER_FACTOR_L_PER_KWH,
            "waste_g":   (total_kwh * config.WASTE_POWER_G_PER_KWH)
                         + (uptime_h * config.WASTE_EWASTE_G_PER_HOUR),
            "net_gb":    net_gb,
            "has_gpu":   self._has_gpu,
        }


def fmt_kwh(kwh: float) -> str:
    if kwh < 0.001:
        return f"{kwh * 1000:.2f} Wh"
    return f"{kwh:.4f} kWh"

def fmt_cost(amount: float, currency: str = "EUR") -> str:
    symbol = config.CURRENCY_SYMBOLS.get(currency, "€")
    if currency == "KRW":
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
