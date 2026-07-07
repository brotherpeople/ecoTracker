"""
ui/overlay.py
─────────────
Frameless, always-on-top, semi-transparent tkinter window
that follows the mouse cursor and displays live eco-metrics.

Windows-specific trick: WS_EX_TRANSPARENT makes the overlay
fully click-through so it never interferes with normal use.

Delta display: each row shows a 10-second rolling increment in
dimmed text on the right edge, e.g. "803.1 mL   (+0.2mL)".
"""

from __future__ import annotations

import ctypes
import platform
import tkinter as tk
from collections import deque

import config
from tracker.engine import Engine, fmt_kwh, fmt_cost, fmt_water, fmt_waste, fmt_net
from ui.icons import (
    ensure_font,
    ICON_BOLT,
    ICON_EURO,
    ICON_WATER,
    ICON_DELETE,
    ICON_WIFI,
)

# How many seconds of history to use for the rolling delta
_DELTA_WINDOW = 10


# ──────────────────────────────────────────────────────────────────────────────
#  Delta formatting helpers
# ──────────────────────────────────────────────────────────────────────────────


def _fmt_delta_kwh(delta: float) -> str:
    if delta <= 0:
        return ""
    wh = delta * 1000.0
    if wh < 0.01:
        return f"(+{wh * 1000:.1f}mWh)"
    return f"(+{wh:.2f}Wh)"


def _fmt_delta_cost(delta: float, currency: str = "EUR") -> str:
    if delta <= 0:
        return ""
    symbol = config.CURRENCY_SYMBOLS.get(currency, "€")
    if currency == "KRW":
        if delta < 0.1:
            return f"(+{symbol}{delta:.3f})"
        if delta < 1.0:
            return f"(+{symbol}{delta:.2f})"
        return f"(+{symbol}{delta:.1f})"
    else:
        cents = delta * 100.0
        if cents < 0.001:
            return ""
        return f"(+{cents:.4f}¢)"


def _fmt_delta_water(delta: float) -> str:
    if delta <= 0:
        return ""
    ml = delta * 1000.0
    if ml < 0.01:
        return f"(+{ml * 1000:.0f}μL)"
    return f"(+{ml:.2f}mL)"


def _fmt_delta_waste(delta: float) -> str:
    if delta <= 0:
        return ""
    if delta < 0.001:
        return f"(+{delta * 1000:.2f}mg)"
    return f"(+{delta:.3f}g)"


def _fmt_delta_net(delta: float) -> str:
    if delta <= 0:
        return ""
    mb = delta * 1000.0
    if mb < 0.001:
        return ""
    if mb < 1.0:
        return f"(+{mb * 1000:.0f}KB)"
    return f"(+{mb:.2f}MB)"


_DELTA_FMTS = [
    _fmt_delta_kwh,
    _fmt_delta_cost,
    _fmt_delta_water,
    _fmt_delta_waste,
    _fmt_delta_net,
]

_METRIC_KEYS = ["kwh_total", "cost", "water_l", "waste_g", "net_gb"]



# ──────────────────────────────────────────────────────────────────────────────
#  Overlay window
# ──────────────────────────────────────────────────────────────────────────────


class Overlay:
    """
    A small floating widget that tracks the mouse cursor and shows
    five live environmental metrics with 10-second rolling deltas.

    Usage:
        root = tk.Tk()
        engine = Engine()
        overlay = Overlay(root, engine)
        root.mainloop()
    """

    _TITLE = "EcoTracker_Overlay"

    # Row layout  [Material Icons codepoint, accent colour]
    # Icons: Bolt · Euro Symbol · Humidity High · Delete · Wifi
    _ROWS = [
        (ICON_BOLT, config.COLOR_ELEC),
        (ICON_EURO, config.COLOR_COST),
        (ICON_WATER, config.COLOR_WATER),
        (ICON_DELETE, config.COLOR_WASTE),
        (ICON_WIFI, config.COLOR_NET),
    ]

    def __init__(self, root: tk.Tk, engine: Engine) -> None:
        self.root = root
        self.engine = engine

        self._text_ids: list[int] = []  # canvas item ids for value labels
        self._delta_ids: list[int] = []  # canvas item ids for delta labels

        # Rolling history of metric snapshots for delta computation
        self._history: deque[dict] = deque(maxlen=_DELTA_WINDOW + 1)

        # Corner pin state: None = follow mouse, else "TL"/"TR"/"BL"/"BR"
        self._pinned_corner: str | None = None
        self._CORNER_MARGIN = 10  # pixels from screen edge when pinned

        # Load Material Icons font (downloads on first run if absent)
        self._icon_font = ensure_font()

        self._setup_window()
        self._build_canvas()
        self._make_click_through()
        self._start_loops()

    # ── window setup ─────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.root.title(self._TITLE)
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", config.OVERLAY_ALPHA)
        self.root.configure(bg=config.COLOR_BG)
        self.root.geometry(f"{config.OVERLAY_WIDTH}x{config.OVERLAY_HEIGHT}+100+100")
        self.root.update_idletasks()
        self.root.deiconify()

    # ── canvas & visual elements ─────────────────────────────────────────────

    def _build_canvas(self) -> None:
        W = config.OVERLAY_WIDTH
        H = config.OVERLAY_HEIGHT

        self.canvas = tk.Canvas(
            self.root,
            width=W,
            height=H,
            bg=config.COLOR_BG,
            highlightthickness=0,
        )
        self.canvas.pack()



        # Five metric rows  (tight, compact layout)
        ROW_H = 16  # vertical spacing between rows
        START_Y = 12  # y of first row centre
        ICON_X = 11  # icon centre x
        VAL_X = 22  # value text left edge
        DELTA_X = W - 5  # delta text right edge

        for i, (icon, accent) in enumerate(self._ROWS):
            cy = START_Y + i * ROW_H

            # Material Icon glyph — coloured with each row's accent colour
            self.canvas.create_text(
                ICON_X,
                cy,
                text=icon,
                anchor="center",
                font=(self._icon_font, 11),
                fill=accent,
            )

            # Value text (left-aligned)
            tid = self.canvas.create_text(
                VAL_X,
                cy,
                text="…",
                anchor="w",
                font=("Segoe UI", 10),
                fill=config.COLOR_TEXT,
            )
            self._text_ids.append(tid)

            # Delta text (right-aligned, dimmed)
            did = self.canvas.create_text(
                DELTA_X,
                cy,
                text="",
                anchor="e",
                font=("Segoe UI", 8),
                fill=config.COLOR_DIM,
            )
            self._delta_ids.append(did)

    # ── Windows click-through ────────────────────────────────────────────────

    def _make_click_through(self) -> None:
        """
        On Windows, add WS_EX_LAYERED | WS_EX_TRANSPARENT so mouse events
        pass through the overlay to whatever is underneath.
        """
        if platform.system() != "Windows":
            return

        self.root.update_idletasks()

        # Prefer FindWindowW because GetParent can return 0 for top-level windows.
        hwnd = ctypes.windll.user32.FindWindowW(None, self._TITLE)
        if hwnd == 0:
            return

        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020

        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT,
        )

    # corner pin

    def set_pin(self, corner) -> None:
        self._pinned_corner = corner
        if corner is not None:
            self._apply_corner(corner)

    def _get_work_area(self) -> tuple[int, int, int, int]:
        """
        Return (left, top, right, bottom) of the usable desktop area,
        i.e. the screen minus taskbar / docked toolbars.
        Falls back to full screen dimensions on non-Windows or on error.
        """
        if platform.system() == "Windows":
            try:
                import ctypes.wintypes

                rect = ctypes.wintypes.RECT()
                # SPI_GETWORKAREA = 0x0030
                ctypes.windll.user32.SystemParametersInfoW(
                    0x0030, 0, ctypes.byref(rect), 0
                )
                return rect.left, rect.top, rect.right, rect.bottom
            except Exception:
                pass
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        return 0, 0, sw, sh

    def _apply_corner(self, corner: str) -> None:
        left, top, right, bottom = self._get_work_area()
        W = config.OVERLAY_WIDTH
        H = config.OVERLAY_HEIGHT
        m = self._CORNER_MARGIN
        positions = {
            "TL": (left + m, top + m),
            "TR": (right - W - m, top + m),
            "BL": (left + m, bottom - H - m),
            "BR": (right - W - m, bottom - H - m),
        }
        wx, wy = positions[corner]
        self.root.geometry(f"+{wx}+{wy}")

    # follow mouse

    def _follow_mouse(self) -> None:
        if self._pinned_corner is None:
            cx = self.root.winfo_pointerx()
            cy = self.root.winfo_pointery()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            wx = min(cx + config.OVERLAY_OFFSET_X, sw - config.OVERLAY_WIDTH - 4)
            wy = min(cy + config.OVERLAY_OFFSET_Y, sh - config.OVERLAY_HEIGHT - 4)
            if cx + config.OVERLAY_OFFSET_X + config.OVERLAY_WIDTH > sw:
                wx = cx - config.OVERLAY_WIDTH - config.OVERLAY_OFFSET_X
            if cy + config.OVERLAY_OFFSET_Y + config.OVERLAY_HEIGHT > sh:
                wy = cy - config.OVERLAY_HEIGHT - config.OVERLAY_OFFSET_Y
            self.root.geometry(f"+{wx}+{wy}")
        self.root.after(config.MOUSE_POLL_MS, self._follow_mouse)

    def _refresh_metrics(self) -> None:
        self.engine.tick()
        m = self.engine.metrics()
        self._history.append(m)
        values = [
            m["kwh_total"],
            m["cost"],
            m["water_l"],
            m["waste_g"],
            m["net_gb"],
        ]
        
        currency = self.engine.currency
        
        formatted_values = [
            fmt_kwh(values[0]),
            fmt_cost(values[1], currency),
            fmt_water(values[2]),
            fmt_waste(values[3]),
            fmt_net(values[4]),
        ]
        
        old = self._history[0] if len(self._history) > 1 else None
        for i, (tid, did, val, key) in enumerate(zip(
            self._text_ids,
            self._delta_ids,
            values,
            _METRIC_KEYS,
        )):
            self.canvas.itemconfig(tid, text=formatted_values[i])
            if old is not None:
                delta = val - old.get(key, val)
                if key == "cost":
                    self.canvas.itemconfig(did, text=_fmt_delta_cost(delta, currency))
                else:
                    self.canvas.itemconfig(did, text=_DELTA_FMTS[i](delta))
        self.root.after(config.METRICS_UPDATE_MS, self._refresh_metrics)

    def _start_loops(self) -> None:
        self.root.after(0, self._follow_mouse)
        self.root.after(0, self._refresh_metrics)
