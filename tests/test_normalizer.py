"""تست‌های core/normalizer.py — تبدیل تلفظ حروف انگلیسی و نرمال‌سازی فارسی.

تمرکز روی باگ v2.2: واژه‌های رایج فارسی که با تلفظ یک حرف هم‌نویسه‌اند
(بی، وی، او، ان، ام، ...) نباید به‌تنهایی به حرف انگلیسی خراب شوند.
"""
from core.normalizer import (
    PersianNormalizer,
    convert_persian_letters_to_english as conv,
)


# ── تبدیل تلفظ حروف انگلیسی ───────────────────────────────────────


def test_dictation_sequence_converts():
    assert conv("بی سی دی اف") == "B C D F"


def test_single_unambiguous_letter_converts():
    # «پی» واژهٔ رایج فارسی نیست؛ به‌تنهایی هم تبدیل می‌شود
    assert conv("من می خوام پی تایپ کنم") == "من می خوام P تایپ کنم"
    assert conv("کیو وای") == "Q Y"


def test_real_persian_homographs_preserved():
    # باگ v2.2: این‌ها واژه/ساختار فارسی واقعی‌اند و نباید خراب شوند
    cases = [
        "من بی صبرم",       # بی = بدون
        "وی گفت",           # وی = او
        "او ام من است",      # او = ضمیر
        "این ان است",        # ان = آن
        "سی عدد",           # سی = عدد ۳۰
        "دی رفتم",          # دی = دیروز
    ]
    for text in cases:
        assert conv(text) == text, f"خروجی برای {text!r} تغییر کرد: {conv(text)!r}"


def test_no_persian_text_untouched():
    assert conv("abc") == "abc"
    assert conv("") == ""


def test_punctuation_preserved_around_letter():
    # علائم داخل set پاک‌سازی حذف و سپس به حرف چسبانده می‌شوند
    assert conv("پی.") == "P."
    assert conv("پی،") == "P،"
    assert conv("پی!") == "P!"


# ── نرمال‌سازی فارسی ──────────────────────────────────────────────


def test_normalize_arabic_characters():
    assert PersianNormalizer.normalize_characters("كيوي") == "کیوی"
    assert PersianNormalizer.normalize_characters("ي") == "ی"
    assert PersianNormalizer.normalize_characters("ك") == "ک"


def test_fix_half_spaces():
    assert PersianNormalizer.fix_half_spaces("می روم") == "می\u200cروم"
    assert PersianNormalizer.fix_half_spaces("نمی خوام") == "نمی\u200cخوام"
    assert PersianNormalizer.fix_half_spaces("بچه ها") == "بچه\u200cها"


def test_remove_fillers():
    assert PersianNormalizer.remove_fillers("عه  امم  سلام") == "سلام"


def test_punctuation_spacing():
    assert PersianNormalizer.fix_punctuations("او گفت .") == "او گفت."


def test_persian_comma_is_handled():
    # باگ v2.2: کاما فارسی ، (U+060C) در کلاس علائم نبود و فاصله‌گذاری نمی‌شد
    assert PersianNormalizer.fix_punctuations("سلام ،دنیا") == "سلام، دنیا"
    assert PersianNormalizer.fix_punctuations("سلام،دنیا") == "سلام، دنیا"


def test_full_normalize():
    out = PersianNormalizer.normalize("سلام    خوبين ؟   عه  امم")
    assert out == "سلام خوبین؟"


def test_normalize_empty():
    assert PersianNormalizer.normalize("") == ""
    assert PersianNormalizer.normalize(None) == ""
