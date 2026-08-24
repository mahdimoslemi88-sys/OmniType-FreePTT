"""تنظیمات مشترک تست‌ها.

یک ریشهٔ Tk واحد و مشترک برای همهٔ تست‌های GUI فراهم می‌کند تا فقط یک‌بار
`tk.Tk()` در کل اجرای pytest ساخته شود (و ساختِ ریشهٔ دوم که در برخی محیط‌ها
با خطای tcl شکست می‌خورد، دیگر رخ ندهد). ریشه به‌صورت تنبل (lazy) و یک‌باره
ساخته می‌شود؛ اگر Tk در دسترس نباشد، فیچر با `pytest.skip` اجرای تست‌ها را
به‌جای خطا متوقف می‌کند.
"""
import tkinter as tk

import pytest

# صندوقچهٔ حالت singleton — ریشه فقط یک‌بار ساخته می‌شود
_state = {"root": None, "ok": None}


def _acquire_root():
    """ساخت یک‌بارهٔ ریشه و نگه‌داشتن آن برای کل اجرا."""
    if _state["ok"] is None:
        try:
            r = tk.Tk()
            r.withdraw()
            _state["root"] = r
            _state["ok"] = True
        except tk.TclError:
            _state["ok"] = False
    return _state["root"]


@pytest.fixture(scope="session")
def tk_root():
    """ریشهٔ مشترک Tk — در دسترس نبودن منجر به skip می‌شود."""
    root = _acquire_root()
    if root is None:
        pytest.skip("Tk unavailable")
    yield root
