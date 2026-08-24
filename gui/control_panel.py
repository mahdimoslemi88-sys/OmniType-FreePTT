"""پنجره کامل کنترل OmniType — تب‌بندی‌شده، اسکرول‌پذیر و شیک.

جایگزین منوی راست‌کلیک گوی شناور: همه امکانات (ترجمه، پرامپت، موتورها،
زبان، میانبر، تاریخچه و تنظیمات) در یک پنجره تمیز با تب‌های مجزا.
"""
import tkinter as tk
from tkinter import ttk

from core import config
from gui.theme import *


def _configure_notebook_style():
    """استایل تیره برای تب‌های ttk.Notebook."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Omni.TNotebook", background=BG_DARKER, borderwidth=0, tabmargins=(4, 6, 4, 0))
    style.configure("Omni.TNotebook.Tab",
                    background=BG_MID, foreground=TEXT_SECONDARY, padding=(14, 7),
                    font=("Segoe UI", 9, "bold"), borderwidth=0)
    style.map("Omni.TNotebook.Tab",
              background=[("selected", BG_SURFACE)],
              foreground=[("selected", ACCENT_CYAN)])
    style.configure("Omni.TFrame", background=BG_DARK)


def _section(frame, title):
    """تیتر بخش داخل هر تب."""
    tk.Label(frame, text=title, bg=BG_DARK, fg=ACCENT_YELLOW,
             font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=(10, 2))


class _ActionButton(tk.Button):
    """دکمه اکشن بزرگ و شیک."""

    def __init__(self, master, text, command, color=ACCENT_BLUE, **kw):
        super().__init__(master, text=text, bg=color, fg=BG_DARKER,
                         font=("Segoe UI", 10, "bold"), command=command,
                         cursor="hand2", relief="flat", bd=0, anchor="w",
                         padx=14, pady=9, **kw)


class ControlPanel(tk.Toplevel):
    """پنجره کامل کنترل OmniType با تب‌های مجزا."""

    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("🎛️ OmniType Control Panel")
        self.geometry("560x620")
        self.minsize(480, 420)
        self.configure(bg=BG_DARKER)

        _configure_notebook_style()

        # ── هدر ──────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_DARKER)
        header.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(header, text="🎛️ OmniType Control Panel", bg=BG_DARKER,
                 fg=ACCENT_CYAN, font=("Segoe UI", 14, "bold")).pack(side="left")

        # نشانگر زنده وضعیت موتور فعال — نقطه رنگی + متن (کلیک = بررسی مجدد)
        self.status_dot = tk.Canvas(header, width=13, height=13, bg=BG_DARKER, highlightthickness=0)
        self.status_dot.pack(side="right", padx=(8, 2))
        self.status_label = tk.Label(header, text="", bg=BG_DARKER, fg=TEXT_SECONDARY,
                                     font=("Segoe UI", 9), cursor="hand2")
        self.status_label.pack(side="right")
        self.status_label.bind("<Button-1>", lambda e: self._refresh_engine_status(force=True))
        self.status_dot.bind("<Button-1>", lambda e: self._refresh_engine_status(force=True))

        # ── تب‌ها ────────────────────────────────────────────────
        self.notebook = ttk.Notebook(self, style="Omni.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(2, 8))

        self.tab_quick = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_engines = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_lang = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_hotkey = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_history = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_stats = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_settings = tk.Frame(self.notebook, bg=BG_DARK)

        self.notebook.add(self.tab_quick, text="⚡ عملیات سریع")
        self.notebook.add(self.tab_engines, text="🤖 موتورها")
        self.notebook.add(self.tab_lang, text="🌐 زبان")
        self.notebook.add(self.tab_hotkey, text="⌨️ میانبر")
        self.notebook.add(self.tab_history, text="📜 تاریخچه")
        self.notebook.add(self.tab_stats, text="📈 آمار")
        self.notebook.add(self.tab_settings, text="⚙️ تنظیمات")

        self._build_quick_tab()
        self._build_engines_tab()
        self._build_lang_tab()
        self._build_hotkey_tab()
        self._build_history_tab()
        self._build_stats_tab()
        self._build_settings_tab()

        # ترسیم نمودار آمار هنگام انتخاب تب (و بعد از چیدمان کامل)
        self.notebook.bind("<<NotebookTabChanged>>",
                           lambda e: self._redraw_stats_if_visible())
        self.after(150, self._redraw_stats_if_visible)

        # وضعیت زنده موتور فعال + بررسی دوره‌ای (هر ۶۰ ثانیه)
        self._status_checking = False
        self._refresh_engine_status()
        self._schedule_status_refresh()

        # ثبت پنل به عنوان شنوندهٔ سطح صدا (نشانگر زنده هنگام ضبط)
        try:
            self.parent.set_level_listener(self._on_meter_level)
        except Exception:
            pass

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.focus_force()
        self.lift()

    def close(self):
        try:
            self.parent.set_level_listener(None)
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    # ── تب ۱: عملیات سریع ────────────────────────────────────────
    def _build_quick_tab(self):
        body = make_scrollable(self.tab_quick)

        _section(body, "🌐 ترجمه")
        _ActionButton(body, "✨ مشاهده ترجمه در پاپ‌آپ شناور   (Ctrl+Alt+X)",
                      self.parent.translate_peek_action, ACCENT_PURPLE).pack(fill="x", padx=12, pady=3)
        _ActionButton(body, "🌐 ترجمه و جایگزینی: فارسی ➔ انگلیسی   (Ctrl+Alt+Z)",
                      lambda: self.parent.translate_manual_action("fa_to_en")).pack(fill="x", padx=12, pady=3)
        _ActionButton(body, "🇮🇷 ترجمه و جایگزینی: انگلیسی ➔ فارسی   (Ctrl+Alt+Shift+Z)",
                      lambda: self.parent.translate_manual_action("en_to_fa")).pack(fill="x", padx=12, pady=3)
        _ActionButton(body, "📄 ترجمه اسناد و متن طولانی   (Ctrl+Alt+F)",
                      self.parent.open_document_translator_window).pack(fill="x", padx=12, pady=3)

        _section(body, "🤖 هوش مصنوعی")
        _ActionButton(body, "🪄 تبدیل متن/درخواست به پرامپت مهندسی‌شده AI   (Ctrl+Alt+P)",
                      self.parent.prompt_engineer_action, ACCENT_GREEN).pack(fill="x", padx=12, pady=3)
        _ActionButton(body, "📚 واژه‌نامه تخصصی اصطلاحات   (Ctrl+Alt+D)",
                      self.parent.open_custom_dict_window, ACCENT_YELLOW).pack(fill="x", padx=12, pady=3)
        _ActionButton(body, "⚙️ مدیریت موتورها و مدل‌ها",
                      self.parent.open_api_keys_window, ACCENT_ORANGE).pack(fill="x", padx=12, pady=3)

    # ── تب ۲: موتورها ────────────────────────────────────────────
    def _build_engines_tab(self):
        body = make_scrollable(self.tab_engines)

        _section(body, "🎙️ موتور تبدیل صوت به متن (ASR)")
        tk.Label(body, text="موتور فعال را انتخاب کنید — تنظیمات بلافاصله اعمال می‌شود.",
                 bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=12)

        self.engine_btns = []

        def _add_engine_btn(key, title, sub, active):
            label = f"{title}\n     {sub}"
            btn = tk.Button(body, text=label, justify="left", anchor="w",
                            bg=ACCENT_GREEN if active else BG_SURFACE,
                            fg=BG_DARKER if active else TEXT_PRIMARY,
                            font=("Segoe UI", 10, "bold") if active else ("Segoe UI", 10),
                            command=lambda k=key: self._pick_engine(k),
                            cursor="hand2", relief="flat", bd=0, padx=14, pady=10)
            btn.pack(fill="x", padx=12, pady=3)
            self.engine_btns.append((key, btn))

        # موتور رایگان گوگل — همیشه موجود و پیش‌فرض
        _add_engine_btn("google", "🌐 Google Speech (رایگان و پیش‌فرض)",
                        "بدون نیاز به کلید — ۱۰۰٪ رایگان",
                        self.parent.current_engine == "google")

        # موتورهای سفارشی — به ترتیب اولویت، با نمایش نقش هر مدل
        for idx, eng in enumerate(config.ENGINES, 1):
            name = eng.get("name", "Custom")
            model = eng.get("model", "")
            role = eng.get("role", config.ROLE_LLM)
            role_text = {
                config.ROLE_ASR: "🎙️ فقط ASR",
                config.ROLE_LLM: "🧠 فقط LLM",
                config.ROLE_BOTH: "🔀 ASR + LLM",
            }.get(role, "🧠 LLM")
            active = (self.parent.current_engine == name)
            _add_engine_btn(name, f"{idx}. {name}  [{model}]",
                            f"نقش: {role_text}   ·   اولویت: {idx}", active)

        # موتور محلی
        _add_engine_btn("local", "🖥️ Faster-Whisper (Local Offline)",
                        "آفلاین و بدون اینترنت",
                        self.parent.current_engine == "local")

        _section(body, "⚙️ مدیریت موتورها")
        tk.Label(body, text="ترتیب موتورها = اولویت استفاده. برای جابه‌جایی اولویت و افزودن موتور جدید:",
                 bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9), anchor="w",
                 wraplength=470, justify="left").pack(fill="x", padx=12)
        tk.Button(body, text="➕ افزودن / ویرایش / تغییر اولویت موتورها...", bg=BG_SURFACE, fg=ACCENT_CYAN,
                  font=("Segoe UI", 9, "bold"), command=self.parent.open_api_keys_window,
                  cursor="hand2", relief="flat", bd=0, padx=10, pady=6).pack(fill="x", padx=12, pady=6)

        _section(body, "🧪 تست همه موتورها")
        tk.Label(body, text="همه موتورهای ذخیره‌شده پشت‌سرهم تست می‌شوند — نتیجه هر کدام با دلیل:",
                 bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9), anchor="w",
                 wraplength=470, justify="left").pack(fill="x", padx=12)
        btn_test_all = tk.Button(body, text="🧪 تست همه موتورها", bg=ACCENT_YELLOW, fg=BG_DARKER,
                                 font=("Segoe UI", 10, "bold"), command=self._test_all_engines,
                                 cursor="hand2", relief="flat", bd=0, padx=14, pady=8)
        btn_test_all.pack(fill="x", padx=12, pady=(4, 4))
        self.btn_test_all = btn_test_all

        # ناحیه نتیجه‌ها — لیست قابل اسکرول
        res_wrap = tk.Frame(body, bg=BG_MID, bd=1, relief="flat")
        res_wrap.pack(fill="x", padx=12, pady=(2, 8))
        self.test_all_text = tk.Text(res_wrap, bg=BG_MID, fg=TEXT_PRIMARY, height=8,
                                     wrap="word", relief="flat", bd=0, padx=8, pady=6,
                                     font=("Consolas", 9), state="disabled")
        scroll = tk.Scrollbar(res_wrap, command=self.test_all_text.yview)
        self.test_all_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.test_all_text.pack(side="left", fill="both", expand=True)

    # ── وضعیت زنده موتور فعال ───────────────────────────────────

    def _set_status(self, color, text):
        """نمایش نقطه رنگی + متن وضعیت."""
        self.status_dot.delete("all")
        self.status_dot.create_oval(1.5, 1.5, 11.5, 11.5, fill=color, outline="")
        self.status_label.config(text=text, fg=color)

    def _refresh_engine_status(self, force=False):
        """به‌روزرسانی زنده وضعیت موتور فعال (سبز = سالم، قرمز = خطا، زرد = در حال بررسی)."""
        name = self.parent.current_engine or "google"

        if name == "google":
            self._set_status(ACCENT_GREEN, "🌐 Google Speech — رایگان و پیش‌فرض")
            return
        if name == "local":
            self._set_status(ACCENT_BLUE, "🖥️ Faster-Whisper محلی — آفلاین")
            return

        # موتور سفارشی — بررسی اتصال واقعی در thread جداگانه
        eng = next((e for e in config.ENGINES if e.get("name") == name), None)
        if eng is None:
            self._set_status(ACCENT_RED, f"⚠️ موتور «{name}» پیکربندی نشده است")
            return
        if self._status_checking and not force:
            return

        self._status_checking = True
        self._set_status(ACCENT_YELLOW, f"⏳ در حال بررسی {name}...")

        import threading
        from core.engine_test import test_engine

        def worker():
            result = test_engine(eng.get("base_url", ""), eng.get("api_key", ""),
                                 eng.get("model", ""), eng.get("role", config.ROLE_LLM))
            try:
                if self.winfo_exists():
                    self.after(0, lambda: self._apply_status_result(name, result))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _apply_status_result(self, name, result):
        self._status_checking = False
        ok = result.startswith("✅")
        if ok:
            self._set_status(ACCENT_GREEN, f"✓ {name} — اتصال برقرار")
        else:
            short = result.split("\n")[0][:42]
            self._set_status(ACCENT_RED, f"✗ {name} — {short}")

    def _schedule_status_refresh(self):
        """بررسی دوره‌ای وضعیت هر ۶۰ ثانیه تا همیشه زنده بماند."""
        try:
            if self.winfo_exists():
                self.after(60000, self._periodic_status)
        except Exception:
            pass

    def _periodic_status(self):
        self._refresh_engine_status()
        self._schedule_status_refresh()

    # ── تست همه موتورها ─────────────────────────────────────────
    def _test_all_engines(self):
        """تست پشت‌سرهم همه موتورهای ذخیره‌شده و نمایش نتیجه هر کدام در لیست."""
        import threading
        from core.engine_test import test_engine

        engines = list(config.ENGINES)
        if not engines:
            self._append_test_result("هیچ موتور ذخیره‌شده‌ای وجود ندارد.")
            return

        self.btn_test_all.config(state="disabled", text="⏳ در حال تست...")
        self._set_test_text(f"⏳ شروع تست {len(engines)} موتور...\n")

        def worker():
            for eng in engines:
                name = eng.get("name", "?")
                model = eng.get("model", "")
                role = eng.get("role", config.ROLE_LLM)
                result = test_engine(eng.get("base_url", ""), eng.get("api_key", ""),
                                     model, role)
                line = f"🔹 {name}  [{model}]\n     {result}\n"
                try:
                    if self.winfo_exists():
                        self.after(0, lambda l=line: self._append_test_result(l))
                except Exception:
                    pass
            try:
                if self.winfo_exists():
                    self.after(0, self._finish_test_all)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _set_test_text(self, text):
        self.test_all_text.config(state="normal")
        self.test_all_text.delete("1.0", "end")
        self.test_all_text.insert("end", text)
        self.test_all_text.config(state="disabled")

    def _append_test_result(self, line):
        self.test_all_text.config(state="normal")
        self.test_all_text.insert("end", line)
        self.test_all_text.see("end")
        self.test_all_text.config(state="disabled")

    def _finish_test_all(self):
        self._append_test_result("\n✅ تست همه موتورها تمام شد.")
        self.btn_test_all.config(state="normal", text="🧪 تست همه موتورها")

    def _pick_engine(self, name):
        self.parent.change_engine(name)
        self._refresh_engine_buttons()
        self._refresh_engine_status()

    def _refresh_engine_buttons(self):
        for key, btn in self.engine_btns:
            active = (self.parent.current_engine == key)
            btn.configure(bg=ACCENT_GREEN if active else BG_SURFACE,
                          fg=BG_DARKER if active else TEXT_PRIMARY,
                          font=("Segoe UI", 10, "bold") if active else ("Segoe UI", 10))

    # ── تب ۳: زبان ───────────────────────────────────────────────
    def _build_lang_tab(self):
        body = make_scrollable(self.tab_lang)

        _section(body, "حالت زبان و ترجمه همزمان")
        langs = [
            ("fa", "🇮🇷 فارسی (دقت هوشمند + کلمات انگلیسی)"),
            ("en", "🇬🇧 انگلیسی خالص (EN)"),
            ("auto", "🌐 تشخیص خودکار زبان (Auto)"),
            ("prompt_engineer", "✨ مهندسی پرامپت: گفتار ➔ پرامپت ساختاریافته AI"),
            ("translate_fa_en", "🔤 ترجمه همزمان: گفتار فارسی ➔ تایپ انگلیسی"),
            ("translate_en_fa", "🌐 ترجمه همزمان: گفتار انگلیسی ➔ تایپ فارسی"),
            ("voice_command", "⚡ دستور صوتی: فرمان‌های صوتی ➔ اجرای کیبورد"),
        ]
        self.lang_btns = []
        for code, label in langs:
            active = (self.parent.current_lang == code)
            btn = tk.Button(body, text=label, justify="left", anchor="w",
                            bg=ACCENT_BLUE if active else BG_SURFACE,
                            fg=BG_DARKER if active else TEXT_PRIMARY,
                            font=("Segoe UI", 10, "bold") if active else ("Segoe UI", 10),
                            command=lambda c=code: self._pick_lang(c),
                            cursor="hand2", relief="flat", bd=0, padx=14, pady=9)
            btn.pack(fill="x", padx=12, pady=3)
            self.lang_btns.append((code, btn))

    def _pick_lang(self, code):
        self.parent.change_engine_language(code)
        for c, btn in self.lang_btns:
            active = (self.parent.current_lang == c)
            btn.configure(bg=ACCENT_BLUE if active else BG_SURFACE,
                          fg=BG_DARKER if active else TEXT_PRIMARY,
                          font=("Segoe UI", 10, "bold") if active else ("Segoe UI", 10))

    # ── تب ۴: میانبر ─────────────────────────────────────────────
    def _build_hotkey_tab(self):
        body = make_scrollable(self.tab_hotkey)

        _section(body, "کلید میانبر PTT (فشار برای صحبت)")
        tk.Label(body, text=f"میانبر فعلی:  «{self.parent.current_hotkey}»",
                 bg=BG_DARK, fg=ACCENT_CYAN, font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x", padx=12, pady=(2, 6))

        hotkeys = [("caps lock", "Caps Lock"), ("ctrl+windows", "Ctrl + Windows"),
                   ("ctrl+shift", "Ctrl + Shift"), ("f2", "F2"), ("ctrl+`", "Ctrl + `")]
        for key_code, key_name in hotkeys:
            active = (self.parent.current_hotkey == key_code)
            btn = tk.Button(body, text=f"  {key_name}", anchor="w",
                            bg=ACCENT_BLUE if active else BG_SURFACE,
                            fg=BG_DARKER if active else TEXT_PRIMARY,
                            font=("Segoe UI", 10, "bold") if active else ("Segoe UI", 10),
                            command=lambda k=key_code: self._pick_hotkey(k),
                            cursor="hand2", relief="flat", bd=0, padx=14, pady=8)
            btn.pack(fill="x", padx=12, pady=3)
            self.hotkey_btns = getattr(self, "hotkey_btns", [])
            self.hotkey_btns.append((key_code, btn))

        _section(body, "میانبر دلخواه")
        tk.Button(body, text="⌨️ تنظیم کلید میانبر دلخواه (Custom)...", bg=ACCENT_PURPLE, fg=BG_DARKER,
                  font=("Segoe UI", 10, "bold"), command=self.parent.open_custom_hotkey_window,
                  cursor="hand2", relief="flat", bd=0, padx=14, pady=9).pack(fill="x", padx=12, pady=3)

    def _pick_hotkey(self, key_code):
        self.parent.change_global_hotkey(key_code)
        for k, btn in self.hotkey_btns:
            active = (self.parent.current_hotkey == k)
            btn.configure(bg=ACCENT_BLUE if active else BG_SURFACE,
                          fg=BG_DARKER if active else TEXT_PRIMARY,
                          font=("Segoe UI", 10, "bold") if active else ("Segoe UI", 10))

    # ── تب ۵: تاریخچه ────────────────────────────────────────────
    def _build_history_tab(self):
        self.history_body = make_scrollable(self.tab_history)
        self._refresh_history()

    def _refresh_history(self):
        for w in self.history_body.winfo_children():
            w.destroy()

        _section(self.history_body, "📜 صحبت‌های اخیر (۵ مورد آخر)")
        if not self.parent.history:
            tk.Label(self.history_body, text="(تاریخچه‌ای ثبت نشده است)", bg=BG_DARK,
                     fg=TEXT_SECONDARY, font=("Segoe UI", 10)).pack(padx=12, pady=8)
        else:
            recent = list(self.parent.history)[-5:]
            recent.reverse()
            for idx, item in enumerate(recent, 1):
                short = item[:70] + ("..." if len(item) > 70 else "")
                row = tk.Frame(self.history_body, bg=BG_MID)
                row.pack(fill="x", padx=12, pady=3)
                tk.Label(row, text=f"{idx}.", bg=BG_MID, fg=ACCENT_BLUE,
                         font=("Segoe UI", 10, "bold"), width=3).pack(side="left")
                tk.Label(row, text=short, bg=BG_MID, fg=TEXT_PRIMARY,
                         font=("Segoe UI", 9), anchor="w").pack(side="left", fill="x", expand=True, padx=4)
                tk.Button(row, text="📋", bg=BG_SURFACE, fg=TEXT_PRIMARY,
                          font=("Segoe UI", 9), command=lambda t=item: self.parent.copy_history_item(t),
                          cursor="hand2", relief="flat", bd=0, padx=6).pack(side="right")
        tk.Button(self.history_body, text="🗑️ پاکسازی تاریخچه صحبت‌ها", bg=ACCENT_RED, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self.parent.clear_history_action,
                  cursor="hand2", relief="flat", bd=0, padx=10, pady=6).pack(fill="x", padx=12, pady=8)

    # ── تب ۶: آمار (نمودار زمانی) ────────────────────────────────
    def _build_stats_tab(self):
        body = make_scrollable(self.tab_stats)

        _section(body, "📈 تاریخچهٔ آمار")
        tk.Label(body, text="نمودار زمانی کلمات تایپ‌شده (آبی) و تعداد ضبط‌ها (زرد) به‌صورت روزانه یا هفتگی.",
                 bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9), anchor="w",
                 wraplength=470, justify="left").pack(fill="x", padx=14, pady=(0, 4))

        # دکمه‌های حالت نمودار
        mode_row = tk.Frame(body, bg=BG_DARK)
        mode_row.pack(fill="x", padx=12, pady=(4, 2))
        self._stats_mode = "daily"
        self.btn_stats_daily = tk.Button(
            mode_row, text="📅 روزانه (۱۴ روز)", bg=ACCENT_BLUE, fg=BG_DARKER,
            font=("Segoe UI", 9, "bold"), command=lambda: self._set_stats_mode("daily"),
            cursor="hand2", relief="flat", bd=0, padx=10, pady=5)
        self.btn_stats_daily.pack(side="left", padx=4)
        self.btn_stats_weekly = tk.Button(
            mode_row, text="🗓️ هفتگی (۸ هفته)", bg=BG_SURFACE, fg=TEXT_PRIMARY,
            font=("Segoe UI", 9, "bold"), command=lambda: self._set_stats_mode("weekly"),
            cursor="hand2", relief="flat", bd=0, padx=10, pady=5)
        self.btn_stats_weekly.pack(side="left", padx=4)

        # بوم نمودار
        self.stats_canvas = tk.Canvas(body, height=240, bg=BG_MID,
                                      highlightthickness=0, bd=1, relief="flat")
        self.stats_canvas.pack(fill="x", padx=12, pady=(6, 4))

        # جمع دوره
        self.stats_period_label = tk.Label(body, text="", bg=BG_DARK, fg=TEXT_SECONDARY,
                                           font=("Segoe UI", 9), anchor="w")
        self.stats_period_label.pack(fill="x", padx=14, pady=(0, 2))

        self._draw_stats_chart()

    def _set_stats_mode(self, mode):
        self._stats_mode = mode
        daily_active = (mode == "daily")
        self.btn_stats_daily.config(bg=ACCENT_BLUE if daily_active else BG_SURFACE,
                                    fg=BG_DARKER if daily_active else TEXT_PRIMARY)
        self.btn_stats_weekly.config(bg=ACCENT_BLUE if not daily_active else BG_SURFACE,
                                     fg=BG_DARKER if not daily_active else TEXT_PRIMARY)
        self._draw_stats_chart()

    def _redraw_stats_if_visible(self):
        """ترسیم نمودار وقتی تب آمار انتخاب شده (یا پنجره چیده شده)."""
        try:
            if not self.winfo_exists():
                return
            if str(self.notebook.select()) == str(self.tab_stats):
                self._draw_stats_chart()
            else:
                # هنوز چیده نشده — پس از چیدمان دوباره ترسیم کن
                self._draw_stats_chart()
        except Exception:
            pass

    def _draw_stats_chart(self):
        """ترسیم نمودار میله‌ای کلمات (آبی) و ضبط‌ها (زرد) روی Canvas."""
        try:
            from core import stats as _s
        except Exception:
            return
        c = self.stats_canvas
        c.delete("all")
        W = max(200, c.winfo_width())
        if W <= 2:
            W = 520
        H = c.winfo_height()
        if H <= 2:
            H = 240

        if self._stats_mode == "daily":
            series = _s.get_daily_history(days=14)
            period_label = "۱۴ روز گذشته"
        else:
            series = _s.get_weekly_history(weeks=8)
            period_label = "۸ هفتهٔ گذشته"

        # عنوان دوره
        total_words = sum(x[1] for x in series)
        total_rec = sum(x[2] for x in series)
        self.stats_period_label.config(
            text=f"{period_label}:  {total_words} کلمه  ·  {total_rec} ضبط")

        if total_words == 0 and total_rec == 0:
            c.create_text(W // 2, H // 2, text="هنوز آماری ثبت نشده است",
                          fill=TEXT_SECONDARY, font=("Segoe UI", 10))
            return

        # مارجین‌ها
        left, right, top, bottom = 34, 8, 24, 26
        plot_w = W - left - right
        plot_h = H - top - bottom
        max_val = max(max(x[1] for x in series), max(x[2] for x in series), 1)
        n = len(series)
        slot = plot_w / n
        bar_w = max(3, min(16, slot * 0.28))
        gap = max(1, int(slot * 0.1))

        # خط مبنا
        base_y = top + plot_h
        c.create_line(left, base_y, W - right, base_y, fill=TEXT_SECONDARY)

        for i, (label, words, recs, _secs) in enumerate(series):
            cx = left + slot * i + slot / 2
            if words > 0:
                bh = max(2, plot_h * words / max_val)
                c.create_rectangle(cx - bar_w - gap, base_y - bh, cx - gap, base_y,
                                   fill=ACCENT_BLUE, outline="")
                c.create_text(cx - bar_w / 2 - gap, base_y - bh - 8, text=str(words),
                              fill=ACCENT_BLUE, font=("Segoe UI", 7, "bold"))
            if recs > 0:
                bh = max(2, plot_h * recs / max_val)
                c.create_rectangle(cx + gap, base_y - bh, cx + bar_w + gap, base_y,
                                   fill=ACCENT_YELLOW, outline="")
                c.create_text(cx + bar_w / 2 + gap, base_y - bh - 8, text=str(recs),
                              fill=ACCENT_YELLOW, font=("Segoe UI", 7, "bold"))
            # برچسب تاریخ (روز/ماه)
            short = self._short_date(label)
            c.create_text(cx, base_y + 12, text=short, fill=TEXT_SECONDARY,
                          font=("Segoe UI", 7))

        # راهنما (legend)
        c.create_rectangle(left, top - 18, left + 10, top - 8, fill=ACCENT_BLUE, outline="")
        c.create_text(left + 14, top - 13, text="کلمات", anchor="w",
                      fill=TEXT_PRIMARY, font=("Segoe UI", 8))
        c.create_rectangle(left + 52, top - 18, left + 62, top - 8, fill=ACCENT_YELLOW, outline="")
        c.create_text(left + 66, top - 13, text="ضبط‌ها", anchor="w",
                      fill=TEXT_PRIMARY, font=("Segoe UI", 8))

    @staticmethod
    def _short_date(iso_date):
        """تبدیل ISO به برچسب کوتاه «روز/ماه» (مثل ۲۴/۰۸)."""
        try:
            _y, m, d = iso_date.split("-")
            return f"{int(d)}/{int(m)}"
        except (ValueError, AttributeError):
            return iso_date

    # ── تب ۷: تنظیمات ────────────────────────────────────────────
    def _build_settings_tab(self):
        body = make_scrollable(self.tab_settings)

        # ── تم رنگی ──────────────────────────────────────────────
        from gui.theme import THEME_NAMES, get_theme_name, set_theme as _set_theme
        _section(body, "🎨 تم رنگی")
        self._theme_var = tk.StringVar(value=get_theme_name())
        theme_frame = tk.Frame(body, bg=BG_DARK)
        theme_frame.pack(fill="x", padx=12, pady=4)
        for key, label in THEME_NAMES.items():
            rb = tk.Radiobutton(
                theme_frame, text=label, variable=self._theme_var, value=key,
                bg=BG_DARK, fg=TEXT_PRIMARY, selectcolor=BG_MID,
                activebackground=BG_DARK, activeforeground=TEXT_BRIGHT,
                font=("Segoe UI", 10), command=self._apply_theme, anchor="w",
                padx=10, pady=4)
            rb.pack(fill="x", anchor="w")
        self._theme_status = tk.Label(body, text="", bg=BG_DARK, fg=TEXT_SECONDARY,
                                       font=("Segoe UI", 9), anchor="w")
        self._theme_status.pack(fill="x", padx=14, pady=2)

        _section(body, "ویدیو / موزیک")
        self.pause_var = tk.BooleanVar(value=self.parent.auto_pause_media)
        chk = tk.Checkbutton(body, text="⏸️ توقف خودکار ویدیو/موزیک هنگام صحبت",
                             variable=self.pause_var, bg=BG_DARK, fg=TEXT_PRIMARY,
                             selectcolor=BG_MID, activebackground=BG_DARK,
                             activeforeground=TEXT_BRIGHT, font=("Segoe UI", 10),
                             command=self._toggle_pause, anchor="w", padx=14, pady=8)
        chk.pack(fill="x", padx=12, pady=3)

        # ── VAD: تشخیص فعالیت گفتار ──────────────────────────
        _section(body, "🎙️ تشخیص خودکار سکوت (VAD)")
        self.vad_var = tk.BooleanVar(value=self.parent.vad_enabled)
        vad_chk = tk.Checkbutton(
            body,
            text="⏯️ توقف خودکار ضبط پس از سکوت",
            variable=self.vad_var,
            bg=BG_DARK, fg=TEXT_PRIMARY, selectcolor=BG_MID,
            activebackground=BG_DARK, activeforeground=TEXT_BRIGHT,
            font=("Segoe UI", 10), command=self._toggle_vad, anchor="w",
            padx=14, pady=8)
        vad_chk.pack(fill="x", padx=12, pady=3)
        tk.Label(body, text="وقتی پس از شروع صحبت، صدا قطع شود، ضبط خودکار متوقف می‌شود.",
                 bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9),
                 anchor="w").pack(fill="x", padx=14, pady=(0, 4))
        # تنظیم آستانه زمان سکوت
        timeout_row = tk.Frame(body, bg=BG_DARK)
        timeout_row.pack(fill="x", padx=12, pady=2)
        tk.Label(timeout_row, text="زمان سکوت (ثانیه):", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 9)).pack(side="left")
        self.vad_timeout_var = tk.StringVar(value=str(self.parent.vad_silence_timeout))
        timeout_spin = tk.Spinbox(timeout_row, from_=0.5, to=5.0, increment=0.1,
                                   textvariable=self.vad_timeout_var, width=6,
                                   font=("Segoe UI", 9), bg=BG_SURFACE, fg=TEXT_PRIMARY,
                                   buttonbackground=BG_MID)
        timeout_spin.pack(side="left", padx=6)
        tk.Button(timeout_row, text="ذخیره", bg=ACCENT_CYAN, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self._save_vad_settings,
                  cursor="hand2", relief="flat", bd=0, padx=10, pady=4).pack(side="left")
        self.vad_status_label = tk.Label(body, text="", bg=BG_DARK, fg=TEXT_SECONDARY,
                                          font=("Segoe UI", 9), anchor="w")
        self.vad_status_label.pack(fill="x", padx=14, pady=2)
        self._refresh_vad_status()

        # ── آمار ──────────────────────────────────────────────
        _section(body, "📊 آمار استفاده")
        from core import stats as _stats
        _s = _stats.get_stats()
        self._stats_frame = tk.Frame(body, bg=BG_DARK)
        self._stats_frame.pack(fill="x", padx=12, pady=4)
        self._refresh_stats_ui(_s)

        _section(body, "کارت گرافیک")
        tk.Button(body, text="🧹 آزادسازی VRAM کارت گرافیک (برای بازی)", bg=BG_SURFACE, fg=ACCENT_YELLOW,
                  font=("Segoe UI", 10, "bold"), command=self.parent.free_vram_action,
                  cursor="hand2", relief="flat", bd=0, padx=14, pady=9).pack(fill="x", padx=12, pady=3)

        # ── میکروفون ──────────────────────────────────────────────
        _section(body, "🎙️ میکروفون")
        tk.Label(body, text="سطح صدای زنده هنگام ضبط:", bg=BG_DARK, fg=TEXT_SECONDARY,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=14, pady=(2, 2))
        self.meter_canvas = tk.Canvas(body, height=14, bg=BG_MID,
                                      highlightthickness=0, bd=1, relief="flat")
        self.meter_canvas.pack(fill="x", padx=12, pady=2)
        self.meter_rect = self.meter_canvas.create_rectangle(0, 0, 0, 14,
                                                             fill=ACCENT_GREEN, outline="")

        frame_mic = tk.Frame(body, bg=BG_DARK)
        frame_mic.pack(fill="x", padx=12, pady=(6, 2))
        tk.Label(frame_mic, text="دستگاه ورودی:", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 9)).pack(side="left")
        self.mic_combo = ttk.Combobox(frame_mic, state="readonly", width=36)
        self.mic_combo.pack(side="left", padx=6)
        tk.Button(frame_mic, text="ذخیره", bg=ACCENT_CYAN, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self._save_mic,
                  cursor="hand2", relief="flat", bd=0, padx=10, pady=4).pack(side="left")
        self.mic_label = tk.Label(body, text="", bg=BG_DARK, fg=TEXT_SECONDARY,
                                  font=("Segoe UI", 9), anchor="w")
        self.mic_label.pack(fill="x", padx=14, pady=2)
        self._populate_mics()

        _section(body, "🔄 به‌روزرسانی")
        self.update_label = tk.Label(body, text="", bg=BG_DARK, fg=TEXT_SECONDARY,
                                     font=("Segoe UI", 9), anchor="w", wraplength=460, justify="left")
        self.update_label.pack(fill="x", padx=14, pady=2)
        tk.Button(body, text="🔄 بررسی به‌روزرسانی", bg=BG_SURFACE, fg=ACCENT_CYAN,
                  font=("Segoe UI", 9, "bold"), command=self._check_updates,
                  cursor="hand2", relief="flat", bd=0, padx=10, pady=6).pack(fill="x", padx=12, pady=6)

        # ── مدل محلی Whisper ──────────────────────────────────────
        from engine.local_whisper import HAS_FASTER_WHISPER, LOCAL_WHISPER
        _section(body, "🖥️ مدل محلی Whisper (آفلاین)")
        if not HAS_FASTER_WHISPER:
            tk.Label(body,
                    text="⚠️ کتابخانه faster-whisper نصب نیست.\n"
                         "برای فعال‌سازی حالت آفلاین اجرا کنید:\n"
                         "pip install faster-whisper",
                    bg=BG_DARK, fg=ACCENT_YELLOW,
                    font=("Segoe UI", 9), anchor="w", justify="left",
                    wraplength=460).pack(fill="x", padx=14, pady=4)
        else:
            tk.Label(body,
                    text="تشخیص گفتار کاملاً محلی و بدون اینترنت. "
                         "مدل اولین بار از HuggingFace دانلود می‌شود.",
                    bg=BG_DARK, fg=TEXT_SECONDARY,
                    font=("Segoe UI", 9), anchor="w", justify="left",
                    wraplength=460).pack(fill="x", padx=14, pady=(2, 6))
            # انتخاب سایز مدل
            model_row = tk.Frame(body, bg=BG_DARK)
            model_row.pack(fill="x", padx=12, pady=2)
            tk.Label(model_row, text="سایز مدل:", bg=BG_DARK, fg=TEXT_PRIMARY,
                     font=("Segoe UI", 9)).pack(side="left")
            model_sizes = ["tiny", "base", "small", "medium", "large-v3-turbo"]
            self._whisper_size_var = tk.StringVar(value=self.parent.whisper_model_size)
            model_combo = ttk.Combobox(model_row, textvariable=self._whisper_size_var,
                                       values=model_sizes, state="readonly", width=16)
            model_combo.pack(side="left", padx=6)
            tk.Button(model_row, text="ذخیره", bg=ACCENT_CYAN, fg=BG_DARKER,
                      font=("Segoe UI", 9, "bold"), command=self._save_whisper_model,
                      cursor="hand2", relief="flat", bd=0, padx=10, pady=4).pack(side="left", padx=4)
            # وضعیت مدل
            self._whisper_status = tk.Label(body, text="", bg=BG_DARK,
                                            fg=TEXT_SECONDARY, font=("Segoe UI", 9),
                                            anchor="w", wraplength=460)
            self._whisper_status.pack(fill="x", padx=14, pady=2)
            # دکمه‌های بارگذاری/آزادسازی
            preload_row = tk.Frame(body, bg=BG_DARK)
            preload_row.pack(fill="x", padx=12, pady=4)
            tk.Button(preload_row, text="⬇️ بارگذاری مدل", bg=ACCENT_GREEN, fg=BG_DARKER,
                      font=("Segoe UI", 9, "bold"), command=self._preload_whisper,
                      cursor="hand2", relief="flat", bd=0, padx=10, pady=6).pack(side="left", padx=4)
            tk.Button(preload_row, text="🗑️ آزادسازی VRAM", bg=ACCENT_RED, fg=BG_DARKER,
                      font=("Segoe UI", 9, "bold"), command=self._unload_whisper,
                      cursor="hand2", relief="flat", bd=0, padx=10, pady=6).pack(side="left", padx=4)
            self._refresh_whisper_status()

        _section(body, "📤/📥 تنظیمات")
        exp_row = tk.Frame(body, bg=BG_DARK)
        exp_row.pack(fill="x", padx=12, pady=3)
        tk.Button(exp_row, text="📤 خروجی تنظیمات", bg=ACCENT_BLUE, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self._export_settings,
                  cursor="hand2", relief="flat", bd=0, padx=10, pady=6).pack(side="left", padx=4)
        tk.Button(exp_row, text="📥 ورودی تنظیمات", bg=ACCENT_ORANGE, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self._import_settings,
                  cursor="hand2", relief="flat", bd=0, padx=10, pady=6).pack(side="left", padx=4)
        self.export_import_label = tk.Label(body, text="", bg=BG_DARK, fg=TEXT_SECONDARY,
                                            font=("Segoe UI", 9), anchor="w")
        self.export_import_label.pack(fill="x", padx=14, pady=2)

        _section(body, "دیگر")
        tk.Button(body, text="🧪 تست اتصال موتور فعال (LLM)", bg=BG_SURFACE, fg=ACCENT_GREEN,
                  font=("Segoe UI", 10, "bold"), command=self._test_connection,
                  cursor="hand2", relief="flat", bd=0, padx=14, pady=9).pack(fill="x", padx=12, pady=3)
        self.test_status = tk.Label(body, text="", bg=BG_DARK, fg=ACCENT_GREEN,
                                    font=("Segoe UI", 9), anchor="w", wraplength=460, justify="left")
        self.test_status.pack(fill="x", padx=14, pady=2)

        tk.Button(body, text="❌ خروج کامل از برنامه", bg=ACCENT_RED, fg=BG_DARKER,
                  font=("Segoe UI", 10, "bold"), command=self.parent.quit_app,
                  cursor="hand2", relief="flat", bd=0, padx=14, pady=10).pack(fill="x", padx=12, pady=(14, 6))

    def _toggle_pause(self):
        self.parent.toggle_auto_pause_media()
        self.pause_var.set(self.parent.auto_pause_media)

    def _toggle_vad(self):
        self.parent.toggle_vad()
        self._refresh_vad_status()

    def _save_vad_settings(self):
        try:
            timeout = float(self.vad_timeout_var.get())
        except (TypeError, ValueError):
            timeout = 1.5
        self.parent.set_vad_settings(silence_timeout=timeout)
        self.vad_status_label.config(
            text=f"✅ ذخیره شد — توقف پس از {timeout}s سکوت", fg=ACCENT_GREEN)

    def _refresh_vad_status(self):
        if self.parent.vad_enabled:
            t = self.parent.vad_silence_timeout
            self.vad_status_label.config(
                text=f"✅ فعال — توقف پس از {t}s سکوت", fg=ACCENT_GREEN)
        else:
            self.vad_status_label.config(text="غیرفعال", fg=TEXT_SECONDARY)

    # ── تم ──────────────────────────────────────────────────────

    def _apply_theme(self):
        """اعمال تم انتخاب‌شده: ذخیره + بازسازی تب تنظیمات."""
        from gui.theme import set_theme as _set_theme, THEME_NAMES
        name = self._theme_var.get()
        _set_theme(name)
        try:
            self.parent.set_theme(name)
        except Exception:
            pass
        label = THEME_NAMES.get(name, name)
        self._theme_status.config(text=f"✅ تم «{label}» اعمال شد — برای تأثیر کامل پنجره را باز کنید", fg=ACCENT_GREEN)
        # بازسازی تب تنظیمات با رنگ‌های جدید
        self._rebuild_settings_tab()

    def _rebuild_settings_tab(self):
        """بازسازی محتوای تب تنظیمات با تم جدید."""
        _configure_notebook_style()
        for w in self.tab_settings.winfo_children():
            w.destroy()
        self._build_settings_tab()

    # ── مدل محلی Whisper ────────────────────────────────────────

    def _save_whisper_model(self):
        size = self._whisper_size_var.get()
        self.parent.set_whisper_model(size)
        self._whisper_status.config(
            text=f"✅ سایز «{size}» ذخیره شد — در دفعهٔ بعدی بارگذاری می‌شود", fg=ACCENT_GREEN)

    def _preload_whisper(self):
        from engine.local_whisper import HAS_FASTER_WHISPER, LOCAL_WHISPER
        if not HAS_FASTER_WHISPER:
            return
        if LOCAL_WHISPER.is_loading:
            self._whisper_status.config(text="⏳ مدل در حال بارگذاری...", fg=ACCENT_YELLOW)
            return
        size = self._whisper_size_var.get()
        LOCAL_WHISPER.preload_model_async(size)
        self._whisper_status.config(text=f"⏳ بارگذاری مدل «{size}» — اولین بار دانلود می‌شود...",
                                     fg=ACCENT_YELLOW)
        # بررسی دوره‌ای وضعیت
        self._poll_whisper_loading()

    def _poll_whisper_loading(self):
        """بررسی دوره‌ای وضعیت بارگذاری مدل."""
        from engine.local_whisper import LOCAL_WHISPER
        if LOCAL_WHISPER.is_loading:
            self.after(1000, self._poll_whisper_loading)
        else:
            self._refresh_whisper_status()

    def _unload_whisper(self):
        from engine.local_whisper import LOCAL_WHISPER
        LOCAL_WHISPER.unload_model()
        self._refresh_whisper_status()

    def _refresh_whisper_status(self):
        from engine.local_whisper import HAS_FASTER_WHISPER, LOCAL_WHISPER
        if not HAS_FASTER_WHISPER or not hasattr(self, "_whisper_status"):
            return
        if LOCAL_WHISPER.is_loading:
            self._whisper_status.config(text="⏳ در حال بارگذاری مدل...", fg=ACCENT_YELLOW)
        elif LOCAL_WHISPER.model is not None:
            size = self.parent.whisper_model_size
            self._whisper_status.config(
                text=f"✅ مدل «{size}» آماده — کاملاً آفلاین", fg=ACCENT_GREEN)
        elif LOCAL_WHISPER.load_error:
            self._whisper_status.config(
                text=f"❌ خطا: {LOCAL_WHISPER.load_error}", fg=ACCENT_RED)
        else:
            self._whisper_status.config(
                text="⬜ مدل بارگذاری نشده — دکمهٔ «بارگذاری» را بزنید",
                fg=TEXT_SECONDARY)

    # ── آمار ─────────────────────────────────────────────────────

    def _refresh_stats_ui(self, data=None):
        """بازسازی محتوای بخش آمار با داده‌های جدید."""
        for w in self._stats_frame.winfo_children():
            w.destroy()
        if data is None:
            from core import stats as _s
            data = _s.get_stats()
        total_words = data.get("total_words", 0)
        total_rec = data.get("total_recordings", 0)
        total_secs = data.get("total_recording_secs", 0.0)
        eng = data.get("engine_usage", {})

        # خلاصه
        mins = int(total_secs // 60)
        secs = int(total_secs % 60)
        summary = (
            f"📝 کل کلمات تایپ‌شده:  {total_words}\n"
            f"🎙️ تعداد ضبط‌ها:      {total_rec}\n"
            f"⏱️ مجموع زمان ضبط:   {mins} دقیقه و {secs} ثانیه"
        )
        tk.Label(self._stats_frame, text=summary, bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Consolas", 10), justify="right", anchor="w").pack(fill="x", padx=2)

        # استفاده از هر موتور
        if eng:
            tk.Label(self._stats_frame, text="\n📊 استفاده از موتورها:",
                     bg=BG_DARK, fg=ACCENT_CYAN,
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
            max_count = max(eng.values()) if eng else 1
            for name, count in sorted(eng.items(), key=lambda x: -x[1]):
                row = tk.Frame(self._stats_frame, bg=BG_DARK)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"  {name}", bg=BG_DARK, fg=TEXT_PRIMARY,
                         font=("Segoe UI", 9), anchor="w", width=28).pack(side="left")
                # نوار پیشرفت
                bar_width = max(2, int(120 * count / max_count))
                canvas = tk.Canvas(row, width=120, height=12, bg=BG_MID, highlightthickness=0)
                canvas.pack(side="left", padx=4)
                canvas.create_rectangle(0, 0, bar_width, 12, fill=ACCENT_CYAN, outline="")
                tk.Label(row, text=str(count), bg=BG_DARK, fg=ACCENT_YELLOW,
                         font=("Consolas", 9, "bold")).pack(side="left", padx=4)
        else:
            tk.Label(self._stats_frame, text="\n(هنوز آماری ثبت نشده است)",
                     bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9),
                     anchor="w").pack(fill="x")

        # دکمهٔ پاک‌سازی آمار
        tk.Button(self._stats_frame, text="🗑️ پاک‌سازی آمار",
                  bg=BG_SURFACE, fg=ACCENT_RED,
                  font=("Segoe UI", 9, "bold"), command=self._reset_stats,
                  cursor="hand2", relief="flat", bd=0, padx=10, pady=4).pack(anchor="w", pady=(6, 0))

    def _reset_stats(self):
        from tkinter import messagebox
        if messagebox.askyesno("پاک‌سازی آمار",
                              "آیا مطمئنید که می‌خواهید همهٔ آمار را پاک کنید?",
                              parent=self):
            from core import stats as _s
            _s.reset()
            self._refresh_stats_ui()

    # ── میکروفون ─────────────────────────────────────────────────

    def _populate_mics(self):
        """پر کردن کشویی دستگاه‌های ورودی و انتخاب دستگاه فعلی."""
        devices = []
        try:
            pa = getattr(self.parent, "p", None)
            from core.audio import list_input_devices
            devices = list_input_devices(pa) if pa else []
        except Exception:
            devices = []
        self._mic_devices = devices
        self.mic_combo["values"] = [f"{i}: {name}" for i, name in devices]
        self._set_current_mic(getattr(self.parent, "input_device_index", None))

    def _set_current_mic(self, index):
        for i, name in self._mic_devices:
            if i == index:
                self.mic_combo.set(f"{i}: {name}")
                return
        self.mic_combo.set("")

    @staticmethod
    def _parse_mic_index(text):
        try:
            return int(str(text).split(":", 1)[0].strip())
        except (ValueError, AttributeError):
            return None

    def _save_mic(self):
        idx = self._parse_mic_index(self.mic_combo.get())
        try:
            self.parent.set_input_device(idx)
        except Exception:
            pass
        if idx is None:
            self.mic_label.config(text="✅ دستگاه ورودی: (پیش‌فرض سیستم)", fg=ACCENT_GREEN)
        else:
            self.mic_label.config(text=f"✅ دستگاه ورودی: {self.mic_combo.get()}", fg=ACCENT_GREEN)

    def _on_meter_level(self, level):
        """به‌روزرسانی نشانگر سطح صدا (از thread اصلی از طریق root.after)."""
        try:
            w = self.meter_canvas.winfo_width()
            if w <= 2:
                w = 200
            h = 14
            level = max(0.0, min(1.0, level or 0.0))
            color = ACCENT_RED if level > 0.75 else (ACCENT_YELLOW if level > 0.4 else ACCENT_GREEN)
            x = max(2, int(level * w))
            self.meter_canvas.itemconfig(self.meter_rect, fill=color)
            self.meter_canvas.coords(self.meter_rect, 1, 1, x, h - 1)
        except Exception:
            pass

    # ── به‌روزرسانی ───────────────────────────────────────────────

    def _check_updates(self):
        """اجرای بررسی به‌روزرسانی (با نمایش دیالوگ نتیجه)."""
        self.update_label.config(text="⏳ در حال بررسی به‌روزرسانی...", fg=ACCENT_YELLOW)
        self.parent.check_for_updates(show_dialog=True)
        self._refresh_update_status()

    def _refresh_update_status(self):
        """نمایش وضعیت به‌روزرسانی از parent (نتیجهٔ آخرین چک)."""
        st = getattr(self.parent, "update_state", None) or {}
        if st.get("available"):
            self.update_label.config(
                text=f"🟢 نسخهٔ جدید {st['latest']} موجود است — از ریلیز گیت‌هاب دانلود کنید.",
                fg=ACCENT_GREEN)
        elif "latest" in st:
            self.update_label.config(text="✅ شما از آخرین نسخه استفاده می‌کنید.", fg=ACCENT_GREEN)
        else:
            self.update_label.config(text="وضعیت به‌روزرسانی نامشخص (یا آفلاین).", fg=TEXT_SECONDARY)

    # ── اکسپورت/ایمپورت تنظیمات ─────────────────────────────────

    def _export_settings(self):
        """خروجی تمام تنظیمات، موتورها و واژه‌نامه به فایل JSON."""
        try:
            from tkinter import filedialog, messagebox
        except Exception:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("همه", "*.*")],
            title="خروجی تنظیمات OmniType"
        )
        if not path:
            return
        try:
            from core.export_import import gather_export_data
            import json
            data = gather_export_data()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            n_engines = len(data.get("engines", []))
            n_terms = len(data.get("dictionary", {}).get("prompts", []))
            self.export_import_label.config(
                text=f"✅ خروجی با موفقیت ذخیره شد: {n_engines} موتور، {n_terms} اصطلاح",
                fg=ACCENT_GREEN)
            messagebox.showinfo("خروجی موفق",
                                f"تنظیمات در فایل ذخیره شد:\n{path}\n\n"
                                f"موتورها: {n_engines}\nاصطلاحات واژه‌نامه: {n_terms}",
                                parent=self)
        except Exception as e:
            self.export_import_label.config(text=f"❌ خطا در خروجی: {e}", fg=ACCENT_RED)

    def _import_settings(self):
        """ورودی تنظیمات از فایل JSON."""
        try:
            from tkinter import filedialog, messagebox
        except Exception:
            return
        path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("JSON", "*.json"), ("همه", "*.*")],
            title="انتخاب فایل تنظیمات OmniType"
        )
        if not path:
            return
        try:
            import json
            from core.export_import import apply_import_data
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.export_import_label.config(text=f"❌ خطا در خواندن فایل: {e}", fg=ACCENT_RED)
            return

        n_engines = len(data.get("engines", []))
        n_terms = len(data.get("dictionary", {}).get("prompts", []))
        confirm = messagebox.askyesno(
            "تأیید ورودی",
            f"آیا از بازیابی تنظیمات زیر اطمینان دارید?\n\n"
            f"موتورها: {n_engines}\n"
            f"اصطلاحات واژه‌نامه: {n_terms}\n\n"
            f"تنظیمات فعلی بازنویسی خواهند شد.",
            parent=self)
        if not confirm:
            return
        if apply_import_data(data):
            self.export_import_label.config(
                text=f"✅ تنظیمات بازیابی شد — برای اعمال کامل برنامه را ری‌استارت کنید.",
                fg=ACCENT_GREEN)
            # ریفرش تب‌ها تا تغییرات تا حد امکان بازتاب یابد
            try:
                self.refresh()
            except Exception:
                pass
        else:
            self.export_import_label.config(
                text="❌ فایل تنظیمات فرمت نامعتبری دارد.", fg=ACCENT_RED)

    def _test_connection(self):
        import threading
        self.test_status.config(text="⏳ در حال تست...")

        def worker():
            try:
                from engine.prompt_engineer import AIPromptEngineer
                result = AIPromptEngineer.generate_engineered_prompt("Say: OK")
                msg = f"✓ اتصال برقرار است — پاسخ مدل: {result[:80]}"
            except Exception as e:
                msg = f"✗ خطا: {e}"

            def update():
                self.test_status.config(text=msg)
            self.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    def refresh(self):
        """بازسازی محتوای پویا (پس از تغییر موتور/تاریخچه)."""
        try:
            self._refresh_engine_buttons()
            self._refresh_history()
            self._refresh_engine_status()
            self._refresh_update_status()
            self._refresh_stats_ui()
            self._draw_stats_chart()
            self._refresh_whisper_status()
        except Exception:
            pass
