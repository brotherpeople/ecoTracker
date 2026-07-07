# 🌱 EcoTracker

🌏 **Language Options**: [한국어 버전 (Korean Version)](./README_KR.md)

![EcoTracker Demonstration](./screenshot.gif)

EcoTracker is a lightweight desktop widget that monitors your PC's real-time resource consumption and translates it into direct environmental impacts, such as indirect carbon footprints, water consumption, solid waste generation, and network infrastructure energy costs.

Featuring a clean, frameless, semi-transparent overlay that floats near your mouse pointer (or pins to any screen corner), it offers a constant and subtle awareness of your computing environmental footprint during daily work or gaming sessions.

---

## ✨ Features

1. **Real-Time Power Estimation (Watts)**
   - Estimates overall system wattage in real time by sampling CPU load & frequency scaling, GPU utilization (via GPUtil), and adding a baseline RAM power consumption.
   - For Windows users, it reads CPU models via the WMI API to automatically detect and scale according to thermal design power (TDP) guidelines.

2. **Environmental Impact Metrology**
   - ⚡ **Energy Consumption**: Displays total hardware + network infrastructure energy consumption (in Wh / kWh).
   - 💶 **Electricity Cost**: Calculates electricity cost based on the active currency rate.
   - 💧 **Water Footprint**: Computes virtual water consumed (for power-plant cooling) per kWh generated (in mL / L).
   - ♻️ **Waste Output**: Combines solid power-grid waste (coal ash/slag) and device e-waste amortized over a standard 4-year lifecycle (in mg / g / kg).
   - 🌐 **Network Cost**: Converts network traffic bytes (via psutil) into equivalent infrastructure transmission energy (in MB / GB).

3. **10-Second Rolling Delta**
   - Each metric displays a dimmed rolling increment representing changes over the last 10 seconds (e.g., `+0.2mL`). This highlights how resource-intensive tasks immediately affect your footprint.

4. **Interactive System Tray Icon**
   - Right-click the green leaf icon in the Windows taskbar system tray to:
     - **Toggle Visibility**: Check or uncheck `Show Overlay` to display or hide the widget.
     - **Pin to Corner**: Affix the overlay to any screen corner (↖ Top-Left, ↗ Top-Right, ↙ Bottom-Left, ↘ Bottom-Right) or let it follow the mouse (`Follow mouse`).
     - **Select Currency**: Switch cost calculations and symbols on the fly between **EUR (€)**, **USD ($)**, and **KRW (₩)**.

5. **Cross-Platform Compatibility**
   - Standard dependencies fail-safes are applied so that non-Windows platforms (macOS / Linux) install successfully without throwing setup errors for Windows-specific WMI components.

---

## 🚀 Getting Started

### Windows (Quick Start)

1. **Install Dependencies**
   - Double-click `install.bat` to install the required Python libraries.
   
2. **Run the App**
   - Double-click `run.bat` or run the compiled `EcoTracker.exe` (if built). The widget will launch silently in the background, and the leaf icon will appear in the system tray.

### macOS (Quick Start)

1. **Install Dependencies**
   - Open terminal and run:
     ```bash
     pip install -r requirements.txt
     ```
2. **Run the App**
   - Double-click `EcoTracker.command` in Finder to launch.
   - *Note: On first launch, macOS security might prevent it from running. If so, open terminal, navigate to the folder, and run `chmod +x EcoTracker.command` to grant execution permissions, or right-click the script in Finder and choose "Open".*

### Linux / Manual Run

1. **Install Dependencies**
   - Run the following in your terminal:
     ```bash
     pip install -r requirements.txt
     ```
     *(Windows-only libraries like `wmi` are ignored on macOS/Linux environments.)*

2. **Run the App**
   - Execute the main entry point:
     ```bash
     python main.py
     ```

---

## 📦 Building Standalone Executable (.exe / .app)

To make EcoTracker look and feel like a native application with its own green leaf icon, you can compile it.

### Windows (.exe)
1. Install PyInstaller if you haven't already:
   ```bash
   pip install pyinstaller
   ```
2. Compile:
   ```bash
   python -m PyInstaller --noconsole --onefile --icon=ui/app.ico --add-data "ui/MaterialIcons-Regular.ttf;ui" --name=EcoTracker main.py
   ```
3. Once the build completes, find your executable at `dist/EcoTracker.exe`. You can move it to the root folder or anywhere and double-click to run it.

### macOS (.app App Bundle)
If you are on macOS, you can build a native double-clickable `.app` application bundle:
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Compile:
   ```bash
   python -m PyInstaller --noconsole --onefile --icon=ui/app.png --add-data "ui/MaterialIcons-Regular.ttf:ui" --name=EcoTracker main.py
   ```
   *(Note: On macOS, the separator in `--add-data` is a colon `:` instead of a semicolon `;`)*
3. Find your app bundle at `dist/EcoTracker.app`. You can drag it to your `Applications` folder!

---

## 🛠️ Configuration (`config.py`)

Open `config.py` in any text editor to customize rates and styles:

- **TDP_WATTS**: Baseline fallback CPU TDP (e.g., 15W for ultrabooks, 45W for standard laptops, 65W+ for desktops).
- **CURRENCY_RATES**: Configure per-kWh rates for EUR, USD, and KRW to match your local utility pricing.
- **OVERLAY_ALPHA**: Adjust transparency (from `0.0` fully transparent to `1.0` opaque).
- **COLOR_\***: Tailor background, borders, and text accents for each environmental metric.

---

## 📂 Project Structure

```text
resource_consumption/
├── tracker/
│   ├── __init__.py
│   └── engine.py       # Power sampling & environmental metrology engine
├── ui/
│   ├── __init__.py
│   ├── icons.py        # Google Material Design icon loader & glyph mappings
│   ├── overlay.py      # Tkinter frameless floating overlay panel
│   ├── tray.py         # System tray daemon & right-click menu options
│   ├── app.ico         # Custom Windows application icon (.ico)
│   ├── app.png         # High-resolution macOS application icon (.png)
│   └── MaterialIcons-Regular.ttf # Embedded icon font file
├── config.py           # Currency rates, power profiling, and UI color configuration
├── requirements.txt    # Python package dependencies (with win32 environment markers)
├── install.bat         # Batch script for dependency installation on Windows
├── run.bat             # Batch script to run the app silently on Windows
├── EcoTracker.command  # Double-clickable startup script for macOS Finder
├── EcoTracker.exe      # Standalone compiled Windows application (new)
├── .gitignore          # Git exclusion config
└── README.md           # Documentation (This file)
```
