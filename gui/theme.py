"""تم رنگی OmniType — سیستم طراحی یکپارچه با پالت مدرن Light Editorial (مشابه Prompt Studio) و پالت‌های تیره.

تم پیش‌فرض: Light Editorial (بر پایه فضای رنگی ادراکی OKLCH)
"""
import math
import tkinter as tk


def _oklch(L, C, h):
    """تبدیل فضای رنگی OKLCH به کد هگز sRGB جهت استفاده در ویجت‌های Tkinter."""
    a = C * math.cos(math.radians(h))
    b = C * math.sin(math.radians(h))
    l = L + 0.3963377774 * a + 0.2158037573 * b
    m = L - 0.1055613458 * a - 0.0638541728 * b
    s = L - 0.0894841775 * a - 1.2914855480 * b
    l3, m3, s3 = l ** 3, m ** 3, s ** 3
    r = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
    g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
    b = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3

    def ch(v):
        v = max(0.0, min(1.0, v))
        return round(255 * (12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055))

    return f"#{ch(r):02x}{ch(g):02x}{ch(b):02x}"


# ── پالت‌ها ───────────────────────────────────────────────────────
_PALETTES = {
    "editorial": {
        "BG_DARK":        _oklch(0.975, 0.007, 330),  # PAPER: خنثی گرم بسیار روشن (#fbf8f9)
        "BG_DARKER":      _oklch(0.940, 0.025, 330),  # TINT: زمینه هدر و کادرها (#f4eff1)
        "BG_MID":         _oklch(0.975, 0.007, 330),  # PAPER
        "BG_SURFACE":     _oklch(0.993, 0.003, 330),  # SURFACE: سفید گرم کارت‌ها و فیلدها (#fdfcfd)
        "TEXT_PRIMARY":   _oklch(0.260, 0.015, 330),  # INK: خاکستری بسیار تیره خوانا (#3e393c)
        "TEXT_SECONDARY": _oklch(0.480, 0.015, 330),  # MUTED: خاکستری خوانا (#777074)
        "TEXT_BRIGHT":    _oklch(0.180, 0.015, 330),  # تیره با کنتراست بالا
        "ACCENT_CYAN":    _oklch(0.460, 0.160, 330),  # ارغوانی / آلبالویی کنترل‌شده (#9b3068)
        "ACCENT_GREEN":   _oklch(0.550, 0.130, 145),  # سبز آرام برای موفقیت (#2e8b57)
        "ACCENT_RED":     _oklch(0.470, 0.160, 25),   # قرمز تیره خوانا برای خطا (#b32d38)
        "ACCENT_BLUE":    _oklch(0.460, 0.160, 330),  # ارغوانی برای دکمه‌های اصلی
        "ACCENT_YELLOW":  _oklch(0.460, 0.160, 330),  # ارغوانی برای تیترهای بخش‌ها
        "ACCENT_PURPLE":  _oklch(0.460, 0.160, 330),  # ارغوانی آلبالویی
        "ACCENT_ORANGE":  _oklch(0.620, 0.140, 65),   # نارنجی کنترل‌شده (#c26d18)
        "BORDER_LINE":    _oklch(0.850, 0.012, 330),  # کادر خاکستری ظریف (#d9d3d6)
    },
    "catppuccin": {
        "BG_DARK":      "#181825",
        "BG_DARKER":    "#11111b",
        "BG_MID":       "#1e1e2e",
        "BG_SURFACE":   "#313244",
        "TEXT_PRIMARY":   "#cdd6f4",
        "TEXT_SECONDARY": "#a6adc8",
        "TEXT_BRIGHT":    "#ffffff",
        "ACCENT_CYAN":    "#89dceb",
        "ACCENT_GREEN":   "#a6e3a1",
        "ACCENT_RED":     "#f38ba8",
        "ACCENT_BLUE":    "#89b4fa",
        "ACCENT_YELLOW":  "#f9e2af",
        "ACCENT_PURPLE":  "#cba6f7",
        "ACCENT_ORANGE":  "#fab387",
        "BORDER_LINE":    "#45475a",
    },
    "midnight": {
        "BG_DARK":      "#0d1117",
        "BG_DARKER":    "#010409",
        "BG_MID":       "#161b22",
        "BG_SURFACE":   "#21262d",
        "TEXT_PRIMARY":   "#c9d1d9",
        "TEXT_SECONDARY": "#8b949e",
        "TEXT_BRIGHT":    "#f0f6fc",
        "ACCENT_CYAN":    "#58a6ff",
        "ACCENT_GREEN":   "#3fb950",
        "ACCENT_RED":     "#f85149",
        "ACCENT_BLUE":    "#58a6ff",
        "ACCENT_YELLOW":  "#d29922",
        "ACCENT_PURPLE":  "#bc8cff",
        "ACCENT_ORANGE":  "#d29922",
        "BORDER_LINE":    "#30363d",
    },
}

# ── فونت‌ها (مشترک بین همه تم‌ها با تایپوگرافی هماهنگ Segoe UI) ──────
FONT_EN    = ("Segoe UI", 9)
FONT_EN_B  = ("Segoe UI", 9, "bold")
FONT_EN_T  = ("Segoe UI", 12, "bold")
FONT_FA    = ("Segoe UI", 9)

# ── نام تم فعال — پیش‌فرض سیستم بر روی Light Editorial تنظیم است ──
_current_theme = "editorial"


# ── اعمال مقادیر پالت ──────────────────────────────────────────────
def _apply_palette(name: str):
    """مقادیر یک پالت را به متغیرهای سطح ماژول می‌نویسد."""
    import sys
    _mod = sys.modules[__name__]
    pal = _PALETTES.get(name, _PALETTES["editorial"])
    for key, value in pal.items():
        setattr(_mod, key, value)


_apply_palette(_current_theme)

# ── رابط عمومی ─────────────────────────────────────────────────────
THEME_NAMES = {
    "editorial":  "✨ Light Editorial (استایل Prompt Studio — پیش‌فرض)",
    "catppuccin": "🎨 Catppuccin Mocha (تیره)",
    "midnight":   "🌙 Midnight Blue (تیره)",
}


def set_theme(name: str):
    """تم فعال را تغییر می‌دهد (module globals فوراً به‌روز می‌شوند)."""
    global _current_theme
    if name not in _PALETTES:
        name = "editorial"
    _current_theme = name
    _apply_palette(name)


def get_theme_name() -> str:
    """نام تم فعال را برمی‌گرداند."""
    return _current_theme


def get_palette(name: str) -> dict:
    """یک پالت کامل را برمی‌گرداند."""
    return dict(_PALETTES.get(name, _PALETTES["editorial"]))


# ── ویجت‌کمک‌ها ───────────────────────────────────────────────────
def make_scrollable(parent):
    """ساخت یک ناحیه اسکرول‌پذیر (Canvas + Scrollbar) داخل parent.

    نکته مهم: scrollregion باید همزمان با تغییر اندازه inner به‌روزرسانی شود.
    """
    canvas = tk.Canvas(parent, bg=BG_DARK, highlightthickness=0)
    sb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                      bg=BG_SURFACE, activebackground=ACCENT_BLUE, troughcolor=BG_DARK)
    inner = tk.Frame(canvas, bg=BG_DARK)
    inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _refresh_scrollregion(event=None):
        try:
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        except Exception:
            pass

    def _on_canvas_configure(event):
        canvas.itemconfigure(inner_id, width=event.width)
        _refresh_scrollregion()

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.configure(yscrollcommand=sb.set)
    canvas.bind("<Configure>", _on_canvas_configure)
    inner.bind("<Configure>", _refresh_scrollregion)
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    canvas.after(120, _refresh_scrollregion)
    return inner
