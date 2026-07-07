"""
main.py – EcoTracker entry point
─────────────────────────────────
Launches the floating overlay and the system-tray icon.

Run with:
    pythonw main.py        (Windows, no console window)
    python  main.py        (with console – useful for debugging)
"""

import sys
import threading
import tkinter as tk

from tracker.engine import Engine
from ui.overlay import Overlay
from ui.tray import TrayIcon


def main() -> None:
    # ── 1. Create the tkinter root (hidden until overlay takes over) ──────────
    root = tk.Tk()
    # withdraw() here would permanently hide the overlay — skip it.
    # overrideredirect(True) inside Overlay already removes the title bar.

    # ── 2. Boot the energy / metrics engine ──────────────────────────────────
    engine = Engine(backfill_from_boot=True)

    # ── 3. Build the floating overlay ────────────────────────────────────────
    overlay = Overlay(root, engine)    # noqa: F841  (kept alive via root)

    def toggle_visibility(visible: bool) -> None:
        if visible:
            root.deiconify()
        else:
            root.withdraw()

    def change_currency(curr: str) -> None:
        engine.currency = curr

    # ── 4. System-tray icon (runs in its own daemon thread) ───────────────────
    tray = TrayIcon(
        on_quit=root.destroy,
        root=root,
        on_pin=overlay.set_pin,
        on_toggle_visibility=toggle_visibility,
        initial_visible=True,
        on_change_currency=change_currency,
        initial_currency="EUR",
    )
    tray_thread = threading.Thread(target=tray.run, daemon=True, name="tray")
    tray_thread.start()

    # ── 5. tkinter event loop ─────────────────────────────────────────────────
    try:
        root.mainloop()
    finally:
        tray.stop()


if __name__ == "__main__":
    main()
