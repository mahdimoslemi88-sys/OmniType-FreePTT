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

OmniType-FreePTT **v2.1** runs silently in your system tray as a sleek floating micro-indicator dot. By holding a single hotkey, it captures your voice, passes it to your preferred speech recognition engine (Google Free Web, Groq, OpenAI, OpenRouter, or Local Faster-Whisper), and instantly types the text into your active editor or IDE (VS Code, Cursor, Antigravity, ...).

### ✨ Key Features

- **True Push-to-Talk (PTT):** Microphone activates *only* while holding the hotkey. Absolute privacy with zero background listening.
- **100% Free Out-of-the-Box:** Works immediately with Google's free speech engine — no API keys required.
- **🎛️ Tabbed Control Panel:** Right-click the floating orb to open a full panel with 6 tabs (Quick Actions, Engines, Language, Hotkey, History, Settings) — replacing the old compact menu.
- **🤖 Multi-Engine System:** Register **several providers and models** at once. Each engine has a **role** (ASR only / LLM only / Both) and the list order defines **priority**. Switch between models with one click.
- **🧪 Built-in Connection Testing:** Test a provider instantly while adding it, or run "Test All" to check every saved engine (✅/❌ with the server's exact error).
- **⏸️ Auto Pause Video/Music While Speaking:** Pauses YouTube/Spotify/VLC via the Windows media key when recording starts, resumes when you finish (toggleable, saved in `.env`).
- **🖥️ System Tray Icon:** Real app icon in the hidden-tray area with a full menu (dictionary, engines, auto-pause, VRAM release, quit) and a live status tooltip.
- **📚 Persian Dictionary & Normalizer:** Custom technical terms (e.g. «پایتون» ➔ `Python`), half-space fixing, Arabic character cleanup, and spoken English letters (e.g. «پی» ➔ `P`).
- **Simultaneous Translation & Prompt Engineering:** Real-time speech-to-English/Persian translation or AI prompt generation on the fly.
- **Safe Auto-Paste Pipeline:** Injects text via native keyboard emulation while preserving your clipboard history.

---

### 🚀 Quick Start (Users)

1. Download `OmniType-FreePTT-v2.1-Windows.zip` from the **[Releases](../../releases)** tab and extract it.
2. Run `OmniType-FreePTT.exe` (or `run_OmniType-FreePTT.bat`). A green dot appears in the bottom-right corner, and the app icon appears in the hidden tray area.
3. Open any text editor, **hold `Caps Lock`** (or `Ctrl + Windows`), speak, and release the key.

> First launch on Windows may show a SmartScreen notice — click **More info → Run anyway** (the app is open-source and unsigned).

---

### 🤖 Managing Engines & Models

Everything is done from the **Control Panel** (right-click the floating orb):

| Step | What to do |
|---|---|
| 1 | Right-click the orb → **🤖 Engines** tab. Google Speech (free, default) is always listed first and marked green. |
| 2 | Click **➕ Add / Edit / Change Priority of Engines...** to open the engine manager. |
| 3 | Fill in just **4 fields**: engine name, **Base URL**, **API Key**, and the exact **model name**. Pick the **role** (🎙️ ASR only / 🧠 LLM only / 🔀 Both). |
| 4 | Click **🧪 Test Connection** to verify the provider *before saving* — you'll see ✅ or the server's exact error (401/404/429...). |
| 5 | Use the ⬆️/⬇️ priority buttons — **list order = usage order** (first working engine wins). Click **⭐ Activate** to make it active. |

Presets (Groq / OpenAI / OpenRouter / Local) pre-fill URL and model for you.

| Provider | Speech (ASR) model | LLM model | Cost |
| :--- | :--- | :--- | :--- |
| **🌐 Google Speech (default)** | built-in free web engine | free Google Translate | **100% Free** |
| **⚡ Groq Cloud** | `whisper-large-v3-turbo` | `openai/gpt-oss-20b` | Free tier available |
| **🤖 OpenAI** | `whisper-1` | `gpt-4o-mini` | Pay-as-you-go |
| **🔀 OpenRouter** | `openai/whisper` | `meta-llama/llama-3.3-70b-instruct` | Flexible |
| **🖥️ Local / Self-Hosted** | Faster-Whisper | Ollama (`llama3`, ...) | **100% Free, offline** |

> ⚠️ The old Groq model `llama-3.3-70b-versatile` was **decommissioned on Aug 16, 2026** (returns 404). Use `openai/gpt-oss-20b` or `openai/gpt-oss-120b` instead.

The top of the Control Panel shows a **live status indicator** (green ✅ / red ❌ / yellow ⏳) for the active engine — click it to re-test immediately.

---

### ⌨️ Hotkeys

| Hotkey | Action |
|---|---|
| **`Caps Lock`** (hold) | Push-to-Talk voice typing in the selected language |
| **`Ctrl + Alt + P`** (or `Ctrl+Alt+ح`) | Convert selected text/request into an **engineered AI prompt** |
| **`Ctrl + Alt + X`** (or `Ctrl+Alt+ط`) | Show translation of highlighted text in a **floating popup** at the cursor |
| **`Ctrl + Alt + Z`** | Translate & replace selected text: **Persian ➔ English** |
| **`Ctrl + Alt + Shift + Z`** | Translate & replace selected text: **English ➔ Persian** |
| **`Ctrl + Alt + F`** (or `Ctrl+Alt+ب`) | Open **document / long-text translation** window |
| **`Ctrl + Alt + D`** (or `Ctrl+Alt+ی`) | Open the **custom dictionary** window |
| **`Esc`** | Close the floating translation popup |

You can change the PTT hotkey in the **⌨️ Hotkey** tab, or record a fully custom combination.

---

### 🛠️ Installation & Running from Source (Developers)

```bash
# 1. Clone the repository
git clone https://github.com/mahdimoslemi88-sys/OmniType-FreePTT.git
cd OmniType-FreePTT

# 2. Create a virtual environment
python -m venv voice_env

# 3. Install dependencies (from requirements.txt)
voice_env\Scripts\pip install -r requirements.txt

# 4. Test-run from source — just double-click run.bat, or:
run.bat
# equivalent:
# voice_env\Scripts\python.exe OmniType-FreePTT.py
```

- `run.bat` runs the app **with a console** so you can see any errors during testing.
- The config files (`.env`, `custom_dictionary.json`) are created next to the app and are safe to edit.
- **Optional** — local offline ASR engine (requires GPU for best performance):
  ```bash
  voice_env\Scripts\pip install faster-whisper ctranslate2
  ```
  Then pick **🖥️ Faster-Whisper (Local Offline)** from the Engines tab.

---

### 📄 License

This project is released under the **MIT** license — free to use, modify, and redistribute.

---

<a id="persian-docs"></a>
## مستندات فارسی 🇮🇷

<div dir="rtl">

نسخه **۲.۱** نرم‌افزار **OmniType-FreePTT** به صورت یک نقطه شناور کوچک در گوشه صفحه دسکتاپ قرار می‌گیرد و هم‌زمان آیکون آن در ناحیه هیدن‌آیکون‌های تسک‌بار ویندوز دیده می‌شود. با نگه داشتن یک کلید میانبر، صدای شما ضبط شده و متن آن فوراً و با رعایت اصول نگارش فارسی در پنجره فعال (VS Code، Cursor، ورد، تلگرام و...) تایپ می‌شود.

---

### ✨ امکانات نسخه ۲.۱

- **🎛️ پنل کنترل تب‌دار:** راست‌کلیک روی گوی، یک پنجره کامل با ۶ تب باز می‌کند (عملیات سریع، موتورها، زبان، میانبر، تاریخچه، تنظیمات) — به‌جای منوی کوچک قبلی.
- **🤖 سیستم چندموتوره:** هم‌زمان چند پرووایدر و چند مدل ثبت کنید؛ هر موتور یک **نقش** دارد (🎙️ فقط ASR / 🧠 فقط LLM / 🔀 هر دو) و **ترتیب لیست = اولویت استفاده**. با یک کلیک بین مدل‌ها جابه‌جا شوید.
- **🧪 تست اتصال همان‌لحظه‌ای:** هنگام افزودن پرووایدر، بدون ذخیره تست بگیرید (✅ یا خطای دقیق سرور)؛ دکمه «تست همه موتورها» هم همه را پشت‌سرهم بررسی می‌کند.
- **⏸️ توقف خودکار ویدیو/موزیک هنگام صحبت:** با شروع ضبط، رسانه (یوتیوب/اسپاتیفای/VLC) متوقف و با پایان صحبت ادامه می‌یابد — با یک تیک در تب تنظیمات خاموش/روشن می‌شود.
- **🖥️ آیکون تسک‌بار:** در هیدن‌آیکون‌ها با منوی کامل (واژه‌نامه، موتورها، توقف ویدیو، آزادسازی VRAM، خروج) و وضعیت زنده (آماده / در حال ضبط / در حال پردازش).
- **🟢 نشانگر زنده وضعیت موتور** بالای پنل کنترل: سبز = سالم، قرمز = خطا، زرد = در حال بررسی.
- **📚 واژه‌نامه و نرمال‌ساز فارسی:** اصطلاحات تخصصی («پایتون» ➔ `Python`)، اصلاح نیم‌فاصله‌ها، حروف عربی و تلفظ فارسی حروف انگلیسی («پی» ➔ `P`).
- **ترجمه همزمان و مهندسی پرامپت:** گفتار فارسی ➔ انگلیسی، گفتار انگلیسی ➔ فارسی، و تبدیل درخواست به پرامپت ساختاریافته AI.

---

### 🚀 راه‌اندازی سریع (کاربران)

۱. فایل `OmniType-FreePTT-v2.1-Windows.zip` را از بخش **[Releases](../../releases)** دانلود و استخراج کنید.  
۲. `OmniType-FreePTT.exe` (یا `run_OmniType-FreePTT.bat`) را اجرا کنید. دایره سبز در گوشه صفحه + آیکون در تسک‌بار ظاهر می‌شود.  
۳. در هر برنامه‌ای، **`Caps Lock` را نگه دارید**، صحبت کنید و رها کنید.

> در اولین اجرا ممکن است ویندوز هشدار SmartScreen نشان دهد — **More info → Run anyway** را بزنید (برنامه متن‌باز و بدون امضای تجاری است).

---

### 🤖 مدیریت موتورها و مدل‌ها

همه چیز از **پنل کنترل** انجام می‌شود (راست‌کلیک روی گوی):

| مرحله | کار |
|---|---|
| ۱ | راست‌کلیک روی گوی → تب «🤖 موتورها». گوگل (رایگان و پیش‌فرض) اول و با رنگ سبز است. |
| ۲ | «➕ افزودن / ویرایش / تغییر اولویت موتورها...» را بزنید. |
| ۳ | فقط **۴ فیلد** پر کنید: نام، **Base URL**، **API Key** و **نام دقیق مدل** + انتخاب **نقش** (فقط ASR / فقط LLM / هر دو). |
| ۴ | «🧪 تست اتصال و مدل» را بزنید تا **قبل از ذخیره** مطمئن شوید (✅ یا خطای دقیق سرور 401/404/429). |
| ۵ | با دکمه‌های ⬆️/⬇️ اولویت را تنظیم کنید — **ترتیب لیست = ترتیب استفاده** — و «⭐ فعال کن» را بزنید. |

پریست‌های آماده (Groq / OpenAI / OpenRouter / محلی) آدرس و مدل را خودکار پر می‌کنند.

| ارائه‌دهنده | مدل صوت (ASR) | مدل LLM | هزینه |
| :--- | :--- | :--- | :--- |
| **🌐 گوگل (پیش‌فرض)** | موتور رایگان وب | مترجم رایگان گوگل | **۱۰۰٪ رایگان** |
| **⚡ گروک** | `whisper-large-v3-turbo` | `openai/gpt-oss-20b` | سهمیه رایگان |
| **🤖 اوپن‌ای‌آی** | `whisper-1` | `gpt-4o-mini` | مصرفی |
| **🔀 اوپن‌روتر** | `openai/whisper` | `meta-llama/llama-3.3-70b-instruct` | متنوع |
| **🖥️ محلی / آفلاین** | Faster-Whisper | Ollama (`llama3` و...) | **۱۰۰٪ رایگان** |

> ⚠️ مدل قدیمی گروک `llama-3.3-70b-versatile` در **۱۶ آگوست ۲۰۲۶ حذف شده** (خطای 404)؛ به‌جای آن از `openai/gpt-oss-20b` یا `openai/gpt-oss-120b` استفاده کنید.

---

### ⌨️ کلیدهای میانبر

| کلید میانبر | عملکرد |
|---|---|
| **`Caps Lock`** (نگه‌داشتن) | تایپ صوتی فشاری (Push-to-Talk) به زبان انتخابی |
| **`Ctrl + Alt + P`** (یا `Ctrl+Alt+ح`) | تبدیل متن/درخواست انتخابی به **پرامپت مهندسی‌شده AI** |
| **`Ctrl + Alt + X`** (یا `Ctrl+Alt+ط`) | نمایش ترجمه متن انتخاب‌شده در **پاپ‌آپ شناور** محل موس |
| **`Ctrl + Alt + Z`** (یا `Ctrl+Alt+ظ`) | ترجمه و جایگزینی: **فارسی ➔ انگلیسی** |
| **`Ctrl + Alt + Shift + Z`** | ترجمه و جایگزینی: **انگلیسی ➔ فارسی** |
| **`Ctrl + Alt + F`** (یا `Ctrl+Alt+ب`) | پنجره **ترجمه اسناد و متن طولانی** |
| **`Ctrl + Alt + D`** (یا `Ctrl+Alt+ی`) | پنجره **واژه‌نامه تخصصی** |
| **`Esc`** | بستن پاپ‌آپ شناور ترجمه |

کلید PTT را می‌توانید از تب «⌨️ میانبر» عوض کنید یا یک ترکیب کاملاً دلخواه ضبط کنید.

---

### 🛠️ نصب و اجرا از سورس (توسعه‌دهندگان)

```bash
# ۱. کلون کردن ریپازیتوری
git clone https://github.com/mahdimoslemi88-sys/OmniType-FreePTT.git
cd OmniType-FreePTT

# ۲. ساخت محیط مجازی
python -m venv voice_env

# ۳. نصب نیازمندی‌ها (از requirements.txt)
voice_env\Scripts\pip install -r requirements.txt

# ۴. اجرای تستی — کافی است run.bat را بزنید:
run.bat
# یا معادل:
# voice_env\Scripts\python.exe OmniType-FreePTT.py
```

- `run.bat` برنامه را **با کنسول** اجرا می‌کند تا خطاها دیده شوند.
- فایل‌های تنظیمات (`.env` و `custom_dictionary.json`) کنار برنامه ساخته می‌شوند.
- **اختیاری** — موتور محلی آفلاین (برای بهترین نتیجه نیاز به کارت گرافیک دارد):
  ```bash
  voice_env\Scripts\pip install faster-whisper ctranslate2
  ```
  سپس از تب «موتورها» گزینه «🖥️ Faster-Whisper (Local Offline)» را انتخاب کنید.

---

### ⚙️ اجرای خودکار هنگام روشن شدن سیستم (Windows Startup)

۱. `Win + R` را بزنید، `shell:startup` را تایپ و Enter بزنید.  
۲. یک Shortcut از `OmniType-FreePTT.exe` ساخته و در این پوشه قرار دهید.

---

### 📄 لایسنس (License)

این پروژه تحت لایسنس **MIT** منتشر شده است؛ استفاده تجاری، تغییر و بازنشر آن کاملاً آزاد و رایگان است.

</div>
