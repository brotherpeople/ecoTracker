"""
ui/icons.py
-----------
Material Icons font loader for tkinter.

Downloads MaterialIcons-Regular.ttf on first run,
registers it with Windows GDI, and exposes codepoint constants.

=== Changing icons ===
1. Browse https://fonts.google.com/icons and find an icon.
2. Click it and note the Codepoint value in the right panel (e.g. e263).
3. Update the matching ICON_* constant below: chr(0xe263)
4. Save and restart the app.
"""

from __future__ import annotations

import ctypes
import platform
import urllib.request
from pathlib import Path

_FONT_FILE = Path(__file__).parent / "MaterialIcons-Regular.ttf"
_FONT_URL = (
    "https://github.com/google/material-design-icons"
    "/raw/master/font/MaterialIcons-Regular.ttf"
)
FONT_NAME = "Material Icons"

# Change the hex value inside chr() to swap an icon.
ICON_BOLT   = chr(0xEA0B)  # bolt
ICON_EURO   = chr(0xE926)  # user-selected
ICON_WATER  = chr(0xE91C)  # user-selected
ICON_DELETE = chr(0xE872)  # delete
ICON_WIFI   = chr(0xE63E)  # wifi

_state: dict = {"loaded": False, "font": "Segoe UI Emoji"}


def ensure_font() -> str:
    """Download and register the font if needed. Returns the font family name."""
    if _state["loaded"]:
        return _state["font"]

    if not _FONT_FILE.exists():
        try:
            print(f"[EcoTracker] Downloading Material Icons font -> {_FONT_FILE}")
            urllib.request.urlretrieve(_FONT_URL, str(_FONT_FILE))
        except Exception as exc:
            print(f"[EcoTracker] Font download failed: {exc}. Using emoji fallback.")
            _state["loaded"] = True
            return _state["font"]

    if platform.system() == "Windows":
        try:
            res = ctypes.windll.gdi32.AddFontResourceW(str(_FONT_FILE))
            if res > 0:
                ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
                _state["font"] = FONT_NAME
                _state["loaded"] = True
                return FONT_NAME
            else:
                print("[EcoTracker] AddFontResourceW returned 0 -- using emoji fallback.")
        except Exception as exc:
            print(f"[EcoTracker] Font registration failed: {exc}. Using emoji fallback.")

    _state["loaded"] = True
    return _state["font"]
