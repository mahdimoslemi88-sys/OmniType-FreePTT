"""پنجره گرافیکی تنظیم کلید میانبر دلخواه."""
import threading
import tkinter as tk

try:
    import keyboard
except ImportError:
    keyboard = None

from gui.theme import *


class CustomHotkeyWindow(tk.Toplevel):
    """پنجره تنظیم کلید میانبر PTT."""

    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("⚙️ تنظیم کلید میانبر (Hotkey)")
        self.geometry("380x250")
        self.configure(bg=BG_DARK)

        tk.Label(self, text="کلید میانبر جدید را وارد کنید\nیا دکمه زیر را زده و کلیدها را روی کیبورد فشار دهید.",
                 bg=BG_DARK, fg=TEXT_PRIMARY, font=("Segoe UI", 10)).pack(pady=15)

        self.entry = tk.Entry(self, bg=BG_MID, fg=TEXT_BRIGHT, font=("Segoe UI", 12),
                              width=25, justify="center")
        self.entry.pack(pady=10)
        self.entry.insert(0, self.parent.current_hotkey)

        btn_detect = tk.Button(self, text="🎯 تشخیص خودکار (فشار دهید)", bg=ACCENT_BLUE, fg=BG_DARKER,
                               font=("Segoe UI", 9, "bold"), command=self.detect_hotkey, cursor="hand2")
        btn_detect.pack(pady=5)

        btn_save = tk.Button(self, text="✅ ذخیره میانبر", bg=ACCENT_GREEN, fg=BG_DARKER,
                             font=("Segoe UI", 10, "bold"), command=self.save_hotkey, cursor="hand2")
        btn_save.pack(pady=15)

    def detect_hotkey(self):
        self.entry.delete(0, 'end')
        self.entry.insert(0, "در حال ضبط... کلید را فشار دهید")
        self.update()

        def worker():
            try:
                hk = keyboard.read_hotkey(suppress=False)
                self.entry.delete(0, 'end')
                self.entry.insert(0, hk)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def save_hotkey(self):
        hk = self.entry.get().strip()
        if hk and "در حال ضبط" not in hk:
            self.parent.change_global_hotkey(hk)
            self.destroy()
