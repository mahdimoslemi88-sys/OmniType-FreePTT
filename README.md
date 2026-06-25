# OmniType-FreePTT 🎙️⌨️

An ultra-lightweight, zero-cost, and private Push-to-Talk (PTT) Voice Typing utility for Windows 11. Designed specifically for developers and power users to streamline typing workflow without any subscription fees.

یک ابزار فوق‌العاده سبک، کاملاً رایگان و امن برای تایپ صوتی فشاری (PTT) در ویندوز ۱۱. طراحی شده مخصوص برنامه‌نویسان و کاربران حرفه‌ای جهت سرعت بخشیدن به فرآیند نوشتن بدون نیاز به پرداخت هزینه‌های اشتراکی.

---

<div align="center">
  <h3>
    <a href="#english-docs">🇺🇸 English</a> | <a href="#persian-docs">🇮🇷 فارسی</a>
  </h3>
</div>

---

<a id="english-docs"></a>
## English Documentation 🌍

OmniType-FreePTT runs silently in your system tray as a micro-indicator dot. By holding a single hotkey, it captures your voice, utilizes Google’s cloud speech recognition engine under the hood, and instantly types the text into your active editor or IDE (like VS Code, Cursor, or Google Antigravity).

### ✨ Features

- **True Push-to-Talk (PTT):** Microphone activates *only* while holding the hotkey. Absolute privacy control.
- **100% Free & Open-Source:** No API keys required, no monthly subscriptions, no hidden limits.
- **Bilingual Dynamic Support:** Seamlessly switch between Persian (fa-IR) and English (en-US) engines via context menu.
- **Micro UI Indicator:** A tiny 32px anti-aliased floating circle that changes color based on system state (Green: Idle, Red: Recording, Yellow: Processing, Blue: Success).
- **Auto-Paste Pipeline:** Synthesizes and injects text via native OS keyboard emulation layers directly into the focused window.

### 🚀 Quick Start (For Users)

1. Download `voice_typer.exe` from the latest Release.
2. Run the executable. A small green dot will appear in the bottom-right corner of your screen.
3. Open any text editor, **Hold `Caps Lock`**, speak your mind, and release the key.

### 🛠️ Installation & Compilation (For Developers)

If you want to run the raw source code or compile it yourself:

```bash
# Clone the repository
git clone https://github.com/your-username/OmniType-FreePTT.git
cd OmniType-FreePTT

# Create and activate environment
python -m venv voice_env
call voice_env\Scripts\activate

# Install dependencies
pip install pyaudio speechrecognition keyboard pyperclip pyinstaller

# Run locally
python voice_typer.py

# Compile to a standalone single EXE
python -m PyInstaller --noconsole --onefile --icon=icon.ico --collect-all pyaudio --collect-all speech_recognition voice_typer.py
```

<br>

---

<a id="persian-docs"></a>
## مستندات فارسی 🇮🇷

<div dir="rtl">

برنامه **OmniType-FreePTT** به صورت یک چراغ مینیاتوری و شناور در گوشه صفحه دسکتاپ شما قرار می‌گیرد. با نگه داشتن یک کلید میانبر، صدای شما را ضبط کرده و با کمک موتور پردازش صوت گوگل، متن ما‌به‌ازای آن را فوراً در پنجره یا ادیتور فعال شما (مانند VS Code یا ادیتورهای دیگر) پیست می‌کند.

### ✨ قابلیت‌های کلیدی

- **مكانیزم واقعی فشاری (PTT):** میکروفون *فقط* زمان نگه داشتن دکمه فعال است؛ امنیت و حریم خصوصی مطلق.
- **۱۰۰٪ رایگان و اپن‌سورس:** بدون نیاز به خرید کلید API، بدون اشتراک ماهیانه و بدون محدودیت در استفاده.
- **پشتیبانی دینامیک دو زبانه:** قابلیت سوییچ آنی بین موتور زبان فارسی (fa-IR) و انگلیسی (en-US) از طریق کلیک‌راست.
- **رابط گرافیکی مینیاتوری:** یک دایره کوچک ۳۲ پیکسلی صیقلی که با تغییر رنگ، وضعیت سیستم را نشان می‌دهد (سبز: آماده، قرمز: ضبط، زرد: پردازش، آبی: موفقیت).
- **تزریق مستقیم به سیستم‌عامل:** شبیه‌سازی لایه سخت‌افزاری کیبورد برای پیست خودکار متن بدون دخالت کاربر.

### 🚀 راه اندازی سریع (برای کاربران)

۱. فایل `voice_typer.exe` را از بخش Releases دانلود کنید.  
۲. فایل را اجرا کنید. یک دایره سبز رنگ مینیاتوری در گوشه پایین سمت راست صفحه ظاهر می‌شود.  
۳. ادیتور خود را باز کنید، **دکمه `Caps Lock` را نگه دارید**، صحبت کنید و سپس دکمه را رها کنید.

### 🛠️ راه اندازی و کامپایل سورس‌کد (برای توسعه‌دهندگان)

اگر می‌خواهید کدهای خام را اجرا کرده یا شخصی‌سازی کنید، مراحل زیر را در CMD طی کنید:

</div>

```bash
# کلون کردن پروژه
git clone https://github.com/your-username/OmniType-FreePTT.git
cd OmniType-FreePTT

# ساخت و فعال‌سازی محیط مجازی
python -m venv voice_env
call voice_env\Scripts\activate

# نصب کتابخانه‌های پیش‌نیاز
pip install pyaudio speechrecognition keyboard pyperclip pyinstaller

# اجرای محلی اسکریپت
python voice_typer.py

# کامپایل به فایل تک اگزه مستقل
python -m PyInstaller --noconsole --onefile --icon=icon.ico --collect-all pyaudio --collect-all speech_recognition voice_typer.py
```

<br>

---

## ⚙️ How to add to Windows Startup / اضافه کردن به استارتاپ ویندوز

To make it launch automatically every time you turn on your PC / برای اجرای خودکار برنامه با هر بار روشن شدن سیستم:

1. Press `Win + R`, type `shell:startup` and hit Enter. *(کلیدهای `Win + R` را بزنید، عبارت `shell:startup` را تایپ کرده و اینتر کنید.)*
2. Create a **Shortcut** of `voice_typer.exe` and move it into that folder. *(یک **Shortcut (میانبر)** از فایل `voice_typer.exe` بسازید و آن را داخل این پوشه بیندازید.)*

---

## 📄 License / لایسنس

This project is licensed under the MIT License - feel free to use, modify, and distribute it for free.  
این پروژه تحت لایسنس MIT منتشر شده است؛ استفاده، تغییر و بازنشر آن کاملاً آزاد و رایگان است.
