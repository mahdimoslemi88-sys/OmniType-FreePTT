"""متن‌به‌گفتار (TTS) — خواندن نتایج ترجمه با صدای سیستم یا صدای آنلاین.

استراتژی پخش:
  1. صدای محلی SAPI ویندوز (pyttsx3) اگر برای زبان متن موجود باشد (مثل David/Zira انگلیسی).
  2. برای فارسی بدون صدای محلی → صدای نورال آنلاین مایکروسافت (edge-tts) با
     `fa-IR-FaridNeural` — تلفظ فارسی واقعی، رایگان و بدون کلید.
  3. اگر هیچ‌کدام ممکن نبود → هیچ‌چیز پخش نمی‌شود و وضعیت به UI گزارش می‌شود
     تا راهنمای نصب صدای فارسی نمایش داده شود.

پخش همیشه در thread جداگانه انجام می‌شود تا پنجرهٔ برنامه هرگز قفل نشود.
هر خطا بی‌صدا نادیده گرفته می‌شود — برنامه هیچ‌وقت نمی‌شکند.
"""
import os
import re
import tempfile
import threading

_HAS_PYTTSX3 = False
try:
    import pyttsx3
    _HAS_PYTTSX3 = True
except ImportError:
    pyttsx3 = None

_HAS_EDGE = False
try:
    import edge_tts  # noqa: F401
    _HAS_EDGE = True
except ImportError:
    edge_tts = None

_PERSIAN_RE = re.compile(r'[\u0600-\u06FF]')

# صدای نورال فارسی مایکروسافت (زن/مرد)
PERSIAN_VOICES = ("fa-IR-DilaraNeural", "fa-IR-FaridNeural")

# حداکثر طول هر قطعه برای سرویس آنلاین (کوتاه‌تر از سقف سرویس تا امن باشد)
_ONLINE_CHUNK_MAX = 900

# ── حالت پخش قابل توقف ───────────────────────────────────────────
# `_stop_requested` از هر thread با `stop_playback()` ست می‌شود؛
# حلقه‌های پخش (SAPI و MCI) آن را چک و متوقف می‌شوند.
_stop_requested = threading.Event()
# ارجاع به موتور pyttsx3 در حال پخش تا `stop_playback` بتواند آن را متوقف کند
_current_engine = None


def stop_playback():
    """توقف فوری هر پخش صوتی در حال انجام."""
    _stop_requested.set()
    engine = _current_engine
    if engine is not None:
        try:
            engine.stop()
        except Exception:
            pass


def is_playing():
    """آیا در حال حاضر پخشی در جریان است؟"""
    return _current_engine is not None


def _reset_stop_flag():
    """پاک‌سازی پرچم توقف در شروع هر پخش جدید."""
    _stop_requested.clear()


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


def has_persian_voice():
    """آیا یک صدای فارسی SAPI روی ویندوز نصب است؟ (برای نمایش راهنما)."""
    if not _HAS_PYTTSX3:
        return False
    try:
        engine = pyttsx3.init()
        try:
            return _pick_voice(engine, "سلام") is not None
        finally:
            try:
                engine.stop()
            except Exception:
                pass
    except Exception:
        return False


def _play_mp3(path):
    """پخش فایل MP3 با MCI ویندوز (بدون وابستگی اضافه) با قابلیت توقف.

    به‌جای `wait` بلوکه، وضعیت پخش را در حلقه چک می‌کند تا با
    `stop_playback()` بتوان فوراً متوقف کرد. برمی‌گرداند موفقیت.
    """
    import time
    try:
        import ctypes
        mci = ctypes.windll.winmm.mciSendStringW
        err_buf = ctypes.create_unicode_buffer(256)
        if mci(f'open "{path}" alias omni_tts', err_buf, 256, 0) != 0:
            return False
        try:
            mci("play omni_tts", err_buf, 256, 0)
            while not _stop_requested.is_set():
                mode_buf = ctypes.create_unicode_buffer(32)
                mci("status omni_tts mode", mode_buf, 32, 0)
                if mode_buf.value.strip().lower() not in ("playing", "paused"):
                    break
                time.sleep(0.05)
            return True
        finally:
            mci("close omni_tts", err_buf, 256, 0)
    except Exception:
        return False


def _chunk_text(text, limit=_ONLINE_CHUNK_MAX):
    """برش متن طولانی به قطعات امن (در مرز جمله/نقطه تا حد امکان)."""
    text = text.strip()
    if len(text) <= limit:
        return [text] if text else []
    chunks = []
    while len(text) > limit:
        cut = text.rfind(" ", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks


def _speak_online(text):
    """پخش فارسی با صدای نورال آنلاین مایکروسافت (edge-tts → MP3 → MCI)."""
    if not _HAS_EDGE:
        return False
    import asyncio

    voice = PERSIAN_VOICES[0]
    chunks = _chunk_text(text)
    ok = False
    for chunk in chunks:
        # اگر بین قطعات توقف خواسته شد، پخش را متوقف کن
        if _stop_requested.is_set():
            break
        path = None
        try:
            fd, path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)

            async def _synth():
                tts = edge_tts.Communicate(chunk, voice=voice)
                await tts.save(path)

            asyncio.run(_synth())
            if _play_mp3(path):
                ok = True
        except Exception as e:
            print(f"[TTS] Online synthesis failed: {e}")
            return False
        finally:
            if path:
                try:
                    os.remove(path)
                except Exception:
                    pass
    return ok


def speak(text, wait=False, on_done=None):
    """خواندن متن: صدای محلی اگر موجود، وگرنه صدای آنلاین فارسی (edge-tts).

    - اجرا در thread جداگانه (wait=False) تا GUI مسدود نشود.
    - ورودی خالی → هیچ.
    - هر پخش جدید پرچم توقف قبلی را پاک می‌کند؛ `stop_playback()` می‌تواند
      هر پخشی را فوراً متوقف کند.
    - `on_done(status)` بعد از پایان (یا توقف) پخش در همان thread صدا زده می‌شود:
        status = {"source": "local"|"online"|"none",
                  "lang": "fa"|"en"|None,
                  "reason": None|"empty"|"online_failed"|"no_local_voice"|"stopped"}
      UI می‌تواند از این برای نمایش راهنمای نصب صدای فارسی استفاده کند.
    """
    global _current_engine
    status = {"source": "none", "lang": None, "reason": None}
    if not text or not text.strip():
        status["reason"] = "empty"
        if on_done:
            on_done(status)
        return

    fa = is_persian(text)

    def worker():
        global _current_engine
        result = dict(status)
        _reset_stop_flag()

        # ── مسیر محلی SAPI ──────────────────────────────────────
        if _HAS_PYTTSX3:
            engine = None
            try:
                engine = pyttsx3.init()
                _current_engine = engine
                voice = _pick_voice(engine, text)
                if voice:
                    engine.setProperty("voice", voice)
                engine.say(text)
                engine.runAndWait()
                if _stop_requested.is_set():
                    result = {"source": "none", "lang": "fa" if fa else "en", "reason": "stopped"}
                else:
                    result = {"source": "local", "lang": "fa" if fa else "en", "reason": None}
                if on_done:
                    on_done(result)
                return
            except Exception as e:
                print(f"[TTS] Local voice failed: {e}")
            finally:
                _current_engine = None
                if engine is not None:
                    try:
                        engine.stop()
                    except Exception:
                        pass

        # ── فارسی بدون صدای محلی → صدای آنلاین ───────────────────
        if fa and _HAS_EDGE:
            if _speak_online(text):
                if _stop_requested.is_set():
                    result = {"source": "none", "lang": "fa", "reason": "stopped"}
                else:
                    result = {"source": "online", "lang": "fa", "reason": None}
                if on_done:
                    on_done(result)
                return
            result = {"source": "none", "lang": "fa",
                      "reason": "stopped" if _stop_requested.is_set() else "online_failed"}
            if on_done:
                on_done(result)
            return

        # ── هیچ راهی نبود ────────────────────────────────────────
        result = {"source": "none", "lang": "fa" if fa else "en",
                  "reason": "stopped" if _stop_requested.is_set()
                  else ("online_failed" if fa else "no_local_voice")}
        if on_done:
            on_done(result)

    if wait:
        worker()
    else:
        threading.Thread(target=worker, daemon=True).start()


def persian_voice_guide():
    """متن راهنمای نصب صدای فارسی SAPI روی ویندوز (برای نمایش به کاربر)."""
    return (
        "صدای فارسی روی ویندوز نصب نیست و سرویس صدای آنلاین در دسترس نبود.\n\n"
        "📥 نصب صدای فارسی (راهنمای ویندوز ۱۰/۱۱):\n"
        "۱. تنظیمات (Settings) → زمان و زبان (Time & language)\n"
        "۲. زبان و منطقه (Language & region)\n"
        "۳. افزودن زبان (Add a language) → فارسی (Persian)\n"
        "۴. روی فارسی کلیک کنید → گزینه‌ها (Options)\n"
        "۵. در بخش «گفتار» (Speech) دکمهٔ دانلود را بزنید و منتظر نصب بمانید\n"
        "۶. برنامه را دوباره اجرا کنید — صدا به‌صورت خودکار انتخاب می‌شود.\n\n"
        "یا اگر اینترنت دارید، همان دکمهٔ «پخش صدا» را دوباره بزنید تا با\n"
        "صدای آنلاین مایکروسافت (fa-IR-DilaraNeural) پخش شود."
    )
