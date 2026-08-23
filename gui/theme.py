"""تم رنگی OmniType v2.1 — پالت تیره مشترک بین همه پنجره‌ها."""
import tkinter as tk

# سطوح
BG_DARK      = "#181825"   # پس‌زمینه اصلی پنجره‌ها
BG_DARKER    = "#11111b"   # پس‌زمینه تیره‌تر
BG_MID       = "#1e1e2e"   # فیلدها و کارت‌ها
BG_SURFACE   = "#313244"   # دکمه‌های ثانویه

# متن
TEXT_PRIMARY   = "#cdd6f4"
TEXT_SECONDARY = "#a6adc8"
TEXT_BRIGHT    = "#ffffff"

# رنگ‌های تاکیدی
ACCENT_CYAN    = "#89dceb"
ACCENT_GREEN   = "#a6e3a1"
ACCENT_RED     = "#f38ba8"
ACCENT_BLUE    = "#89b4fa"
ACCENT_YELLOW  = "#f9e2af"
ACCENT_PURPLE  = "#cba6f7"
ACCENT_ORANGE  = "#fab387"

# فونت‌ها
FONT_EN    = ("Segoe UI", 9)
FONT_EN_B  = ("Segoe UI", 9, "bold")
FONT_EN_T  = ("Segoe UI", 12, "bold")
FONT_FA    = ("Tahoma", 9)


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
    # هر تغییری در اندازه inner (بعد از اضافه شدن ویجت‌ها) scrollregion را تازه می‌کند
    inner.bind("<Configure>", _refresh_scrollregion)
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    # تازه‌سازی نهایی پس از چیدمان کامل محتوا
    canvas.after(120, _refresh_scrollregion)
    return inner
