# OmniType-FreePTT 🎙️⌨️

An ultra-lightweight, zero-cost, and private Push-to-Talk (PTT) Voice Typing utility for Windows 11. Designed specifically for developers and power users to streamline typing workflow without any subscription fees.

یک ابزار فوق‌العاده سبک، کاملاً رایگان و امن برای تایپ صوتی فشاری (PTT) در ویندوز ۱۱. طراحی شده مخصوص برنامه‌نویسان و کاربران حرفه‌ای جهت سرعت بخشیدن به فرآیند نوشتن بدون نیاز به پرداخت هزینه‌های اشتراکی.

---

<div align="center">
  <h3>
    <a href="#english-docs">🇺🇸 English Documentation</a> | <a href="#persian-docs">🇮🇷 مستندات فارسی</a>
  </h3>
</div>

---

<a id="english-docs"></a>
## English Documentation 🌍

OmniType-FreePTT runs silently in your system tray as a sleek micro-indicator dot. By holding a single hotkey, it captures your voice, passes it to your preferred speech recognition engine (Google Free Web, Groq, OpenAI, OpenRouter, or Local Ollama/vLLM), and instantly types the text into your active editor or IDE (such as VS Code, Cursor, or Antigravity).

### ✨ Key Features

- **True Push-to-Talk (PTT):** Microphone activates *only* while holding the hotkey. Absolute privacy control with zero background listening.
- **100% Free & Open-Source Out-of-the-Box:** Works immediately using Google's free speech engine without requiring any API keys or subscriptions.
- **Universal AI & API Provider Support:** Seamlessly connect to **any** OpenAI-compatible provider (Groq, OpenAI, OpenRouter, local Ollama/vLLM, or custom Base URLs & Models) via the in-app settings window.
- **Custom Hotkey Mapping:** Easily define any custom key combination (e.g., `Ctrl + Windows`, `Caps Lock`, `F2`) via the interactive UI setting.
- **Persian Text Normalization & Custom Dictionary:** Automatically fixes half-spaces (نیم‌فاصله), Arabic characters, punctuations, and intelligently translates spoken terms (e.g., "پایتون" ➔ "Python").
- **Simultaneous Translation & Prompt Engineering:** Real-time speech-to-English translation or AI prompt generation on the fly.
- **Micro UI Indicator:** A 58px anti-aliased floating circle that changes color based on system state (Green: Idle, Red: Recording, Yellow: Processing, Cyan: Success).
- **Safe Auto-Paste Pipeline:** Synthesizes and injects text via native OS keyboard emulation layers directly into the focused window while preserving your clipboard history.

---

### 🌐 Recommended AI Providers (پرووایدرهای پیشنهادی)

OmniType-FreePTT is completely open and flexible. You can use any provider of your choice:

| Provider | Speech Engine (ASR) | Language Model (LLM) | Speed | Cost | Recommended For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **🔍 Google Speech (Default)** | Built-in Free Web Engine | Free Google Translate Web | ⚡ Fast (~1.0s) | **100% Free** | Instant zero-setup usage without API keys |
| **⚡ Groq Cloud (Recommended)** | `whisper-large-v3-turbo` | `llama-3.3-70b-versatile` | 🚀 Realtime (<0.3s) | **Free Tier Available** | Best speed, daily coding, ultra-low latency |
| **🤖 OpenAI** | `whisper-1` | `gpt-4o-mini` | ⚡ Fast (~0.8s) | Paid (Pay-as-you-go) | Maximum accuracy on complex technical jargon |
| **🔀 OpenRouter** | `openai/whisper` | `meta-llama/llama-3.3-70b-instruct` | ⚡ Fast (~0.9s) | Flexible | Access to 100+ models with one unified API key |
| **🖥️ Local / Self-Hosted** | `whisper` / Faster-Whisper | `llama3` / `qwen2.5-coder` | 💻 Depends on GPU | **100% Free** | Maximum data privacy, offline corporate usage |

#### 🔑 How to Configure Providers:
1. Right-click the floating circle on your screen.
2. Select **⚙️ تنظیمات ارائه‌دهندگان هوش مصنوعی (Universal AI & API)**.
3. Choose a **Preset** from the dropdown (e.g., `⚡ Groq Cloud` or `🤖 OpenAI`) or type your custom `Base URL`, `API Key`, and `Model Name`.
4. Click **✅ ذخیره کلیه تنظیمات**.

---

### 🚀 Quick Start (For Users)

1. Download `OmniType-FreePTT.exe` from the latest **[Releases](../../releases)** tab.
2. Run the executable. A small green dot will appear in the bottom-right corner of your screen.
3. Open any text editor, **Hold `Caps Lock`** (or `Ctrl + Windows`), speak your mind, and release the key.

### 🛠️ Installation & Compilation (For Developers)

```bash
# Clone the repository
git clone https://github.com/your-username/OmniType-FreePTT.git
cd OmniType-FreePTT

# Create and activate environment
python -m venv voice_env
call voice_env\Scripts\activate

# Install dependencies
pip install pyaudio speechrecognition keyboard pyperclip requests pyinstaller

# Run locally
python OmniType-FreePTT.py

# Compile to a standalone single EXE
python -m PyInstaller --noconsole --onefile --clean --icon=icon.ico --collect-all pyaudio --collect-all speech_recognition OmniType-FreePTT.py
```

<br>

---

<a id="persian-docs"></a>
## مستندات فارسی 🇮🇷

<div dir="rtl">

نرم‌افزار **OmniType-FreePTT** به صورت یک چراغ مینیاتوری و شناور شیشه‌ای در گوشه صفحه دسکتاپ شما قرار می‌گیرد. با نگه داشتن یک کلید میانبر (مانند `Caps Lock` یا `Ctrl + Windows`)، صدای شما را با بالاترین کیفیت ضبط کرده و متن ما‌به‌ازای آن را فوراً و با رعایت دقیق اصول نگارش فارسی در پنجره فعال شما (مانند VS Code، Cursor، ورد یا تلگرام) تایپ می‌کند.

---

### 🌟 پرووایدرهای پیشنهادی هوش مصنوعی (AI Providers)

این برنامه هیچ محدودیتی برای انتخاب سرویس‌دهنده ندارد و با تمامی ارائه‌دهندگان استاندارد سازگار با OpenAI کار می‌کند:

| ارائه‌دهنده | موتور صوت (ASR) | مدل زبانی و ترجمه (LLM) | سرعت | هزینه | موارد کاربرد پیشنهادی |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **🔍 گوگل (Google Speech - پیش‌فرض)** | موتور رایگان تحت وب گوگل | مترجم رایگان گوگل | ⚡ سریع (~۱ ثانیه) | **۱۰۰٪ رایگان** | شروع فوری بدون نیاز به هیچ کلید یا ثبت‌نام |
| **⚡ گروک کلود (Groq Cloud - پیشنهادی)** | `whisper-large-v3-turbo` | `llama-3.3-70b-versatile` | 🚀 فوق‌سریع (<۰.۳ ثانیه) | **سهمیه رایگان سخاوتمندانه** | تایپ بلادرنگ و سریع‌ترین سرعت پردازش |
| **🤖 اوپن‌ای‌آی (OpenAI)** | `whisper-1` | `gpt-4o-mini` | ⚡ سریع (~۰.۸ ثانیه) | هزینه مصرفی ارزان | بالاترین دقت نگارشی در متون علمی و تخصصی |
| **🔀 اوپن‌روتر (OpenRouter)** | `openai/whisper` | `meta-llama/llama-3.3-70b-instruct` | ⚡ سریع (~۰.۹ ثانیه) | متنوع | دسترسی به صدها مدل هوش مصنوعی با یک کلید |
| **🖥️ سرور محلی (Ollama / vLLM / محلی)** | `whisper` / Faster-Whisper | `llama3` / `qwen2.5-coder` | 💻 وابسته به کارت گرافیک | **۱۰۰٪ رایگان** | امنیت مطلق و کارکرد کاملاً آفلاین و درون‌سازمانی |

#### 🔑 راهنمای اتصال و دریافت کلید:
- **برای Groq (پیشنهادی):** در سایت [console.groq.com](https://console.groq.com) ثبت‌نام کنید و از بخش API Keys کلید رایگان دریافت کرده و در پنجره تنظیمات برنامه وارد کنید.
- **برای OpenAI:** کلید خود را از [platform.openai.com](https://platform.openai.com) دریافت نمایید.
- **بدون کلید (پیش‌فرض):** برنامه به طور پیش‌فرض روی موتور رایگان وب گوگل تنظیم است و بدون نیاز به هیچ کانفیگی کار می‌کند.

---

### ✨ قابلیت‌های برجسته

- **مكانیزم واقعی فشاری (Push-to-Talk):** میکروفون *فقط* هنگام نگه داشتن دکمه فعال است؛ امنیت و حریم خصوصی ۱۰۰٪ تضمین شده.
- **پشتیبانی کامل از تمامی پرووایدرها (Universal AI):** امکان اتصال به هر API دلخواه با پریست‌های آماده یک‌کلیکه.
- **شخصی‌سازی میانبر (Custom Hotkeys):** تنظیم هر نوع کلید دلخواه تکی یا ترکیبی (`Ctrl + Windows`, `Caps Lock`, `F2`).
- **نرمالساز و ویراستار متون فارسی:** اصلاح خودکار نیم‌فاصله‌ها، حذف حروف عربی، تنظیم فواصل علائم نگارشی و پاکسازی اصوات پرکننده گفتاری.
- **واژه‌نامه تخصصی برنامه‌نویسی:** تبدیل هوشمند اصطلاحات فنی گفتاری (مانند «پایتون» به «Python» یا «داکر» به «Docker»).
- **ترجمه همزمان و مهندسی پرامپت:** تبدیل گفتار فارسی به انگلیسی روان یا تولید پرامپت ساختاریافته هوش مصنوعی.
- **رابط کاربری مینیاتوری:** گوی شیشه‌ای ۵۸ پیکسلی با انیمیشن‌های تنفسی، موج‌های هولوگرافیک و وضعیت پردازش.
- **تزریق ایمن متن:** بازگردانی خودکار محتوای کلیپ‌بورد کاربر پس از تایپ بدون دزدیدن فوکوس پنجره فعال.

### 🛡️ نکته امنیتی مهم هنگام اجرای اولین بار در ویندوز (SmartScreen Notice)

از آنجا که نرم‌افزار **OmniType-FreePTT** به صورت ۱۰۰٪ **رایگان و متن‌باز (Open Source)** توسعه داده شده و نیازی به گواهی‌های چندصد دلاری تجاری ندارد، ویندوز ممکن است هنگام اولین اجرا پیام *"Windows protected your PC"* را نشان دهد.

**نحوه اجرای بی‌خطر و آسان (فقط بار اول):**
1. روی لینک **More info** (اطلاعات بیشتر) در کادر هشدار کلیک کنید.
2. دکمه **Run anyway** (به هر حال اجرا شود) را بزنید.

---

### 🎮 کلیدهای میانبر اصلی نسخه جدید

| کلید میانبر | عملکرد |
|---|---|
| **`Caps Lock`** (نگه‌داشتن) | تایپ صوتی فوق‌العاده سریع به زبان انتخابی (Push-to-Talk) |
| **`Ctrl + Alt + P`** (یا `Ctrl+Alt+ح`) | 🤖 **تبدیل درخواست/متن فارسی به پرامپت مهندسی‌شده ساختاریافته AI** |
| **`Ctrl + Alt + X`** (یا `Ctrl+Alt+ط` / `Ctrl+Alt+خ`) | ✨ **مشاهده آنی ترجمه متون هایلایت‌شده در پاپ‌آپ شناور در محل موس** |
| **`Ctrl + Alt + Z`** (یا `Ctrl+Alt+ظ`) | 🌐 **ترجمه و جایگزینی مستقیم روی صفحه: فارسی ➔ انگلیسی** |
| **`Ctrl + Alt + Shift + Z`** | 🇮🇷 **ترجمه و جایگزینی مستقیم روی صفحه: انگلیسی ➔ فارسی** |
| **`Esc`** | بستن فوری پاپ‌آپ شناور |

---

### 🚀 راه اندازی سریع (برای کاربران)

۱. فایل `OmniType-FreePTT-v2.0-Windows.zip` را از بخش **[Releases](../../releases)** دانلود و استخراج کنید.  
۲. فایل `OmniType-FreePTT.exe` یا `run_OmniType-FreePTT.bat` را اجرا کنید. یک دایره سبز رنگ مینیاتوری در گوشه صفحه ظاهر می‌شود.  
۳. در هر برنامه‌ای که می‌خواهید بنویسید (ادیتور، مرورگر، تلگرام و...)، **دکمه `Caps Lock` را نگه دارید**، صحبت کنید و سپس دکمه را رها کنید.

### 🛠️ راه اندازی و کامپایل سورس‌کد (برای توسعه‌دهندگان)

</div>

```bash
# ۱. کلون کردن ریپازیتوری
git clone https://github.com/your-username/OmniType-FreePTT.git
cd OmniType-FreePTT

# ۲. ایجاد و فعال‌سازی محیط مجازی پایتون
python -m venv voice_env
call voice_env\Scripts\activate

# ۳. نصب نیازمندی‌ها
pip install pyaudio speechrecognition keyboard pyperclip requests pyinstaller

# ۴. اجرای اسکریپت
python OmniType-FreePTT.py

# ۵. کامپایل به فایل تک‌اگزه مستقل و پرتابل
python -m PyInstaller --noconsole --onefile --clean --icon=icon.ico --collect-all pyaudio --collect-all speech_recognition OmniType-FreePTT.py
```

<div dir="rtl">

---

### ⚙️ اجرای خودکار هنگام روشن شدن سیستم (Windows Startup)

۱. کلیدهای `Win + R` را بزنید، عبارت `shell:startup` را تایپ کرده و Enter بزنید.  
۲. یک Shortcut (میانبر) از فایل `OmniType-FreePTT.exe` ساخته و در این پوشه قرار دهید.

---

### 📄 لایسنس (License)

این پروژه تحت لایسنس **MIT** منتشر شده است؛ استفاده تجاری، تغییر و بازنشر آن کاملاً آزاد و رایگان است.

</div>
