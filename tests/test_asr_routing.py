"""تست‌های مسیریابی زبان Google Speech (engine/asr.py).

بررسی اینکه هر حالت برنامه به کد زبان صحیح Google نگاشت می‌شود —
به‌ویژه حالت prompt_engineer که گفتار فارسی را به پرامپت تبدیل می‌کند.
"""
from engine.asr import _google_lang


def test_persian_states_map_to_fa_ir():
    for lang in ("fa", "auto", "translate_fa_en", "prompt_engineer"):
        assert _google_lang(lang) == "fa-IR", lang


def test_english_states_map_to_en_us():
    for lang in ("en", "translate_en_fa"):
        assert _google_lang(lang) == "en-US", lang


def test_prompt_engineer_is_persian_fix():
    # باگ v2.1: prompt_engineer (گفتار فارسی) به en-US می‌رفت و شکست می‌خورد
    assert _google_lang("prompt_engineer") == "fa-IR"


def test_unknown_state_defaults_to_english():
    assert _google_lang("anything-else") == "en-US"
