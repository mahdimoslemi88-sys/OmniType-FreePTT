"""متن‌به‌گفتار (TTS) — خواندن نتایج ترجمه با صدای سیستم.

پیاده‌سازی با `pyttsx3` (SAPI5 ویندوز) و اجرای آن در thread جداگانه تا
پنجرهٔ برنامه هرگز قفل نشود. اگر pyttsx3 نصب نباشد یا خطایی رخ دهد،
هیچ‌چیز پخش نمی‌شود و برنامه نمی‌شکند.
"""
import re
import threading

_HAS_PYTTSX3 = False
try:
    import pyttsx3
    _HAS_PYTTSX3 = True
except ImportError:
    pyttsx3 = None

_PERSIAN_RE = re.compile(r'[\u0600-\u06FF]')


def is_persian(text):
    """آیا متن شامل حروف فارسی است؟"""
    return bool(_PERSIAN_RE.search(text or ""))


def _pick_voice(engine, text):
    """انتخاب صدا: فارسی → صدای فارسی (اگر موجود)، انگلیسی → صدای en.

    برمی‌گرداند id صدا یا None (پیش‌فرض سیستم).
    """
    try:
        voices = engine.getProperty("voices") or []
    except Exception:
        return None
    if not voices:
        return None
    fa = is_persian(text)

    def lang_of(v):
        try:
            langs = getattr(v, "languages", None) or []
            return str(langs[0]).lower() if langs else ""
        except Exception:
            return ""

    for v in voices:
        vid = (v.id or "").lower()
        if fa and ("fa-" in vid or "fa_" in vid or "persian" in vid or "fa-" in lang_of(v)):
            return v.id
    for v in voices:
        vid = (v.id or "").lower()
        if (not fa) and ("en-" in vid or "en_" in vid or "english" in vid or "en-" in lang_of(v)):
            return v.id
    return None


def speak(text, wait=False):
    """خواندن متن با صدای سیستم.

    - اجرا در thread جداگانه (wait=False) تا GUI مسدود نشود.
    - ورودی خالی → هیچ.
    - هر خطای داخلی بی‌صدا نادیده گرفته می‌شود.
    """
    if not text or not text.strip():
        return
    if not _HAS_PYTTSX3:
        return

    def worker():
        engine = None
        try:
            engine = pyttsx3.init()
            voice = _pick_voice(engine, text)
            if voice:
                engine.setProperty("voice", voice)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS] Error: {e}")
        finally:
            if engine is not None:
                try:
                    engine.stop()
                except Exception:
                    pass

    if wait:
        worker()
    else:
        threading.Thread(target=worker, daemon=True).start()
