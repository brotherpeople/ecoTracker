# ─────────────────────────────────────────────
#  EcoTracker – configuration
# ─────────────────────────────────────────────

# ── Device power profile ──────────────────────
# Adjust TDP_WATTS to match your device.
#   Ultrabook / thin laptop  : 15–28 W
#   Standard laptop           : 35–45 W  ← default
#   Gaming laptop             : 65–120 W
#   Desktop PC                : 65–200 W
TDP_WATTS: float = 45.0
IDLE_POWER_W: float = 8.0   # baseline consumption at 0 % CPU

# RAM power: watts per GB of installed capacity, applied to the actual
# detected RAM size (psutil.virtual_memory().total) instead of a flat guess.
# ~0.4 W/GB is corroborated by Micron's DDR4 power model and Teads
# Engineering's cloud-instance power study; Crucial's public rule of thumb
# (~3 W / 8 GB DDR3/DDR4) works out to ~0.375 W/GB, the same order.
# Source: https://medium.com/teads-engineering/estimating-aws-ec2-instances-power-consumption-c9745e347959
RAM_POWER_W_PER_GB: float = 0.4
RAM_POWER_W: float = 3.0    # fallback flat estimate if RAM size can't be read

# GPU (discrete) – only used if GPUtil detects a GPU
GPU_IDLE_W: float = 5.0
GPU_TDP_W: float = 80.0

# ── Electricity pricing & Currencies ──────────────────
# Every currency selectable in the tray menu has an entry in tracker/rates.json,
# so this only matters if rates.json itself fails to load.
FALLBACK_RATE: float = 0.28  # currency-agnostic EUR-equivalent fallback

CURRENCY_SYMBOLS: dict[str, str] = {
    "EUR": "€",
    "USD": "$",
    "KRW": "₩",
    "GBP": "£",
    "JPY": "¥",
    "CNY": "¥",
    "CAD": "$",
    "AUD": "$",
    "CHF": "CHF",
    "SEK": "kr",
    "NOK": "kr",
    "DKK": "kr",
    "NZD": "$",
    "SGD": "$",
    "BRL": "R$",
    "INR": "₹",
    "VND": "₫",
    "MXN": "$",
    "ZAR": "R",
}

# ── Environmental conversion factors ─────────
# Water: litres consumed per kWh (thermal-plant cooling average)
WATER_FACTOR_L_PER_KWH: float = 1.8

# Waste:
#   Power-generation solid waste (coal ash, slag) – EU grid mix
WASTE_POWER_G_PER_KWH: float = 35.0

#   E-waste amortised over device lifetime, split by device profile
#   (psutil.sensors_battery() distinguishes laptop vs. desktop at runtime).
#   g/h = device_mass_g / (lifespan_years * 365 * assumed_hours_per_day)
#   The 8 h/day conversion factor is a modeling assumption (not independently
#   sourced), carried over unchanged from the original single-profile constant.
#
#   Laptop: 3.5 kg (SWICO Recycling Guarantee 2006 / ecoinvent v2.0, via
#           https://ewasteguide.info/weight/), 3.7-year lifespan (Gartner
#           2024 enterprise average, via https://sobrii.io/blog/computer-lifespan-real-numbers-2026)
#           -> 3500 / (3.7*365*8) ~= 0.324 g/h
#   Desktop: 9.9 kg tower (Eugster et al. 2007) + 4.7 kg LCD monitor (SWICO/
#            ecoinvent v2.0), both via https://ewasteguide.info/weight/ = 14.6 kg,
#            4.6-year lifespan (Gartner 2024 enterprise average, same source as above)
#            -> 14600 / (4.6*365*8) ~= 1.087 g/h
WASTE_EWASTE_LAPTOP_G_PER_HOUR: float = 0.324
WASTE_EWASTE_DESKTOP_G_PER_HOUR: float = 1.087
#   Fallback if laptop/desktop can't be determined (e.g. battery status
#   unreadable) — reuses the laptop figure as the more common default.
WASTE_EWASTE_G_PER_HOUR: float = WASTE_EWASTE_LAPTOP_G_PER_HOUR

# Network: energy cost of internet infrastructure per GB transferred
# Source: IEA / Shift Project estimate (~0.06 kWh/GB)
NETWORK_KWH_PER_GB: float = 0.06

# ── UI settings ───────────────────────────────
OVERLAY_ALPHA: float = 0.50  # window transparency  (0.0–1.0)
OVERLAY_OFFSET_X: int = 6  # pixels right of cursor
OVERLAY_OFFSET_Y: int = 6  # pixels below cursor
MOUSE_POLL_MS: int = 50  # cursor-tracking interval
METRICS_UPDATE_MS: int = 1000  # metric-refresh interval

# Colours (dark-navy theme)
COLOR_BG: str = "#0f172a"
COLOR_BORDER: str = "#000000"
COLOR_TEXT: str = "#e2e8f0"
COLOR_DIM: str = "#94a3b8"
COLOR_ELEC: str  = "#facc15"  # yellow
COLOR_COST: str  = "#c084fc"  # purple
COLOR_WATER: str = "#38bdf8"  # sky-blue
COLOR_WASTE: str = "#a3e635"  # lime
COLOR_NET: str   = "#fb923c"  # orange

# Overlay dimensions (5 rows, wide enough for delta text)
OVERLAY_WIDTH: int = 165
OVERLAY_HEIGHT: int = 88
