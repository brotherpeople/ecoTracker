# EcoTracker

🌏 **Language Options**: [한국어 버전 (Korean Version)](./README_KR.md)

![EcoTracker Demonstration](./screenshot.gif)

EcoTracker is a lightweight cross-platform desktop widget that monitors your PC's real-time resource consumption and translates it into direct environmental impacts. It floats near your mouse pointer (or pins to any screen corner) in a clean, frameless, semi-transparent overlay to raise ecological awareness during daily work or gaming sessions.

---

## Table of Contents
* [Features](#features)
* [Calculation Methodology & Coefficients](#calculation-methodology--coefficients)
  * [1. Energy Consumption](#1-energy-consumption)
  * [2. Electricity Cost](#2-electricity-cost)
  * [3. Water Footprint](#3-water-footprint)
  * [4. Solid Waste & E-Waste](#4-solid-waste--e-waste)
  * [5. Network Data Traffic](#5-network-data-traffic)
* [Limitations & Known Trade-offs](#limitations--known-trade-offs)
* [Getting Started](#getting-started)
* [Compiling Standalone Executable (.exe / .app)](#compiling-standalone-executable-exe--app)
* [Project Structure](#project-structure)
* [References](#references)

---

## Features

1. **Real-Time Power Sampling (Watts)**
   - Estimates system wattage dynamically by combining active CPU loads (adjusted using auto-detected WMI TDP on Windows), discrete GPU load (via GPUtil), and RAM power scaled to your actual installed capacity.
2. **Environmental Metrology**
   - Calculates electricity costs, virtual water consumption, solid power-grid waste, e-waste amortization, and network infrastructure energy costs.
3. **Geo-IP Location & Global Currency Auto-Detection**
   - Automatically detects your currency on startup (via IP geolocation) and maps it to an average residential electricity rate from a database of 19 currencies.
4. **9-Language Translation & Localized Currencies**
   - Supports English, Korean, German, Spanish, French, Japanese, Chinese, Portuguese, and Vietnamese. All menus and currency names dynamically translate on the fly.
5. **Interactive System Tray Settings**
   - Right-click the leaf icon to toggle visibility, pin the overlay to any screen corner, switch manual/auto currencies, or change language settings.
6. **Accuracy Table & Opt-In Real Hardware Measurement**
   - Tray → *Accuracy...* opens a table showing, per metric, whether the displayed number is a real hardware/OS reading ("Measured") or a modeled estimate ("Estimated"), plus plain factual detail about what was detected. CPU and GPU rows include a permission checkbox: granting it makes the engine try to read real hardware counters instead of modeling — NVIDIA GPU power via `pynvml`, CPU package power via Linux `intel-rapl` — and pressing **Refresh** re-applies the permissions and updates the table with the outcome. Nothing is read from hardware counters unless you explicitly grant it.
   - The **Boot backfill** row is expandable: click it to reveal a small graph showing the frozen, boot-to-launch energy estimate (flat/dashed segment) next to a live, Task-Manager-style scrolling chart of real wattage sampled while the row is open. An **Include** checkbox lets you exclude the backfilled estimate from all totals.

---

## Calculation Methodology & Coefficients

EcoTracker calculates your environmental footprint using the following structured formulas:

### 1. Energy Consumption ($E_{\text{total}}$)
$$
E_{\text{total}} = E_{\text{hardware}} + E_{\text{network}}
$$

* **Hardware Power** (`P_hw`): `P_hw = P_cpu + P_gpu + P_ram`
  - **CPU Power** (`P_cpu`): `P_cpu = P_idle + (U_cpu / 100) * (TDP - P_idle)`
    - `P_idle`: CPU idle baseline power consumption (fixed at 8.0W).
    - `U_cpu`: Current CPU load percentage (0% - 100%).
    - `TDP`: Thermal Design Power, auto-detected per-OS or defaults to 45.0W — Windows (WMI), Linux (`/proc/cpuinfo`), macOS (`sysctl machdep.cpu.brand_string`).
    - This is a linear interpolation between idle and TDP wattage as a function of utilization, the same approach used by the [Cloud Carbon Footprint methodology](https://www.cloudcarbonfootprint.org/docs/methodology/) (`Average Watts = Min Watts + Utilization × (Max Watts − Min Watts)`, derived from the SPECpower_ssj2008 database) and consistent with the energy-proportionality model in Barroso & Hölzle, ["The Case for Energy-Proportional Computing"](https://www.barroso.org/publications/ieee_computer07.pdf), IEEE Computer, 2007.
    - Intel/AMD `TDP` auto-detection bands (15/28/45/65/105/125 W by CPU model-name suffix) follow Intel's official [processor number / suffix conventions](https://www.intel.com/content/www/us/en/support/articles/000058567/processors/intel-core-processors.html) and [TDP documentation](https://www.intel.com/content/www/us/en/support/articles/000055611/processors.html), and the commonly documented AMD Ryzen mobile/desktop suffix conventions (U/H/HS/X), e.g. as summarized in [SlashGear's AMD suffix explainer](https://www.slashgear.com/1695345/what-does-u-h-hs-hx-mean-amd-processors/).
    - Apple Silicon (M-series) bands (20/30/45/60 W for base/Pro/Max/Ultra) are coarse tier-based estimates, since Apple never publishes an official TDP and independent third-party power measurements are inconsistent across sources — treat these as rough ballparks, not a precise citation.
  - **GPU Power** (`P_gpu`): GPU idle power (5.0W) + load-scaled TDP (sampled via `GPUtil` if a discrete GPU is present). If GPU measurement permission is granted and an NVIDIA GPU + `pynvml` are available, real power draw (`nvmlDeviceGetPowerUsage`) is used instead of this model.
  - **RAM Power** (`P_ram`): `P_ram = RAM_installed_GB × 0.4 W/GB`, using the real installed capacity from `psutil.virtual_memory().total`. The 0.4 W/GB coefficient is corroborated by Micron's DDR4 power model and [Teads Engineering's cloud-instance power study](https://medium.com/teads-engineering/estimating-aws-ec2-instances-power-consumption-c9745e347959) (Crucial's public rule of thumb, ~3W/8GB, works out to the same order, ~0.375 W/GB).
  - **Measured vs. estimated**: by default all of the above are modeled. If CPU measurement permission is granted and the OS exposes Linux `intel-rapl`, real CPU package energy is read instead of modeled. Open tray → *Accuracy...* to see, per metric, whether the current value is measured or estimated, grant/revoke permission, and refresh.
* **Network Infrastructure Energy** (`E_network`): `E_network = D_net * 0.06 kWh/GB`
  - `D_net`: Cumulative network data traffic in GB.
  - `0.06 kWh/GB`: Indirect energy consumption coefficient of routing infrastructure (Source: IEA / Shift Project, [Aslan et al. 2017](https://doi.org/10.1111/jiec.12630) — the paper's own "2015" estimate, applied unchanged; the same paper notes intensity has roughly halved every ~2 years since 2000, so this likely overstates current-day network energy).
* **Boot-to-Launch Backfill**: energy consumed between system boot and the moment EcoTracker was launched is estimated once at startup, from real signals only, and frozen for the rest of the session:
  - CPU: uses the OS's real cumulative busy/idle time counters (`psutil.cpu_times()`) to get the actual average CPU utilization since boot — not an assumed percentage.
  - RAM: uses the real installed capacity (same as above), so its contribution is measured, not guessed.
  - GPU: excluded (0) rather than guessed, since granting GPU measurement permission before the app was even open isn't possible.
  - Tray → *Accuracy...* → **Boot backfill** row lets you inspect and exclude this estimate from all totals via an **Include** checkbox.

---

### 2. Electricity Cost ($\text{Cost}$)
$$
\text{Cost} = E_{\text{total}} \times \text{Rate}_{\text{local}}
$$

* `Rate_local`: Electricity rate per kWh loaded dynamically from `tracker/rates.json`, keyed by **currency** (not country) — e.g. 150.0 KRW/kWh, \$0.17/kWh USD, 0.33 EUR/kWh. Geo-IP detection resolves your currency directly (ipapi.co returns it natively) and the active currency (auto-detected or manually picked from the tray menu) is looked up the same way either way, so there's no ambiguity about which country's rate applies to a shared currency like EUR — the EUR rate is a simple average across the Eurozone countries previously tracked individually. This trades some per-country precision for removing that ambiguity; rates aren't kept continuously up to date.

---

### 3. Water Footprint ($W$)
$$
W = E_{\text{total}} \times 1.8 \text{ L/kWh}
$$

* `1.8 L/kWh`: Virtual water evaporated per kWh generated due to thermal power-plant cooling requirements (Source: [Torcellini, Long & Judkoff, "Consumptive Water Use for U.S. Power Production", NREL/TP-550-33905, 2003](references/Water/Consumptive%20Water%20Use%20for%20U.S.%20Power%20Production.pdf) — the paper's thermoelectric-only figure, 0.47 gal/kWh).
  - This is a single global constant and does **not** account for a country's actual generation mix. The same NREL source reports hydroelectric generation evaporates ~68 L/kWh — about 38× higher — so this figure can significantly understate the real footprint in hydro-heavy grids (e.g. Norway, Canada, Brazil) and overstate it in grids with little thermal cooling (e.g. heavily wind/solar). Building a per-country water-intensity dataset was judged out of scope for now.

---

### 4. Solid Waste & E-Waste ($M_{\text{waste}}$)
$$
M_{\text{waste}} = M_{\text{power}} + M_{\text{e-waste}}
$$

* **Power Generation Solid Waste** (`M_power`): `M_power = E_total * 35.0 g/kWh`
  - `35.0 g/kWh`: Solid waste (fly ash, slag) produced per kWh generated (Source: European grid mix average).
* **Device E-Waste Amortization** (`M_e-waste`): `M_e-waste = Uptime * G_profile`
  - `Uptime`: Hours elapsed since system boot (the app's purpose is to show resources used since boot, so sleep/idle time is intentionally included, not carved out).
  - `G_profile`: g/h amortization rate, chosen automatically by device profile — `psutil.sensors_battery()` detects a laptop (battery present) vs. desktop (no battery):
    - **Laptop** (`0.324 g/h`): 3.5 kg (SWICO Recycling Guarantee 2006 / ecoinvent v2.0, via [ewasteguide.info](https://ewasteguide.info/weight/)), 3.7-year lifespan ([Gartner 2024 enterprise average](https://sobrii.io/blog/computer-lifespan-real-numbers-2026)), assuming 8h/day → `3500g / (3.7yr × 365 × 8h)`.
    - **Desktop** (`1.087 g/h`): 9.9 kg tower (Eugster et al. 2007) + 4.7 kg LCD monitor (SWICO/ecoinvent v2.0), both via [ewasteguide.info](https://ewasteguide.info/weight/) = 14.6 kg total, 4.6-year lifespan (Gartner 2024), assuming 8h/day → `14600g / (4.6yr × 365 × 8h)`.
    - The 8h/day conversion factor itself is a carried-over modeling assumption, not independently sourced.

---

### 5. Network Data Traffic ($D_{\text{net}}$)
$$
D_{\text{net}} = \frac{\text{Bytes}_{\text{sent}} + \text{Bytes}_{\text{received}}}{1024^3}
$$

* **Bytes Sent / Bytes Received** (`Bytes_sent / Bytes_received`): Cumulative network data traffic since the application started, polled using `psutil.net_io_counters()`.

---

## Limitations & Known Trade-offs

EcoTracker prioritizes citing real sources and real hardware/OS signals over inventing numbers, but several deliberate simplifications remain. This section collects them in one place.

* **Most values are modeled, not measured, by default.** CPU and GPU power are estimated from a utilization-based model (Section 1) unless you explicitly grant permission in tray → *Accuracy...* **and** the underlying mechanism is actually available:
  - CPU real measurement requires **Linux** (`intel-rapl`). It is not possible on Windows or macOS at all — granting permission there has no effect, and the checkbox is shown disabled to make that clear.
  - GPU real measurement requires an **NVIDIA** GPU with `pynvml` installed. Non-NVIDIA GPUs, or a missing `pynvml`, mean granting permission has no effect.
* **Some model constants have no independent citation.** GPU idle/TDP (5.0W / 80.0W) is a plausible order-of-magnitude guess, not sourced. Apple Silicon TDP tiers (20/30/45/60W) are especially rough — Apple never publishes an official figure, and independent measurements disagree by up to ~3× depending on methodology.
* **The water coefficient (1.8 L/kWh) is a single global constant** based on U.S. thermoelectric plants (Section 3) and does not reflect a given country's actual generation mix. The same source reports hydroelectric generation at ~68 L/kWh — about 38× higher — so this can significantly understate the footprint in hydro-heavy grids (Norway, Canada, Brazil) and overstate it where thermal cooling is rare (heavily wind/solar grids).
* **The network coefficient (0.06 kWh/GB) is a 2015 estimate**, applied unchanged (Section 1). Its own source paper notes that transmission efficiency has roughly halved every ~2 years since 2000, so this likely overstates current-day network energy — by a potentially large factor, since over a decade has passed.
* **Electricity rates (`tracker/rates.json`) are a static, unmaintained snapshot**, keyed by currency rather than country (Section 2) to remove an ambiguity that existed when multiple countries shared one currency. The trade-off: the EUR rate is a simple average across the Eurozone countries previously tracked individually, not any specific country's real rate.
* **Geo-IP currency detection (ipapi.co) can be wrong** under VPNs, corporate proxies, or mobile carrier routing, with no built-in verification. You can always override it manually from the tray currency menu.
* **E-waste device-profile detection is a heuristic.** Laptop vs. desktop is inferred from battery presence (`psutil.sensors_battery()`), which can misclassify edge cases — e.g. a desktop reporting a UPS as a battery, or a laptop that's permanently docked and used like a desktop. The 8h/day usage-intensity conversion factor (Section 4) is also a carried-over modeling assumption, not independently sourced.
* **The boot-to-launch backfill is frozen once at startup and partially modeled.** Its CPU and RAM contributions come from real signals (`psutil.cpu_times()`, installed capacity), but the CPU portion still runs through the same modeled TDP-based wattage curve as live tracking — it's a measured *input* to a model, not a direct energy reading. Its GPU contribution is excluded entirely (treated as 0), since GPU measurement permission cannot have been granted before the app was even open.

---

## Getting Started

Double-click the installer script corresponding to your operating system. The installer will automatically copy files to standard folders, create a desktop shortcut, and register EcoTracker to start automatically on login.

To uninstall, run the corresponding uninstaller script, which will cleanly remove all directories, shortcuts, and startup tasks.

| Operating System | Installer File | Uninstaller File | Execution Instruction |
| :--- | :--- | :--- | :--- |
| **Windows** | `install.bat` | `uninstall.bat` | Double-click to run. (Requires python/pip for install) |
| **macOS** | `install.command` | `uninstall.command` | Double-click in Finder to run. |
| **Linux** | `install.sh` | `uninstall.sh` | Run in terminal. |

---

## Compiling Standalone Executable (.exe / .app)

To package EcoTracker into a single, self-contained double-clickable application with the custom green leaf icon:

### Windows (.exe)
```bash
python -m PyInstaller --noconsole --onefile --icon=ui/app.ico --add-data "ui/MaterialIcons-Regular.ttf;ui" --add-data "tracker/rates.json;tracker" --name=EcoTracker main.py
```
*(Build output saved to `dist/EcoTracker.exe`)*

### macOS (.app)
```bash
python -m PyInstaller --noconsole --onefile --icon=ui/app.png --add-data "ui/MaterialIcons-Regular.ttf:ui" --add-data "tracker/rates.json:tracker" --name=EcoTracker main.py
```

---

## Project Structure

```text
resource_consumption/
├── tracker/
│   ├── rates.json        # Electricity rates keyed by currency (19 currencies)
│   ├── geo.py            # Asynchronous Geo-IP location background detector
│   └── engine.py         # Hardware power sampling & metrics engine
├── ui/
│   ├── icons.py            # Google Material icons glyphs loader
│   ├── overlay.py          # Frameless floating overlay panel (Tkinter)
│   ├── accuracy_window.py  # Measured-vs-estimated table & permission toggles
│   └── tray.py             # Multi-language system tray daemon (9 languages)
├── config.py             # Custom currency mappings, TDP defaults, and UI colors
├── install.bat / .sh     # One-click installation scripts
└── install.command       # One-click macOS Finder installation script
```

---

## References

Papers, official documentation, and industry sources the calculation methodology (see above) is built on or corroborated by:

* Cloud Carbon Footprint, ["Methodology"](https://www.cloudcarbonfootprint.org/docs/methodology/) — CPU power linear-interpolation model (Average Watts = Min Watts + Utilization × (Max Watts − Min Watts)), derived from the SPECpower_ssj2008 database.
* Luiz André Barroso & Urs Hölzle, ["The Case for Energy-Proportional Computing"](https://www.barroso.org/publications/ieee_computer07.pdf), *IEEE Computer*, 40(12), 2007 — energy-proportionality model underlying the CPU power curve.
* Intel, [Processor Numbers, Names and Letter Suffixes](https://www.intel.com/content/www/us/en/support/articles/000058567/processors/intel-core-processors.html) and [Thermal Design Power (TDP) in Intel Processors](https://www.intel.com/content/www/us/en/support/articles/000055611/processors.html) — Intel CPU suffix-to-TDP-segment conventions.
* SlashGear, ["What Do the Letters Mean in AMD Processors?"](https://www.slashgear.com/1695345/what-does-u-h-hs-hx-mean-amd-processors/) — AMD Ryzen suffix-to-TDP-segment conventions.
* Benjamin Davy, Teads Engineering, ["Estimating AWS EC2 Instances Power Consumption"](https://medium.com/teads-engineering/estimating-aws-ec2-instances-power-consumption-c9745e347959) — RAM power-per-GB coefficient (corroborated by Micron's DDR4 power model).
* Joshua Aslan, Kieren Mayers, Jonathan G. Koomey & Chris France, ["Electricity Intensity of Internet Data Transmission: Untangling the Estimates"](https://doi.org/10.1111/jiec.12630), *Journal of Industrial Ecology*, 22(4), 2017 (local copy: [`references/Network/Electricity Intensity of Internet Data Transmission - Untangling the Estimates.pdf`](references/Network/Electricity%20Intensity%20of%20Internet%20Data%20Transmission%20-%20Untangling%20the%20Estimates.pdf)) — network transmission energy-intensity coefficient (0.06 kWh/GB) and its stated ~2-year efficiency-halving trend.
* Paul Torcellini, Nicholas Long & Ron Judkoff, ["Consumptive Water Use for U.S. Power Production"](references/Water/Consumptive%20Water%20Use%20for%20U.S.%20Power%20Production.pdf), NREL/TP-550-33905, National Renewable Energy Laboratory, 2003 — thermoelectric (and, for comparison, hydroelectric) water-consumption-per-kWh figures.
* [ewasteguide.info](https://ewasteguide.info/weight/) (StEP Initiative), citing Eugster et al. (2007) and the SWICO Recycling Guarantee 2006 / ecoinvent v2.0 database — laptop, desktop, and LCD monitor mass figures used for e-waste amortization.
* sobrii.io, ["How Long Does a Business Laptop Really Last? (2026 Data)"](https://sobrii.io/blog/computer-lifespan-real-numbers-2026), citing Gartner (2024) — laptop and desktop device-lifespan averages used for e-waste amortization.
