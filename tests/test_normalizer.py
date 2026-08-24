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


def test_persian_question_and_semicolon_punctuation():
    assert conv("پی؟") == "P؟"
    assert conv("پی؛") == "P؛"
    assert conv("پی:") == "P:"


def test_dictation_mode_bypasses_homograph_stoplist():
    """وقتی ≥۳ نام حرف پشت‌سرهم باشد، حتی واژه‌های هم‌نویس هم تبدیل می‌شوند."""
    assert conv("پی بی سی دی اف") == "P B C D F"
    assert conv("ای بی سی") == "I B C"
    assert conv("پی و بی و سی") == "P و B و C"


def test_two_homograph_letters_stay_persian():
    """فقط ۲ نام حرف هم‌نویس → زیر آستانهٔ تشخیص → فارسی می‌مانند."""
    assert conv("بی سی") == "بی سی"
    assert conv("سی دی") == "سی دی"
    assert conv("پی و بی") == "P و بی"


def test_letter_plus_homograph_mixed():
    # «ان» هم‌نویسِ آن است و حفظ می‌شود؛ «پی» تبدیل می‌شود
    assert conv("ان پی") == "ان P"


def test_zwnj_combo_sequence_converts():
    """رشتهٔ چسبیده با نیم‌فاصله: بی‌سی‌دی‌اف → BCDF"""
    assert conv("بی\u200cسی\u200cدی\u200cاف") == "BCDF"
    assert conv("بی\u200cسی") == "BC"


def test_hyphen_combo_sequence_converts():
    """باگ v2.3: خط تیره در regex ترکیبی نبود → بی-سی-دی تبدیل نمی‌شد."""
    assert conv("بی-سی-دی") == "BCD"
    assert conv("دی-وی-دی") == "DVD"


def test_real_words_containing_letter_names_untouched():
    # کلمات واقعی فارسی که بخشی از تلفظ حرف را دارند نباید خراب شوند
    assert conv("پیام") == "پیام"
    assert conv("می پیچم") == "می پیچم"
    assert conv("می\u200cپیچم") == "می\u200cپیچم"
    assert conv("آینده") == "آینده"


def test_letter_dictation_with_digits():
    assert conv("پی ۳") == "P ۳"


def test_mixed_latin_and_persian():
    assert conv("A B پی") == "A B P"


def test_letter_sequence_with_punctuation_between():
    assert conv("پی. بی. سی.") == "P. B. C."


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


def test_punctuation_after_ascii_comma():
    # کاما انگلیسی بعد از حرف لاتین هم باید فاصله بگیرد
    assert PersianNormalizer.fix_punctuations("Hello,world") == "Hello, world"
    assert PersianNormalizer.fix_punctuations("سلام,دنیا") == "سلام, دنیا"


def test_double_space_after_punctuation_collapsed():
    assert PersianNormalizer.fix_punctuations("سلام،  دنیا") == "سلام، دنیا"


def test_question_mark_spacing():
    assert PersianNormalizer.fix_punctuations("چرا ؟") == "چرا؟"
    assert PersianNormalizer.fix_punctuations("چرا؟چرا") == "چرا؟ چرا"


def test_emails_and_urls_not_broken():
    """باگ v2.3: نقطهٔ داخل ایمیل/URL فاصله می‌گرفت: gmail.com → gmail. com"""
    assert PersianNormalizer.fix_punctuations("amir@gmail.com") == "amir@gmail.com"
    assert PersianNormalizer.fix_punctuations("مراجعه کنید به example.org") == "مراجعه کنید به example.org"


def test_decimal_and_version_numbers_not_broken():
    assert PersianNormalizer.fix_punctuations("3.14") == "3.14"
    assert PersianNormalizer.fix_punctuations("v2.1") == "v2.1"


def test_persian_period_still_spaced():
    # نقطهٔ فارسی بین دو واژهٔ فارسی همچنان فاصله می‌گیرد
    assert PersianNormalizer.fix_punctuations("سلام.دنیا") == "سلام. دنیا"
    assert PersianNormalizer.fix_punctuations("سلام .دنیا") == "سلام. دنیا"


def test_half_space_with_ه_suffix():
    # «ه» + شناسه → نیم‌فاصله: خنده ام → خنده‌ام
    assert PersianNormalizer.fix_half_spaces("خنده ام") == "خنده\u200cام"
    assert PersianNormalizer.fix_half_spaces("کتاب های من") == "کتاب\u200cهای من"


def test_existing_zwnj_preserved():
    assert PersianNormalizer.fix_half_spaces("می\u200cروم") == "می\u200cروم"
    assert PersianNormalizer.fix_half_spaces("فاصله\u200cدار") == "فاصله\u200cدار"


def test_arabic_characters_all_mapped():
    out = PersianNormalizer.normalize_characters("ي ك إ أ ة ئ")
    assert out == "ی ک ا ا ه ئ"


def test_remove_fillers_repeats():
    assert PersianNormalizer.remove_fillers("امممم") == ""
    assert PersianNormalizer.remove_fillers("امم سلام عه") == "سلام"


def test_normalize_persian_period_sentence():
    assert PersianNormalizer.normalize("سلام.دنیا") == "سلام. دنیا"
    assert PersianNormalizer.normalize("ایمیل من amir@gmail.com است") == "ایمیل من amir@gmail.com است"
