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
* [Getting Started](#getting-started)
* [Compiling Standalone Executable (.exe / .app)](#compiling-standalone-executable-exe--app)
* [Project Structure](#project-structure)

---

## Features

1. **Real-Time Power Sampling (Watts)**
   - Estimates system wattage dynamically by combining active CPU loads (adjusted using auto-detected WMI TDP on Windows), discrete GPU load (via GPUtil), and static baseline RAM power.
2. **Environmental Metrology**
   - Calculates electricity costs, virtual water consumption, solid power-grid waste, e-waste amortization, and network infrastructure energy costs.
3. **Geo-IP Location & Global Currency Auto-Detection**
   - Automatically detects your country on startup to map your local currency symbol and average residential electricity rate from a database of 26 major countries.
4. **9-Language Translation & Localized Currencies**
   - Supports English, Korean, German, Spanish, French, Japanese, Chinese, Portuguese, and Vietnamese. All menus and currency names dynamically translate on the fly.
5. **Interactive System Tray Settings**
   - Right-click the leaf icon to toggle visibility, pin the overlay to any screen corner, switch manual/auto currencies, or change language settings.

---

## Calculation Methodology & Coefficients

EcoTracker calculates your environmental footprint using the following structured formulas:

### 1. Energy Consumption ($E_{\text{total}}$)
\[E_{\text{total}} = E_{\text{hardware}} + E_{\text{network}}\]

* **Hardware Power ($P_{\text{hw}}$)**:
  \[P_{\text{hw}} = P_{\text{cpu}} + P_{\text{gpu}} + P_{\text{ram}}\]
  - **CPU Power ($P_{\text{cpu}}$)**:
    \[P_{\text{cpu}} = P_{\text{cpu\_idle}} + \left(\frac{U_{\text{cpu}}}{100}\right) \times (TDP - P_{\text{cpu\_idle}})\]
    - $P_{\text{cpu\_idle}}$: CPU idle baseline power consumption (fixed at $8.0\text{ W}$).
    - $U_{\text{cpu}}$: Current CPU load percentage ($0\% - 100\%$).
    - $TDP$: Thermal Design Power (auto-detected via WMI on Windows or defaults to $45.0\text{ W}$).
  - **GPU Power ($P_{\text{gpu}}$)**: GPU idle power ($5.0\text{ W}$) + load-scaled TDP (sampled via `GPUtil` if a discrete GPU is present).
  - **RAM Power ($P_{\text{ram}}$)**: Fixed RAM power estimate ($3.0\text{ W}$).
* **Network Infrastructure Energy ($E_{\text{network}}$)**:
  \[E_{\text{network}} = D_{\text{net}} \times 0.06 \text{ kWh/GB}\]
  - $D_{\text{net}}$: Cumulative network data traffic in GB.
  - $0.06\text{ kWh/GB}$: Indirect energy consumption coefficient of routing infrastructure (Source: IEA / Shift Project).

---

### 2. Electricity Cost ($\text{Cost}$)
\[\text{Cost} = E_{\text{total}} \times \text{Rate}_{\text{local}}\]

* $\text{Rate}_{\text{local}}$: Electricity rate per kWh loaded dynamically from `tracker/rates.json` based on IP location or manual selection (e.g. $150.0\text{ ₩/kWh}$ for South Korea, $0.17\text{ \$/kWh}$ for United States, $0.38\text{ €/kWh}$ for Germany).

---

### 3. Water Footprint ($W$)
\[W = E_{\text{total}} \times 1.8 \text{ L/kWh}\]

* $1.8\text{ L/kWh}$: Virtual water evaporated per kWh generated due to thermal power-plant cooling requirements (Source: Global thermal plant cooling averages).

---

### 4. Solid Waste & E-Waste ($M_{\text{waste}}$)
\[M_{\text{waste}} = M_{\text{power}} + M_{\text{e-waste}}\]

* **Power Generation Solid Waste ($M_{\text{power}}$)**:
  \[M_{\text{power}} = E_{\text{total}} \times 35.0 \text{ g/kWh}\]
  - $35.0\text{ g/kWh}$: Solid waste (fly ash, slag) produced per kWh generated (Source: European grid mix average).
* **Device E-Waste Amortization ($M_{\text{e-waste}}$)**:
  \[M_{\text{e-waste}} = \text{Uptime (hours)} \times 0.17 \text{ g/h}\]
  - $0.17\text{ g/h}$: Amortization rate based on a standard $2.0\text{ kg}$ laptop over a 4-year lifecycle, assuming 8 hours of usage per day.

---

### 5. Network Data Traffic ($D_{\text{net}}$)
\[D_{\text{net}} = \frac{\text{Bytes}_{\text{sent}} + \text{Bytes}_{\text{received}}}{1024^3}\]

* $\text{Bytes}_{\text{sent}} / \text{Bytes}_{\text{received}}$: Cumulative network data traffic since the application started, polled using `psutil.net_io_counters()`.

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
│   ├── rates.json        # Global utility rates database for 26 countries
│   ├── geo.py            # Asynchronous Geo-IP location background detector
│   └── engine.py         # Hardware power sampling & metrics engine
├── ui/
│   ├── icons.py          # Google Material icons glyphs loader
│   ├── overlay.py        # Frameless floating overlay panel (Tkinter)
│   └── tray.py           # Multi-language system tray daemon (9 languages)
├── config.py             # Custom currency mappings, TDP defaults, and UI colors
├── install.bat / .sh     # One-click installation scripts
└── install.command       # One-click macOS Finder installation script
```
