"""آمار استفاده — ذخیره و بازیابی تعداد کلمات، استفاده از هر موتور و زمان ضبط.

داده‌ها در فایل `stats.json` در کنار برنامه ذخیره می‌شوند و بین نشست‌ها پایدار
هستند. همهٔ متدها در برابر خطا ایمن‌اند (هیچ‌وقت exception بالا نمی‌اندازند).
"""
import datetime
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
    # تاریخچه روزانه برای نمودار زمانی:
    # {"YYYY-MM-DD": {"words": 10, "recordings": 2, "secs": 3.5}, ...}
    "daily_history": {},
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
    """ثبت یک رویداد تایپ صوتی: افزودن کلمات، شمارنده موتور، زمان ضبط و تاریخچه روزانه."""
    data = load()
    words = len(str(text).split()) if text else 0
    data["total_words"] += words
    data["total_recordings"] += 1
    data["total_recording_secs"] += max(0.0, duration_sec)
    eng_usage = data.get("engine_usage", {})
    eng_usage[engine] = eng_usage.get(engine, 0) + 1
    data["engine_usage"] = eng_usage

    # ── تاریخچه روزانه ──
    today = datetime.date.today().isoformat()
    history = data.setdefault("daily_history", {})
    day = dict(history.get(today, {"words": 0, "recordings": 0, "secs": 0.0}))
    day["words"] += words
    day["recordings"] += 1
    day["secs"] += max(0.0, duration_sec)
    history[today] = day

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


def get_daily_history(days=14):
    """تاریخچهٔ روزانه برای نمودار زمانی.

    برمی‌گرداند لیست آخرین `days` روز به ترتیب قدیمی → جدید:
    [(date_str, words, recordings, secs), ...]
    """
    data = load()
    history = data.get("daily_history", {})
    today = datetime.date.today()
    result = []
    for i in range(days - 1, -1, -1):
        d = (today - datetime.timedelta(days=i)).isoformat()
        entry = history.get(d, {})
        result.append((d, entry.get("words", 0), entry.get("recordings", 0),
                       entry.get("secs", 0.0)))
    return result


def get_weekly_history(weeks=8):
    """تاریخچهٔ هفتگی (شروع هفته = دوشنبه).

    برمی‌گرداند لیست آخرین `weeks` هفته به ترتیب قدیمی → جدید:
    [(week_start_date_str, words, recordings, secs), ...]
    """
    data = load()
    history = data.get("daily_history", {})

    # جمع روزهای هر هفته
    buckets = {}
    for day_str, entry in history.items():
        try:
            d = datetime.date.fromisoformat(day_str)
        except (TypeError, ValueError):
            continue
        week_start = d - datetime.timedelta(days=d.weekday())
        bucket = buckets.setdefault(week_start.isoformat(),
                                    {"words": 0, "recordings": 0, "secs": 0.0})
        bucket["words"] += entry.get("words", 0)
        bucket["recordings"] += entry.get("recordings", 0)
        bucket["secs"] += entry.get("secs", 0.0)

    today = datetime.date.today()
    this_week = today - datetime.timedelta(days=today.weekday())
    result = []
    for i in range(weeks - 1, -1, -1):
        ws = (this_week - datetime.timedelta(weeks=i)).isoformat()
        b = buckets.get(ws, {"words": 0, "recordings": 0, "secs": 0.0})
        result.append((ws, b["words"], b["recordings"], b["secs"]))
    return result


def reset():
    """پاک‌سازی کامل آمار."""
    save(dict(_DEFAULT))
