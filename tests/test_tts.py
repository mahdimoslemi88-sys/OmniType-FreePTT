"""تست‌های core/tts.py — تشخیص زبان، انتخاب صدا و رفتار بی‌خطا.

هیچ صدایی واقعاً پخش نمی‌شود؛ pyttsx3 با یک engine جعلی جایگزین می‌شود.
"""
from core import tts


def test_is_persian():
    assert tts.is_persian("سلام دنیا") is True
    assert tts.is_persian("Hello world") is False
    assert tts.is_persian("میکس Hello") is True
    assert tts.is_persian("") is False
    assert tts.is_persian(None) is False


class _FakeVoice:
    def __init__(self, vid, langs=()):
        self.id = vid
        self.languages = list(langs)


class _FakeEngine:
    def __init__(self, voices):
        self._voices = voices
        self.set_voice = None

    def getProperty(self, name):
        return self._voices

    def setProperty(self, name, value):
        self.set_voice = value


EN_DAVID = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0"
FA_VOICE = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_FA-IR_ZIRA_11.0"


def test_pick_voice_english_prefers_en():
    engine = _FakeEngine([_FakeVoice(EN_DAVID), _FakeVoice(FA_VOICE)])
    # متن فارسی → صدای فارسی اگر باشد
    assert tts._pick_voice(engine, "سلام") == FA_VOICE
    # متن انگلیسی → صدای en
    assert tts._pick_voice(engine, "Hello") == EN_DAVID


def test_pick_voice_fallback_default():
    # فقط صدای فارسی موجود است؛ متن انگلیسی → پیش‌فرض (None)
    engine = _FakeEngine([_FakeVoice(FA_VOICE)])
    assert tts._pick_voice(engine, "Hello") is None
    # هیچ صدایی → None
    assert tts._pick_voice(_FakeEngine([]), "Hello") is None


def test_pick_voice_uses_languages_attribute():
    engine = _FakeEngine([_FakeVoice("some-id", ["en-US"]),
                          _FakeVoice("other-id", ["fa-IR"])])
    assert tts._pick_voice(engine, "درود") == "other-id"
    assert tts._pick_voice(engine, "hi there") == "some-id"


def test_speak_empty_does_nothing(monkeypatch):
    started = []

    class _FakeThread:
        def __init__(self, *a, **k):
            pass

        def start(self):
            started.append(1)

    monkeypatch.setattr(tts.threading, "Thread", _FakeThread)
    tts.speak("")
    tts.speak("   ")
    assert started == []  # هیچ thread پخش صدایی ساخته نشد


def test_speak_no_pyttsx3_quiet(monkeypatch):
    # اگر pyttsx3 نباشد، نباید خطا بدهد
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", False)
    tts.speak("hello", wait=True)  # باید بی‌صدا برگردد


def test_speak_worker_swallows_errors(monkeypatch):
    # اگر engine.init خطا بدهد، worker نباید خطا بالا بیندازد
    def boom(*a, **k):
        raise RuntimeError("no sapi")

    monkeypatch.setattr(tts, "_HAS_PYTTSX3", True)
    monkeypatch.setattr(tts.pyttsx3, "init", boom)
    tts.speak("hello", wait=True)  # نباید exception بدهد
