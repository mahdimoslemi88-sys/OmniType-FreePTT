import sys
import os

# 🛡️ سپر محافظ برای جلوگیری از کرش هشدارهای پس‌زمینه در حالت No-Console ویندوز 11
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import gc
import io
import re
import json
import wave
import time
import math
import ctypes
from ctypes import wintypes

# 🎯 فعال‌سازی وضوح تصویر فوق‌العاده بالا و برداری (High-DPI Awareness v2)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import threading
import collections
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import pyaudio
import speech_recognition as sr
import keyboard
import pyperclip

# وارد کردن ماژول نرمالساز اختصاصی متون فارسی (فاز ۲)
try:
    from normalizer import PersianNormalizer
except ImportError:
    class PersianNormalizer:
        @classmethod
        def normalize(cls, text): return text

# وارد کردن پکیج Faster-Whisper برای ASR محلی و آفلاین (فاز ۱)
HAS_FASTER_WHISPER = False
try:
    import ctranslate2
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False

# ==========================================
# پرامپت پایه‌ای هدایت‌گر ویسپر
# ==========================================
BASE_WHISPER_PROMPT = "متن پیاده‌سازی شده صحبت‌های فارسی همراه با اصطلاحات و کلمات انگلیسی مانند Python, Code, Download, VS Code."

# ==========================================
# خواندن تنظیمات از فایل .env
# ==========================================
def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars

ENV = load_env()

# ==========================================
# تنظیمات ارائه‌دهنده سرویس‌های صوتی و متنی (Universal OpenAI-Compatible & Presets)
# ==========================================
CUSTOM_ASR_BASE_URL = ENV.get("CUSTOM_ASR_BASE_URL", "https://api.groq.com/openai/v1")
CUSTOM_ASR_API_KEY = ENV.get("CUSTOM_ASR_API_KEY", "")
CUSTOM_ASR_MODEL = ENV.get("CUSTOM_ASR_MODEL", "whisper-large-v3-turbo")

CUSTOM_LLM_BASE_URL = ENV.get("CUSTOM_LLM_BASE_URL", "https://api.groq.com/openai/v1")
CUSTOM_LLM_API_KEY = ENV.get("CUSTOM_LLM_API_KEY", "")
CUSTOM_LLM_MODEL = ENV.get("CUSTOM_LLM_MODEL", "llama-3.3-70b-versatile")

GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")

# برای سازگاری با تنظیمات قبلی
if not CUSTOM_ASR_API_KEY:
    if ENV.get("GROQ_API_KEY"):
        CUSTOM_ASR_API_KEY = ENV.get("GROQ_API_KEY")

if not CUSTOM_LLM_API_KEY and ENV.get("GROQ_API_KEY"):
    CUSTOM_LLM_API_KEY = ENV.get("GROQ_API_KEY")

def save_env_dict(updates):
    global ENV, CUSTOM_ASR_BASE_URL, CUSTOM_ASR_API_KEY, CUSTOM_ASR_MODEL
    global CUSTOM_LLM_BASE_URL, CUSTOM_LLM_API_KEY, CUSTOM_LLM_MODEL, GEMINI_API_KEY
    
    for k, v in updates.items():
        ENV[k] = v
        
    CUSTOM_ASR_BASE_URL = ENV.get("CUSTOM_ASR_BASE_URL", "https://api.groq.com/openai/v1")
    CUSTOM_ASR_API_KEY = ENV.get("CUSTOM_ASR_API_KEY", "")
    CUSTOM_ASR_MODEL = ENV.get("CUSTOM_ASR_MODEL", "whisper-large-v3-turbo")

    CUSTOM_LLM_BASE_URL = ENV.get("CUSTOM_LLM_BASE_URL", "https://api.groq.com/openai/v1")
    CUSTOM_LLM_API_KEY = ENV.get("CUSTOM_LLM_API_KEY", "")
    CUSTOM_LLM_MODEL = ENV.get("CUSTOM_LLM_MODEL", "llama-3.3-70b-versatile")

    GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
    key_indices = {}
    for i, line in enumerate(lines):
        if "=" in line and not line.strip().startswith("#"):
            k = line.split("=", 1)[0].strip()
            key_indices[k] = i

    for k, v in updates.items():
        if k in key_indices:
            lines[key_indices[k]] = f"{k}={v}\n"
        else:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(f"{k}={v}\n")
            
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

# ==========================================
# مدیریت واژه‌نامه تخصصی اصطلاحات فنی (Custom Dictionary Engine)
# ==========================================
class CustomDictionaryManager:
    """مدیریت واژه‌نامه تخصصی اصطلاحات، لغات انگلیسی و جایگزینی هوشمند"""
    def __init__(self, file_path="custom_dictionary.json"):
        self.file_path = os.path.join(os.path.dirname(__file__), file_path)
        self.prompts = []
        self.replacements = {}
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.prompts = data.get("prompts", [])
                    self.replacements = data.get("replacements", {})
            except Exception as e:
                print(f"Error loading custom_dictionary.json: {e}")
                self.load_defaults()
        else:
            self.load_defaults()

    def load_defaults(self):
        self.prompts = ['Python', 'VS Code', 'Next.js', 'TailwindCSS', 'PyTorch', 'Docker', 'Kubernetes', 'Faster-Whisper', 'Groq', 'API', 'OmniType']
        self.replacements = {
            'پایتون': 'Python',
            'وی اس کد': 'VS Code',
            'نکست جی اس': 'Next.js',
            'تیلویند': 'TailwindCSS',
            'داکر': 'Docker',
            'کوبارنتیس': 'Kubernetes',
            'فست ویسپر': 'Faster-Whisper',
            'گروک': 'Groq',
            'ای پی ای': 'API'
        }
        self.save()

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({"prompts": self.prompts, "replacements": self.replacements}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving custom_dictionary.json: {e}")

    def get_prompt_string(self):
        if self.prompts:
            return "واژگان تخصصی: " + ", ".join(self.prompts) + "."
        return ""

    def apply_replacements(self, text):
        if not text:
            return text
        for fa_word, en_word in self.replacements.items():
            pattern = re.compile(re.escape(fa_word), re.IGNORECASE)
            text = pattern.sub(en_word, text)
        return text

    def add_term(self, en_term, fa_term=""):
        en_term = en_term.strip()
        fa_term = fa_term.strip()
        if en_term and en_term not in self.prompts:
            self.prompts.append(en_term)
        if fa_term and en_term:
            self.replacements[fa_term] = en_term
        self.save()

    def remove_term(self, en_term):
        if en_term in self.prompts:
            self.prompts.remove(en_term)
        # پاکسازی از لیست جایگزین‌ها
        to_delete = [fa for fa, en in self.replacements.items() if en == en_term]
        for fa in to_delete:
            del self.replacements[fa]
        self.save()

CUSTOM_DICT = CustomDictionaryManager()

# ==========================================
# موتور ترجمه هوشمند (Google Translate Free GTX + Universal LLM Engine)
# ==========================================
class LLMTranslatorEngine:
    """ترجمه فوق‌العاده روان، دقیق و سریع با پشتیبانی از هر پرووایدر دلخواه، گروک، اوپن‌ای‌آی و گوگل رایگان"""
    
    @classmethod
    def translate(cls, text, mode="fa_to_en", style="tech"):
        if not text or not text.strip():
            return ""
            
        text = text.strip()
        
        # ۱. موتور اول (پرووایدر سفارشی OpenAI-Compatible مثل Groq, OpenAI, OpenRouter یا سرور محلی)
        if CUSTOM_LLM_API_KEY or "localhost" in CUSTOM_LLM_BASE_URL or "127.0.0.1" in CUSTOM_LLM_BASE_URL:
            try:
                translated = cls._translate_custom_openai(text, mode=mode, style=style)
                if translated:
                    return translated
            except Exception as e:
                print(f"Custom LLM translation failed: {e}. Falling back...")

        # ۲. موتور دوم (Google AI Studio Gemini API)
        if GEMINI_API_KEY:
            try:
                translated = cls._translate_gemini(text, mode=mode)
                if translated:
                    return translated
            except Exception as e:
                print(f"Gemini API translation failed: {e}")

        # ۳. موتور سوم و پیش‌فرض پایدار و بدون نیاز به کلید (Google Translate Free)
        try:
            translated = cls._translate_google_free(text, mode=mode)
            if translated:
                return translated
        except Exception as e:
            print(f"Google Free Translate failed: {e}")

        return text

    @classmethod
    def _translate_custom_openai(cls, text, mode="fa_to_en", style="tech"):
        url = f"{CUSTOM_LLM_BASE_URL.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if CUSTOM_LLM_API_KEY:
            headers["Authorization"] = f"Bearer {CUSTOM_LLM_API_KEY}"
        
        system_prompt = (
            "You are an expert translator. Translate the text accurately and fluently. "
            "Output ONLY the final translated text without any explanation, markdown formatting, or quotes."
        )
        if mode == "fa_to_en":
            system_prompt += " Translate from Persian to English. Preserve technical words like Python, VS Code, Git, Docker, API."
        else:
            system_prompt += " Translate from English to Persian (Farsi)."
            
        payload = {
            "model": CUSTOM_LLM_MODEL or "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.1,
            "max_tokens": 1024
        }
        
        res = requests.post(url, headers=headers, json=payload, timeout=12)
        if res.status_code == 200:
            content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                content = content[1:-1].strip()
            return content
        raise Exception(f"Custom LLM API status {res.status_code}: {res.text}")

    @classmethod
    def _translate_google_free(cls, text, mode="fa_to_en"):
        src = "fa" if mode == "fa_to_en" else "en"
        dest = "en" if mode == "fa_to_en" else "fa"

        # تقسیم متن‌های طولانی و چندخطی به قطعات ایمن (زیر ۸۰۰ کاراکتر) جهت جلوگیری از HTTP 400
        lines = text.split("\n")
        chunks = []
        cur_chunk = []
        cur_len = 0

        for line in lines:
            if cur_len + len(line) + 1 > 800 and cur_chunk:
                chunks.append("\n".join(cur_chunk))
                cur_chunk = [line]
                cur_len = len(line)
            else:
                cur_chunk.append(line)
                cur_len += len(line) + 1
            if cur_chunk:
                chunks.append("\n".join(cur_chunk))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        translated_chunks = []
        for chunk in chunks:
            if not chunk.strip():
                translated_chunks.append("")
                continue

            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={dest}&dt=t&q={requests.utils.quote(chunk)}"
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                result = res.json()
                sentences = result[0]
                chunk_trans = "".join([s[0] for s in sentences if s and len(s) > 0 and s[0]])
                translated_chunks.append(chunk_trans.strip())
            else:
                raise Exception(f"Google translate API status {res.status_code}")

        return "\n".join(translated_chunks).strip()

    @classmethod
    def _translate_gemini(cls, text, mode="fa_to_en"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        prompt_text = f"Translate the following text to {'English' if mode == 'fa_to_en' else 'Persian'}. Return ONLY the translated string without quotes or notes:\n{text}"
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        raise Exception(f"Gemini API status {res.status_code}")

class AIPromptEngineer:
    """تبدیل درخواست‌های گفتاری یا متنی فارسی به پرامپت‌های مهندسی‌شده و ساختاریافته انگلیسی برای AI با هر پرووایدر دلخواه"""

    @classmethod
    def generate_engineered_prompt(cls, user_text):
        if not user_text or not user_text.strip():
            return ""

        user_text = user_text.strip()
        system_prompt = (
            "You are an elite AI Prompt Engineer. The user will provide a raw request or idea in Persian or English. "
            "Your task is to transform their raw input into a world-class, highly structured, clear, and professional AI Prompt in English. "
            "Format the prompt with clear sections:\n"
            "- **Role / Persona**\n"
            "- **Task Objective & Context**\n"
            "- **Key Requirements & Steps**\n"
            "- **Output Format & Constraints**\n"
            "Output ONLY the final engineered prompt text in English without any meta commentary, intro text, or quotes."
        )

        if CUSTOM_LLM_API_KEY or "localhost" in CUSTOM_LLM_BASE_URL or "127.0.0.1" in CUSTOM_LLM_BASE_URL:
            try:
                url = f"{CUSTOM_LLM_BASE_URL.rstrip('/')}/chat/completions"
                headers = {"Content-Type": "application/json"}
                if CUSTOM_LLM_API_KEY:
                    headers["Authorization"] = f"Bearer {CUSTOM_LLM_API_KEY}"
                payload = {
                    "model": CUSTOM_LLM_MODEL or "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.3
                }
                res = requests.post(url, headers=headers, json=payload, timeout=12)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"Custom Prompt Engineer failed: {e}")

        if GEMINI_API_KEY:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
                headers = {"Content-Type": "application/json"}
                prompt = f"{system_prompt}\n\nUser Request: {user_text}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = requests.post(url, headers=headers, json=payload, timeout=8)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                print(f"Gemini Prompt Engineer failed: {e}")

        return LLMTranslatorEngine.translate(user_text, mode="fa_to_en")


# ==========================================
# پنجره گرافیکی مدیریت واژه‌نامه تخصصی
# ==========================================
class CustomDictionaryWindow(tk.Toplevel):
    def __init__(self, parent, dict_mgr):
        super().__init__(parent.root)
        self.parent = parent
        self.dict_mgr = dict_mgr
        self.title("📚 واژه‌نامه تخصصی اصطلاحات و کلمات فنی")
        self.geometry("520x580")
        self.configure(bg="#181825")
        self.attributes("-topmost", True)

        # عنوان اصلی
        lbl_title = tk.Label(self, text="📚 واژه‌نامه تخصصی اصطلاحات فنی", bg="#181825", fg="#89dceb", font=("Segoe UI", 12, "bold"), pady=10)
        lbl_title.pack()

        lbl_desc = tk.Label(self, text="کلمات انگلیسی تخصصی و معادل‌های تلفظ فارسی آن‌ها را وارد کنید تا هوش مصنوعی متون شما را دقیق تایپ کند.", bg="#181825", fg="#a6adc8", font=("Segoe UI", 9), wraplength=480, justify="center")
        lbl_desc.pack(pady=(0, 10))

        # فرم افزودن اصطلاح جدید
        frame_add = tk.LabelFrame(self, text=" ➕ افزودن اصطلاح جدید ", bg="#181825", fg="#f9e2af", font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        frame_add.pack(fill="x", padx=15, pady=5)

        tk.Label(frame_add, text="کلمه انگلیسی (مثلاً PyTorch):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_en = tk.Entry(frame_add, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9.5), width=24)
        self.entry_en.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(frame_add, text="تلفظ فارسی (مثلاً پایتورچ):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_fa = tk.Entry(frame_add, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9.5), width=24)
        self.entry_fa.grid(row=1, column=1, padx=5, pady=2)

        btn_add = tk.Button(frame_add, text="➕ افزودن کلمه", bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.add_term_action, cursor="hand2", padx=10)
        btn_add.grid(row=2, column=0, columnspan=2, pady=(8, 0))

        # جدول کلمات ثبت شده
        frame_list = tk.LabelFrame(self, text=" 📜 کلمات و معادل‌های فعال ", bg="#181825", fg="#89b4fa", font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        frame_list.pack(fill="both", expand=True, padx=15, pady=10)

        # Treeview لیست کلمات
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

        # دکمه حذف کلمه انتخابی
        btn_remove = tk.Button(self, text="🗑️ حذف کلمه انتخابی", bg="#f38ba8", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.remove_term_action, cursor="hand2")
        btn_remove.pack(pady=(0, 12))

        self.refresh_list()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # نمایش کلمات ثبت شده
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

# ==========================================
# پنجره گرافیکی تنظیم کلید میانبر دلخواه
# ==========================================
class CustomHotkeyWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("⚙️ تنظیم کلید میانبر (Hotkey)")
        self.geometry("380x250")
        self.configure(bg="#181825")
        self.attributes("-topmost", True)
        
        lbl = tk.Label(self, text="کلید میانبر جدید را وارد کنید\nیا دکمه زیر را زده و کلیدها را روی کیبورد فشار دهید.", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 10))
        lbl.pack(pady=15)
        
        self.entry = tk.Entry(self, bg="#1e1e2e", fg="#ffffff", font=("Segoe UI", 12), width=25, justify="center")
        self.entry.pack(pady=10)
        self.entry.insert(0, self.parent.current_hotkey)
        
        btn_detect = tk.Button(self, text="🎯 تشخیص خودکار (فشار دهید)", bg="#89b4fa", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.detect_hotkey, cursor="hand2")
        btn_detect.pack(pady=5)

        btn_save = tk.Button(self, text="✅ ذخیره میانبر", bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 10, "bold"), command=self.save_hotkey, cursor="hand2")
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
            except Exception as e:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def save_hotkey(self):
        hk = self.entry.get().strip()
        if hk and "در حال ضبط" not in hk:
            self.parent.change_global_hotkey(hk)
            self.destroy()

# ==========================================
# پنجره جامع و مدرن تنظیمات ارائه‌دهندگان هوش مصنوعی (Universal AI & API Provider Settings)
# ==========================================
class UniversalAPISettingsWindow(tk.Toplevel):
    PRESETS = {
        "⚡ Groq Cloud (بسیار سریع و پیشنهادی)": {
            "asr_url": "https://api.groq.com/openai/v1",
            "asr_model": "whisper-large-v3-turbo",
            "llm_url": "https://api.groq.com/openai/v1",
            "llm_model": "llama-3.3-70b-versatile"
        },
        "🤖 OpenAI (ChatGPT / Whisper-1)": {
            "asr_url": "https://api.openai.com/v1",
            "asr_model": "whisper-1",
            "llm_url": "https://api.openai.com/v1",
            "llm_model": "gpt-4o-mini"
        },
        "🔀 OpenRouter AI (دسترسی به تمام مدل‌ها)": {
            "asr_url": "https://openrouter.ai/api/v1",
            "asr_model": "openai/whisper",
            "llm_url": "https://openrouter.ai/api/v1",
            "llm_model": "meta-llama/llama-3.3-70b-instruct"
        },
        "🖥️ Local / Self-Hosted (سرور محلی / Ollama / vLLM)": {
            "asr_url": "http://localhost:8000/v1",
            "asr_model": "whisper",
            "llm_url": "http://localhost:11434/v1",
            "llm_model": "llama3"
        },
        "⚙️ سفارشی و دلخواه (Custom Provider)": {
            "asr_url": "",
            "asr_model": "",
            "llm_url": "",
            "llm_model": ""
        }
    }

    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("⚙️ تنظیمات ارائه‌دهندگان هوش مصنوعی (Universal API & Provider)")
        self.geometry("540x590")
        self.configure(bg="#181825")
        self.attributes("-topmost", True)

        # عنوان
        lbl_title = tk.Label(self, text="🌐 تنظیمات پیشرفته ارائه‌دهندگان هوش مصنوعی", bg="#181825", fg="#89dceb", font=("Segoe UI", 12, "bold"), pady=8)
        lbl_title.pack()

        lbl_desc = tk.Label(self, text="شما می‌توانید از هر سرویس‌دهنده دلخواه (Groq, OpenAI, OpenRouter یا سرورهای محلی)\nبرای تبدیل صوت و مدل‌های زبانی استفاده کنید.", bg="#181825", fg="#a6adc8", font=("Segoe UI", 9), justify="center")
        lbl_desc.pack(pady=(0, 6))

        # بخش پریست‌های آماده (Presets)
        frame_preset = tk.LabelFrame(self, text=" ⚡ انتخاب سریع سرویس‌دهنده (Presets) ", bg="#181825", fg="#f9e2af", font=("Segoe UI", 9, "bold"), padx=10, pady=6)
        frame_preset.pack(fill="x", padx=15, pady=4)

        self.preset_var = tk.StringVar(value="⚡ Groq Cloud (بسیار سریع و پیشنهادی)")
        preset_cb = ttk.Combobox(frame_preset, textvariable=self.preset_var, values=list(self.PRESETS.keys()), state="readonly", font=("Segoe UI", 9), width=45)
        preset_cb.pack(side="left", padx=5, pady=4, fill="x", expand=True)
        preset_cb.bind("<<ComboboxSelected>>", self.on_preset_selected)

        # بخش تبدیل صوت ASR
        frame_asr = tk.LabelFrame(self, text=" 🎙️ تنظیمات تبدیل صوت (Speech-to-Text / Whisper API) ", bg="#181825", fg="#a6e3a1", font=("Segoe UI", 9, "bold"), padx=10, pady=6)
        frame_asr.pack(fill="x", padx=15, pady=4)

        tk.Label(frame_asr, text="آدرس پایه سرور (Base URL):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_asr_url = tk.Entry(frame_asr, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9), width=36)
        self.entry_asr_url.grid(row=0, column=1, padx=5, pady=2)
        self.entry_asr_url.insert(0, CUSTOM_ASR_BASE_URL)

        tk.Label(frame_asr, text="کلید دسترسی (API Key):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_asr_key = tk.Entry(frame_asr, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9), width=36, show="•")
        self.entry_asr_key.grid(row=1, column=1, padx=5, pady=2)
        self.entry_asr_key.insert(0, CUSTOM_ASR_API_KEY)

        tk.Label(frame_asr, text="نام مدل (Model Name):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=2)
        self.entry_asr_model = tk.Entry(frame_asr, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9), width=36)
        self.entry_asr_model.grid(row=2, column=1, padx=5, pady=2)
        self.entry_asr_model.insert(0, CUSTOM_ASR_MODEL)

        # بخش مدل زبانی و ترجمه LLM
        frame_llm = tk.LabelFrame(self, text=" 🧠 تنظیمات هوش مصنوعی و ترجمه (LLM / Translation / Prompts) ", bg="#181825", fg="#89b4fa", font=("Segoe UI", 9, "bold"), padx=10, pady=6)
        frame_llm.pack(fill="x", padx=15, pady=4)

        tk.Label(frame_llm, text="آدرس پایه سرور (Base URL):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_llm_url = tk.Entry(frame_llm, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9), width=36)
        self.entry_llm_url.grid(row=0, column=1, padx=5, pady=2)
        self.entry_llm_url.insert(0, CUSTOM_LLM_BASE_URL)

        tk.Label(frame_llm, text="کلید دسترسی (API Key):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_llm_key = tk.Entry(frame_llm, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9), width=36, show="•")
        self.entry_llm_key.grid(row=1, column=1, padx=5, pady=2)
        self.entry_llm_key.insert(0, CUSTOM_LLM_API_KEY)

        tk.Label(frame_llm, text="نام مدل (Model Name):", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=2)
        self.entry_llm_model = tk.Entry(frame_llm, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9), width=36)
        self.entry_llm_model.grid(row=2, column=1, padx=5, pady=2)
        self.entry_llm_model.insert(0, CUSTOM_LLM_MODEL)

        # بخش اختیاری جمنای
        frame_gemini = tk.LabelFrame(self, text=" ⚡ کلید اختصاصی Google Gemini API (اختیاری) ", bg="#181825", fg="#cba6f7", font=("Segoe UI", 9, "bold"), padx=10, pady=4)
        frame_gemini.pack(fill="x", padx=15, pady=4)

        tk.Label(frame_gemini, text="Gemini API Key:", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_gemini = tk.Entry(frame_gemini, bg="#1e1e2e", fg="#ffffff", insertbackground="white", font=("Segoe UI", 9), width=36, show="•")
        self.entry_gemini.grid(row=0, column=1, padx=5, pady=2)
        self.entry_gemini.insert(0, GEMINI_API_KEY)

        # دکمه‌های پایانی
        btn_frame = tk.Frame(self, bg="#181825")
        btn_frame.pack(pady=10)

        btn_save = tk.Button(btn_frame, text="✅ ذخیره کلیه تنظیمات", bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 10, "bold"), command=self.save_settings, cursor="hand2", padx=12, pady=3)
        btn_save.pack(side="left", padx=8)

        btn_reset = tk.Button(btn_frame, text="🔄 بازنشانی به پیش‌فرض گوگل", bg="#f38ba8", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.reset_to_google, cursor="hand2", padx=8, pady=3)
        btn_reset.pack(side="left", padx=8)

        self.focus_force()
        self.lift()

    def on_preset_selected(self, event=None):
        preset_name = self.preset_var.get()
        data = self.PRESETS.get(preset_name, {})
        if data.get("asr_url") is not None:
            self.entry_asr_url.delete(0, 'end')
            self.entry_asr_url.insert(0, data["asr_url"])
        if data.get("asr_model") is not None:
            self.entry_asr_model.delete(0, 'end')
            self.entry_asr_model.insert(0, data["asr_model"])
        if data.get("llm_url") is not None:
            self.entry_llm_url.delete(0, 'end')
            self.entry_llm_url.insert(0, data["llm_url"])
        if data.get("llm_model") is not None:
            self.entry_llm_model.delete(0, 'end')
            self.entry_llm_model.insert(0, data["llm_model"])

    def save_settings(self):
        updates = {
            "CUSTOM_ASR_BASE_URL": self.entry_asr_url.get().strip(),
            "CUSTOM_ASR_API_KEY": self.entry_asr_key.get().strip(),
            "CUSTOM_ASR_MODEL": self.entry_asr_model.get().strip(),
            "CUSTOM_LLM_BASE_URL": self.entry_llm_url.get().strip(),
            "CUSTOM_LLM_API_KEY": self.entry_llm_key.get().strip(),
            "CUSTOM_LLM_MODEL": self.entry_llm_model.get().strip(),
            "GEMINI_API_KEY": self.entry_gemini.get().strip(),
        }
        save_env_dict(updates)
        messagebox.showinfo("موفقیت", "تنظیمات ارائه‌دهنده با موفقیت ذخیره و اعمال شد.", parent=self)
        self.destroy()

    def reset_to_google(self):
        self.parent.change_engine("google")
        messagebox.showinfo("اطلاع", "موتور اصلی روی Google Speech (رایگان وب و بدون نیاز به کلید) تنظیم شد.", parent=self)
        self.destroy()

# ==========================================
# تنظیمات فنی کارت صدا
# ==========================================
CHUNK = 1024        
FORMAT = pyaudio.paInt16 
CHANNELS = 1        
RATE = 16000        

# ==========================================
# مدیریت مدل Faster-Whisper محلی (Cold-Start & VRAM)
# ==========================================
class LocalWhisperManager:
    """مدیریت لودینگ پس‌زمینه، اجرای مدل محلی و آزادسازی حافظه VRAM برای گیمینگ"""
    def __init__(self):
        self.model = None
        self.is_loading = False
        self.load_error = None

    def preload_model_async(self, model_size="large-v3-turbo"):
        if self.model is not None or self.is_loading:
            return
        self.is_loading = True
        threading.Thread(target=self._load_worker, args=(model_size,), daemon=True).start()

    def _load_worker(self, model_size):
        try:
            device = "cuda" if (HAS_FASTER_WHISPER and ctranslate2.get_cuda_device_count() > 0) else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            print(f"Loading local Faster-Whisper model '{model_size}' on {device} ({compute_type})...")
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            print("Local Faster-Whisper model loaded successfully!")
        except Exception as e:
            self.load_error = str(e)
            print(f"Error loading local model '{model_size}': {e}. Falling back to 'base'...")
            try:
                device = "cuda" if (HAS_FASTER_WHISPER and ctranslate2.get_cuda_device_count() > 0) else "cpu"
                self.model = WhisperModel("base", device=device, compute_type="int8")
                print("Fallback 'base' model loaded successfully!")
            except Exception as ex:
                self.load_error = str(ex)
        finally:
            self.is_loading = False

    def unload_model(self):
        """آزادسازی ۱۰۰ درصدی حافظه VRAM کارت گرافیک برای بازی و برنامه‌های سنگین"""
        if self.model is not None or self.is_loading:
            print("Unloading local Faster-Whisper model and freeing VRAM...")
            self.model = None
            self.is_loading = False
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            print("VRAM successfully released!")
            return True
        return False

    def transcribe(self, wav_bytes, lang="fa", prompt=None, task="transcribe"):
        if self.model is None:
            if self.is_loading:
                raise Exception("مدل محلی هنوز در حال بارگذاری است، لطفاً چند لحظه صبر کنید...")
            else:
                self.preload_model_async()
                raise Exception("مدل محلی در حال استارت اولیه است...")
        
        audio_stream = io.BytesIO(wav_bytes)
        segments, info = self.model.transcribe(
            audio_stream,
            language=lang,
            task=task,
            initial_prompt=prompt or BASE_WHISPER_PROMPT,
            beam_size=5
        )
        text = " ".join([seg.text for seg in segments]).strip()
        return text

LOCAL_WHISPER = LocalWhisperManager()

class HighlightPeekPopup:
    """پنجره پاپ‌آپ شناور، اسکرول‌پذیر، اسکیل‌پذیر و شیک برای مشاهده ترجمه متون با فونت فارسی روان و دکمه‌های کامل"""

    def __init__(self, parent_root, text_original, text_translated, x_cursor, y_cursor, on_replace_callback=None):
        self.top = tk.Toplevel(parent_root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.config(bg="#11111b")

        # محاسبه هوشمند اندازه بر اساس حجم متن
        char_len = len(text_translated)
        if char_len < 60:
            w, max_h = 380, 180
        elif char_len < 200:
            w, max_h = 460, 260
        else:
            w, max_h = 540, 360

        # فریم اصلی با حاشیه برجسته بنفش پاستلی
        main_frame = tk.Frame(self.top, bg="#1e1e2e", highlightbackground="#cba6f7", highlightthickness=2, bd=0)
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # ۱. نوار عنوان (Header Bar)
        header_frame = tk.Frame(main_frame, bg="#181825")
        header_frame.pack(fill="x", padx=8, pady=6)

        lbl_icon = tk.Label(header_frame, text="✨ 🌐", font=("Segoe UI Emoji", 11), bg="#181825", fg="#f5e0dc")
        lbl_icon.pack(side="left", padx=(4, 2))

        lbl_title = tk.Label(header_frame, text="ترجمه هوشمند | Smart Preview 🪄", font=("Segoe UI", 10, "bold"), bg="#181825", fg="#cba6f7")
        lbl_title.pack(side="left", padx=4)

        btn_close_top = tk.Label(header_frame, text=" ✕ ", font=("Segoe UI", 11, "bold"), bg="#181825", fg="#f38ba8", cursor="hand2")
        btn_close_top.pack(side="right", padx=4)
        btn_close_top.bind("<Button-1>", lambda e: self.close())

        # خط جداکننده بالا
        sep1 = tk.Frame(main_frame, bg="#313244", height=1)
        sep1.pack(fill="x", padx=6, pady=2)

        # ۲. متن اصلی کوچک شده (برای ارجاع)
        if text_original and text_original.strip() != text_translated.strip():
            clean_orig = text_original.strip().replace("\r\n", " ").replace("\n", " ")
            orig_snippet = clean_orig[:70] + ("..." if len(clean_orig) > 70 else "")
            lbl_orig = tk.Label(main_frame, text=f"🔤 متن اصلی: {orig_snippet}", font=("Segoe UI", 8, "italic"), bg="#1e1e2e", fg="#a6adc8", anchor="w", justify="left")
            lbl_orig.pack(fill="x", padx=10, pady=(4, 2))

        # ۳. بدنه اسکرول‌پذیر ترجمه (Scrollable Text Area)
        text_container = tk.Frame(main_frame, bg="#181825")
        text_container.pack(fill="both", expand=True, padx=8, pady=4)

        scrollbar = tk.Scrollbar(text_container, bg="#313244", activebackground="#45475a", troughcolor="#181825", width=10)
        scrollbar.pack(side="right", fill="y")

        # استفاده از tk.Text با حمایت کامل از فشرده‌سازی RTL و چرخ موس
        is_rtl = bool(re.search(r'[\u0600-\u06FF]', text_translated))
        text_widget = tk.Text(
            text_container,
            wrap="word",
            font=("Tahoma", 10, "bold") if is_rtl else ("Segoe UI", 10, "bold"),
            bg="#181825",
            fg="#a6e3a1",
            insertbackground="white",
            relief="flat",
            bd=0,
            padx=8,
            pady=8,
            yscrollcommand=scrollbar.set,
            height=6 if char_len > 120 else 3
        )
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        # درج متن ترجمه در ویجت
        text_widget.insert("1.0", text_translated.strip())
        text_widget.config(state="disabled")

        # شنود چرخ موس برای اسکرول متن ترجمه
        def _on_mousewheel(event):
            text_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        text_widget.bind("<MouseWheel>", _on_mousewheel)

        # ۴. خط جداکننده پایین
        sep2 = tk.Frame(main_frame, bg="#313244", height=1)
        sep2.pack(fill="x", padx=6, pady=2)

        # ۵. نوار دکمه‌ها و اکشن‌ها (Footer Action Buttons)
        btn_frame = tk.Frame(main_frame, bg="#181825")
        btn_frame.pack(fill="x", padx=6, pady=6)

        def copy_action():
            pyperclip.copy(text_translated)
            btn_copy.config(text="✓ کپی شد!", fg="#a6e3a1")
            self.top.after(1000, self.close)

        btn_copy = tk.Label(btn_frame, text="📋 کپی", font=("Segoe UI", 9, "bold"), bg="#313244", fg="#89b4fa", padx=8, pady=4, cursor="hand2")
        btn_copy.pack(side="left", padx=4)
        btn_copy.bind("<Button-1>", lambda e: copy_action())

        if on_replace_callback:
            def replace_action():
                on_replace_callback(text_translated)
                self.close()

            btn_replace = tk.Label(btn_frame, text="✍️ جایگزینی در متن", font=("Segoe UI", 9, "bold"), bg="#313244", fg="#f9e2af", padx=8, pady=4, cursor="hand2")
            btn_replace.pack(side="left", padx=4)
            btn_replace.bind("<Button-1>", lambda e: replace_action())

        btn_dismiss = tk.Label(btn_frame, text=" ✕ بستن ", font=("Segoe UI", 9, "bold"), bg="#313244", fg="#f38ba8", padx=8, pady=4, cursor="hand2")
        btn_dismiss.pack(side="right", padx=4)
        btn_dismiss.bind("<Button-1>", lambda e: self.close())

        # محاسبه ارتفاع دقیق و جلوگیری از برش خوردن
        self.top.update_idletasks()
        req_w = w
        req_h = min(max(self.top.winfo_reqheight(), 160), max_h)

        # موقعیت‌یابی هوشمند کنار نشانگر موس
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

        # بستن با Esc
        self.top.bind("<Escape>", lambda e: self.close())
        self.top.focus_set()

    def close(self):
        try:
            self.top.destroy()
        except Exception:
            pass

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
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # قطر متعادل، شکیل و استاندارد گوی صوتی (۵۸ پیکسل)
        self.size = 58
        
        # بوم نقاشی فوق‌العاده باکیفیت
        self.canvas = tk.Canvas(self.root, bg=self.TRANS_COLOR, highlightthickness=0, width=self.size, height=self.size)
        self.canvas.pack()
        
        # کانفیگ‌های پیش‌فرض
        self.current_engine = "google"   # Google Speech پیش‌فرض فعال شد برای بالاترین دقت و کیفیت صوت فارسی
        self.current_hotkey = "caps lock"
        self.current_lang = "fa"        # "fa", "translate_fa_en", "translate_en_fa", "auto", "en"
        self.auto_pause_media = True    # توقف خودکار ویدیو/موزیک هنگام صحبت
        self.recording_mode = "hotkey"  # "hotkey" (نگه داشتن کلید) یا "mouse" (کلیک موس)
        self.anim_timer = None
        self.anim_step = 0
        self.current_state = "idle"
        self.target_hwnd = None

        # حافظه کانتکست ۱۰ صحبت اخیر کاربر
        self.history = collections.deque(maxlen=10)

        # ساخت منوی کلیک‌راست ۱۰۰٪ پایدار، شکیل و بدون کرش نیتیو
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='#1e1e2e', fg='white', activebackground='#3b82f6', activeforeground='white', font=('Segoe UI', 9))
        self.engine_menu = tk.Menu(self.context_menu, tearoff=0, bg='#1e1e2e', fg='white', activebackground='#3b82f6', activeforeground='white', font=('Segoe UI', 9))
        self.hotkey_menu = tk.Menu(self.context_menu, tearoff=0, bg='#1e1e2e', fg='white', activebackground='#3b82f6', activeforeground='white', font=('Segoe UI', 9))
        self.lang_menu = tk.Menu(self.context_menu, tearoff=0, bg='#1e1e2e', fg='white', activebackground='#3b82f6', activeforeground='white', font=('Segoe UI', 9))
        self.history_menu = tk.Menu(self.context_menu, tearoff=0, bg='#1e1e2e', fg='white', activebackground='#3b82f6', activeforeground='white', font=('Segoe UI', 9))
        
        # اتصال رویدادهای موس (کلیک‌چپ برای ضبط/توقف با انیمیشن، کلیک‌راست برای منوی کلیک‌راست نیتیو)
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

    def apply_no_activate_style(self):
        """جلوگیری از دزدیده شدن فوکوس پنجره فعال و چشمک‌زن کیبورد هنگام کلیک روی دایره شناور (WS_EX_NOACTIVATE)"""
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

    def on_left_click(self, event):
        """کلیک چپ روی دایره: شروع ضبط یا توقف ضبط با موس بدون دزدیدن فوکوس تکست‌باکس"""
        if self.is_recording:
            # کلیک دوم -> توقف ضبط
            self.is_recording = False
        else:
            # کلیک اول -> شروع ضبط در حالت موس
            self.start_recording(mode="mouse")

    def cancel_anim(self):
        """توقف انیمیشن جاری"""
        if self.anim_timer:
            self.root.after_cancel(self.anim_timer)
            self.anim_timer = None

    def draw_idle_breathing(self):
        """انیمیشن تنفس نرم و شیشه‌ای (3D Glassmorphic Emerald Orb) در حالت آماده‌به‌کار"""
        if self.current_state != "idle":
            return
        
        self.anim_step = (self.anim_step + 1) % 60
        pulse = math.sin(self.anim_step * math.pi / 30)
        cx, cy = self.size / 2, self.size / 2
        r_core = 14.5 + 1.2 * pulse
        r_halo = 22.5 + 2.2 * pulse

        self.canvas.delete("all")
        # ۱. هاله بیرونی زمردین فید شونده (Soft Emerald Halo)
        self.canvas.create_oval(
            cx - r_halo, cy - r_halo, cx + r_halo, cy + r_halo,
            fill="", outline="#34d399", width=2.0
        )
        # ۲. بدنه اصلی گوی سبز شیشه‌ای (Glassmorphic Core)
        self.canvas.create_oval(
            cx - r_core, cy - r_core, cx + r_core, cy + r_core,
            fill="#10b981", outline="#059669", width=2.0
        )
        # ۳. نقطه درخشش سه بعدی بالای گوی (3D Specular Highlight)
        hx, hy = cx - r_core * 0.35, cy - r_core * 0.35
        hr = r_core * 0.35
        self.canvas.create_oval(
            hx - hr, hy - hr, hx + hr, hy + hr,
            fill="#ffffff", outline=""
        )

        if self.current_state == "idle":
            self.anim_timer = self.root.after(40, self.draw_idle_breathing)

    def draw_recording_pulse(self):
        """انیمیشن موج‌های امواج هولوگرافیک (Vivid Holographic Ripple Waves) موقع ضبط صدا"""
        if not self.is_recording:
            return
        
        self.anim_step = (self.anim_step + 1) % 40
        cx, cy = self.size / 2, self.size / 2
        
        self.canvas.delete("all")
        
        # محاسبه فاز دو موج شعاعی متوالی
        p1 = (self.anim_step % 20) / 20.0
        p2 = ((self.anim_step + 10) % 20) / 20.0

        r1 = 15 + p1 * 12
        w1 = max(0.5, 3.0 * (1.0 - p1))

        r2 = 15 + p2 * 12
        w2 = max(0.5, 3.0 * (1.0 - p2))

        # موج بیرونی ۱
        self.canvas.create_oval(cx - r1, cy - r1, cx + r1, cy + r1, outline="#f87171", width=w1)
        # موج بیرونی ۲
        self.canvas.create_oval(cx - r2, cy - r2, cx + r2, cy + r2, outline="#fca5a5", width=w2)

        # گوی قرمز درخشان مرکز (Crimson Glowing Core)
        r_core = 15.0
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core, fill="#ef4444", outline="#dc2626", width=2.0)

        # نقطه درخشش سه بعدی
        hx, hy = cx - r_core * 0.35, cy - r_core * 0.35
        hr = r_core * 0.35
        self.canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr, fill="#ffffff", outline="")

        if self.is_recording:
            self.anim_timer = self.root.after(30, self.draw_recording_pulse)

    def draw_processing_spinner(self):
        """انیمیشن چرخشی/طلایی هنگام پردازش هوش مصنوعی (Golden Rotary Pulse)"""
        if self.current_state != "processing":
            return
        
        self.anim_step = (self.anim_step + 1) % 360
        cx, cy = self.size / 2, self.size / 2
        r_core = 14.5
        r_ring = 22.5

        self.canvas.delete("all")
        # کمان چرخنده طلایی
        start_angle = (self.anim_step * 8) % 360
        self.canvas.create_arc(
            cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring,
            start=start_angle, extent=110, style="arc", outline="#fbbf24", width=3.0
        )

        # گوی کهربایی مرکز
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core, fill="#f59e0b", outline="#d97706", width=2.0)
        # درخشش سه بعدی
        hx, hy = cx - r_core * 0.35, cy - r_core * 0.35
        hr = r_core * 0.35
        self.canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr, fill="#ffffff", outline="")

        if self.current_state == "processing":
            self.anim_timer = self.root.after(30, self.draw_processing_spinner)

    def draw_success_pulse(self):
        """انیمیشن موج آبی الکتریسیته هنگام تایپ موفقیت‌آمیز (Electric Cyan Wave)"""
        if self.current_state != "success":
            return

        self.anim_step = (self.anim_step + 1) % 30
        cx, cy = self.size / 2, self.size / 2
        r_core = 15.0
        pulse_r = 15.0 + (self.anim_step / 30.0) * 11
        width = max(0.5, 3.0 * (1.0 - self.anim_step / 30.0))

        self.canvas.delete("all")
        # موج الکتریسیته فیروزه‌ای بیرونی
        self.canvas.create_oval(cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r, outline="#06b6d4", width=width)
        
        # گوی آبی تیره
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core, fill="#3b82f6", outline="#2563eb", width=2.0)
        # درخشش سه بعدی
        hx, hy = cx - r_core * 0.35, cy - r_core * 0.35
        hr = r_core * 0.35
        self.canvas.create_oval(hx - hr, hy - hr, hx + hr, hy + hr, fill="#ffffff", outline="")

        if self.current_state == "success" and self.anim_step < 29:
            self.anim_timer = self.root.after(25, self.draw_success_pulse)

    def start_idle_breathing(self):
        self.current_state = "idle"
        self.draw_idle_breathing()

    def get_dynamic_prompt(self):
        """ساخت پرامپت با کانتکست واژه‌نامه تخصصی و صحبت‌های اخیر کاربر"""
        prompt_parts = [BASE_WHISPER_PROMPT]
        dict_prompt = CUSTOM_DICT.get_prompt_string()
        if dict_prompt:
            prompt_parts.append(dict_prompt)
        if self.history:
            recent_context = " | ".join(list(self.history)[-3:])
            prompt_parts.append(f"زمینه صحبت‌های اخیر: [{recent_context}]")
        return " ".join(prompt_parts)

    def update_menu_indicators(self):
        """تولید مجدد منوها همراه با تیک (✓) و زیرمنوی تاریخچه ۵ صحبت اخیر"""
        self.context_menu.delete(0, 'end')
        
        # عنوان وضعیت جاری موتور
        engine_titles = {
            "google": "🔍 گوگل (رایگان وب - بدون کلید)",
            "custom": "☁️ سرویس ابری دلخواه (OpenAI / Groq / ...)",
            "local": "💻 ویسپر محلی (آفلاین/گرافیک)"
        }
        active_title = engine_titles.get(self.current_engine, self.current_engine)
        # گزینه‌های ترجمه دستی و مهندسی پرامپت هوشمند
        self.context_menu.add_command(label="✨ مشاهده ترجمه در پاپ‌آپ شناور (Ctrl+Alt+X)", command=lambda: self.translate_peek_action())
        self.context_menu.add_command(label="🤖 تبدیل متن/درخواست به پرامپت مهندسی‌شده AI (Ctrl+Alt+P)", command=self.prompt_engineer_action)
        self.context_menu.add_command(label="🌐 ترجمه و جایگزینی: فارسی ➔ انگلیسی (Ctrl+Alt+Z)", command=lambda: self.translate_manual_action("fa_to_en"))
        self.context_menu.add_command(label="🇮🇷 ترجمه و جایگزینی: انگلیسی ➔ فارسی (Ctrl+Alt+Shift+Z)", command=lambda: self.translate_manual_action("en_to_fa"))
        self.context_menu.add_separator()

        # باز کردن پنجره مدیریت واژه‌نامه تخصصی
        self.context_menu.add_command(label="📚 واژه‌نامه تخصصی (اصطلاحات و کلمات انگلیسی)", command=self.open_custom_dict_window)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="⚙️ تنظیمات ارائه‌دهندگان هوش مصنوعی (Universal AI & API)", command=self.open_api_keys_window)
        self.context_menu.add_separator()

        # زیرمنوی تاریخچه ۵ صحبت اخیر
        self.history_menu.delete(0, 'end')
        if not self.history:
            self.history_menu.add_command(label="(تاریخچه‌ای ثبت نشده است)", state="disabled")
        else:
            recent_items = list(self.history)[-5:]
            recent_items.reverse()
            for idx, item in enumerate(recent_items, 1):
                short_label = item[:32] + ("..." if len(item) > 32 else "")
                self.history_menu.add_command(
                    label=f"{idx}. {short_label}",
                    command=lambda t=item: self.copy_history_item(t)
                )
            self.history_menu.add_separator()
            self.history_menu.add_command(label="🗑️ پاکسازی تاریخچه صحبت‌ها", command=self.clear_history_action)

        self.context_menu.add_cascade(label="📜 تاریخچه ۵ صحبت اخیر", menu=self.history_menu)
        self.context_menu.add_separator()

        # زیرمنوی موتورها با تیک
        self.engine_menu.delete(0, 'end')
        engines = [
            ("google", "Google Speech (Free Web - پیش‌فرض و ۱۰۰٪ رایگان)"),
            ("custom", "سرویس ابری هوش مصنوعی (Custom / Groq / OpenAI / ...)"),
            ("local", "Faster-Whisper (Local Offline - آفلاین و با گرافیک)"),
        ]
        for key, label_name in engines:
            prefix = "✓ " if self.current_engine == key else "    "
            self.engine_menu.add_command(
                label=f"{prefix}{label_name}",
                command=lambda k=key: self.change_engine(k)
            )
        self.context_menu.add_cascade(label="🤖 تغییر موتور تبدیل گفتار", menu=self.engine_menu)

        # گزینه توقف خودکار رسانه (ویدیو/موزیک)
        pause_prefix = "✓ " if self.auto_pause_media else "    "
        self.context_menu.add_command(
            label=f"{pause_prefix}⏸️ توقف خودکار ویدیو/موزیک هنگام صحبت",
            command=self.toggle_auto_pause_media
        )

        # گزینه تخلیه VRAM
        self.context_menu.add_command(label="🧹 آزادسازی VRAM کارت گرافیک (برای بازی)", command=self.free_vram_action)

        # زیرمنوی کلید میانبر با تیک
        self.hotkey_menu.delete(0, 'end')
        hotkeys = [("caps lock", "Caps Lock"), ("ctrl+windows", "Ctrl + Windows"), ("ctrl+shift", "Ctrl + Shift"), ("f2", "F2"), ("ctrl+`", "Ctrl + `")]
        for key_code, key_name in hotkeys:
            prefix = "✓ " if self.current_hotkey == key_code else "    "
            self.hotkey_menu.add_command(
                label=f"{prefix}{key_name}",
                command=lambda k=key_code: self.change_global_hotkey(k)
            )
        self.hotkey_menu.add_separator()
        self.hotkey_menu.add_command(label="⌨️ تنظیم کلید میانبر دلخواه (Custom)...", command=self.open_custom_hotkey_window)
        self.context_menu.add_cascade(label="⚙️ کلید میانبر PTT", menu=self.hotkey_menu)

        # زیرمنوی زبان با تیک
        self.lang_menu.delete(0, 'end')
        langs = [
            ("fa", "🇮🇷 فارسی (دقت هوشمند + کلمات انگلیسی)"),
            ("prompt_engineer", "✨ مهندسی پرامپت: گفتار فارسی ➔ پرامپت ساختاریافته AI"),
            ("translate_fa_en", "🔤 ترجمه همزمان: گفتار فارسی ➔ تایپ انگلیسی (FA to EN)"),
            ("translate_en_fa", "🌐 ترجمه همزمان: گفتار انگلیسی ➔ تایپ فارسی (EN to FA)"),
            ("auto", "🌐 تشخیص خودکار زبان ها (Auto)"),
            ("en", "🇬🇧 انگلیسی خالص (EN)"),
        ]
        for code, label_name in langs:
            prefix = "✓ " if self.current_lang == code else "    "
            self.lang_menu.add_command(
                label=f"{prefix}{label_name}",
                command=lambda c=code: self.change_engine_language(c)
            )
        self.context_menu.add_cascade(label="🌐 حالت زبان و ترجمه همزمان", menu=self.lang_menu)

        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ خروج کامل از برنامه", command=self.quit_app)

    def open_custom_dict_window(self):
        """پنجره مدیریت واژه‌نامه تخصصی"""
        CustomDictionaryWindow(self, CUSTOM_DICT)

    def open_custom_hotkey_window(self):
        """پنجره مدیریت میانبر دلخواه"""
        CustomHotkeyWindow(self)

    def open_api_keys_window(self):
        """پنجره مدیریت جامع ارائه‌دهندگان هوش مصنوعی"""
        UniversalAPISettingsWindow(self)

    def open_document_translator_window(self):
        """پنجره اختصاصی ترجمه فایل و متن طولانی همراه با نگارش فارسی"""
        DocumentTranslatorWindow(self.root)

    def toggle_auto_pause_media(self):
        """فعال/غیرفعال‌سازی توقف خودکار رسانه"""
        self.auto_pause_media = not self.auto_pause_media
        self.set_ui_state("idle")

    def copy_history_item(self, text):
        """کپی مجدد آیتم تاریخچه روی کلیپ‌بورد و تایپ آن"""
        pyperclip.copy(text)
        time.sleep(0.05)
        keyboard.send('ctrl+v')
        self.set_ui_state("success")

    def clear_history_action(self):
        """پاکسازی تاریخچه صحبت‌ها"""
        self.history.clear()
        self.set_ui_state("idle")

    def bind_hotkey_system(self):
        if self.hotkey_hook:
            try: keyboard.remove_hotkey(self.hotkey_hook)
            except Exception: pass

        # پاکسازی هوک‌های قبلی ترجمه
        for attr in ['translate_hotkey_fa_en', 'translate_hotkey_en_fa', 'tr_fa_1', 'tr_fa_2', 'tr_en_1', 'tr_en_2', 'tr_peek_1', 'tr_peek_2', 'tr_peek_3', 'tr_doc_1', 'tr_doc_2']:
            hook = getattr(self, attr, None)
            if hook:
                try: keyboard.remove_hotkey(hook)
                except Exception: pass

        self.hotkey_hook = keyboard.add_hotkey(self.current_hotkey, lambda: self.start_recording(mode="hotkey"), trigger_on_release=False)

        # میانبر مترجم فایل و متون طولانی (Ctrl+Alt+F)
        doc_cb = lambda: self.root.after(0, self.open_document_translator_window)
        try: self.tr_doc_1 = keyboard.add_hotkey("ctrl+alt+f", doc_cb, trigger_on_release=False)
        except Exception: pass
        try: self.tr_doc_2 = keyboard.add_hotkey("ctrl+alt+ب", doc_cb, trigger_on_release=False)
        except Exception: pass

        # میانبر جدید مشاهده ترجمه در پاپ‌آپ شناور در محل نشانگر موس (Ctrl+Alt+X)
        peek_cb = lambda: self.translate_peek_action()
        try: self.tr_peek_1 = keyboard.add_hotkey("ctrl+alt+x", peek_cb, trigger_on_release=False)
        except Exception: pass
        try: self.tr_peek_2 = keyboard.add_hotkey("ctrl+alt+ط", peek_cb, trigger_on_release=False)
        except Exception: pass
        try: self.tr_peek_3 = keyboard.add_hotkey("ctrl+alt+خ", peek_cb, trigger_on_release=False)
        except Exception: pass

        # میانبر ترجمه فارسی به انگلیسی و جایگزینی (Ctrl+Alt+Z)
        fa_en_cb = lambda: self.translate_manual_action("fa_to_en")
        try: self.tr_fa_1 = keyboard.add_hotkey("ctrl+alt+z", fa_en_cb, trigger_on_release=False)
        except Exception: pass
        try: self.tr_fa_2 = keyboard.add_hotkey("ctrl+alt+ظ", fa_en_cb, trigger_on_release=False)
        except Exception: pass
        try: keyboard.add_hotkey("ctrl+alt+ژ", fa_en_cb, trigger_on_release=False)
        except Exception: pass

        # میانبر ترجمه انگلیسی به فارسی و جایگزینی (Ctrl+Alt+Shift+Z)
        en_fa_cb = lambda: self.translate_manual_action("en_to_fa")
        try: self.tr_en_1 = keyboard.add_hotkey("ctrl+alt+shift+z", en_fa_cb, trigger_on_release=False)
        except Exception: pass
        try: self.tr_en_2 = keyboard.add_hotkey("ctrl+alt+shift+ظ", en_fa_cb, trigger_on_release=False)
        except Exception: pass
        try: keyboard.add_hotkey("ctrl+alt+shift+ژ", en_fa_cb, trigger_on_release=False)
        except Exception: pass

        # میانبر جدید تبدیل متن به پرامپت مهندسی‌شده AI (Ctrl+Alt+P)
        p_cb = lambda: self.prompt_engineer_action()
        try: self.tr_p_1 = keyboard.add_hotkey("ctrl+alt+p", p_cb, trigger_on_release=False)
        except Exception: pass
        try: self.tr_p_2 = keyboard.add_hotkey("ctrl+alt+ح", p_cb, trigger_on_release=False)
        except Exception: pass

        self.set_ui_state("idle")

    def prompt_engineer_action(self):
        """تبدیل متن انتخابی به پرامپت مهندسی‌شده AI با کلید میانبر Ctrl+Alt+P"""
        print("[OmniType] AI Prompt Engineer triggered!")
        text_orig, saved_clip = self.get_selected_text()
        if not text_orig:
            return

        self.set_ui_state("processing")

        def worker():
            prompt_engineered = AIPromptEngineer.generate_engineered_prompt(text_orig)
            def update_ui():
                self.safe_type_and_restore_clipboard(prompt_engineered)
                self.set_ui_state("success")
            self.root.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def translate_peek_action(self):
        """ترجمه متن انتخاب شده و نمایش آن در پاپ‌آپ شیک شناور در محل نشانگر موس بدون دستکاری متن اصلی صفحه"""
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

            print(f"[OmniType] Peek Translating text: '{text_to_translate[:40]}...' (mode: {mode})")
            try:
                translated = LLMTranslatorEngine.translate(text_to_translate, mode=mode)
                if translated:
                    translated = CUSTOM_DICT.apply_replacements(translated)
                    self.history.append(translated)
                    self.set_ui_state("success")
                    
                    def replace_cb(new_text):
                        self.safe_type_and_restore_clipboard(new_text)

                    self.root.after(0, lambda: HighlightPeekPopup(
                        self.root, text_to_translate, translated, cursor_x, cursor_y, on_replace_callback=replace_cb
                    ))
                else:
                    self.set_ui_state("idle")
            except Exception as e:
                print(f"Error in peek translation worker: {e}")
                self.set_ui_state("idle")

        threading.Thread(target=worker, daemon=True).start()

    def translate_manual_action(self, mode="fa_to_en"):
        """ترجمه دستی هوشمند متن انتخاب‌شده یا آخرین صحبت کاربر"""
        print(f"[OmniType] Manual translation triggered! (mode: {mode})")

        # ۱. ذخیره پنجره فعال جاری که فوکوس کاربر روی آن قرار دارد
        try:
            self.target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass

        # ۲. تغییر گوی شناور به انیمیشن طلایی پردازش
        self.set_ui_state("processing")

        # ۳. اجرای فرآیند کپی، ترجمه و تایپ در یک Thread پس‌زمینه بدون بلاک کردن UI
        def worker():
            # مکث کوتاه ۱۵۰ میلی ثانیه‌ای برای رها شدن کلید Alt و Ctrl از سمت کاربر
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

            # تلاش برای کپی متن انتخاب شده روی صفحه
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
                # اگر متنی انتخاب نشده بود، آخرین صحبت در history را بردار
                if self.history:
                    text_to_translate = list(self.history)[-1]
                # بازیابی کلیپ بورد قبلی کاربر
                try:
                    pyperclip.copy(old_clip)
                except Exception:
                    pass

            if not text_to_translate:
                print("[OmniType] No text found to translate (selected or history).")
                self.set_ui_state("idle")
                return

            print(f"[OmniType] Translating text: '{text_to_translate[:40]}...'")
            try:
                translated = LLMTranslatorEngine.translate(text_to_translate, mode=mode)
                if translated:
                    print(f"[OmniType] Result: '{translated[:40]}...'")
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

    @staticmethod
    def pcm_to_wav_bytes(pcm_data, sample_rate=RATE, channels=CHANNELS, sampwidth=2):
        """تبدیل بایت‌های خام PCM به فرمت استاندارد فایل صوتی WAV در حافظه"""
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)
        return buf.getvalue()

    def transcribe_custom_api(self, wav_bytes, lang_code="fa", prompt=None):
        """تبدیل صوت به متن با استفاده از هر اندپوینت دلخواه سازگار با استاندارد OpenAI / Whisper"""
        url = f"{CUSTOM_ASR_BASE_URL.rstrip('/')}/audio/transcriptions"
        headers = {}
        if CUSTOM_ASR_API_KEY:
            headers["Authorization"] = f"Bearer {CUSTOM_ASR_API_KEY}"
            
        files = {"file": ("voice.wav", wav_bytes, "audio/wav")}
        data = {
            "model": CUSTOM_ASR_MODEL or "whisper-large-v3-turbo",
            "prompt": prompt or self.get_dynamic_prompt()
        }
        if lang_code:
            data["language"] = lang_code

        res = requests.post(url, headers=headers, files=files, data=data, timeout=15)
        if res.status_code == 200:
            return res.json().get("text", "").strip()
        else:
            raise Exception(f"ASR API Error ({res.status_code}): {res.text}")

    def safe_type_and_restore_clipboard(self, text):
        """تایپ ایمن متن و بازگردانی کلیپ‌بورد قبلی کاربر همراه با تضمین حفظ فوکوس پنجره فعال"""
        # بازگردانی کامل فوکوس به پنجره هدف قبل از Paste
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
        
        # کپی متن جدید و Paste
        pyperclip.copy(text)
        time.sleep(0.05) 
        keyboard.send('ctrl+v')
        keyboard.send('space')
        
        # بازگردانی کلیپ‌بورد قبلی کاربر در یک ترد جداگانه
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
            wav_bytes = self.pcm_to_wav_bytes(raw_data)
            
            # تعیین زبان و نوع پرامپت (Transcribe یا Translate)
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
            elif self.current_engine in ["custom", "cloud", "groq"]:
                try:
                    text = self.transcribe_custom_api(wav_bytes, lang_code=lang_code, prompt=prompt)
                except Exception as e:
                    print(f"Cloud ASR API failed: {e}. Falling back to Google Speech...")
                    r = sr.Recognizer()
                    audio = sr.AudioData(raw_data, RATE, 2)
                    g_lang = "fa-IR" if self.current_lang in ["fa", "auto", "translate_fa_en"] else "en-US"
                    try:
                        text = r.recognize_google(audio, language=g_lang)
                    except Exception:
                        text = ""
            else: # google
                r = sr.Recognizer()
                audio = sr.AudioData(raw_data, RATE, 2)
                g_lang = "fa-IR" if self.current_lang in ["fa", "auto", "translate_fa_en"] else "en-US"
                try:
                    text = r.recognize_google(audio, language=g_lang)
                except sr.UnknownValueError:
                    print("[Google Speech] Audio not understood / silence")
                    text = ""
                except Exception as e:
                    print(f"[Google Speech] Error: {e}")
                    text = ""

            if text:
                if self.current_lang == "prompt_engineer":
                    text = AIPromptEngineer.generate_engineered_prompt(text)
                elif self.current_lang in ["translate_fa_en", "translate_en_fa"]:
                    # در صورتی که موتور گوگل بوده و ترجمه نیاز است
                    if self.current_engine == "google":
                        mode = "fa_to_en" if self.current_lang == "translate_fa_en" else "en_to_fa"
                        text = LLMTranslatorEngine.translate(text, mode=mode)
                else:
                    # ۱. اعمال نرمالسازی متون فارسی
                    if self.current_lang in ["fa", "auto", "translate_en_fa"]:
                        text = PersianNormalizer.normalize(text)

                    # ۲. اعمال جایگزینی هوشمند واژه‌نامه تخصصی (مثلاً "پایتون" ➔ "Python")
                    text = CUSTOM_DICT.apply_replacements(text)

                # ۳. افزودن متن به حافظه کانتکست تاریخچه
                self.history.append(text)

                # ۴. تایپ ایمن و بازیابی کلیپ‌بورد
                self.safe_type_and_restore_clipboard(text)
                self.set_ui_state("success")
            else:
                self.set_ui_state("idle")
        except Exception as e:
            print(f"Error in recognition: {e}")
            self.set_ui_state("idle")

    def is_hotkey_held(self):
        """تشخیص پایدار و بدون قطعی نگه داشته شدن کلید یا ترکیب کلیدها در ویندوز"""
        hk = self.current_hotkey.lower().replace(" ", "")
        keys = hk.split("+")
        
        # نگاشت به کدهای مجازی ویندوز Win32 GetAsyncKeyState
        VK_MAP = {
            "ctrl": 0x11, "control": 0x11, "leftctrl": 0xA2, "rightctrl": 0xA3,
            "shift": 0x10, "leftshift": 0xA0, "rightshift": 0xA1,
            "alt": 0x12, "leftalt": 0xA4, "rightalt": 0xA5,
            "windows": 0x5B, "win": 0x5B, "leftwindows": 0x5B, "rightwindows": 0x5C,
            "capslock": 0x14, "caps_lock": 0x14,
            "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74,
            "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
            "space": 0x20, "tab": 0x09, "insert": 0x2D, "delete": 0x2E, "`": 0xC0
        }
        
        def is_down(k):
            vk = VK_MAP.get(k)
            if vk:
                return (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000) != 0
            try:
                return keyboard.is_pressed(k)
            except Exception:
                return False

        if len(keys) == 1:
            return is_down(keys[0])
        else:
            # برای ترکیبات، تا زمانی که کلیدها نگه داشته شده‌اند ضبط ادامه دارد
            return any(is_down(k) for k in keys)

    def change_engine(self, engine_name):
        self.current_engine = engine_name
        if engine_name == "local":
            if HAS_FASTER_WHISPER:
                LOCAL_WHISPER.preload_model_async("large-v3-turbo")
        else:
            # پاکسازی کامل VRAM هنگام سوئیچ به آنلاین
            LOCAL_WHISPER.unload_model()
        self.set_ui_state("idle")

    def free_vram_action(self):
        """دستور دستی آزادسازی VRAM از منو"""
        LOCAL_WHISPER.unload_model()
        self.current_engine = "custom"
        self.set_ui_state("idle")

    def change_global_hotkey(self, new_key):
        self.current_hotkey = new_key
        self.bind_hotkey_system()

    def change_engine_language(self, new_lang):
        self.current_lang = new_lang
        self.set_ui_state("idle")

    def update_geometry(self):
        """تنظیم دقیق موقعیت دایره در بالای گوشه سمت راست تسک‌بار ویندوز با padding عالی"""
        try:
            rect = wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0) # SPI_GETWORKAREA
            usable_width = rect.right
            usable_height = rect.bottom
        except Exception:
            usable_width = self.screen_width
            usable_height = self.screen_height - 60

        x_position = usable_width - self.size - 22
        y_position = usable_height - self.size - 22
        self.root.geometry(f"{self.size}x{self.size}+{x_position}+{y_position}")

    def set_ui_state(self, state):
        """تغییر آنی وضعیت و انیمیشن گوی صوتی"""
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
                # بازگشت به حالت آماده‌به‌کار بعد از ۲ ثانیه
                self.reset_timer = self.root.after(2000, lambda: self.set_ui_state("idle"))
        self.root.after(0, update)

    def start_recording(self, mode="hotkey"):
        if self.is_recording:
            return
        
        # ذخیره پنجره فعال جاری (کد ادیتور، مرورگر، برنامه متنی و...)
        try:
            self.target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            self.target_hwnd = None

        self.recording_mode = mode
        self.is_recording = True
        self.set_ui_state("recording")

        threading.Thread(target=self.record_worker, daemon=True).start()

    def record_worker(self):
        self.frames = []
        try:
            stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.is_recording = False
            self.set_ui_state("idle")
            return
            
        while self.is_recording:
            # اگر حالت ضبط با کلید کیبورد است و کلید رها شد -> توقف
            if self.recording_mode == "hotkey" and not self.is_hotkey_held():
                self.is_recording = False
                break
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
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



    def show_context_menu(self, event):
        self.update_menu_indicators()
        self.context_menu.post(event.x_root, event.y_root)

    def quit_app(self):
        LOCAL_WHISPER.unload_model()
        self.p.terminate()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = VoiceTyperGUI()
    app.run()