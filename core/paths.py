"""مسیرهای پایه برنامه — سازگار با حالت توسعه (اسکریپت) و حالت exe."""
import os
import sys


def app_base_dir():
    """پوشه داده‌های برنامه.

    - در exe (frozen): کنار فایل اجرایی تا فایل‌های config قابل‌خواندن/نوشتن باشند.
    - در توسعه: ریشه پروژه (والد پوشه core).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_icon_path():
    """جستجوی آیکون برنامه در مسیرهای مختلف (dev و packaged)."""
    here = app_base_dir()
    candidates = [
        os.path.join(getattr(sys, "_MEIPASS", ""), "icon.ico"),
        os.path.join(here, "icon.ico"),
        os.path.join(here, "assets", "icon.ico"),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None
