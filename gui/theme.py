"""تم رنگی OmniType — پالت‌های تیره با قابلیت سوئیچ.

تم پیش‌فرض: Catppuccin Mocha
تم جدید:    Midnight Blue
"""
import tkinter as tk

# ── پالت‌ها ───────────────────────────────────────────────────────
_PALETTES = {
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
    },
}

# ── فونت‌ها (مشترک بین همه تم‌ها) ────────────────────────────────
FONT_EN    = ("Segoe UI", 9)
FONT_EN_B  = ("Segoe UI", 9, "bold")
FONT_EN_T  = ("Segoe UI", 12, "bold")
FONT_FA    = ("Tahoma", 9)

# ── نام تم فعال ──────────────────────────────────────────────────
_current_theme = "catppuccin"

# ── اعمال مقادیر پیش‌فرض (Catppuccin) ───────────────────────────
def _apply_palette(name: str):
    """مقادیر یک پالت را به متغیرهای سطح ماژول می‌نویسد."""
    import sys
    _mod = sys.modules[__name__]
    pal = _PALETTES.get(name, _PALETTES["catppuccin"])
    for key, value in pal.items():
        setattr(_mod, key, value)

_apply_palette(_current_theme)

# ── رابطٔ عمومی ──────────────────────────────────────────────────
THEME_NAMES = {
    "catppuccin": "🎨 Catppuccin Mocha (پیش‌فرض)",
    "midnight":   "🌙 Midnight Blue",
}

def set_theme(name: str):
    """تم فعال را تغییر می‌دهد (module globals فوراً به‌روز می‌شوند)."""
    global _current_theme
    if name not in _PALETTES:
        name = "catppuccin"
    _current_theme = name
    _apply_palette(name)

def get_theme_name() -> str:
    """نام تم فعال را برمی‌گرداند."""
    return _current_theme

def get_palette(name: str) -> dict:
    """یک پالت کامل را برمی‌گرداند."""
    return dict(_PALETTES.get(name, _PALETTES["catppuccin"]))


# ── ویجت‌کمک‌ها (بدون تغییر) ────────────────────────────────────
def make_scrollable(parent):
    """ساخت یک ناحیه اسکرول‌پذیر (Canvas + Scrollbar) داخل parent.

    نکته مهم: scrollregion باید همزمان با تغییر اندازه inner به‌روزرسانی شود،
    در غیر این صورت انتهای محتوا هنگام اسکرول به پایین دیده نمی‌شود.
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
    # هر تغییری در اندازه inner (بعد ازضافه شدن ویجت‌ها) scrollregion را تازه می‌کند
    inner.bind("<Configure>", _refresh_scrollregion)
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    # تازه‌سازی نهایی پس از چیدمان کامل محتوا
    canvas.after(120, _refresh_scrollregion)
    return inner
