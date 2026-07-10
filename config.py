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
RAM_POWER_W: float = 3.0    # fixed RAM power estimate (DDR4/5 average)

# GPU (discrete) – only used if GPUtil detects a GPU
GPU_IDLE_W: float = 5.0
GPU_TDP_W: float = 80.0

# ── Electricity pricing & Currencies ──────────────────
# Rates per kWh
CURRENCY_RATES: dict[str, float] = {
    "EUR": 0.28,   # EUR / kWh
    "USD": 0.16,   # USD / kWh (US residential average ~16 cents)
    "KRW": 150.0,  # KRW / kWh (KR residential average ~150 Won)
}
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
# Default rate fallback
ELECTRICITY_RATE_EUR: float = 0.28  # EUR / kWh

# ── Environmental conversion factors ─────────
# Water: litres consumed per kWh (thermal-plant cooling average)
WATER_FACTOR_L_PER_KWH: float = 1.8

# Waste:
#   Power-generation solid waste (coal ash, slag) – EU grid mix
WASTE_POWER_G_PER_KWH: float = 35.0
#   E-waste amortised over device lifetime
#   Assumes 2 kg laptop, 4-year life, 8 h/day  →  ~0.17 g/h
WASTE_EWASTE_G_PER_HOUR: float = 0.17

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
