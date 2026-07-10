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
from tracker.geo import GeoDetector
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

    def toggle_auto_currency(use_auto: bool) -> None:
        engine.use_auto = use_auto
        if use_auto and engine.detected_currency:
            engine.currency = engine.detected_currency
            tray.set_currency(engine.detected_currency, True)

    def on_geo_detected(country_code: str, currency_code: str) -> None:
        def _apply():
            engine.apply_detected_location(country_code, currency_code)
            if engine.detected_currency:
                tray.set_detected_currency(engine.detected_currency)
                if engine.use_auto:
                    tray.set_currency(engine.detected_currency, True)
        root.after(0, _apply)

    # ── 4. System-tray icon (runs in its own daemon thread) ───────────────────
    tray = TrayIcon(
        on_quit=root.destroy,
        root=root,
        on_pin=overlay.set_pin,
        on_toggle_visibility=toggle_visibility,
        initial_visible=True,
        on_change_currency=change_currency,
        initial_currency="EUR",
        on_toggle_auto_currency=toggle_auto_currency,
        initial_use_auto=True,
    )
    tray_thread = threading.Thread(target=tray.run, daemon=True, name="tray")
    tray_thread.start()

    # ── 5. Run Geo-IP location background detector ───────────────────────────
    detector = GeoDetector(callback=on_geo_detected)
    detector.start()

    # ── 6. tkinter event loop ─────────────────────────────────────────────────
    try:
        root.mainloop()
    finally:
        tray.stop()


if __name__ == "__main__":
    main()
