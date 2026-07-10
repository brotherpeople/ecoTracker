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


# ── Translation System ────────────────────────────────────────────────────────
TRANSLATIONS: dict[str, dict[str, str]] = {
    "EN": {
        "show_overlay": "Show Overlay",
        "pin_to_corner": "Pin to corner",
        "top_left": "↖ Top-Left",
        "top_right": "↗ Top-Right",
        "bottom_left": "↙ Bottom-Left",
        "bottom_right": "↘ Bottom-Right",
        "follow_mouse": "✕ Follow mouse",
        "currency": "Currency",
        "auto_detecting": "Auto (Detecting...)",
        "auto_detected": "Auto: {}",
        "language": "Language",
        "quit": "Quit",
        "tooltip": "EcoTracker – running",
    },
    "KR": {
        "show_overlay": "오버레이 표시",
        "pin_to_corner": "화면 모퉁이에 고정",
        "top_left": "↖ 좌측 상단",
        "top_right": "↗ 우측 상단",
        "bottom_left": "↙ 좌측 하단",
        "bottom_right": "↘ 우측 하단",
        "follow_mouse": "✕ 마우스 따라가기",
        "currency": "화폐 단위",
        "auto_detecting": "자동 감지 중...",
        "auto_detected": "자동 감지: {}",
        "language": "언어 설정",
        "quit": "종료",
        "tooltip": "EcoTracker – 실행 중",
    },
    "DE": {
        "show_overlay": "Overlay anzeigen",
        "pin_to_corner": "An Ecke anheften",
        "top_left": "↖ Oben links",
        "top_right": "↗ Oben rechts",
        "bottom_left": "↙ Unten links",
        "bottom_right": "↘ Unten rechts",
        "follow_mouse": "✕ Maus folgen",
        "currency": "Währung",
        "auto_detecting": "Auto (Erkennung...)",
        "auto_detected": "Auto: {}",
        "language": "Sprache",
        "quit": "Beenden",
        "tooltip": "EcoTracker – läuft",
    },
    "ES": {
        "show_overlay": "Mostrar superposición",
        "pin_to_corner": "Fijar en la esquina",
        "top_left": "↖ Arriba izquierda",
        "top_right": "↗ Arriba derecha",
        "bottom_left": "↙ Abajo izquierda",
        "bottom_right": "↘ Abajo derecha",
        "follow_mouse": "✕ Seguir al ratón",
        "currency": "Moneda",
        "auto_detecting": "Auto (Detectando...)",
        "auto_detected": "Auto: {}",
        "language": "Idioma",
        "quit": "Salir",
        "tooltip": "EcoTracker – ejecutándose",
    },
    "FR": {
        "show_overlay": "Afficher l'overlay",
        "pin_to_corner": "Épingler au coin",
        "top_left": "↖ En haut à gauche",
        "top_right": "↗ En haut à droite",
        "bottom_left": "↙ En bas à gauche",
        "bottom_right": "↘ En bas à droite",
        "follow_mouse": "✕ Suivre la souris",
        "currency": "Devise",
        "auto_detecting": "Auto (Détection...)",
        "auto_detected": "Auto : {}",
        "language": "Langue",
        "quit": "Quitter",
        "tooltip": "EcoTracker – en cours d'exécution",
    },
    "JP": {
        "show_overlay": "オーバーレイを表示",
        "pin_to_corner": "コーナーに固定",
        "top_left": "↖ 左上",
        "top_right": "↗ 右上",
        "bottom_left": "↙ 左下",
        "bottom_right": "↘ 右下",
        "follow_mouse": "✕ マウスに追従",
        "currency": "通貨",
        "auto_detecting": "自動検出中...",
        "auto_detected": "自動検出: {}",
        "language": "言語設定",
        "quit": "終了",
        "tooltip": "EcoTracker – 実行中",
    },
    "CN": {
        "show_overlay": "显示悬浮窗",
        "pin_to_corner": "固定在角落",
        "top_left": "↖ 左上角",
        "top_right": "↗ 右上角",
        "bottom_left": "↙ 左下角",
        "bottom_right": "↘ 右下角",
        "follow_mouse": "✕ 跟随鼠标",
        "currency": "货币单位",
        "auto_detecting": "自动检测中...",
        "auto_detected": "自动检测: {}",
        "language": "语言设置",
        "quit": "退出",
        "tooltip": "EcoTracker – 正在运行",
    },
    "PT": {
        "show_overlay": "Mostrar sobreposição",
        "pin_to_corner": "Fixar no canto",
        "top_left": "↖ Canto superior esquerdo",
        "top_right": "↗ Canto superior direito",
        "bottom_left": "↙ Canto inferior esquerdo",
        "bottom_right": "↘ Canto inferior direito",
        "follow_mouse": "✕ Seguir o mouse",
        "currency": "Moeda",
        "auto_detecting": "Auto (Detectando...)",
        "auto_detected": "Auto: {}",
        "language": "Idioma",
        "quit": "Sair",
        "tooltip": "EcoTracker – executando",
    },
    "VN": {
        "show_overlay": "Hiển thị lớp phủ",
        "pin_to_corner": "Ghim vào góc",
        "top_left": "↖ Trên cùng bên trái",
        "top_right": "↗ Trên cùng bên phải",
        "bottom_left": "↙ Dưới cùng bên trái",
        "bottom_right": "↘ Dưới cùng bên phải",
        "follow_mouse": "✕ Theo con trỏ chuột",
        "currency": "Tiền tệ",
        "auto_detecting": "Tự động phát hiện...",
        "auto_detected": "Tự động: {}",
        "language": "Ngôn ngữ",
        "quit": "Thoát",
        "tooltip": "EcoTracker – đang hoạt động",
    }
}


# ── Currency Display Symbols ──────────────────────────────────────────────────
CURRENCY_SYMBOLS_SHORT: dict[str, str] = {
    "AUD": "$ AUD",
    "BRL": "R$ BRL",
    "CAD": "$ CAD",
    "CHF": "CHF CHF",
    "CNY": "¥ CNY",
    "DKK": "kr DKK",
    "EUR": "€ EUR",
    "GBP": "£ GBP",
    "INR": "₹ INR",
    "JPY": "¥ JPY",
    "KRW": "₩ KRW",
    "MXN": "$ MXN",
    "NOK": "kr NOK",
    "NZD": "$ NZD",
    "SEK": "kr SEK",
    "SGD": "$ SGD",
    "USD": "$ USD",
    "VND": "₫ VND",
    "ZAR": "R ZAR",
}


# ── Currency Localized Names ──────────────────────────────────────────────────
CURRENCY_NAMES: dict[str, dict[str, str]] = {
    "EN": {
        "AUD": "Australian Dollar", "BRL": "Brazilian Real", "CAD": "Canadian Dollar",
        "CHF": "Swiss Franc", "CNY": "Chinese Yuan", "DKK": "Danish Krone",
        "EUR": "Euro", "GBP": "British Pound", "INR": "Indian Rupee",
        "JPY": "Japanese Yen", "KRW": "Korean Won", "MXN": "Mexican Peso",
        "NOK": "Norwegian Krone", "NZD": "New Zealand Dollar", "SEK": "Swedish Krona",
        "SGD": "Singapore Dollar", "USD": "US Dollar", "VND": "Vietnamese Dong",
        "ZAR": "South African Rand",
    },
    "KR": {
        "AUD": "호주 달러", "BRL": "브라질 헤알", "CAD": "캐나다 달러",
        "CHF": "스위스 프랑", "CNY": "중국 위안", "DKK": "덴마크 크로네",
        "EUR": "유로화", "GBP": "영국 파운드", "INR": "인도 루피",
        "JPY": "일본 엔", "KRW": "대한민국 원", "MXN": "멕시코 페소",
        "NOK": "노르웨이 크로네", "NZD": "뉴질랜드 달러", "SEK": "스웨덴 크로나",
        "SGD": "싱가포르 달러", "USD": "미국 달러", "VND": "베트남 동",
        "ZAR": "남아공 랜드",
    },
    "DE": {
        "AUD": "Australischer Dollar", "BRL": "Brasilianischer Real", "CAD": "Kanadischer Dollar",
        "CHF": "Schweizer Franken", "CNY": "Chinesischer Yuan", "DKK": "Dänische Krone",
        "EUR": "Euro", "GBP": "Britisches Pfund", "INR": "Indische Rupie",
        "JPY": "Japanischer Yen", "KRW": "Südkoreanischer Won", "MXN": "Mexikanischer Peso",
        "NOK": "Norwegische Krone", "NZD": "Neuseeland-Dollar", "SEK": "Schwedische Krone",
        "SGD": "Singapur-Dollar", "USD": "US-Dollar", "VND": "Vietnamesischer Dong",
        "ZAR": "Südafrikanischer Rand",
    },
    "ES": {
        "AUD": "Dólar australiano", "BRL": "Real brasileño", "CAD": "Dólar canadiense",
        "CHF": "Franco suizo", "CNY": "Yuan chino", "DKK": "Corona danesa",
        "EUR": "Euro", "GBP": "Libra esterlina", "INR": "Rupia india",
        "JPY": "Yen japonés", "KRW": "Won surcoreano", "MXN": "Peso mexicano",
        "NOK": "Corona noruega", "NZD": "Dólar neozelandés", "SEK": "Corona sueca",
        "SGD": "Dólar de Singapur", "USD": "Dólar estadounidense", "VND": "Dong vietnamita",
        "ZAR": "Rand sudafricano",
    },
    "FR": {
        "AUD": "Dollar australien", "BRL": "Réal brésilien", "CAD": "Dollar canadien",
        "CHF": "Franc suisse", "CNY": "Yuan chinois", "DKK": "Couronne danoise",
        "EUR": "Euro", "GBP": "Livre sterling", "INR": "Roupie indienne",
        "JPY": "Yen japonais", "KRW": "Won sud-coréen", "MXN": "Peso mexicain",
        "NOK": "Couronne norvégienne", "NZD": "Dollar néo-zélandais", "SEK": "Couronne suédoise",
        "SGD": "Dollar de Singapour", "USD": "Dollar américain", "VND": "Dong vietnamien",
        "ZAR": "Rand sud-africain",
    },
    "JP": {
        "AUD": "オーストラリア・ドル", "BRL": "ブラジル・レアル", "CAD": "カナダ・ドル",
        "CHF": "スイス・フラン", "CNY": "中国元", "DKK": "デンマーク・クローネ",
        "EUR": "ユーロ", "GBP": "英ポンド", "INR": "インド・ルピー",
        "JPY": "日本円", "KRW": "大韓民国ウォン", "MXN": "メキシコ・ペソ",
        "NOK": "ノルウェー・クローネ", "NZD": "ニュージーランド・ドル", "SEK": "スウェーデン・クローナ",
        "SGD": "シンガポール・ドル", "USD": "米ドル", "VND": "ベトナム・ドン",
        "ZAR": "ランド",
    },
    "CN": {
        "AUD": "澳大利亚元", "BRL": "巴西雷亚尔", "CAD": "加拿大元",
        "CHF": "瑞士法郎", "CNY": "人民币", "DKK": "丹麦克朗",
        "EUR": "欧元", "GBP": "英镑", "INR": "印度卢比",
        "JPY": "日元", "KRW": "韩元", "MXN": "墨西哥比索",
        "NOK": "挪威克朗", "NZD": "新西兰元", "SEK": "瑞典克朗",
        "SGD": "新加坡元", "USD": "美元", "VND": "越南盾",
        "ZAR": "南非兰特",
    },
    "PT": {
        "AUD": "Dólar australiano", "BRL": "Real brasileiro", "CAD": "Dólar canadense",
        "CHF": "Franco suíço", "CNY": "Yuan chinês", "DKK": "Coroa dinamarquesa",
        "EUR": "Euro", "GBP": "Libra esterlina", "INR": "Rupia indiana",
        "JPY": "Iene japonês", "KRW": "Won sul-coreano", "MXN": "Peso mexicano",
        "NOK": "Coroa norueguesa", "NZD": "Dólar neozelandês", "SEK": "Coroa sueca",
        "SGD": "Dólar de Singapura", "USD": "Dólar americano", "VND": "Dong vietnamita",
        "ZAR": "Rand sul-africano",
    },
    "VN": {
        "AUD": "Đô la Úc", "BRL": "Real Brazil", "CAD": "Đô la Canada",
        "CHF": "Franc Thụy Sĩ", "CNY": "Nhân dân tệ", "DKK": "Krone Đan Mạch",
        "EUR": "Euro", "GBP": "Bảng Anh", "INR": "Rupee Ấn Độ",
        "JPY": "Yên Nhật", "KRW": "Won Hàn Quốc", "MXN": "Peso Mexico",
        "NOK": "Krone Na Uy", "NZD": "Đô la New Zealand", "SEK": "Krona Thụy Điển",
        "SGD": "Đô la Singapore", "USD": "Đô la Mỹ", "VND": "Đồng Việt Nam",
        "ZAR": "Rand Nam Phi",
    }
}


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
    on_pin   : callable(str|None) – called with corner code or None.
    on_toggle_visibility : callable(bool) – called with visibility state.
    initial_visible : bool     – initial visibility state of the overlay.
    on_change_currency : callable(str)   – called with selected currency code.
    initial_currency : str     – initial currency code (EUR, USD, KRW).
    on_toggle_auto_currency : callable(bool) – called when toggling auto-detection mode.
    initial_use_auto : bool     – initial state of auto-detection mode.
    on_change_language : callable(str)   – called with selected language code.
    initial_language : str     – initial language code (EN, KR, DE, ES, FR, JP, CN, PT, VN).
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
        on_change_language: Callable[[str], None] | None = None,
        initial_language: str = "EN",
    ) -> None:
        self._root   = root
        self._on_pin = on_pin
        self._on_toggle_visibility = on_toggle_visibility
        self._visible = initial_visible
        self._on_change_currency = on_change_currency
        self._currency = initial_currency
        self._on_toggle_auto_currency = on_toggle_auto_currency
        self._use_auto = initial_use_auto
        self._on_change_language = on_change_language
        self._language = initial_language
        self._detected_currency: str | None = None

        # Pin submenu
        def _pin(corner):
            def _cb(icon, item):
                if self._on_pin:
                    self._root.after(0, lambda: self._on_pin(corner))
            return _cb

        pin_submenu = pystray.Menu(
            pystray.MenuItem(lambda item: self._get_text("top_left"),     _pin("TL")),
            pystray.MenuItem(lambda item: self._get_text("top_right"),    _pin("TR")),
            pystray.MenuItem(lambda item: self._get_text("bottom_left"),  _pin("BL")),
            pystray.MenuItem(lambda item: self._get_text("bottom_right"), _pin("BR")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: self._get_text("follow_mouse"), _pin(None)),
        )

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

        # Build currency submenu dynamically with all 19 unique options
        currency_menu_items = [
            pystray.MenuItem(
                lambda item: self._get_text("auto_detected").format(self._detected_currency) if self._detected_currency else self._get_text("auto_detecting"),
                _set_auto,
                checked=lambda item: self._use_auto
            ),
            pystray.Menu.SEPARATOR
        ]
        
        # Add 19 manual currencies sorted alphabetically
        sorted_currencies = sorted(CURRENCY_SYMBOLS_SHORT.keys())
        for curr_code in sorted_currencies:
            display_str = CURRENCY_SYMBOLS_SHORT[curr_code]
            def _make_label_callback(code=curr_code, disp=display_str):
                return lambda item: f"{disp} ({CURRENCY_NAMES.get(self._language, CURRENCY_NAMES['EN']).get(code, code)})"
            
            currency_menu_items.append(
                pystray.MenuItem(
                    _make_label_callback(curr_code),
                    _set_currency(curr_code),
                    checked=lambda item, code=curr_code: not self._use_auto and self._currency == code,
                    radio=True
                )
            )
            
        currency_submenu = pystray.Menu(*currency_menu_items)

        # Language actions
        def _set_language(lang_val):
            def _cb(icon, item):
                self._language = lang_val
                # Update icon title dynamically
                self._icon.title = self._get_text("tooltip")
                if self._on_change_language:
                    self._root.after(0, lambda: self._on_change_language(lang_val))
            return _cb

        language_submenu = pystray.Menu(
            pystray.MenuItem("English", _set_language("EN"), checked=lambda item: self._language == "EN", radio=True),
            pystray.MenuItem("한국어 (Korean)", _set_language("KR"), checked=lambda item: self._language == "KR", radio=True),
            pystray.MenuItem("Deutsch (German)", _set_language("DE"), checked=lambda item: self._language == "DE", radio=True),
            pystray.MenuItem("Español (Spanish)", _set_language("ES"), checked=lambda item: self._language == "ES", radio=True),
            pystray.MenuItem("Français (French)", _set_language("FR"), checked=lambda item: self._language == "FR", radio=True),
            pystray.MenuItem("日本語 (Japanese)", _set_language("JP"), checked=lambda item: self._language == "JP", radio=True),
            pystray.MenuItem("简体中文 (Chinese)", _set_language("CN"), checked=lambda item: self._language == "CN", radio=True),
            pystray.MenuItem("Português (Portuguese)", _set_language("PT"), checked=lambda item: self._language == "PT", radio=True),
            pystray.MenuItem("Tiếng Việt (Vietnamese)", _set_language("VN"), checked=lambda item: self._language == "VN", radio=True),
        )

        def _toggle_visible(icon, item):
            self._visible = not self._visible
            if self._on_toggle_visibility:
                self._root.after(0, lambda: self._on_toggle_visibility(self._visible))

        menu = pystray.Menu(
            pystray.MenuItem("EcoTracker", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: self._get_text("show_overlay"),
                _toggle_visible,
                checked=lambda item: self._visible
            ),
            pystray.MenuItem(lambda item: self._get_text("pin_to_corner"), pin_submenu),
            pystray.MenuItem(lambda item: self._get_text("currency"), currency_submenu),
            pystray.MenuItem(lambda item: self._get_text("language"), language_submenu),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: self._get_text("quit"), self._quit),
        )

        self._icon = pystray.Icon(
            "EcoTracker",
            icon=_make_icon_image(),
            title=self._get_text("tooltip"),
            menu=menu,
        )
        self._on_quit = on_quit

    def _get_text(self, key: str) -> str:
        return TRANSLATIONS.get(self._language, TRANSLATIONS["EN"]).get(key, "")

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
