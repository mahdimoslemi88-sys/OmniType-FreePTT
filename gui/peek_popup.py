"""پنجره پاپ‌آپ شناور مشاهده ترجمه در محل نشانگر موس."""
import re
import tkinter as tk

import pyperclip


class HighlightPeekPopup:
    """پاپ‌آپ شناور، اسکرول‌پذیر و شیک برای نمایش ترجمه متون."""

    def __init__(self, parent_root, text_original, text_translated, x_cursor, y_cursor, on_replace_callback=None):
        self.top = tk.Toplevel(parent_root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.config(bg="#11111b")

        char_len = len(text_translated)
        if char_len < 60:
            w, max_h = 380, 180
        elif char_len < 200:
            w, max_h = 460, 260
        else:
            w, max_h = 540, 360

        main_frame = tk.Frame(self.top, bg="#1e1e2e", highlightbackground="#cba6f7",
                              highlightthickness=2, bd=0)
        main_frame.pack(fill="both", expand=True)

        # ── هدر ──────────────────────────────────────────────────
        header_frame = tk.Frame(main_frame, bg="#181825")
        header_frame.pack(fill="x", padx=8, pady=6)
        tk.Label(header_frame, text="✨ 🌐", font=("Segoe UI Emoji", 11),
                 bg="#181825", fg="#f5e0dc").pack(side="left", padx=(4, 2))
        tk.Label(header_frame, text="ترجمه هوشمند | Smart Preview 🪄",
                 font=("Segoe UI", 10, "bold"), bg="#181825", fg="#cba6f7").pack(side="left", padx=4)
        btn_close_top = tk.Label(header_frame, text=" ✕ ", font=("Segoe UI", 11, "bold"),
                                 bg="#181825", fg="#f38ba8", cursor="hand2")
        btn_close_top.pack(side="right", padx=4)
        btn_close_top.bind("<Button-1>", lambda e: self.close())

        tk.Frame(main_frame, bg="#313244", height=1).pack(fill="x", padx=6, pady=2)

        # ── متن اصلی (کوچک) ──────────────────────────────────────
        if text_original and text_original.strip() != text_translated.strip():
            clean_orig = text_original.strip().replace("\r\n", " ").replace("\n", " ")
            orig_snippet = clean_orig[:70] + ("..." if len(clean_orig) > 70 else "")
            tk.Label(main_frame, text=f"🔤 متن اصلی: {orig_snippet}",
                     font=("Segoe UI", 8, "italic"), bg="#1e1e2e", fg="#a6adc8",
                     anchor="w", justify="left").pack(fill="x", padx=10, pady=(4, 2))

        # ── بدنه اسکرول‌پذیر ─────────────────────────────────────
        text_container = tk.Frame(main_frame, bg="#181825")
        text_container.pack(fill="both", expand=True, padx=8, pady=4)
        scrollbar = tk.Scrollbar(text_container, bg="#313244", activebackground="#45475a",
                                 troughcolor="#181825", width=10)
        scrollbar.pack(side="right", fill="y")

        is_rtl = bool(re.search(r'[\u0600-\u06FF]', text_translated))
        text_widget = tk.Text(
            text_container,
            wrap="word",
            font=("Tahoma", 10, "bold") if is_rtl else ("Segoe UI", 10, "bold"),
            bg="#181825", fg="#a6e3a1", insertbackground="white",
            relief="flat", bd=0, padx=8, pady=8,
            yscrollcommand=scrollbar.set,
            height=6 if char_len > 120 else 3,
        )
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        text_widget.insert("1.0", text_translated.strip())
        text_widget.config(state="disabled")

        def _on_mousewheel(event):
            text_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")

        text_widget.bind("<MouseWheel>", _on_mousewheel)

        tk.Frame(main_frame, bg="#313244", height=1).pack(fill="x", padx=6, pady=2)

        # ── دکمه‌های اکشن ────────────────────────────────────────
        btn_frame = tk.Frame(main_frame, bg="#181825")
        btn_frame.pack(fill="x", padx=6, pady=6)

        def copy_action():
            pyperclip.copy(text_translated)
            btn_copy.config(text="✓ کپی شد!", fg="#a6e3a1")
            self.top.after(1000, self.close)

        btn_copy = tk.Label(btn_frame, text="📋 کپی", font=("Segoe UI", 9, "bold"),
                            bg="#313244", fg="#89b4fa", padx=8, pady=4, cursor="hand2")
        btn_copy.pack(side="left", padx=4)
        btn_copy.bind("<Button-1>", lambda e: copy_action())

        if on_replace_callback:
            def replace_action():
                on_replace_callback(text_translated)
                self.close()

            btn_replace = tk.Label(btn_frame, text="✍️ جایگزینی در متن", font=("Segoe UI", 9, "bold"),
                                   bg="#313244", fg="#f9e2af", padx=8, pady=4, cursor="hand2")
            btn_replace.pack(side="left", padx=4)
            btn_replace.bind("<Button-1>", lambda e: replace_action())

        btn_dismiss = tk.Label(btn_frame, text=" ✕ بستن ", font=("Segoe UI", 9, "bold"),
                               bg="#313244", fg="#f38ba8", padx=8, pady=4, cursor="hand2")
        btn_dismiss.pack(side="right", padx=4)
        btn_dismiss.bind("<Button-1>", lambda e: self.close())

        # ── موقعیت‌یابی ──────────────────────────────────────────
        self.top.update_idletasks()
        req_w = w
        req_h = min(max(self.top.winfo_reqheight(), 160), max_h)

        screen_w = parent_root.winfo_screenwidth()
        screen_h = parent_root.winfo_screenheight()

        pos_x = x_cursor + 15
        pos_y = y_cursor + 15
        if pos_x + req_w > screen_w - 20:
            pos_x = x_cursor - req_w - 15
        if pos_y + req_h > screen_h - 40:
            pos_y = y_cursor - req_h - 15
        pos_x = max(10, min(pos_x, screen_w - req_w - 10))
        pos_y = max(10, min(pos_y, screen_h - req_h - 10))

        self.top.geometry(f"{req_w}x{req_h}+{pos_x}+{pos_y}")
        self.top.bind("<Escape>", lambda e: self.close())
        self.top.focus_set()

    def close(self):
        try:
            self.top.destroy()
        except Exception:
            pass
