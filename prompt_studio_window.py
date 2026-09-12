"""Native, scrollable Tkinter Prompt Studio window.

Design System: Light editorial utility with OKLCH-derived tokens.
Multi-provider support: OpenRouter Free, Gemini 3.8 Flash, GLM-5.3.
PyAudio + Google Speech Recognition (fa-IR) integration.
Strict thread safety: Network & Audio workers communicate via queue.Queue.
"""
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import pyperclip

from prompt_studio_engine import PromptStudioEngine, StudioError, Cancelled


def _oklch(L, C, h):
    """Convert perceptual OKLCH color space to sRGB Hex for Tkinter."""
    a = C * math.cos(math.radians(h))
    b = C * math.sin(math.radians(h))
    l = L + 0.3963377774 * a + 0.2158037573 * b
    m = L - 0.1055613458 * a - 0.0638541728 * b
    s = L - 0.0894841775 * a - 1.2914855480 * b
    l3, m3, s3 = l ** 3, m ** 3, s ** 3
    r = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
    g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
    b = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3

    def ch(v):
        v = max(0.0, min(1.0, v))
        return round(255 * (12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055))

    return f"#{ch(r):02x}{ch(g):02x}{ch(b):02x}"


# Design Tokens (OKLCH-authored, warm neutral light editorial palette)
PAPER = _oklch(0.975, 0.007, 330)      # Warm very light neutral with subtle pink undertone
SURFACE = _oklch(0.993, 0.003, 330)    # Soft warm white
INK = _oklch(0.260, 0.015, 330)        # Deep dark gray, not pure black
MUTED = _oklch(0.480, 0.015, 330)      # Readable secondary gray
LINE = _oklch(0.850, 0.012, 330)       # Light gray border
ACCENT = _oklch(0.460, 0.160, 330)     # Controlled plum / berry magenta
TINT = _oklch(0.940, 0.025, 330)       # Very light pink-gray
SUCCESS = _oklch(0.550, 0.130, 145)    # Calm green
WARNING = _oklch(0.620, 0.140, 65)     # Controlled orange
ERROR = _oklch(0.470, 0.160, 25)       # Dark readable red


class PromptStudioWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent_app = parent
        self.closed = False
        self.busy = False
        self.recording = False
        self.ready = False

        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.stop_audio = threading.Event()

        self.job = 0
        self.questions = ()
        self.answer_history = []
        self.poll_id = None

        # Provider and Model state
        self.provider = tk.StringVar(value=PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB)
        self.key = tk.StringVar(value="اتصال لوکال (بدون نیاز به کلید)")
        self.model = tk.StringVar(value=PromptStudioEngine.DEFAULT_ANTIGRAVITY_MODEL)

        self.status = tk.StringVar(value="خواسته‌ات را بنویس یا ضبط کن؛ بعد متن را بازبینی و ارسال کن.")
        self.counter = tk.StringVar(value="0 / 16,000")
        self.model_used = tk.StringVar(value="موتور فعال: Antigravity Hub (Local Flash)")

        self.title("OmniType | Prompt Studio")
        # Ensure at least 800x600 layout
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        init_w = min(1040, max(840, screen_w - 80))
        init_h = min(780, max(640, screen_h - 100))
        self.geometry(f"{init_w}x{init_h}")
        self.minsize(800, 600)
        self.configure(bg=PAPER)

        self._narrow = None
        self._build()

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Control-Return>", lambda e: self.generate())
        self.bind("<Escape>", lambda e: self.cancel())

        self.model.trace_add("write", lambda *_: self._invalidate())
        self.provider.trace_add("write", lambda *_: self._on_provider_change())

        self.poll_id = self.after(50, self._poll)
        self.input.focus_set()
        self.lift()

    def _label(self, parent, text, size=11, bold=False, color=INK, **kw):
        return tk.Label(
            parent, text=text, bg=parent.cget("bg"), fg=color,
            font=("Segoe UI", size, "bold" if bold else "normal"), **kw
        )

    def _button(self, parent, text, command, primary=False, **kw):
        bg = ACCENT if primary else TINT
        fg = SURFACE if primary else INK
        hover_bg = INK if primary else LINE
        hover_fg = SURFACE if primary else INK

        btn = tk.Button(
            parent, text=text, command=command, relief="flat", bd=0,
            bg=bg, fg=fg, activebackground=hover_bg, activeforeground=hover_fg,
            disabledforeground=MUTED, font=("Segoe UI", 10, "bold"), cursor="hand2",
            padx=14, pady=8, takefocus=True, highlightthickness=1,
            highlightbackground=LINE, highlightcolor=ACCENT, **kw
        )

        # Hover state handlers
        def on_enter(e):
            if btn["state"] != "disabled":
                btn.configure(bg=hover_bg, fg=hover_fg)

        def on_leave(e):
            if btn["state"] != "disabled":
                btn.configure(bg=bg, fg=fg)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _text(self, parent, height, rtl=False, readonly=False):
        w = ScrolledText(
            parent, height=height, width=28, wrap="word", undo=not readonly,
            bg=SURFACE, fg=INK, insertbackground=ACCENT, selectbackground=TINT,
            selectforeground=INK, font=("Segoe UI", 11), relief="flat", bd=0,
            padx=12, pady=10, highlightthickness=1, highlightbackground=LINE,
            highlightcolor=ACCENT, spacing1=3, spacing3=5
        )
        if rtl:
            w.tag_configure("rtl", justify="right")
        if readonly:
            w.configure(state="disabled")
        return w

    def _build(self):
        self.canvas = tk.Canvas(self, bg=PAPER, highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=scroll.set)

        self.body = tk.Frame(self.canvas, bg=PAPER, padx=28, pady=24)
        self.body.columnconfigure(0, weight=1)
        self.body_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._resize)
        for w in (self.canvas, self.body):
            w.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))

        # ── Header ────────────────────────────────────────────────────────
        header = tk.Frame(self.body, bg=PAPER)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.columnconfigure(0, weight=1)

        self._label(header, "OMNITYPE  /  PROMPT STUDIO", 10, True, MUTED).pack(anchor="w")
        self._label(header, "تبدیل گفتار به پرامپت ساختاریافته هوش مصنوعی", 20, True, anchor="e").pack(fill="x", pady=(6, 2))
        self._label(header, "گفتار فارسی با Google Speech  ←  بازبینی و ویرایش  ←  پرامپت مهندسی‌شده انگلیسی",
                    10, color=MUTED, anchor="e").pack(fill="x")

        # ── Connection Strip ──────────────────────────────────────────────
        connection = tk.Frame(self.body, bg=TINT, padx=16, pady=12)
        connection.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        connection.columnconfigure(0, weight=2)
        connection.columnconfigure(1, weight=2)
        connection.columnconfigure(2, weight=1)
        connection.columnconfigure(3, weight=0)

        # Provider Selector
        self._label(connection, "سرویس (Provider):", 9, True, MUTED).grid(row=0, column=0, sticky="w")
        provider_frame = tk.Frame(connection, bg=TINT)
        provider_frame.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        providers = [
            ("⚡ Antigravity Hub (لوکال - رایگان و پرسرعت)", PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB),
            ("OpenRouter (رایگان)", PromptStudioEngine.PROVIDER_OPENROUTER),
            ("Gemini 3.8 Flash (ابری)", PromptStudioEngine.PROVIDER_GEMINI),
            ("GLM-5.3 (Pro)", PromptStudioEngine.PROVIDER_GLM),
        ]
        self.provider_combo = ttk.Combobox(
            provider_frame, state="readonly", font=("Segoe UI", 10),
            values=[p[0] for p in providers]
        )
        self.provider_combo.current(0)
        self.provider_combo.pack(fill="x", ipady=2)
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_combo_provider_selected)

        # API Key
        self._label(connection, "کلید API (در حافظه، بدون ذخیره دیسک):", 9, True, MUTED).grid(row=0, column=1, sticky="w", padx=(12, 0))
        entry_opts = dict(relief="flat", font=("Segoe UI", 10), bg=SURFACE, fg=INK,
                          insertbackground=ACCENT, highlightthickness=1,
                          highlightbackground=LINE, highlightcolor=ACCENT)
        self.key_entry = tk.Entry(connection, textvariable=self.key, show="•", state="disabled", **entry_opts)
        self.key_entry.grid(row=1, column=1, sticky="ew", ipady=4, padx=(12, 0), pady=(4, 0))

        # Model ID
        self._label(connection, "شناسه مدل:", 9, True, MUTED).grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.model_entry = tk.Entry(connection, textvariable=self.model, **entry_opts)
        self.model_entry.grid(row=1, column=2, sticky="ew", ipady=4, padx=(12, 0), pady=(4, 0))

        # Reset Session Button
        self.reset_session_btn = self._button(connection, "🔄 سشن جدید", self.reset_hub_session)
        self.reset_session_btn.grid(row=1, column=3, sticky="w", padx=(10, 0), pady=(4, 0))

        # ── Workspace (2 Panes) ───────────────────────────────────────────
        self.workspace = tk.Frame(self.body, bg=PAPER)
        self.workspace.grid(row=2, column=0, sticky="ew")

        self.left = tk.Frame(self.workspace, bg=PAPER)
        self.right = tk.Frame(self.workspace, bg=PAPER)

        for pane in (self.left, self.right):
            pane.columnconfigure(0, weight=1)
            pane.rowconfigure(1, weight=1)

        # Left Pane: Persian Input
        self._label(self.left, "۰۱  /  خواستهٔ تو (ورودی فارسی)", 13, True, anchor="e").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.input = self._text(self.left, 11, rtl=True)
        self.input.grid(row=1, column=0, sticky="nsew")
        self.input.bind("<<Modified>>", lambda e: self._edited(self.input, request=True))

        input_tools = tk.Frame(self.left, bg=PAPER)
        input_tools.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self.record_button = self._button(input_tools, "🎙️ ضبط گفتار", self.record)
        self.record_button.pack(side="right")

        self.clear_input_btn = self._button(input_tools, "پاک کردن", self.clear_input)
        self.clear_input_btn.pack(side="right", padx=(0, 8))

        tk.Label(input_tools, textvariable=self.counter, bg=PAPER, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")

        self._label(self.left, "صدا با Google Speech به متن تبدیل می‌شود؛ حداکثر ۶۰ ثانیه. متن قبل از ارسال قابل ویرایش است.",
                    9, color=MUTED, anchor="e").grid(row=3, column=0, sticky="ew", pady=(6, 0))

        # Right Pane: English Output
        self._label(self.right, "۰۲  /  پرامپت انگلیسی ساختاریافته", 13, True, anchor="e").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.output = self._text(self.right, 11, readonly=True)
        self.output.grid(row=1, column=0, sticky="nsew")

        output_tools = tk.Frame(self.right, bg=PAPER)
        output_tools.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self.copy_button = self._button(output_tools, "📋 کپی پرامپت", self.copy)
        self.copy_button.pack(side="right")
        self.copy_button.configure(state="disabled")

        self.model_label = tk.Label(self.right, textvariable=self.model_used, bg=PAPER, fg=MUTED,
                                    font=("Segoe UI", 9), anchor="w", justify="left")
        self.model_label.grid(row=3, column=0, sticky="ew", pady=(6, 0))

        # ── Clarification Area ────────────────────────────────────────────
        self.clarify = tk.Frame(self.body, bg=TINT, padx=16, pady=14, highlightthickness=1, highlightbackground=LINE)
        self.clarify.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        self.clarify.columnconfigure(0, weight=1)

        self._label(self.clarify, "❓ سؤال‌های ضروری برای رفع ابهام (قبل از ساخت پرامپت):", 11, True, ACCENT, anchor="e").pack(fill="x", pady=(0, 6))
        self.question_label = self._label(self.clarify, "", 10, justify="right", anchor="e")
        self.question_label.pack(fill="x", pady=(0, 8))

        self.answers = self._text(self.clarify, 4, rtl=True)
        self.answers.pack(fill="x")
        self.answers.bind("<<Modified>>", lambda e: self._edited(self.answers))

        clarify_tools = tk.Frame(self.clarify, bg=TINT)
        clarify_tools.pack(fill="x", pady=(8, 0))
        self.record_answer_btn = self._button(clarify_tools, "🎙️ ضبط پاسخ صوتی", self.record_answer)
        self.record_answer_btn.pack(side="right")
        self._label(clarify_tools, "پاسخ‌هایت در درخواست بعدی به عنوان زمینه در نظر گرفته می‌شوند.", 9, color=MUTED, anchor="e").pack(side="left")

        self.clarify.grid_remove()

        # ── Footer Actions ────────────────────────────────────────────────
        footer = tk.Frame(self.body, bg=PAPER)
        footer.grid(row=4, column=0, sticky="ew", pady=(20, 0))

        actions = tk.Frame(footer, bg=PAPER)
        actions.pack(fill="x")

        self.generate_button = self._button(actions, "✨ ساخت پرامپت انگلیسی", self.generate, primary=True)
        self.generate_button.pack(side="right")

        self.cancel_button = self._button(actions, "❌ لغو", self.cancel)
        self.cancel_button.pack(side="right", padx=(0, 8))
        self.cancel_button.configure(state="disabled")

        self.clear_all_button = self._button(actions, "🗑️ پاکسازی همه", self.clear_all)
        self.clear_all_button.pack(side="right", padx=(0, 8))

        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=120)
        self.progress.pack(side="left", pady=8)

        self.status_label = tk.Label(footer, textvariable=self.status, bg=PAPER, fg=MUTED,
                                     font=("Segoe UI", 10), anchor="e", justify="right")
        self.status_label.pack(fill="x", pady=(8, 4))

        self.privacy_label = self._label(
            footer,
            "حریم خصوصی: صوت فقط به Google و متن فقط به سرویس هوش مصنوعی انتخابی ارسال می‌شود. هیچ فایلی ذخیره نمی‌شود.",
            9, color=MUTED, anchor="e", justify="right"
        )
        self.privacy_label.pack(fill="x")

    def _on_combo_provider_selected(self, event=None):
        idx = self.provider_combo.current()
        providers = [
            (PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB, PromptStudioEngine.DEFAULT_ANTIGRAVITY_MODEL),
            (PromptStudioEngine.PROVIDER_OPENROUTER, PromptStudioEngine.DEFAULT_OPENROUTER_MODEL),
            (PromptStudioEngine.PROVIDER_GEMINI, PromptStudioEngine.DEFAULT_GEMINI_MODEL),
            (PromptStudioEngine.PROVIDER_GLM, PromptStudioEngine.DEFAULT_GLM_MODEL),
        ]
        if 0 <= idx < len(providers):
            p, m = providers[idx]
            self.provider.set(p)
            self.model.set(m)
            if p == PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB:
                self.key.set("اتصال لوکال (بدون نیاز به کلید)")
                self.key_entry.configure(state="disabled")
            else:
                self.key_entry.configure(state="normal")
                configured = PromptStudioEngine.configured_key(p)
                if configured and configured != "LOCAL_HUB":
                    self.key.set(configured)
                else:
                    self.key.set("")
            self._on_provider_change()
            self._invalidate()

    def _on_provider_change(self):
        p = self.provider.get()
        if p == PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB:
            sid = PromptStudioEngine.get_active_session_id()
            short_sid = f" (سشن: {sid[:8]}...)" if sid else " (سشن تازه)"
            self.model_used.set(f"موتور فعال: Antigravity Hub (Local Flash){short_sid}")
        elif p == PromptStudioEngine.PROVIDER_GEMINI:
            self.model_used.set("مدل فعال: Gemini 3.8 Flash (Thinking)")
        elif p == PromptStudioEngine.PROVIDER_GLM:
            self.model_used.set("مدل فعال: GLM-5.3 (Pro)")
        else:
            self.model_used.set(f"مدل فعال: {self.model.get() or 'openrouter/free'}")

    def reset_hub_session(self):
        """بازنشانی سشن ایزوله Antigravity Hub برای شروع مکالمه کاملاً تمیز."""
        PromptStudioEngine.reset_session()
        self.questions = ()
        self.answer_history = []
        self._on_provider_change()
        self.status.set("سشن اختصاصی Antigravity بازنشانی شد. پرامپت بعدی در سشن تمیز اجرا خواهد شد.")
        self.status_label.configure(fg=ACCENT)

    def set_persian_input(self, text: str):
        """دریافت متن گفتار فارسی از خارج (مثلاً ضبط سراسری PTT) و قرار دادن در کادر ورودی."""
        if not text:
            return
        self._write(self.input, text.strip())
        self.input.tag_add("rtl", "1.0", "end")
        self.counter.set(f"{len(text.strip()):,} / 16,000")
        self.status.set("متن گفتار فارسی دریافت شد. می‌توانید آن را ویرایش کرده یا روی «تولید پرامپت» بزنید.")
        self.status_label.configure(fg=SUCCESS)
        self._invalidate()

    def _resize(self, event):
        if self.closed:
            return
        self.canvas.itemconfigure(self.body_id, width=event.width)
        narrow = event.width < 850
        if narrow != self._narrow:
            self._narrow = narrow
            self.left.grid_forget()
            self.right.grid_forget()
            self.workspace.columnconfigure(0, weight=1, uniform="panes")
            self.workspace.columnconfigure(1, weight=0 if narrow else 1, uniform="" if narrow else "panes")
            self.left.grid(row=0, column=0, sticky="nsew", padx=0 if narrow else (0, 10))
            self.right.grid(row=1 if narrow else 0, column=0 if narrow else 1, sticky="nsew",
                            padx=0 if narrow else (10, 0), pady=(16, 0) if narrow else 0)
            self.input.configure(height=8 if narrow else 11)
            self.output.configure(height=8 if narrow else 11)

        for label in (self.status_label, self.privacy_label, self.question_label):
            label.configure(wraplength=max(400, event.width - 64))
        self.model_label.configure(wraplength=max(240, (event.width - 72) // 2))

    @staticmethod
    def _write(widget, text, readonly=False):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.edit_modified(False)
        if readonly:
            widget.configure(state="disabled")

    def _edited(self, widget, request=False):
        if not widget.edit_modified():
            return
        widget.edit_modified(False)
        widget.tag_add("rtl", "1.0", "end")
        self._invalidate()
        if request:
            txt = self.input.get("1.0", "end-1c")
            self.counter.set(f"{len(txt):,} / 16,000")
            if not self.busy:
                self.questions = ()
                self.answer_history = []
                self.clarify.grid_remove()

    def _invalidate(self):
        if not self.busy and self.ready:
            self.ready = False
            self._write(self.output, "", readonly=True)
            self.copy_button.configure(state="disabled")
            self.status.set("ورودی ویرایش شد؛ آماده برای ساخت مجدد پرامپت.")
            self.status_label.configure(fg=MUTED)

    def clear_input(self):
        self._write(self.input, "")
        self.counter.set("0 / 16,000")
        self._invalidate()

    def clear_all(self):
        self.clear_input()
        self._write(self.output, "", readonly=True)
        self._write(self.answers, "")
        self.questions = ()
        self.answer_history = []
        self.clarify.grid_remove()
        self.status.set("تمام بخش‌ها پاکسازی شدند.")
        self.status_label.configure(fg=MUTED)

    def copy(self):
        text = self.output.get("1.0", "end-1c").strip()
        if text:
            try:
                pyperclip.copy(text)
                self.status.set("✅ پرامپت انگلیسی با موفقیت در کلیپ‌بورد کپی شد.")
                self.status_label.configure(fg=SUCCESS)
            except Exception:
                self.status.set("خطا در کپی کلیپ‌بورد؛ می‌توانید متن را به صورت دستی انتخاب کنید.")
                self.status_label.configure(fg=ERROR)

    def cancel(self):
        if self.busy:
            self.cancel_event.set()
            self.status.set("در حال لغو درخواست...")
            self.status_label.configure(fg=WARNING)

    # ── Generation Pipeline ───────────────────────────────────────────
    def generate(self):
        if self.busy or self.recording:
            return

        text = self.input.get("1.0", "end-1c").strip()
        if not text:
            self.status.set("⚠️ لطفاً ابتدا خواسته‌ات را بنویس یا ضبط کن.")
            self.status_label.configure(fg=WARNING)
            self.input.focus_set()
            return

        api_key = self.key.get().strip()
        if not api_key:
            self.status.set("⚠️ لطفاً کلید API را وارد کن.")
            self.status_label.configure(fg=WARNING)
            self.key_entry.focus_set()
            return

        provider = self.provider.get()
        model = self.model.get().strip()
        answers = self.answers.get("1.0", "end-1c").strip()

        self.busy = True
        self.ready = False
        self.cancel_event.clear()
        self.job += 1
        current_job = self.job

        self.generate_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.copy_button.configure(state="disabled")
        self.progress.start(10)

        prov_desc = "Antigravity Hub (لوکال)" if provider == PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB else (
            "Gemini 3.8 Flash" if provider == PromptStudioEngine.PROVIDER_GEMINI else (
                "GLM-5.3" if provider == PromptStudioEngine.PROVIDER_GLM else "OpenRouter (مدل رایگان)"
            )
        )
        self.status.set(f"در حال ساخت پرامپت با {prov_desc}...")
        self.status_label.configure(fg=ACCENT)

        def worker():
            try:
                res = PromptStudioEngine.generate(
                    text=text,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                    answers=answers,
                    questions=self.questions,
                    cancel=self.cancel_event,
                )
                self.events.put(("generate_done", current_job, res))
            except Cancelled as ce:
                self.events.put(("generate_cancelled", current_job, str(ce)))
            except StudioError as se:
                self.events.put(("generate_error", current_job, str(se)))
            except Exception as ex:
                self.events.put(("generate_error", current_job, f"خطای ناشناخته: {str(ex)[:100]}"))

        threading.Thread(target=worker, daemon=True).start()

    # ── Voice Recording Pipeline ──────────────────────────────────────
    def record(self):
        if self.busy:
            return
        if self.recording:
            self.stop_audio.set()
            return
        self._start_audio_thread(target_field="input")

    def record_answer(self):
        if self.busy:
            return
        if self.recording:
            self.stop_audio.set()
            return
        self._start_audio_thread(target_field="answers")

    def _start_audio_thread(self, target_field="input"):
        self.recording = True
        self.stop_audio.clear()
        self.record_button.configure(text="⏹️ توقف ضبط", bg=ERROR, fg=SURFACE)
        self.status.set("در حال ضبط صدا (Google Speech)... برای پایان دکمه را دوباره بزنید.")
        self.status_label.configure(fg=ACCENT)

        # Notify parent app not to listen on global hotkey during studio recording
        if hasattr(self.parent_app, "_prompt_studio_audio_busy"):
            self.parent_app._prompt_studio_audio_busy = True

        def audio_worker():
            pyaudio_instance = None
            stream = None
            try:
                import pyaudio
                import speech_recognition as sr
                from core.audio import RATE, CHUNK

                pyaudio_instance = pyaudio.PyAudio()
                # Find configured device if parent has it
                dev_idx = getattr(self.parent_app, "input_device_index", None)
                stream = pyaudio_instance.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=dev_idx
                )

                frames = []
                start_time = time.time()

                while not self.stop_audio.is_set():
                    # 60s max recording
                    if time.time() - start_time >= 60:
                        break
                    try:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        frames.append(data)
                    except Exception:
                        break

                raw_data = b"".join(frames)
                if len(raw_data) < 3200:  # less than ~0.1s
                    self.events.put(("audio_short", None, None))
                    return

                # Perform Google Speech recognition
                r = sr.Recognizer()
                audio_data = sr.AudioData(raw_data, RATE, 2)
                text = r.recognize_google(audio_data, language="fa-IR")
                self.events.put(("audio_done", target_field, text))

            except Exception as e:
                self.events.put(("audio_error", target_field, str(e)))
            finally:
                if stream is not None:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except Exception:
                        pass
                if pyaudio_instance is not None:
                    try:
                        pyaudio_instance.terminate()
                    except Exception:
                        pass
                if hasattr(self.parent_app, "_prompt_studio_audio_busy"):
                    self.parent_app._prompt_studio_audio_busy = False

        threading.Thread(target=audio_worker, daemon=True).start()

    # ── UI Event Loop Polling ─────────────────────────────────────────
    def _poll(self):
        if self.closed:
            return

        while True:
            try:
                msg, job_or_tgt, data = self.events.get_nowait()
            except queue.Empty:
                break

            if msg == "generate_done":
                if job_or_tgt == self.job:
                    self._handle_result(data)
            elif msg == "generate_error":
                if job_or_tgt == self.job:
                    self._handle_error(data)
            elif msg == "generate_cancelled":
                if job_or_tgt == self.job:
                    self._handle_cancelled(data)
            elif msg == "audio_done":
                self._handle_audio_done(job_or_tgt, data)
            elif msg == "audio_short":
                self._handle_audio_short()
            elif msg == "audio_error":
                self._handle_audio_error(data)

        self.poll_id = self.after(50, self._poll)

    def _handle_result(self, result):
        self.busy = False
        self.progress.stop()
        self.generate_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

        if result.status == "ready":
            self.ready = True
            self._write(self.output, result.prompt, readonly=True)
            self.copy_button.configure(state="normal")
            self.clarify.grid_remove()
            self.status.set("✅ پرامپت انگلیسی آماده است. می‌توانید آن را کپی کنید.")
            self.status_label.configure(fg=SUCCESS)
            model_disp = result.model or self.model.get()
            self.model_used.set(f"پاسخ‌دهنده: {model_disp}")

        elif result.status == "needs_clarification":
            self.ready = False
            self.questions = result.questions
            bullets = "\n".join(f"• {q}" for q in result.questions)
            self.question_label.configure(text=bullets)
            self.clarify.grid()
            self._write(self.output, "", readonly=True)
            self.copy_button.configure(state="disabled")
            self.status.set("⚠️ مدل برای ساخت پرامپت دقیق نیاز به رفع ابهام دارد؛ لطفاً پاسخ دهید.")
            self.status_label.configure(fg=WARNING)
            self.answers.focus_set()

    def _handle_error(self, err_msg):
        self.busy = False
        self.progress.stop()
        self.generate_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.status.set(f"❌ {err_msg}")
        self.status_label.configure(fg=ERROR)

    def _handle_cancelled(self, cancel_msg):
        self.busy = False
        self.progress.stop()
        self.generate_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.status.set("عملیات لغو شد.")
        self.status_label.configure(fg=MUTED)

    def _handle_audio_done(self, target_field, text):
        self.recording = False
        self.record_button.configure(text="🎙️ ضبط گفتار", bg=TINT, fg=INK)
        self.status.set("صدا با موفقیت به متن تبدیل شد.")
        self.status_label.configure(fg=SUCCESS)

        widget = self.input if target_field == "input" else self.answers
        current = widget.get("1.0", "end-1c").strip()
        new_text = (current + " " + text).strip() if current else text
        self._write(widget, new_text)
        widget.tag_add("rtl", "1.0", "end")
        if target_field == "input":
            self.counter.set(f"{len(new_text):,} / 16,000")
            self._invalidate()

    def _handle_audio_short(self):
        self.recording = False
        self.record_button.configure(text="🎙️ ضبط گفتار", bg=TINT, fg=INK)
        self.status.set("صدای ضبط‌شده بیش از حد کوتاه یا نامفهوم بود.")
        self.status_label.configure(fg=WARNING)

    def _handle_audio_error(self, err):
        self.recording = False
        self.record_button.configure(text="🎙️ ضبط گفتار", bg=TINT, fg=INK)
        self.status.set("امکان تبدیل گفتار وجود نداشت. می‌توانید متن را دستی وارد کنید.")
        self.status_label.configure(fg=WARNING)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.cancel_event.set()
        self.stop_audio.set()
        if self.poll_id:
            try:
                self.after_cancel(self.poll_id)
            except Exception:
                pass
        self.destroy()
