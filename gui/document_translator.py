"""پنجره ترجمه اسناد و متون طولانی — این کلاس در نسخه ۲ تعریف نشده بود و کرش می‌کرد."""
import threading
import tkinter as tk
from tkinter import messagebox

import pyperclip

from core.dictionary import CUSTOM_DICT
from engine.translator import LLMTranslatorEngine
from gui.theme import *


class DocumentTranslatorWindow(tk.Toplevel):
    """پنجره اختصاصی ترجمه فایل و متن طولانی همراه با نگارش فارسی."""

    def __init__(self, parent):
        super().__init__(parent.root)
        self._app = parent
        self.title("📄 ترجمه اسناد و متون طولانی")
        self.geometry("760x620")
        self.configure(bg=BG_DARK)

        tk.Label(self, text="📄 ترجمه اسناد و متون طولانی (FA ↔ EN)",
                 bg=BG_DARK, fg=ACCENT_CYAN, font=("Segoe UI", 13, "bold"), pady=8).pack()
        tk.Label(self, text="متن خود را در کادر بالا وارد کنید، سپس جهت ترجمه را انتخاب کنید. "
                            "متن‌های طولانی به صورت خودکار به قطعات امن تقسیم می‌شوند.",
                 bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9),
                 wraplength=700, justify="center").pack(pady=(0, 8))

        # ── ورودی ────────────────────────────────────────────────
        tk.Label(self, text="متن اصلی:", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15)
        frame_in = tk.Frame(self, bg=BG_DARK)
        frame_in.pack(fill="both", expand=True, padx=15, pady=4)
        self._in_text = tk.Text(frame_in, wrap="word", bg=BG_MID, fg=TEXT_BRIGHT,
                                insertbackground="white", font=("Tahoma", 10),
                                relief="flat", bd=0, padx=8, pady=8)
        self._in_text.pack(side="left", fill="both", expand=True)
        sb_in = tk.Scrollbar(frame_in, command=self._in_text.yview)
        sb_in.pack(side="right", fill="y")
        self._in_text.config(yscrollcommand=sb_in.set)

        # ── دکمه‌های ترجمه ───────────────────────────────────────
        btn_row = tk.Frame(self, bg=BG_DARK)
        btn_row.pack(fill="x", padx=15, pady=8)
        tk.Button(btn_row, text="🌐 فارسی ➔ انگلیسی", bg=ACCENT_BLUE, fg=BG_DARKER,
                  font=("Segoe UI", 10, "bold"), command=lambda: self._translate("fa_to_en"),
                  cursor="hand2", padx=12).pack(side="left", padx=4)
        tk.Button(btn_row, text="🌐 انگلیسی ➔ فارسی", bg=ACCENT_GREEN, fg=BG_DARKER,
                  font=("Segoe UI", 10, "bold"), command=lambda: self._translate("en_to_fa"),
                  cursor="hand2", padx=12).pack(side="left", padx=4)
        self._status = tk.Label(btn_row, text="", bg=BG_DARK, fg=ACCENT_YELLOW,
                                font=("Segoe UI", 9, "bold"))
        self._status.pack(side="right", padx=8)

        # ── خروجی ────────────────────────────────────────────────
        tk.Label(self, text="نتیجه ترجمه:", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15)
        frame_out = tk.Frame(self, bg=BG_DARK)
        frame_out.pack(fill="both", expand=True, padx=15, pady=4)
        self._out_text = tk.Text(frame_out, wrap="word", bg=BG_MID, fg=ACCENT_GREEN,
                                 insertbackground="white", font=("Tahoma", 10),
                                 relief="flat", bd=0, padx=8, pady=8)
        self._out_text.pack(side="left", fill="both", expand=True)
        sb_out = tk.Scrollbar(frame_out, command=self._out_text.yview)
        sb_out.pack(side="right", fill="y")
        self._out_text.config(yscrollcommand=sb_out.set)

        # ── اکشن‌های نتیجه ───────────────────────────────────────
        action_row = tk.Frame(self, bg=BG_DARK)
        action_row.pack(fill="x", padx=15, pady=(4, 12))
        tk.Button(action_row, text="📋 کپی نتیجه", bg=BG_SURFACE, fg=TEXT_PRIMARY,
                  font=("Segoe UI", 9, "bold"), command=self._copy_result,
                  cursor="hand2", padx=10).pack(side="left", padx=4)
        tk.Button(action_row, text="⌨️ تایپ در پنجره قبلی", bg=BG_SURFACE, fg=ACCENT_YELLOW,
                  font=("Segoe UI", 9, "bold"), command=self._type_result,
                  cursor="hand2", padx=10).pack(side="left", padx=4)

        self.focus_force()
        self.lift()

    def _translate(self, mode):
        text = self._in_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("خطا", "لطفاً ابتدا متن را وارد کنید.", parent=self)
            return

        self._status.config(text="⏳ در حال ترجمه...")
        self.update_idletasks()

        def worker():
            try:
                result = LLMTranslatorEngine.translate(text, mode=mode)
                if result:
                    result = CUSTOM_DICT.apply_replacements(result)
                else:
                    result = ""
            except Exception as e:
                print(f"[DocumentTranslator] Error: {e}")
                result = ""

            def update():
                self._out_text.delete("1.0", "end")
                self._out_text.insert("1.0", result)
                self._status.config(text="✓ ترجمه شد" if result else "❌ خطا در ترجمه")

            self.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    def _copy_result(self):
        result = self._out_text.get("1.0", "end").strip()
        if result:
            pyperclip.copy(result)
            self._status.config(text="✓ کپی شد")

    def _type_result(self):
        result = self._out_text.get("1.0", "end").strip()
        if not result:
            return
        try:
            self.destroy()
        except Exception:
            pass
        if hasattr(self._app, "safe_type_and_restore_clipboard"):
            self._app.safe_type_and_restore_clipboard(result)
