"""OmniType-FreePTT v2.1 — Push-to-Talk Voice Typing & AI Translator.

لانچر اصلی — منطق برنامه در پکیج‌های core/ engine/ gui/ قرار دارد.
"""
import os
import sys

# 🛡️ سپر محافظ برای جلوگیری از کرش هشدارهای پس‌زمینه در حالت No-Console ویندوز 11
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import ctypes

# 🎯 فعال‌سازی وضوح تصویر بالا (High-DPI Awareness v2)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from gui.app import VoiceTyperGUI


if __name__ == "__main__":
    app = VoiceTyperGUI()
    app.run()
