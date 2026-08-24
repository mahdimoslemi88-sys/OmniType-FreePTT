"""کلاس اصلی برنامه OmniType v2.1 — گوی شناور، ضبط PTT، منوها و اتصال همه ماژول‌ها."""
import collections
import ctypes
import math
import re
import threading
import time
import tkinter as tk
from ctypes import wintypes

import keyboard
import pyaudio
import pyperclip

from core import config, stats, updater
from core.audio import RATE, get_input_level, list_input_devices, pcm_to_wav_bytes
from core.config import ENV, save_env_dict
from core.dictionary import CUSTOM_DICT
from core.hotkey import is_hotkey_held
from core.media_control import MediaController
from core.normalizer import PersianNormalizer, convert_persian_letters_to_english
from engine.asr import recognize_google, transcribe_custom_api
from engine.local_whisper import HAS_FASTER_WHISPER, LOCAL_WHISPER, BASE_WHISPER_PROMPT
from engine.prompt_engineer import AIPromptEngineer
from engine.translator import LLMTranslatorEngine
from gui.api_settings_window import UniversalAPISettingsWindow
from gui.control_panel import ControlPanel
from gui.dictionary_window import CustomDictionaryWindow
from gui.document_translator import DocumentTranslatorWindow
from gui.hotkey_window import CustomHotkeyWindow
from gui.peek_popup import HighlightPeekPopup
from gui.system_tray import SystemTray


class VoiceTyperGUI:
    """کنترلر اصلی برنامه — گوی شناور، ضبط، تشخیص گفتار و تایپ ایمن."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VoiceTyper Micro Dot")

        # ترفند ایجاد پنجره کاملاً نامرئی و غیب کردن حاشیه‌ها
        self.TRANS_COLOR = '#abcdef'
        self.root.configure(bg=self.TRANS_COLOR)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.wm_attributes("-transparentcolor", self.TRANS_COLOR)

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # قطر گوی صوتی
        self.size = 58

        # بوم نقاشی
        self.canvas = tk.Canvas(self.root, bg=self.TRANS_COLOR, highlightthickness=0,
                                width=self.size, height=self.size)
        self.canvas.pack()

        # کانفیگ‌های پیش‌فرض
        # موتور اصلی تبدیل صوت به متن به‌صورت پیش‌فرض Google رایگان است؛
        # کاربر می‌تواند از تب «موتورها» موتور دیگری (Groq و ...) را انتخاب کند.
        self.current_engine = "google"
        self.active_engine_name = ""
        self.current_hotkey = "caps lock"
        self.current_lang = "fa"
        # توقف خودکار ویدیو/موزیک هنگام صحبت (خواندن از .env)
        self.auto_pause_media = ENV.get("AUTO_PAUSE_MEDIA", "true").strip().lower() in ("1", "true", "yes", "on")
        # ── VAD: تشخیص فعالیت گفتار و توقف خودکار هنگام سکوت ──
        self.vad_enabled = ENV.get("VAD_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")
        try:
            self.vad_silence_timeout = float(ENV.get("VAD_SILENCE_TIMEOUT", "1.5"))
        except (TypeError, ValueError):
            self.vad_silence_timeout = 1.5
        try:
            self.vad_threshold = float(ENV.get("VAD_THRESHOLD", "0.02"))
        except (TypeError, ValueError):
            self.vad_threshold = 0.02
        self.media = MediaController(enabled=self.auto_pause_media)
        # دستگاه ورودی صوت انتخابی (ایندکس pyaudio؛ اگر خالی باشد پیش‌فرض سیستم)
        self.input_device_index = None
        raw_dev = ENV.get("INPUT_DEVICE_INDEX", "")
        if raw_dev:
            try:
                self.input_device_index = int(raw_dev)
            except (TypeError, ValueError):
                self.input_device_index = None
        # شنوندهٔ سطح صدا (پنل کنترل برای نشانگر زنده آن را ثبت می‌کند)
        self._level_listener = None
        self._level_throttle = 0
        self.recording_mode = "hotkey"
        self.anim_timer = None
        self.anim_step = 0
        self.current_state = "idle"
        self.target_hwnd = None

        # حافظه کانتکست ۱۰ صحبت اخیر کاربر
        self.history = collections.deque(maxlen=10)

        # رویدادهای موس
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.show_context_menu)

        self.is_recording = False
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.reset_timer = None
        self.hotkey_hook = None
        self.translate_hotkey_fa_en = None
        self.translate_hotkey_en_fa = None

        self.bind_hotkey_system()
        self.update_geometry()
        self.apply_no_activate_style()
        self.start_idle_breathing()

        # آیکون System Tray در هیدن‌آیکون‌های تسک‌بار
        self.sys_tray = SystemTray()
        self.sys_tray.on("dict", self.open_custom_dict_window)
        self.sys_tray.on("api_settings", self.open_api_keys_window)
        self.sys_tray.on("doc_translator", self.open_document_translator_window)
        self.sys_tray.on("toggle_pause", self.toggle_auto_pause_media)
        self.sys_tray.on("vram", self.free_vram_action)
        self.sys_tray.on("updates", self.check_for_updates)
        self.sys_tray.on("quit", self.quit_app)
        self.sys_tray.set_auto_pause_state(self.auto_pause_media)
        self.sys_tray.create()

        # وضعیت به‌روزرسانی + بررسی بی‌صدا در پس‌زمینه هنگام شروع
        self.update_state = {}
        self.check_for_updates(show_dialog=False)

    # ── پنجره ────────────────────────────────────────────────────

    def apply_no_activate_style(self):
        """جلوگیری از دزدیده شدن فوکوس پنجره فعال (WS_EX_NOACTIVATE)."""
        try:
            self.root.update()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE)
        except Exception:
            pass

    def update_geometry(self):
        """تنظیم موقعیت گوی در گوشه پایین-راست ناحیه کاری ویندوز."""
        try:
            rect = wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
            usable_width = rect.right
            usable_height = rect.bottom
        except Exception:
            usable_width = self.screen_width
            usable_height = self.screen_height - 60

        x_position = usable_width - self.size - 22
        y_position = usable_height - self.size - 22
        self.root.geometry(f"{self.size}x{self.size}+{x_position}+{y_position}")

    # ── رویدادهای موس ────────────────────────────────────────────

    def on_left_click(self, event):
        """کلیک چپ روی گوی: شروع/توقف ضبط با موس."""
        if self.is_recording:
            self.is_recording = False
        else:
            self.start_recording(mode="mouse")

    def show_context_menu(self, event):
        """باز کردن پنجره کامل کنترل به‌جای منوی راست‌کلیک."""
        # بستن پنجره قبلی (در صورت باز بودن) و باز کردن پنجره جدید
        try:
            if getattr(self, "control_panel_win", None) is not None:
                try:
                    self.control_panel_win.destroy()
                except Exception:
                    pass
        except Exception:
            pass
        self.control_panel_win = ControlPanel(self)
        self.control_panel_win.refresh()

    # ── انیمیشن‌ها ────────────────────────────────────────────────

    def cancel_anim(self):
        if self.anim_timer:
            self.root.after_cancel(self.anim_timer)
            self.anim_timer = None

    def draw_idle_breathing(self):
        if self.current_state != "idle":
            return
        self.anim_step = (self.anim_step + 1) % 60
        pulse = math.sin(self.anim_step * math.pi / 30)
        cx, cy = self.size / 2, self.size / 2
        r_core = 14.5 + 1.2 * pulse
        r_halo = 22.5 + 2.2 * pulse

        self.canvas.delete("all")
        self.canvas.create_oval(cx - r_halo, cy - r_halo, cx + r_halo, cy + r_halo,
                                fill="", outline="#34d399", width=2.0)
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core,
                                fill="#10b981", outline="#059669", width=2.0)
        hx, hy = cx - r_core * 0.35, cy - r_core * 0.35
        hr = r_core * 0.35
        self.canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr, fill="#ffffff", outline="")

        if self.current_state == "idle":
            self.anim_timer = self.root.after(40, self.draw_idle_breathing)

    def draw_recording_pulse(self):
        if not self.is_recording:
            return
        self.anim_step = (self.anim_step + 1) % 40
        cx, cy = self.size / 2, self.size / 2

        self.canvas.delete("all")
        p1 = (self.anim_step % 20) / 20.0
        p2 = ((self.anim_step + 10) % 20) / 20.0
        r1, w1 = 15 + p1 * 12, max(0.5, 3.0 * (1.0 - p1))
        r2, w2 = 15 + p2 * 12, max(0.5, 3.0 * (1.0 - p2))
        self.canvas.create_oval(cx - r1, cy - r1, cx + r1, cy + r1, outline="#f87171", width=w1)
        self.canvas.create_oval(cx - r2, cy - r2, cx + r2, cy + r2, outline="#fca5a5", width=w2)

        r_core = 15.0
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core,
                                fill="#ef4444", outline="#dc2626", width=2.0)
        hx, hy = cx - r_core * 0.35, cy - r_core * 0.35
        hr = r_core * 0.35
        self.canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr, fill="#ffffff", outline="")

        if self.is_recording:
            self.anim_timer = self.root.after(30, self.draw_recording_pulse)

    def draw_processing_spinner(self):
        if self.current_state != "processing":
            return
        self.anim_step = (self.anim_step + 1) % 360
        cx, cy = self.size / 2, self.size / 2
        r_core, r_ring = 14.5, 22.5

        self.canvas.delete("all")
        start_angle = (self.anim_step * 8) % 360
        self.canvas.create_arc(cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring,
                               start=start_angle, extent=110, style="arc",
                               outline="#fbbf24", width=3.0)
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core,
                                fill="#f59e0b", outline="#d97706", width=2.0)
        hx, hy = cx - r_core * 0.35, cy - r_core * 0.35
        hr = r_core * 0.35
        self.canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr, fill="#ffffff", outline="")

        if self.current_state == "processing":
            self.anim_timer = self.root.after(30, self.draw_processing_spinner)

    def draw_success_pulse(self):
        if self.current_state != "success":
            return
        self.anim_step = (self.anim_step + 1) % 30
        cx, cy = self.size / 2, self.size / 2
        r_core = 15.0
        pulse_r = 15.0 + (self.anim_step / 30.0) * 11
        width = max(0.5, 3.0 * (1.0 - self.anim_step / 30.0))

        self.canvas.delete("all")
        self.canvas.create_oval(cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r,
                                outline="#06b6d4", width=width)
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core,
                                fill="#3b82f6", outline="#2563eb", width=2.0)
        hx, hy = cx - r_core * 0.35, cy - r_core * 0.35
        hr = r_core * 0.35
        self.canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr, fill="#ffffff", outline="")

        if self.current_state == "success" and self.anim_step < 29:
            self.anim_timer = self.root.after(25, self.draw_success_pulse)

    def start_idle_breathing(self):
        self.current_state = "idle"
        self.draw_idle_breathing()

    def set_ui_state(self, state):
        """تغییر آنی وضعیت و انیمیشن گوی صوتی."""
        def update():
            self.cancel_anim()
            if self.reset_timer:
                self.root.after_cancel(self.reset_timer)
                self.reset_timer = None

            self.current_state = state
            self.anim_step = 0

            if state == "idle":
                self.draw_idle_breathing()
            elif state == "recording":
                self.draw_recording_pulse()
            elif state == "processing":
                self.draw_processing_spinner()
            elif state == "success":
                self.draw_success_pulse()
                self.reset_timer = self.root.after(2000, lambda: self.set_ui_state("idle"))

        self.root.after(0, update)

        # به‌روزرسانی tooltip آیکون تسک‌بار با وضعیت جاری
        try:
            state_titles = {
                "idle": "OmniType v2.2 — آماده",
                "recording": "OmniType v2.2 — در حال ضبط...",
                "processing": "OmniType v2.2 — در حال پردازش...",
                "success": "OmniType v2.2 — تایپ شد ✓",
            }
            self.sys_tray.update_tooltip(state_titles.get(state, "OmniType v2.2"))
        except Exception:
            pass

    # ── پرامپت و منو ─────────────────────────────────────────────

    def get_dynamic_prompt(self):
        """ساخت پرامپت با کانتکست واژه‌نامه تخصصی و صحبت‌های اخیر کاربر."""
        prompt_parts = [BASE_WHISPER_PROMPT]
        dict_prompt = CUSTOM_DICT.get_prompt_string()
        if dict_prompt:
            prompt_parts.append(dict_prompt)
        if self.history:
            recent_context = " | ".join(list(self.history)[-3:])
            prompt_parts.append(f"زمینه صحبت‌های اخیر: [{recent_context}]")
        return " ".join(prompt_parts)

    # ── پنجره‌ها ─────────────────────────────────────────────────

    def open_custom_dict_window(self):
        """پنجره مدیریت واژه‌نامه تخصصی."""
        CustomDictionaryWindow(self, CUSTOM_DICT)

    def open_custom_hotkey_window(self):
        CustomHotkeyWindow(self)

    def open_api_keys_window(self):
        UniversalAPISettingsWindow(self)

    def open_document_translator_window(self):
        """پنجره ترجمه اسناد — ذخیره پنجره فعال برای تایپ نتیجه در همان پنجره."""
        try:
            self.target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass
        DocumentTranslatorWindow(self)

    # ── توقف خودکار رسانه ────────────────────────────────────────

    def toggle_auto_pause_media(self):
        """فعال/غیرفعال‌سازی توقف خودکار رسانه (با ذخیره در .env)."""
        self.auto_pause_media = not self.auto_pause_media
        self.media.set_enabled(self.auto_pause_media)
        try:
            save_env_dict({"AUTO_PAUSE_MEDIA": "true" if self.auto_pause_media else "false"})
        except Exception:
            pass
        self.sys_tray.set_auto_pause_state(self.auto_pause_media)
        self.set_ui_state("idle")

    def toggle_vad(self):
        """فعال/غیرفعال‌سازی VAD (تشخیص سکوت و توقف خودکار ضبط)."""
        self.vad_enabled = not self.vad_enabled
        try:
            save_env_dict({"VAD_ENABLED": "true" if self.vad_enabled else "false"})
        except Exception:
            pass

    def set_vad_settings(self, enabled=None, silence_timeout=None, threshold=None):
        """تنظیم پارامترهای VAD و ذخیره در .env."""
        updates = {}
        if enabled is not None:
            self.vad_enabled = enabled
            updates["VAD_ENABLED"] = "true" if enabled else "false"
        if silence_timeout is not None:
            self.vad_silence_timeout = float(silence_timeout)
            updates["VAD_SILENCE_TIMEOUT"] = str(self.vad_silence_timeout)
        if threshold is not None:
            self.vad_threshold = float(threshold)
            updates["VAD_THRESHOLD"] = str(self.vad_threshold)
        try:
            save_env_dict(updates)
        except Exception:
            pass

    # ── تاریخچه ──────────────────────────────────────────────────

    def copy_history_item(self, text):
        pyperclip.copy(text)
        time.sleep(0.05)
        keyboard.send('ctrl+v')
        self.set_ui_state("success")

    def clear_history_action(self):
        self.history.clear()
        self.set_ui_state("idle")

    # ── هوک‌های کیبورد ───────────────────────────────────────────

    def bind_hotkey_system(self):
        if self.hotkey_hook:
            try:
                keyboard.remove_hotkey(self.hotkey_hook)
            except Exception:
                pass

        for attr in ['translate_hotkey_fa_en', 'translate_hotkey_en_fa', 'tr_fa_1', 'tr_fa_2',
                     'tr_en_1', 'tr_en_2', 'tr_peek_1', 'tr_peek_2', 'tr_peek_3',
                     'tr_doc_1', 'tr_doc_2', 'tr_dict_1', 'tr_dict_2', 'tr_p_1', 'tr_p_2']:
            hook = getattr(self, attr, None)
            if hook:
                try:
                    keyboard.remove_hotkey(hook)
                except Exception:
                    pass

        self.hotkey_hook = keyboard.add_hotkey(self.current_hotkey,
                                               lambda: self.start_recording(mode="hotkey"),
                                               trigger_on_release=False)

        # ترجمه اسناد (Ctrl+Alt+F)
        doc_cb = lambda: self.root.after(0, self.open_document_translator_window)
        try:
            self.tr_doc_1 = keyboard.add_hotkey("ctrl+alt+f", doc_cb, trigger_on_release=False)
        except Exception:
            pass
        try:
            self.tr_doc_2 = keyboard.add_hotkey("ctrl+alt+ب", doc_cb, trigger_on_release=False)
        except Exception:
            pass

        # واژه‌نامه تخصصی (Ctrl+Alt+D)
        dict_cb = lambda: self.root.after(0, self.open_custom_dict_window)
        try:
            self.tr_dict_1 = keyboard.add_hotkey("ctrl+alt+d", dict_cb, trigger_on_release=False)
        except Exception:
            pass
        try:
            self.tr_dict_2 = keyboard.add_hotkey("ctrl+alt+ی", dict_cb, trigger_on_release=False)
        except Exception:
            pass

        # ترجمه پاپ‌آپ (Ctrl+Alt+X)
        peek_cb = lambda: self.root.after(0, self.translate_peek_action)
        for name, key in [("tr_peek_1", "ctrl+alt+x"), ("tr_peek_2", "ctrl+alt+ط"),
                          ("tr_peek_3", "ctrl+alt+خ")]:
            try:
                setattr(self, name, keyboard.add_hotkey(key, peek_cb, trigger_on_release=False))
            except Exception:
                pass

        # ترجمه FA→EN (Ctrl+Alt+Z)
        fa_en_cb = lambda: self.root.after(0, self.translate_manual_action, "fa_to_en")
        for name, key in [("tr_fa_1", "ctrl+alt+z"), ("tr_fa_2", "ctrl+alt+ظ"), (None, "ctrl+alt+ژ")]:
            try:
                hook = keyboard.add_hotkey(key, fa_en_cb, trigger_on_release=False)
                if name:
                    setattr(self, name, hook)
            except Exception:
                pass

        # ترجمه EN→FA (Ctrl+Alt+Shift+Z)
        en_fa_cb = lambda: self.root.after(0, self.translate_manual_action, "en_to_fa")
        for name, key in [("tr_en_1", "ctrl+alt+shift+z"), ("tr_en_2", "ctrl+alt+shift+ظ"),
                          (None, "ctrl+alt+shift+ژ")]:
            try:
                hook = keyboard.add_hotkey(key, en_fa_cb, trigger_on_release=False)
                if name:
                    setattr(self, name, hook)
            except Exception:
                pass

        # مهندسی پرامپت (Ctrl+Alt+P)
        p_cb = lambda: self.root.after(0, self.prompt_engineer_action)
        for name, key in [("tr_p_1", "ctrl+alt+p"), ("tr_p_2", "ctrl+alt+ح")]:
            try:
                setattr(self, name, keyboard.add_hotkey(key, p_cb, trigger_on_release=False))
            except Exception:
                pass

        self.set_ui_state("idle")

    # ── اکشن‌ها: مهندسی پرامپت / ترجمه ───────────────────────────

    def get_selected_text(self):
        """خواندن متن انتخاب‌شده از پنجره فعال از طریق کلیپ‌بورد (بدون دست زدن به محتوای صفحه)."""
        try:
            self.target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass

        time.sleep(0.15)
        try:
            keyboard.release('alt')
            keyboard.release('ctrl')
        except Exception:
            pass

        old_clip = ""
        try:
            old_clip = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy("___OMNI_EMPTY___")
        time.sleep(0.04)
        keyboard.send('ctrl+c')
        time.sleep(0.1)

        copied = ""
        try:
            copied = pyperclip.paste().strip()
        except Exception:
            pass

        text = ""
        if copied and copied != "___OMNI_EMPTY___":
            text = copied
        else:
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass
        return text, old_clip

    def prompt_engineer_action(self):
        """تبدیل متن انتخابی به پرامپت مهندسی‌شده AI با کلید میانبر Ctrl+Alt+P."""
        print("[OmniType] AI Prompt Engineer triggered!")
        text_orig, saved_clip = self.get_selected_text()
        if not text_orig:
            self.set_ui_state("idle")
            return

        self.set_ui_state("processing")

        def worker():
            try:
                prompt_engineered = AIPromptEngineer.generate_engineered_prompt(text_orig)
            except Exception as e:
                print(f"[OmniType] Prompt Engineer error: {e}")
                prompt_engineered = f"[خطا] {e}"

            def update_ui():
                if prompt_engineered.startswith("[خطا]"):
                    self.set_ui_state("idle")
                    try:
                        import tkinter.messagebox as mb
                        mb.showerror("پرامپت مهندسی‌شده", prompt_engineered, parent=self.root)
                    except Exception:
                        pass
                    return
                self.safe_type_and_restore_clipboard(prompt_engineered)
                self.set_ui_state("success")

            self.root.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def translate_peek_action(self):
        """ترجمه متن انتخاب شده و نمایش در پاپ‌آپ شناور در محل نشانگر موس."""
        print("[OmniType] Highlight Peek Translation triggered!")

        pt = wintypes.POINT()
        try:
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            cursor_x, cursor_y = pt.x, pt.y
        except Exception:
            cursor_x, cursor_y = self.screen_width // 2, self.screen_height // 2

        try:
            self.target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass

        self.set_ui_state("processing")

        def worker():
            time.sleep(0.15)
            try:
                keyboard.release('alt')
                keyboard.release('ctrl')
            except Exception:
                pass

            old_clip = ""
            try:
                old_clip = pyperclip.paste()
            except Exception:
                pass

            pyperclip.copy("___OMNI_EMPTY___")
            time.sleep(0.04)
            keyboard.send('ctrl+c')
            time.sleep(0.1)

            copied = ""
            try:
                copied = pyperclip.paste().strip()
            except Exception:
                pass

            text_to_translate = ""
            if copied and copied != "___OMNI_EMPTY___":
                text_to_translate = copied
            else:
                if self.history:
                    text_to_translate = list(self.history)[-1]
                try:
                    pyperclip.copy(old_clip)
                except Exception:
                    pass

            if not text_to_translate:
                print("[OmniType] No text found for peek translation.")
                self.set_ui_state("idle")
                return

            has_fa = bool(re.search(r'[\u0600-\u06FF]', text_to_translate))
            mode = "fa_to_en" if has_fa else "en_to_fa"

            try:
                translated = LLMTranslatorEngine.translate(text_to_translate, mode=mode)
                if translated:
                    translated = CUSTOM_DICT.apply_replacements(translated)
                    self.history.append(translated)
                    self.set_ui_state("success")

                    def replace_cb(new_text):
                        self.safe_type_and_restore_clipboard(new_text)

                    self.root.after(0, lambda: HighlightPeekPopup(
                        self.root, text_to_translate, translated, cursor_x, cursor_y,
                        on_replace_callback=replace_cb,
                    ))
                else:
                    self.set_ui_state("idle")
            except Exception as e:
                print(f"Error in peek translation worker: {e}")
                self.set_ui_state("idle")

        threading.Thread(target=worker, daemon=True).start()

    def translate_manual_action(self, mode="fa_to_en"):
        """ترجمه دستی هوشمند متن انتخاب‌شده یا آخرین صحبت کاربر."""
        print(f"[OmniType] Manual translation triggered! (mode: {mode})")

        try:
            self.target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass

        self.set_ui_state("processing")

        def worker():
            time.sleep(0.15)
            try:
                keyboard.release('alt')
                keyboard.release('ctrl')
            except Exception:
                pass

            old_clip = ""
            try:
                old_clip = pyperclip.paste()
            except Exception:
                pass

            pyperclip.copy("___OMNI_EMPTY___")
            time.sleep(0.04)
            keyboard.send('ctrl+c')
            time.sleep(0.1)

            copied = ""
            try:
                copied = pyperclip.paste().strip()
            except Exception:
                pass

            text_to_translate = ""
            if copied and copied != "___OMNI_EMPTY___":
                text_to_translate = copied
            else:
                if self.history:
                    text_to_translate = list(self.history)[-1]
                try:
                    pyperclip.copy(old_clip)
                except Exception:
                    pass

            if not text_to_translate:
                print("[OmniType] No text found to translate (selected or history).")
                self.set_ui_state("idle")
                return

            try:
                translated = LLMTranslatorEngine.translate(text_to_translate, mode=mode)
                if translated:
                    translated = CUSTOM_DICT.apply_replacements(translated)
                    self.history.append(translated)
                    self.safe_type_and_restore_clipboard(translated)
                    self.set_ui_state("success")
                else:
                    self.set_ui_state("idle")
            except Exception as e:
                print(f"Error in manual translation worker: {e}")
                self.set_ui_state("idle")

        threading.Thread(target=worker, daemon=True).start()

    # ── تایپ و تشخیص گفتار ────────────────────────────────────────

    def safe_type_and_restore_clipboard(self, text):
        """تایپ ایمن متن و بازگردانی کلیپ‌بورد قبلی کاربر."""
        if getattr(self, 'target_hwnd', None):
            try:
                ctypes.windll.user32.SetForegroundWindow(self.target_hwnd)
                time.sleep(0.03)
            except Exception:
                pass

        old_clip = ""
        try:
            old_clip = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(text)
        time.sleep(0.05)
        keyboard.send('ctrl+v')
        keyboard.send('space')

        def restore():
            time.sleep(0.5)
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass

        threading.Thread(target=restore, daemon=True).start()

    def recognize_audio(self, raw_data):
        if not raw_data or len(raw_data) < 2000:
            self.set_ui_state("idle")
            return

        text = ""
        try:
            wav_bytes = pcm_to_wav_bytes(raw_data)

            lang_code = "fa"
            prompt = self.get_dynamic_prompt()
            task_mode = "transcribe"

            if self.current_lang == "translate_fa_en":
                lang_code = "fa"
                task_mode = "translate"
                prompt = "Translate the spoken Persian audio into fluent, natural English text."
            elif self.current_lang == "translate_en_fa":
                lang_code = "en"
                task_mode = "translate"
                prompt = "Translate the spoken English audio into fluent Persian text."
            elif self.current_lang == "en":
                lang_code = "en"
                prompt = "English speech transcription."
            elif self.current_lang == "auto":
                lang_code = None
                prompt = self.get_dynamic_prompt()

            if self.current_engine == "local":
                text = LOCAL_WHISPER.transcribe(wav_bytes, lang=lang_code, prompt=prompt, task=task_mode)
            elif self.current_engine in ("google", ""):
                text = recognize_google(raw_data, lang=self.current_lang)
            else:  # هر موتور سفارشی (Groq / OpenAI / OpenRouter / ...)
                try:
                    text = transcribe_custom_api(wav_bytes, lang_code=lang_code, prompt=prompt,
                                                 preferred_engine=self.current_engine)
                except Exception as e:
                    print(f"Cloud ASR API failed: {e}. Falling back to Google Speech...")
                    text = recognize_google(raw_data, lang=self.current_lang)

            if text:
                if self.current_lang == "prompt_engineer":
                    try:
                        text = AIPromptEngineer.generate_engineered_prompt(text)
                    except Exception as e:
                        # در exe کنسول دیده نمی‌شود؛ خطا را برای کاربر نشان بده
                        err = str(e)
                        self.set_ui_state("idle")

                        def _notify():
                            try:
                                import tkinter.messagebox as mb
                                mb.showerror("مهندسی پرامپت",
                                             f"خطا در ساخت پرامپت مهندسی‌شده:\n{err}",
                                             parent=self.root)
                            except Exception:
                                pass
                        self.root.after(0, _notify)
                        return
                elif self.current_lang in ["translate_fa_en", "translate_en_fa"]:
                    mode = "fa_to_en" if self.current_lang == "translate_fa_en" else "en_to_fa"
                    text = LLMTranslatorEngine.translate(text, mode=mode)
                else:
                    # ابتدا تبدیل تلفظ فارسی حروف انگلیسی (مثلاً «پی» → "P")
                    text = convert_persian_letters_to_english(text)
                    if self.current_lang in ["fa", "auto", "translate_en_fa"]:
                        text = PersianNormalizer.normalize(text)
                    text = CUSTOM_DICT.apply_replacements(text)

                self.history.append(text)
                self.safe_type_and_restore_clipboard(text)
                self.set_ui_state("success")
                # ── ثبت آمار + به‌روزرسانی تسک‌بار ──
                try:
                    elapsed = time.time() - getattr(self, "_recording_start", time.time())
                    stats.record_typing(text, engine=self.current_engine, duration_sec=elapsed)
                    _data = stats.get_stats()
                    _today = __import__("datetime").date.today().isoformat()
                    _tw = _data.get("daily_history", {}).get(_today, {}).get("words", 0)
                    self.sys_tray.set_stats(_data["total_words"], _tw)
                except Exception:
                    pass
            else:
                self.set_ui_state("idle")
        except Exception as e:
            print(f"Error in recognition: {e}")
            self.set_ui_state("idle")

    # ── ضبط ───────────────────────────────────────────────────────

    def start_recording(self, mode="hotkey"):
        if self.is_recording:
            return

        try:
            self.target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            self.target_hwnd = None

        self.recording_mode = mode
        self.is_recording = True
        self._recording_start = time.time()
        # توقف خودکار ویدیو/موزیک هنگام شروع صحبت
        self.media.pause()
        self.set_ui_state("recording")

        threading.Thread(target=self.record_worker, daemon=True).start()

    def record_worker(self):
        self.frames = []
        self._level_throttle = 0
        try:
            stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                                 input=True, frames_per_buffer=1024,
                                 input_device_index=self.input_device_index)
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.is_recording = False
            self.set_ui_state("idle")
            self._notify_level(0.0)
            return

        # ── VAD state ──────────────────────────────────────────────
        silence_start = None
        speech_started = False

        while self.is_recording:
            if self.recording_mode == "hotkey" and not is_hotkey_held(self.current_hotkey):
                self.is_recording = False
                break
            try:
                data = stream.read(1024, exception_on_overflow=False)
                self.frames.append(data)
                level = get_input_level(data)
                self._notify_level(level)

                # ── VAD: تشخیص فعالیت گفتار / سکوت ──
                if self.vad_enabled:
                    now = time.time()
                    if level >= self.vad_threshold:
                        # صدا شنیده شد → شروع صحبت یا ادامه
                        speech_started = True
                        silence_start = None
                    else:
                        # سکوت
                        if speech_started:
                            if silence_start is None:
                                silence_start = now
                            elif (now - silence_start) >= self.vad_silence_timeout:
                                print("[VAD] Silence detected — auto-stopping recording.")
                                self.is_recording = False
                                break
            except Exception:
                break

        # ادامه خودکار ویدیو/موزیک پس از پایان صحبت
        self.media.resume()

        self.set_ui_state("processing")
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass

        # پایان ضبط → نشانگر سطح صدا صفر شود
        if self._level_listener:
            try:
                self.root.after(0, lambda: self._level_listener(0.0))
            except Exception:
                pass

        audio_data = b''.join(self.frames)
        self.recognize_audio(audio_data)

    # ── سطح صدا و دستگاه ورودی ────────────────────────────────────

    def _notify_level(self, level):
        """ارسال سطح صدا به شنونده (پنل کنترل) با کاهش نرخ تا UI سنگین نشود."""
        if not self._level_listener:
            return
        self._level_throttle += 1
        if self._level_throttle % 3 != 0:
            return
        try:
            self.root.after(0, lambda l=level: self._level_listener(l))
        except Exception:
            pass

    def set_level_listener(self, cb):
        """ثبت شنوندهٔ سطح صدا (پنل کنترل). cb(None) یعنی لغو ثبت."""
        self._level_listener = cb
        if cb is None:
            self._level_throttle = 0

    def set_input_device(self, index):
        """تنظیم دستگاه ورودی صوت و ذخیره در .env."""
        try:
            index = int(index)
            self.input_device_index = index if index >= 0 else None
        except (TypeError, ValueError):
            self.input_device_index = None
        try:
            save_env_dict({"INPUT_DEVICE_INDEX": "" if self.input_device_index is None
                            else str(self.input_device_index)})
        except Exception:
            pass

    # ── موتور و تنظیمات ──────────────────────────────────────────

    def change_engine(self, engine_name):
        """تغییر موتور: google / local / نام یک موتور سفارشی از لیست."""
        if engine_name == "google":
            self.current_engine = "google"
            self.active_engine_name = ""
        elif engine_name == "local":
            self.current_engine = "local"
            self.active_engine_name = ""
            if HAS_FASTER_WHISPER:
                LOCAL_WHISPER.preload_model_async("large-v3-turbo")
        else:
            # موتور سفارشی از لیست — فعال‌سازی و ذخیره در .env
            try:
                config.set_active_engine(engine_name)
                self.active_engine_name = engine_name
                self.current_engine = engine_name
            except Exception as e:
                print(f"Engine activation failed: {e}")
            LOCAL_WHISPER.unload_model()
        self.set_ui_state("idle")

    def free_vram_action(self):
        LOCAL_WHISPER.unload_model()
        # بازگشت به موتور پیش‌فرض Google رایگان برای تبدیل صوت
        self.current_engine = "google"
        self.active_engine_name = ""
        self.set_ui_state("idle")

    def change_global_hotkey(self, new_key):
        self.current_hotkey = new_key
        self.bind_hotkey_system()

    def change_engine_language(self, new_lang):
        self.current_lang = new_lang
        self.set_ui_state("idle")

    # ── به‌روزرسانی ────────────────────────────────────────────────

    def check_for_updates(self, show_dialog=True):
        """بررسی به‌روزرسانی در thread جداگانه و به‌روزرسانی وضعیت/اعلام نتیجه."""
        def worker():
            info = updater.check_for_update()

            def finish():
                self.update_state = info or {}
                if info and info.get("available"):
                    try:
                        self.sys_tray.update_tooltip(
                            f"نسخهٔ جدید {info['latest']} موجود است — راست‌کلیک تسکبار")
                    except Exception:
                        pass
                    if show_dialog:
                        self._show_update_dialog(info)
                elif show_dialog:
                    self._show_update_dialog(None)

            try:
                self.root.after(0, finish)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _show_update_dialog(self, info):
        """نمایش نتیجهٔ چک به‌روزرسانی برای کاربر."""
        try:
            from tkinter import messagebox as mb
        except Exception:
            return
        if not info:
            mb.showinfo("به‌روزرسانی", "در حال حاضر از آخرین نسخه استفاده می‌کنید ✅", parent=self.root)
            return
        msg = (f"نسخهٔ جدید **{info['latest']}** در دسترس است.\n\n"
               f"نسخهٔ فعلی شما: {info['current']}\n"
               f"ریلیز: {info['url']}")
        if info.get("download_url"):
            msg += f"\n\nفایل دانلود: {info['asset_name']}"
        mb.showinfo("به‌روزرسانی موجود", msg, parent=self.root)

    # ── خروج ──────────────────────────────────────────────────────

    def quit_app(self):
        """خروج کامل و تمیز: توقف رسانه، تسک‌بار، هوک‌ها و صدا."""
        try:
            self.media.reset()
        except Exception:
            pass
        try:
            self.sys_tray.stop()
        except Exception:
            pass
        LOCAL_WHISPER.unload_model()
        try:
            self.p.terminate()
        except Exception:
            pass
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
