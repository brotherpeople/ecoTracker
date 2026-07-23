import urllib.request
import json
import threading
from typing import Callable

class GeoDetector:
    """
    Background IP location detector.
    Fetches location data asynchronously using ipapi.co.
    """
    def __init__(self, callback: Callable[[str], None]) -> None:
        """
        Parameters
        ----------
        callback : Callable[[str], None]
            Called with (currency_code) when location is detected.
        """
        self._callback = callback

    def start(self) -> None:
        """Starts the background detection thread."""
        thread = threading.Thread(target=self._run, daemon=True, name="geo-detector")
        thread.start()

    def _run(self) -> None:
        try:
            # Using ipapi.co free JSON API
            url = "https://ipapi.co/json/"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    currency = data.get("currency")
                    if currency:
                        self._callback(currency)
        except Exception as exc:
            # Fallback if offline or API limits reached
            print(f"[EcoTracker] Geo-IP detection failed: {exc}")
