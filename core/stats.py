"""آمار استفاده — ذخیره و بازیابی تعداد کلمات، استفاده از هر موتور و زمان ضبط.

داده‌ها در فایل `stats.json` در کنار برنامه ذخیره می‌شوند و بین نشست‌ها پایدار
هستند. همهٔ متدها در برابر خطا ایمن‌اند (هیچ‌وقت exception بالا نمی‌اندازند).
"""
import json
import os
import time

from core.paths import app_base_dir

_STATS_FILE = "stats.json"

_DEFAULT = {
    "total_words": 0,
    "total_recordings": 0,
    "total_recording_secs": 0.0,
    "engine_usage": {},   # {"google": 5, "Groq Cloud (ASR)": 3, ...}
}


def _stats_path():
    return os.path.join(app_base_dir(), _STATS_FILE)


def load():
    """بارگذاری آمار از فایل JSON. در صورت خطا، مقادیر پیش‌فرض برمی‌گرداند."""
    path = _stats_path()
    if not os.path.exists(path):
        return dict(_DEFAULT)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # اطمینان از وجود همه کلیدها
        result = dict(_DEFAULT)
        result.update({k: data.get(k, v) for k, v in _DEFAULT.items()})
        return result
    except Exception:
        return dict(_DEFAULT)


def save(data):
    """ذخیرهٔ آمار در فایل JSON."""
    try:
        with open(_stats_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def record_typing(text, engine="unknown", duration_sec=0.0):
    """ثبت یک رویداد تایپ صوتی: افزودن کلمات، شمارنده موتور و زمان ضبط."""
    data = load()
    words = len(str(text).split()) if text else 0
    data["total_words"] += words
    data["total_recordings"] += 1
    data["total_recording_secs"] += max(0.0, duration_sec)
    eng_usage = data.get("engine_usage", {})
    eng_usage[engine] = eng_usage.get(engine, 0) + 1
    data["engine_usage"] = eng_usage
    save(data)


def record_engine_use(engine):
    """ثبت فقط شمارندهٔ استفاده از موتور (بدون کلمه/زمان)."""
    data = load()
    eng_usage = data.get("engine_usage", {})
    eng_usage[engine] = eng_usage.get(engine, 0) + 1
    data["engine_usage"] = eng_usage
    save(data)


def get_stats():
    """برگرداندن آمار فعلی به صورت dict."""
    return load()


def reset():
    """پاک‌سازی کامل آمار."""
    save(dict(_DEFAULT))
