"""
ui/tray.py
──────────
System-tray icon (bottom-right taskbar area).
Right-click → menu with Settings stub and Quit.
"""

from __future__ import annotations

import threading
from typing import Callable

from PIL import Image, ImageDraw
import pystray


def _make_icon_image(size: int = 64) -> Image.Image:
    """
    Generate a simple tray icon: dark circle with a green leaf shape.
    No external image file required.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    pad = 4
    draw.ellipse([pad, pad, size - pad, size - pad], fill="#0f172a")

    # Outer ring
    draw.ellipse(
        [pad, pad, size - pad, size - pad],
        outline="#4ade80",
        width=3,
    )

    # Lightning bolt  ⚡  drawn as a simple polygon
    cx, cy = size // 2, size // 2
    bolt = [
        (cx + 3, cy - 14),
        (cx - 3, cy - 2),
        (cx + 4, cy - 2),
        (cx - 3, cy + 14),
        (cx + 2, cy + 2),
        (cx - 5, cy + 2),
    ]
    draw.polygon(bolt, fill="#facc15")

    return img


class TrayIcon:
    """
    Wraps a pystray.Icon so it can run in a background daemon thread.

    Parameters
    ----------
    on_quit  : callable        – called on the main thread via root.after.
    root     : tk.Tk           – needed to schedule callbacks safely.
    on_toggle_visibility : callable(bool) – called with visibility state.
    initial_visible : bool     – initial visibility state of the overlay.
    on_change_currency : callable(str)   – called with selected currency code.
    initial_currency : str     – initial currency code (EUR, USD, KRW).
    on_toggle_auto_currency : callable(bool) – called when toggling auto-detection mode.
    initial_use_auto : bool     – initial state of auto-detection mode.
    """

    def __init__(
        self,
        on_quit: Callable,
        root,
        on_pin: Callable | None = None,
        on_toggle_visibility: Callable[[bool], None] | None = None,
        initial_visible: bool = True,
        on_change_currency: Callable[[str], None] | None = None,
        initial_currency: str = "EUR",
        on_toggle_auto_currency: Callable[[bool], None] | None = None,
        initial_use_auto: bool = True,
    ) -> None:
        self._root   = root
        self._on_pin = on_pin
        self._on_toggle_visibility = on_toggle_visibility
        self._visible = initial_visible
        self._on_change_currency = on_change_currency
        self._currency = initial_currency
        self._on_toggle_auto_currency = on_toggle_auto_currency
        self._use_auto = initial_use_auto
        self._detected_currency: str | None = None

        # Pin submenu
        def _pin(corner):
            def _cb(icon, item):
                if self._on_pin:
                    self._root.after(0, lambda: self._on_pin(corner))
            return _cb

        def _toggle_visible(icon, item):
            self._visible = not self._visible
            if self._on_toggle_visibility:
                self._root.after(0, lambda: self._on_toggle_visibility(self._visible))

        # Currency actions
        def _set_auto(icon, item):
            self._use_auto = True
            if self._on_toggle_auto_currency:
                self._root.after(0, lambda: self._on_toggle_auto_currency(True))

        def _set_currency(curr):
            def _cb(icon, item):
                self._currency = curr
                self._use_auto = False
                if self._on_toggle_auto_currency:
                    self._root.after(0, lambda: self._on_toggle_auto_currency(False))
                if self._on_change_currency:
                    self._root.after(0, lambda: self._on_change_currency(curr))
            return _cb

        pin_submenu = pystray.Menu(
            pystray.MenuItem("↖ Top-Left",     _pin("TL")),
            pystray.MenuItem("↗ Top-Right",    _pin("TR")),
            pystray.MenuItem("↙ Bottom-Left",  _pin("BL")),
            pystray.MenuItem("↘ Bottom-Right", _pin("BR")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕ Follow mouse", _pin(None)),
        )

        currency_submenu = pystray.Menu(
            pystray.MenuItem(
                lambda item: f"Auto: {self._detected_currency}" if self._detected_currency else "Auto (Detecting...)",
                _set_auto,
                checked=lambda item: self._use_auto
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("₩ KRW (원)",  _set_currency("KRW"), checked=lambda item: not self._use_auto and self._currency == "KRW", radio=True),
            pystray.MenuItem("$ USD (달러)", _set_currency("USD"), checked=lambda item: not self._use_auto and self._currency == "USD", radio=True),
            pystray.MenuItem("€ EUR (유로)", _set_currency("EUR"), checked=lambda item: not self._use_auto and self._currency == "EUR", radio=True),
        )

        menu = pystray.Menu(
            pystray.MenuItem("EcoTracker", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Show Overlay",
                _toggle_visible,
                checked=lambda item: self._visible
            ),
            pystray.MenuItem("Pin to corner", pin_submenu),
            pystray.MenuItem("Currency", currency_submenu),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

        self._icon = pystray.Icon(
            "EcoTracker",
            icon=_make_icon_image(),
            title="EcoTracker – running",
            menu=menu,
        )
        self._on_quit = on_quit

    def run(self) -> None:
        """Blocking call – run inside a daemon thread."""
        self._icon.run()

    def stop(self) -> None:
        self._icon.stop()

    def set_detected_currency(self, curr: str) -> None:
        self._detected_currency = curr

    def set_currency(self, curr: str, use_auto: bool) -> None:
        self._currency = curr
        self._use_auto = use_auto

    def _quit(self, icon, item) -> None:
        icon.stop()
        # Schedule quit on the tkinter main thread
        self._root.after(0, self._on_quit)
