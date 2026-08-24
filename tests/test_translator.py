"""تست‌های موتور ترجمه engine/translator.py.

همه تست‌ها بدون تماس شبکه‌ای هستند: متدهای شبکه‌ای کلاس با mock
جایگزین می‌شوند و زنجیرهٔ fallback (گوگل → LLM → Gemini → گوگل رایگان
→ برگشت متن اصلی) به‌صورت قطعی بررسی می‌شود.
"""
from engine import translator
from engine.translator import LLMTranslatorEngine


def test_empty_text_returns_empty():
    assert LLMTranslatorEngine.translate("") == ""
    assert LLMTranslatorEngine.translate("   ") == ""


def test_strips_and_returns_empty(monkeypatch):
    # مدل‌های شبکه نباید با ورودی خالی صدا زده شوند
    called = []

    def boom(*a, **k):
        called.append(a)
        raise AssertionError("network method should not be called")

    monkeypatch.setattr(translator, "HAS_DEEP_TRANSLATOR", True)
    monkeypatch.setattr(translator, "get_llm_candidates", lambda: [])
    monkeypatch.setattr(translator, "GEMINI_API_KEY", "")
    monkeypatch.setattr(LLMTranslatorEngine, "_translate_deep_translator", boom)

    assert LLMTranslatorEngine.translate("   ") == ""
    assert called == []


def test_falls_back_to_original_when_everything_fails(monkeypatch):
    text = "hello world"

    def fail(*a, **k):
        raise Exception("engine down")

    monkeypatch.setattr(translator, "HAS_DEEP_TRANSLATOR", False)
    monkeypatch.setattr(translator, "get_llm_candidates", lambda: [])
    monkeypatch.setattr(translator, "GEMINI_API_KEY", "")
    monkeypatch.setattr(LLMTranslatorEngine, "_translate_google_free", fail)

    assert LLMTranslatorEngine.translate(text) == text


def test_google_free_used_when_llm_missing(monkeypatch):
    # deep-translator خراب؛ بدون LLM و بدون Gemini → موتور چهارم
    def fail(*a, **k):
        raise Exception("deep translator down")

    monkeypatch.setattr(translator, "HAS_DEEP_TRANSLATOR", True)
    monkeypatch.setattr(LLMTranslatorEngine, "_translate_deep_translator", fail)
    monkeypatch.setattr(translator, "get_llm_candidates", lambda: [])
    monkeypatch.setattr(translator, "GEMINI_API_KEY", "")
    monkeypatch.setattr(
        LLMTranslatorEngine, "_translate_google_free",
        lambda text, mode: "Google-Free-Result",
    )
    assert LLMTranslatorEngine.translate("salam") == "Google-Free-Result"


def test_llm_tried_in_priority_before_gemini_free(monkeypatch):
    # بدون گوگل (deep-translator خاموش) → موتور LLM باید نتیجه بدهد
    llm_cfg = [
        {"base_url": "https://api.groq.com/openai/v1",
         "api_key": "k", "model": "gpt-oss-20b"},
    ]

    def fake_llm(text, mode, style, cfg):
        assert cfg == llm_cfg[0]
        return "LLM-Result"

    monkeypatch.setattr(translator, "HAS_DEEP_TRANSLATOR", False)
    monkeypatch.setattr(translator, "get_llm_candidates", lambda: llm_cfg)
    monkeypatch.setattr(LLMTranslatorEngine, "_translate_custom_openai", fake_llm)

    # گوگل رایگان نباید فراخوانی شود چون LLM جواب داده است
    def boom(*a, **k):
        raise AssertionError("should not reach google free")

    monkeypatch.setattr(LLMTranslatorEngine, "_translate_google_free", boom)

    assert LLMTranslatorEngine.translate("salam", mode="fa_to_en") == "LLM-Result"


def test_second_llm_tried_if_first_fails(monkeypatch):
    def fake_llm(text, mode, style, cfg):
        if cfg["model"] == "bad":
            raise Exception("bad model")
        return "Good-Result"

    llm_cfgs = [
        {"base_url": "u", "api_key": "k", "model": "bad"},
        {"base_url": "u", "api_key": "k", "model": "good"},
    ]
    seen = []

    def fake_llm_recording(text, mode, style, cfg):
        seen.append(cfg["model"])
        return fake_llm(text, mode, style, cfg)

    monkeypatch.setattr(translator, "HAS_DEEP_TRANSLATOR", False)
    monkeypatch.setattr(translator, "get_llm_candidates", lambda: llm_cfgs)
    monkeypatch.setattr(
        LLMTranslatorEngine, "_translate_custom_openai", fake_llm_recording,
    )

    assert LLMTranslatorEngine.translate("salam") == "Good-Result"
    assert seen == ["bad", "good"]  # مدل‌ها به ترتیب اولویت امتحان شدند


# ── تقسیم متن‌های طولانی در deep-translator (چانکینگ) ─────────────────


class _FakeGoogleTranslator:
    """جایگزین GoogleTranslator: ورودی/خروجی گیرنده و مقدارساز برای تست."""

    last_source = None
    last_target = None
    calls = []

    def __init__(self, source, target):
        _FakeGoogleTranslator.last_source = source
        _FakeGoogleTranslator.last_target = target
        _FakeGoogleTranslator.calls = []

    def translate(self, text):
        _FakeGoogleTranslator.calls.append(text)
        return text  # هم‌ارز، تا چانک‌ها قابل بازسازی باشند


def test_deep_translator_chunking_long_text(monkeypatch):
    monkeypatch.setattr(translator, "GoogleTranslator", _FakeGoogleTranslator)

    long_text = ("سطر اول متن طولانی برای تست چانک‌بندی. \n" * 600)  # >> 4500 کاراکتر

    result = LLMTranslatorEngine._translate_deep_translator(long_text, mode="fa_to_en")

    assert _FakeGoogleTranslator.last_source == "fa"
    assert _FakeGoogleTranslator.last_target == "en"
    # بیش از یک چانک تولید شده است
    assert len(_FakeGoogleTranslator.calls) > 1
    # بدون فاصله/نوبلاین (مرز برش) محتوا باید به متن اصلی برسد
    def nospace(s):
        return s.replace(" ", "").replace("\n", "")

    assert nospace(result) == nospace(long_text.strip())


def test_deep_translator_long_single_word_no_infinite_loop(monkeypatch):
    # کلمهٔ تکی بدون فاصله/نوبلاین > ۴۵۰۰ — حلقه نباید بی‌پایان شود
    monkeypatch.setattr(translator, "GoogleTranslator", _FakeGoogleTranslator)
    long_word = "س" * 9000
    LLMTranslatorEngine._translate_deep_translator(long_word, mode="fa_to_en")
    assert 1 < len(_FakeGoogleTranslator.calls) <= 3  # به چند چانک اما محدود


def test_deep_translator_empty_input(monkeypatch):
    monkeypatch.setattr(translator, "GoogleTranslator", _FakeGoogleTranslator)
    assert LLMTranslatorEngine._translate_deep_translator("", mode="fa_to_en") == ""


def test_deep_chunks_never_exceed_4500(monkeypatch):
    monkeypatch.setattr(translator, "GoogleTranslator", _FakeGoogleTranslator)
    # ۳۰۰۰ کلمهٔ ۱۰ حرفی → قطعاً >> ۴۵۰۰
    text = " ".join(["کلمه‌آزمایشی" * 3] * 1000)
    LLMTranslatorEngine._translate_deep_translator(text, mode="fa_to_en")
    chunks = _FakeGoogleTranslator.calls
    assert len(chunks) > 1
    for c in chunks[:-1]:
        assert len(c) <= 4500, f"چانک از حد ۴۵۰۰ رد شد: {len(c)}"


def test_deep_prefers_newline_breaks(monkeypatch):
    monkeypatch.setattr(translator, "GoogleTranslator", _FakeGoogleTranslator)
    # سه خط ~۱۸۰۰ کاراکتری که با نوبلاین جدا شده‌اند — برش باید سر نوبلاین باشد
    line = "س" * 1800
    text = "\n".join([line, line, line])  # ~5400 کاراکتر
    LLMTranslatorEngine._translate_deep_translator(text, mode="fa_to_en")
    chunks = _FakeGoogleTranslator.calls
    # برش در مرز نوبلاین → ۲ چانک تمیز (نه برش دلخواهِ وسط خط)
    assert len(chunks) == 2
    last = chunks[-1]
    assert last == line  # آخرین چانک دقیقاً یک خط کامل است


def test_falsy_deep_result_advances_to_fallback(monkeypatch):
    # اگر deep-translator بدون خطا نتیجهٔ خالی بدهد، باید به موتور بعد برود
    monkeypatch.setattr(translator, "HAS_DEEP_TRANSLATOR", True)
    monkeypatch.setattr(LLMTranslatorEngine, "_translate_deep_translator",
                        lambda text, mode: "")
    monkeypatch.setattr(translator, "get_llm_candidates", lambda: [])
    monkeypatch.setattr(translator, "GEMINI_API_KEY", "")
    monkeypatch.setattr(
        LLMTranslatorEngine, "_translate_google_free",
        lambda text, mode: "Google-Free-Result",
    )
    assert LLMTranslatorEngine.translate("salam") == "Google-Free-Result"


def test_deep_translator_small_text_single_chunk(monkeypatch):
    monkeypatch.setattr(translator, "GoogleTranslator", _FakeGoogleTranslator)
    LLMTranslatorEngine._translate_deep_translator("سلام دنیا", mode="en_to_fa")
    assert _FakeGoogleTranslator.last_source == "en"
    assert _FakeGoogleTranslator.last_target == "fa"
    assert len(_FakeGoogleTranslator.calls) == 1
