"""تبدیل صوت به متن با API ابری (OpenAI-compatible) و Google Speech رایگان."""
import requests
import speech_recognition as sr

from core.audio import RATE
from core.config import get_asr_candidates


def _transcribe_with(cfg, wav_bytes, lang_code="fa", prompt=None):
    """تبدیل صوت به متن با یک موتور مشخص (اندپوینت سازگار با OpenAI / Whisper)."""
    base_url = (cfg.get("base_url") or "https://api.groq.com/openai/v1").rstrip('/')
    url = f"{base_url}/audio/transcriptions"
    headers = {}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    files = {"file": ("voice.wav", wav_bytes, "audio/wav")}
    data = {
        "model": cfg.get("model") or "whisper-large-v3-turbo",
        "prompt": prompt or "",
    }
    if lang_code:
        data["language"] = lang_code

    res = requests.post(url, headers=headers, files=files, data=data, timeout=15)
    if res.status_code == 200:
        return res.json().get("text", "").strip()
    else:
        raise Exception(f"ASR API Error ({res.status_code}): {res.text}")


def transcribe_custom_api(wav_bytes, lang_code="fa", prompt=None, preferred_engine=None):
    """تبدیل صوت به متن — ابتدا موتور انتخابی کاربر، سپس بقیه به ترتیب اولویت."""
    candidates = get_asr_candidates()
    if not candidates:
        raise Exception("No ASR engine configured")
    # موتور انتخابی کاربر را اول امتحان کن
    if preferred_engine:
        ordered = [c for c in candidates if c.get("name") == preferred_engine]
        ordered += [c for c in candidates if c.get("name") != preferred_engine]
        candidates = ordered
    last_err = None
    for cfg in candidates:
        try:
            text = _transcribe_with(cfg, wav_bytes, lang_code=lang_code, prompt=prompt)
            if text:
                return text
        except Exception as e:
            last_err = e
            print(f"ASR engine '{cfg.get('name')}' failed: {e}")
    raise Exception(f"All ASR engines failed: {last_err}")


def recognize_google(raw_data, lang="fa"):
    """تشخیص گفتار با Google Speech رایگان."""
    r = sr.Recognizer()
    audio = sr.AudioData(raw_data, RATE, 2)
    g_lang = "fa-IR" if lang in ("fa", "auto", "translate_fa_en") else "en-US"
    try:
        return r.recognize_google(audio, language=g_lang)
    except sr.UnknownValueError:
        print("[Google Speech] Audio not understood / silence")
        return ""
    except Exception as e:
        print(f"[Google Speech] Error: {e}")
        return ""
