"""اکسپورت/ایمپورت تنظیمات، موتورها و واژه‌نامه به‌صورت JSON.

فرمت فایل:
  {
    "version": 1,
    "exported_at": "2026-08-24T...",
    "settings": {"AUTO_PAUSE_MEDIA": "true", ...},
    "engines": [{"name": "Groq", ...}, ...],
    "dictionary": {"prompts": [...], "replacements": {...}}
  }
"""
import json
import os
from datetime import datetime, timezone


SCHEMA_VERSION = 1


def gather_export_data():
    """جمع‌آوری همهٔ اطلاعات قابل‌اکسپورت از حافظهٔ فعلی."""
    from core.config import ENV, ENGINES
    from core.dictionary import CUSTOM_DICT

    settings = {k: v for k, v in ENV.items() if k != "ENGINES"}
    return {
        "version": SCHEMA_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "settings": settings,
        "engines": ENGINES,
        "dictionary": {
            "prompts": list(CUSTOM_DICT.prompts),
            "replacements": dict(CUSTOM_DICT.replacements),
        },
    }


def apply_import_data(data):
    """اعمال داده‌های واردشده روی تنظیمات، موتورها و واژه‌نامه.

    خروجی: True در صورت موفقیت، False در صورت فرمت نامعتبر.
    برای اعمال کامل، بهتر است پس از اجرا برنامه ری‌استارت شود.
    """
    if not isinstance(data, dict) or data.get("version") != SCHEMA_VERSION:
        return False

    from core import config
    from core.dictionary import CUSTOM_DICT

    # ۱. تنظیمات → .env و حافظه
    settings = data.get("settings")
    if settings and isinstance(settings, dict):
        try:
            config.save_env_dict(settings)
        except Exception:
            pass

    # ۲. موتورها → .env و حافظه
    engines = data.get("engines")
    if engines and isinstance(engines, list):
        try:
            config.save_engines(engines)
        except Exception:
            pass

    # ۳. واژه‌نامه → فایل و حافظه
    dictionary = data.get("dictionary")
    if dictionary and isinstance(dictionary, dict):
        CUSTOM_DICT.prompts = list(dictionary.get("prompts", []))
        CUSTOM_DICT.replacements = dict(dictionary.get("replacements", {}))
        try:
            CUSTOM_DICT.save()
        except Exception:
            pass

    return True
