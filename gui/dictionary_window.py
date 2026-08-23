"""پنجره گرافیکی مدیریت واژه‌نامه تخصصی — افزودن/حذف اصطلاحات فنی."""
import tkinter as tk
from tkinter import ttk, messagebox

from gui.theme import *


class CustomDictionaryWindow(tk.Toplevel):
    """پنجره مدیریت واژه‌نامه تخصصی با فرم ورود کامل."""

    def __init__(self, parent, dict_mgr):
        super().__init__(parent.root)
        self.parent = parent
        self.dict_mgr = dict_mgr
        self.title("📚 واژه‌نامه تخصصی اصطلاحات و کلمات فنی")
        self.geometry("520x600")
        self.configure(bg=BG_DARK)
        self._center_window()

        # عنوان اصلی
        tk.Label(self, text="📚 واژه‌نامه تخصصی اصطلاحات فنی",
                 bg=BG_DARK, fg=ACCENT_CYAN, font=("Segoe UI", 12, "bold"), pady=10).pack()

        tk.Label(self, text="کلمه انگلیسی و تلفظ فارسی آن را وارد کنید تا هوش مصنوعی\n"
                            "متون شما را دقیق تایپ کند (کار در هر دو جهت FA → EN و EN → FA).",
                 bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9),
                 wraplength=480, justify="center").pack(pady=(0, 10))

        # ── فرم افزودن اصطلاح جدید ──────────────────────────────
        frame_add = tk.LabelFrame(self, text=" ➕ افزودن اصطلاح جدید ",
                                  bg=BG_DARK, fg=ACCENT_YELLOW, font=("Segoe UI", 9, "bold"),
                                  padx=10, pady=10)
        frame_add.pack(fill="x", padx=15, pady=5)

        tk.Label(frame_add, text="کلمه انگلیسی (مثلاً PyTorch):",
                 bg=BG_DARK, fg=TEXT_PRIMARY, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_en = tk.Entry(frame_add, bg=BG_MID, fg=TEXT_BRIGHT, insertbackground="white",
                                 font=("Segoe UI", 9), width=24)
        self.entry_en.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(frame_add, text="تلفظ فارسی (مثلاً پایتورچ):",
                 bg=BG_DARK, fg=TEXT_PRIMARY, font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_fa = tk.Entry(frame_add, bg=BG_MID, fg=TEXT_BRIGHT, insertbackground="white",
                                 font=("Segoe UI", 9), width=24)
        self.entry_fa.grid(row=1, column=1, padx=5, pady=2)

        btn_add = tk.Button(frame_add, text="➕ افزودن کلمه", bg=ACCENT_GREEN, fg=BG_DARKER,
                            font=("Segoe UI", 9, "bold"), command=self.add_term_action, cursor="hand2", padx=10)
        btn_add.grid(row=2, column=0, columnspan=2, pady=(8, 0))

        # پیام وضعیت پس از افزودن
        self._status_label = tk.Label(self, text="", bg=BG_DARK, fg=ACCENT_GREEN,
                                      font=("Segoe UI", 9, "bold"))
        self._status_label.pack(pady=(6, 0))

        # ── جدول کلمات ثبت شده ──────────────────────────────────
        frame_list = tk.LabelFrame(self, text=" 📜 کلمات و معادل‌های فعال ",
                                   bg=BG_DARK, fg=ACCENT_BLUE, font=("Segoe UI", 9, "bold"),
                                   padx=10, pady=8)
        frame_list.pack(fill="both", expand=True, padx=15, pady=10)

        columns = ("en", "fa")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings", height=8)
        self.tree.heading("en", text="کلمه/اصطلاح انگلیسی")
        self.tree.heading("fa", text="تلفظ/معادل فارسی")
        self.tree.column("en", width=220, anchor="center")
        self.tree.column("fa", width=220, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn_remove = tk.Button(self, text="🗑️ حذف کلمه انتخابی", bg=ACCENT_RED, fg=BG_DARKER,
                               font=("Segoe UI", 9, "bold"), command=self.remove_term_action, cursor="hand2")
        btn_remove.pack(pady=(0, 12))

        self.refresh_list()

    def _center_window(self):
        self.update_idletasks()
        w, h = 520, 600
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 3
        self.geometry(f"{w}x{h}+{x}+{y}")

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        all_en_terms = set(self.dict_mgr.prompts)
        for en in sorted(all_en_terms):
            fa_terms = [fa for fa, target_en in self.dict_mgr.replacements.items() if target_en == en]
            fa_str = ", ".join(fa_terms) if fa_terms else "-"
            self.tree.insert("", "end", values=(en, fa_str))

    def add_term_action(self):
        en_term = self.entry_en.get().strip()
        fa_term = self.entry_fa.get().strip()
        if not en_term:
            messagebox.showwarning("خطا", "لطفاً کلمه انگلیسی را وارد نمایید.", parent=self)
            return

        self.dict_mgr.add_term(en_term, fa_term)
        self.entry_en.delete(0, 'end')
        self.entry_fa.delete(0, 'end')
        self.refresh_list()
        self._status_label.config(text=f"✓ «{en_term}» به واژه‌نامه اضافه شد")
        self.after(2500, lambda: self._status_label.config(text=""))

    def remove_term_action(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("خطا", "لطفاً یک کلمه را برای حذف انتخاب کنید.", parent=self)
            return

        for sel in selected:
            item_values = self.tree.item(sel, "values")
            if item_values:
                en_term = item_values[0]
                self.dict_mgr.remove_term(en_term)
        self.refresh_list()
        self._status_label.config(text="✓ کلمه حذف شد")
        self.after(2500, lambda: self._status_label.config(text=""))
