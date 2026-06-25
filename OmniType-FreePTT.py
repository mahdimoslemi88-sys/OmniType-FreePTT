import sys
import os

# 🛡️ سپر محافظ برای جلوگیری از کرش هشدارهای پس‌زمینه در حالت No-Console ویندوز 11
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import tkinter as tk
import threading
import time
import pyaudio
import speech_recognition as sr
import keyboard
import pyperclip

# ==========================================
# تنظیمات فنی کارت صدا
# ==========================================
CHUNK = 1024        
FORMAT = pyaudio.paInt16 
CHANNELS = 1        
RATE = 16000        

class VoiceTyperGUI:
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
        
        # کدهای رنگی وضعیت چراغ مینیاتوری
        self.COLOR_IDLE = '#2ecc71'     # سبز = آماده کار
        self.COLOR_REC = '#e74c3c'      # قرمز = در حال ضبط
        self.COLOR_PROC = '#f1c40f'     # زرد = در حال پردازش گوگل
        self.COLOR_SUCCESS = '#3498db'  # آبی = تایپ موفقیت‌آمیز
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # افزایش جزیی قطر کادر به ۳۲ پیکسل برای رندر باکیفیت‌تر هندسه دایره
        self.size = 32
        
        # ساخت بوم نقاشی برای رندر کردن دایره کامل
        self.canvas = tk.Canvas(self.root, bg=self.TRANS_COLOR, highlightthickness=0, width=self.size, height=self.size)
        self.canvas.pack()
        
        # ساخت منوی کلیک‌راست روی دایره برای تنظیمات و خروج
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='#2d2d2d', fg='white', activebackground='#3498db', activeforeground='white', font=('Segoe UI', 9))
        
        # زیرمنوی کلید میانبر
        self.hotkey_menu = tk.Menu(self.context_menu, tearoff=0, bg='#2d2d2d', fg='white', activebackground='#3498db')
        self.hotkey_menu.add_command(label="Caps Lock", command=lambda: self.change_global_hotkey("caps lock"))
        self.hotkey_menu.add_command(label="F2", command=lambda: self.change_global_hotkey("f2"))
        self.hotkey_menu.add_command(label="Ctrl + `", command=lambda: self.change_global_hotkey("ctrl+`"))
        self.context_menu.add_cascade(label="⚙️ کلید میانبر", menu=self.hotkey_menu)
        
        # زیرمنوی زبان
        self.lang_menu = tk.Menu(self.context_menu, tearoff=0, bg='#2d2d2d', fg='white', activebackground='#3498db')
        self.lang_menu.add_command(label="فارسی (FA)", command=lambda: self.change_engine_language("fa-IR"))
        self.lang_menu.add_command(label="English (EN)", command=lambda: self.change_engine_language("en-US"))
        self.context_menu.add_cascade(label="🌐 زبان موتور", menu=self.lang_menu)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ خروج کامل", command=self.quit_app)
        
        # اتصال کلیک‌راست روی دایره به منو
        self.canvas.bind("<Button-3>", self.show_context_menu)
        
        self.is_recording = False
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.reset_timer = None
        self.hotkey_hook = None 
        
        # کانفیگ‌های پیش‌فرض
        self.current_hotkey = "caps lock"
        self.current_lang = "fa-IR"
        
        self.bind_hotkey_system()
        self.update_geometry()

    def bind_hotkey_system(self):
        if self.hotkey_hook:
            try: keyboard.remove_hotkey(self.hotkey_hook)
            except Exception: pass
        self.hotkey_hook = keyboard.add_hotkey(self.current_hotkey, self.start_recording, trigger_on_release=False)
        self.set_ui_state("idle")

    def change_global_hotkey(self, new_key):
        self.current_hotkey = new_key
        self.bind_hotkey_system()

    def change_engine_language(self, new_lang):
        self.current_lang = new_lang
        self.set_ui_state("idle")

    def update_geometry(self):
        """تنظیم دایره در دورترین نقطه گوشه پایین راست مانیتور"""
        x_position = self.screen_width - self.size - 20
        y_position = self.screen_height - self.size - 55
        self.root.geometry(f"{self.size}x{self.size}+{x_position}+{y_position}")

    def draw_circle(self, color):
        """رسم دایره کامل با متد تصحیح لبه‌های پیکسلی (Anti-aliased Real Drop)"""
        self.canvas.delete("all")
        # رسم یک دایره اصلی نرم با پدینگ مناسب از دیواره شفاف برای حذف دندانه‌ها
        self.canvas.create_oval(4, 4, self.size-4, self.size-4, fill=color, outline=color, width=1)

    def set_ui_state(self, state):
        """تغییر آنی رنگ دایره بر اساس وضعیت پروسس صوتی"""
        def update():
            if self.reset_timer:
                self.root.after_cancel(self.reset_timer)
                self.reset_timer = None

            if state == "idle":
                self.draw_circle(self.COLOR_IDLE)
            elif state == "recording":
                self.draw_circle(self.COLOR_REC)
            elif state == "processing":
                self.draw_circle(self.COLOR_PROC)
            elif state == "success":
                self.draw_circle(self.COLOR_SUCCESS)
                # بازگشت به رنگ سبز بعد از ۲ ثانیه
                self.reset_timer = self.root.after(2000, lambda: self.set_ui_state("idle"))
        self.root.after(0, update)

    def start_recording(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.set_ui_state("recording")
        threading.Thread(target=self.record_worker, daemon=True).start()

    def record_worker(self):
        self.frames = []
        try:
            stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        except Exception:
            self.is_recording = False
            self.set_ui_state("idle")
            return
            
        check_key = self.current_hotkey.split('+')[-1]
            
        while self.is_recording:
            if not keyboard.is_pressed(check_key):
                self.is_recording = False
                break
            try:
                data = stream.read(CHUNK)
                self.frames.append(data)  
            except Exception:
                break
                
        self.set_ui_state("processing")
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
            
        audio_data = b''.join(self.frames)
        self.recognize_audio(audio_data)

    def recognize_audio(self, raw_data):
        r = sr.Recognizer()
        audio = sr.AudioData(raw_data, RATE, 2) 
        try:
            text = r.recognize_google(audio, language=self.current_lang)
            pyperclip.copy(text)
            time.sleep(0.05) 
            keyboard.send('ctrl+v')
            keyboard.send('space')
            self.set_ui_state("success")
        except Exception:
            self.set_ui_state("idle")

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def quit_app(self):
        self.p.terminate()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = VoiceTyperGUI()
    app.run()