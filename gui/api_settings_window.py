"""پنجره مدیریت موتورهای هوش مصنوعی (ساده: URL + مدل + نقش + اولویت)."""
import threading
import tkinter as tk
from tkinter import messagebox

from core import config
from gui.theme import *

ROLE_LABELS = {
    config.ROLE_ASR: "🎙️ فقط ASR (تبدیل صوت به متن)",
    config.ROLE_LLM: "🧠 فقط LLM (ترجمه / پرامپت AI)",
    config.ROLE_BOTH: "🔀 هر دو (ASR + LLM)",
}


class UniversalAPISettingsWindow(tk.Toplevel):
    """مدیریت چند موتور — هر موتور: نام + URL + کلید + مدل + نقش. ترتیب لیست = اولویت."""

    # پریست‌های آماده: فقط URL و مدل را پر می‌کنند (کلید را کاربر وارد می‌کند)
    PRESETS = {
        "⚡ Groq Cloud (پیشنهادی)": {
            "base_url": "https://api.groq.com/openai/v1",
            "llm_model": "openai/gpt-oss-20b",
            "asr_model": "whisper-large-v3-turbo",
        },
        "🤖 OpenAI (ChatGPT / Whisper-1)": {
            "base_url": "https://api.openai.com/v1",
            "llm_model": "gpt-4o-mini",
            "asr_model": "whisper-1",
        },
        "🔀 OpenRouter AI (تمام مدل‌ها)": {
            "base_url": "https://openrouter.ai/api/v1",
            "llm_model": "meta-llama/llama-3.3-70b-instruct",
            "asr_model": "openai/whisper",
        },
        "🖥️ Local / Self-Hosted (Ollama)": {
            "base_url": "http://localhost:11434/v1",
            "llm_model": "llama3",
            "asr_model": "whisper",
        },
    }

    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("⚙️ مدیریت موتورها و مدل‌ها")
        self.geometry("620x600")
        self.minsize(520, 420)
        self.configure(bg=BG_DARK)

        # کل محتوای پنجره داخل یک ناحیه اسکرول‌پذیر
        body = make_scrollable(self)

        tk.Label(body, text="🧠 مدیریت موتورها و مدل‌ها",
                 bg=BG_DARK, fg=ACCENT_CYAN, font=("Segoe UI", 12, "bold"), pady=6).pack()
        tk.Label(body, text="برای هر موتور فقط URL، کلید و نام دقیق مدل را وارد کنید.\n"
                            "نقش هر مدل را مشخص کنید و با دکمه‌های بالا/پایین ترتیب اولویت را تعیین کنید.",
                 bg=BG_DARK, fg=TEXT_SECONDARY, font=("Segoe UI", 9), justify="center").pack(pady=(0, 6))

        # ── لیست موتورها (با اولویت) ────────────────────────────
        frame_list = tk.LabelFrame(body, text=" 📋 موتورها (ترتیب = اولویت) ", bg=BG_DARK,
                                   fg=ACCENT_YELLOW, font=("Segoe UI", 9, "bold"), padx=8, pady=6)
        frame_list.pack(fill="x", padx=15, pady=4)

        list_wrap = tk.Frame(frame_list, bg=BG_DARK)
        list_wrap.pack(fill="x")
        self.listbox = tk.Listbox(list_wrap, bg=BG_MID, fg=TEXT_BRIGHT, selectbackground=ACCENT_BLUE,
                                  selectforeground=BG_DARKER, font=("Segoe UI", 9), height=6,
                                  relief="flat", bd=0)
        self.listbox.pack(side="left", fill="x", expand=True, padx=(2, 4), pady=2)
        self.listbox.bind("<<ListboxSelect>>", self.on_select_engine)

        # دکمه‌های اولویت
        prio_col = tk.Frame(frame_list, bg=BG_DARK)
        prio_col.pack(fill="x", pady=(2, 0))
        tk.Button(prio_col, text="⬆️ اولویت بالاتر", bg=ACCENT_BLUE, fg=BG_DARKER,
                  font=("Segoe UI", 8, "bold"), command=lambda: self._move_selected(-1),
                  cursor="hand2", padx=6).pack(side="left", padx=2)
        tk.Button(prio_col, text="⬇️ اولویت پایین‌تر", bg=ACCENT_BLUE, fg=BG_DARKER,
                  font=("Segoe UI", 8, "bold"), command=lambda: self._move_selected(1),
                  cursor="hand2", padx=6).pack(side="left", padx=2)

        btn_row = tk.Frame(frame_list, bg=BG_DARK)
        btn_row.pack(fill="x", pady=(4, 0))
        tk.Button(btn_row, text="➕ جدید", bg=ACCENT_GREEN, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self.new_engine, cursor="hand2",
                  padx=8).pack(side="left", padx=3)
        tk.Button(btn_row, text="💾 ذخیره", bg=ACCENT_BLUE, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self.save_selected, cursor="hand2",
                  padx=8).pack(side="left", padx=3)
        tk.Button(btn_row, text="⭐ فعال کن", bg=ACCENT_PURPLE, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self.activate_selected, cursor="hand2",
                  padx=8).pack(side="left", padx=3)
        tk.Button(btn_row, text="🗑️ حذف", bg=ACCENT_RED, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self.delete_selected, cursor="hand2",
                  padx=8).pack(side="left", padx=3)

        # ── فرم ساده موتور ──────────────────────────────────────
        frame_form = tk.LabelFrame(body, text=" ✏️ مشخصات موتور ", bg=BG_DARK,
                                   fg=ACCENT_CYAN, font=("Segoe UI", 9, "bold"), padx=10, pady=6)
        frame_form.pack(fill="x", padx=15, pady=4)

        self.var_name = tk.StringVar()
        self._add_field(frame_form, 0, "نام موتور:", self.var_name)
        self.var_url = tk.StringVar()
        self._add_field(frame_form, 1, "Base URL (آدرس API):", self.var_url)
        self.var_key = tk.StringVar()
        self._add_field(frame_form, 2, "API Key:", self.var_key, show="•")
        self.var_model = tk.StringVar()
        self._add_field(frame_form, 3, "نام دقیق مدل (Model):", self.var_model)

        tk.Label(frame_form, text="نقش (کار این مدل):", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", pady=2)
        import tkinter.ttk as ttk
        self.var_role = tk.StringVar(value=config.ROLE_LLM)
        role_cb = ttk.Combobox(frame_form, textvariable=self.var_role,
                               values=list(ROLE_LABELS.values()), state="readonly",
                               font=("Segoe UI", 9), width=40)
        role_cb.grid(row=4, column=1, padx=5, pady=2)

        # ── تست اتصال (همان لحظه، بدون نیاز به ذخیره) ────────────
        test_row = tk.Frame(frame_form, bg=BG_DARK)
        test_row.grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.btn_test = tk.Button(test_row, text="🧪 تست اتصال و مدل", bg=ACCENT_YELLOW, fg=BG_DARKER,
                                  font=("Segoe UI", 9, "bold"), command=self.test_provider, cursor="hand2",
                                  padx=10)
        self.btn_test.pack(side="left")
        self.var_test_status = tk.StringVar(value="")
        self.lbl_test_status = tk.Label(test_row, textvariable=self.var_test_status, bg=BG_DARK,
                                        fg=TEXT_SECONDARY, font=("Segoe UI", 9))
        self.lbl_test_status.pack(side="left", padx=8)

        # ── پریست‌ها ─────────────────────────────────────────────
        frame_preset = tk.Frame(body, bg=BG_DARK)
        frame_preset.pack(fill="x", padx=15, pady=4)
        tk.Label(frame_preset, text="پریست سریع:", bg=BG_DARK, fg=TEXT_SECONDARY,
                 font=("Segoe UI", 9)).pack(side="left")
        import tkinter.ttk as ttk2
        self.preset_var = tk.StringVar(value=list(self.PRESETS.keys())[0])
        preset_cb = ttk2.Combobox(frame_preset, textvariable=self.preset_var,
                                  values=list(self.PRESETS.keys()), state="readonly",
                                  font=("Segoe UI", 9), width=34)
        preset_cb.pack(side="left", padx=6)
        tk.Button(frame_preset, text="اعمال پریست", bg=BG_SURFACE, fg=TEXT_PRIMARY,
                  font=("Segoe UI", 9, "bold"), command=self.apply_preset, cursor="hand2",
                  padx=8).pack(side="left")

        # ── Gemini ───────────────────────────────────────────────
        frame_gemini = tk.LabelFrame(body, text=" ⚡ کلید اختصاصی Google Gemini (اختیاری) ",
                                     bg=BG_DARK, fg=ACCENT_PURPLE, font=("Segoe UI", 9, "bold"),
                                     padx=10, pady=4)
        frame_gemini.pack(fill="x", padx=15, pady=4)
        self.var_gemini = tk.StringVar(value=config.GEMINI_API_KEY)
        self._add_field(frame_gemini, 0, "Gemini API Key:", self.var_gemini, show="•")

        # ── دکمه‌ها ──────────────────────────────────────────────
        btn_frame = tk.Frame(body, bg=BG_DARK)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="✅ ذخیره کلیه تنظیمات و بستن", bg=ACCENT_GREEN, fg=BG_DARKER,
                  font=("Segoe UI", 10, "bold"), command=self.save_all, cursor="hand2",
                  padx=12, pady=3).pack(side="left", padx=8)
        tk.Button(btn_frame, text="🔄 بازنشانی به Google رایگان", bg=ACCENT_RED, fg=BG_DARKER,
                  font=("Segoe UI", 9, "bold"), command=self.reset_to_google, cursor="hand2",
                  padx=8, pady=3).pack(side="left", padx=8)

        self._refresh_list()
        self.focus_force()
        self.lift()

    # ── ابزارها ─────────────────────────────────────────────────

    def _add_field(self, frame, row, label, var, show=None):
        tk.Label(frame, text=label, bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 9)).grid(row=row, column=0, sticky="w", pady=2)
        ent = tk.Entry(frame, bg=BG_MID, fg=TEXT_BRIGHT, textvariable=var,
                       show=show, insertbackground="white", font=("Segoe UI", 9), width=42)
        ent.grid(row=row, column=1, padx=5, pady=2)

    def _role_key(self):
        for k, label in ROLE_LABELS.items():
            if label == self.var_role.get():
                return k
        return config.ROLE_LLM

    def _refresh_list(self, select_name=None):
        self.listbox.delete(0, 'end')
        for i, eng in enumerate(config.ENGINES, 1):
            name = eng.get("name", "?")
            model = eng.get("model", "")
            role = ROLE_LABELS.get(eng.get("role", "llm"), "")
            active = " ⭐" if eng.get("active") else ""
            self.listbox.insert('end', f"{i}. {name}{active}  [{model}]  {role}")
        for i, eng in enumerate(config.ENGINES):
            if (select_name and eng.get("name") == select_name) or (not select_name and eng.get("active")):
                self.listbox.selection_clear(0, 'end')
                self.listbox.selection_set(i)
                self.listbox.activate(i)
                break

    def _selected_engine(self):
        sel = self.listbox.curselection()
        if not sel:
            return None, None
        idx = sel[0]
        if idx < 0 or idx >= len(config.ENGINES):
            return None, None
        return idx, config.ENGINES[idx]

    # ── اولویت ──────────────────────────────────────────────────

    def _move_selected(self, direction):
        idx, eng = self._selected_engine()
        if eng is None:
            messagebox.showwarning("خطا", "ابتدا یک موتور را انتخاب کنید.", parent=self)
            return
        if config.move_engine(idx, direction):
            self._refresh_list(select_name=eng.get("name"))

    # ── رویدادها ────────────────────────────────────────────────

    def on_select_engine(self, event=None):
        idx, eng = self._selected_engine()
        if not eng:
            return
        self.var_name.set(eng.get("name", ""))
        self.var_url.set(eng.get("base_url", ""))
        self.var_key.set(eng.get("api_key", ""))
        self.var_model.set(eng.get("model", ""))
        self.var_role.set(ROLE_LABELS.get(eng.get("role", config.ROLE_LLM)))

    def new_engine(self):
        self.var_name.set("")
        self.var_url.set("")
        self.var_key.set("")
        self.var_model.set("")
        self.var_role.set(ROLE_LABELS[config.ROLE_LLM])
        self.listbox.selection_clear(0, 'end')

    def apply_preset(self):
        data = self.PRESETS.get(self.preset_var.get(), {})
        if not self.var_name.get().strip():
            self.var_name.set(self.preset_var.get().split(" (")[0])
        self.var_url.set(data.get("base_url", self.var_url.get()))
        role = self._role_key()
        if role == config.ROLE_ASR:
            self.var_model.set(data.get("asr_model", self.var_model.get()))
        else:
            self.var_model.set(data.get("llm_model", self.var_model.get()))

    # ── تست اتصال ──────────────────────────────────────────────

    def test_provider(self):
        """تست همان‌لحظه‌ای پرووایدر واردشده در فرم (بدون نیاز به ذخیره)."""
        url = self.var_url.get().strip()
        key = self.var_key.get().strip()
        model = self.var_model.get().strip()
        if not url:
            messagebox.showwarning("خطا", "ابتدا Base URL را وارد کنید.", parent=self)
            return
        if not model:
            messagebox.showwarning("خطا", "ابتدا نام دقیق مدل را وارد کنید.", parent=self)
            return

        role = self._role_key()
        self.btn_test.config(state="disabled")
        self.var_test_status.set("⏳ در حال تست اتصال... (چند ثانیه)")
        self.lbl_test_status.config(fg=TEXT_SECONDARY)
        threading.Thread(target=self._test_worker, args=(url, key, model, role),
                         daemon=True).start()

    def _test_worker(self, url, key, model, role):
        """اجرا در thread جداگانه تا رابط کاربری قفل نشود."""
        from core.engine_test import test_engine
        result = test_engine(url, key, model, role)
        # اگر پنجره هنوز باز است، نتیجه را روی thread اصلی نمایش بده
        try:
            if self.winfo_exists():
                self.after(0, lambda: self._show_test_result(result))
        except Exception:
            pass

    def _show_test_result(self, result):
        """نمایش نتیجه تست روی همان صفحه + پنجره پیام."""
        self.btn_test.config(state="normal")
        ok = result.startswith("✅")
        self.var_test_status.set("✅ اتصال موفق" if ok else "❌ ناموفق")
        self.lbl_test_status.config(fg=ACCENT_GREEN if ok else ACCENT_RED)
        messagebox.showinfo("🧪 نتیجه تست", result, parent=self)

    def save_selected(self):
        name = self.var_name.get().strip()
        if not name:
            messagebox.showwarning("خطا", "نام موتور را وارد کنید.", parent=self)
            return
        if not self.var_url.get().strip():
            messagebox.showwarning("خطا", "Base URL را وارد کنید.", parent=self)
            return
        if not self.var_model.get().strip():
            messagebox.showwarning("خطا", "نام مدل را وارد کنید.", parent=self)
            return

        role = self._role_key()
        idx, eng = self._selected_engine()
        if eng:
            eng["name"] = name
            eng["base_url"] = self.var_url.get().strip()
            eng["api_key"] = self.var_key.get().strip()
            eng["model"] = self.var_model.get().strip()
            eng["role"] = role
        else:
            for e in config.ENGINES:
                if e.get("name") == name:
                    messagebox.showwarning("خطا", "موتوری با این نام وجود دارد.", parent=self)
                    return
            config.ENGINES.append({
                "name": name,
                "base_url": self.var_url.get().strip(),
                "api_key": self.var_key.get().strip(),
                "model": self.var_model.get().strip(),
                "role": role,
                "active": False,
            })
        config.save_engines(config.ENGINES)
        self._refresh_list(select_name=name)
        self.on_select_engine()

    def activate_selected(self):
        idx, eng = self._selected_engine()
        if not eng:
            messagebox.showwarning("خطا", "ابتدا یک موتور را انتخاب کنید.", parent=self)
            return
        config.set_active_engine(eng.get("name"))
        self._refresh_list(select_name=eng.get("name"))
        try:
            self.parent.current_engine = eng.get("name")
            self.parent.active_engine_name = eng.get("name")
        except Exception:
            pass

    def delete_selected(self):
        idx, eng = self._selected_engine()
        if not eng:
            messagebox.showwarning("خطا", "ابتدا یک موتور را انتخاب کنید.", parent=self)
            return
        if not messagebox.askyesno("حذف", f"موتور «{eng.get('name')}» حذف شود؟", parent=self):
            return
        del config.ENGINES[idx]
        config.save_engines(config.ENGINES)
        self._refresh_list()

    def save_all(self):
        if self.var_name.get().strip():
            self.save_selected()
        config.save_env_dict({"GEMINI_API_KEY": self.var_gemini.get().strip()})
        config.save_engines(config.ENGINES)
        messagebox.showinfo("موفقیت",
                            "تنظیمات موتورها ذخیره شد.\nاز تب «موتورها» می‌توانید موتور فعال و اولویت‌ها را انتخاب کنید.",
                            parent=self)
        self.destroy()

    def reset_to_google(self):
        self.parent.change_engine("google")
        messagebox.showinfo("اطلاع", "موتور اصلی روی Google Speech (رایگان وب و بدون نیاز به کلید) تنظیم شد.",
                            parent=self)
        self.destroy()
