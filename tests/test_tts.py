"""تست‌های core/tts.py — تشخیص زبان، انتخاب صدا، پخش آنلاین فارسی و رفتار بی‌خطا.

هیچ صدایی واقعاً پخش نمی‌شود؛ pyttsx3/edge-tts با اشیاء جعلی جایگزین می‌شوند.
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


class _WorkingEngine(_FakeEngine):
    """موتور کامل‌تر که say/runAndWait را پیاده می‌کند (بدون پخش واقعی)."""

    def __init__(self, voices):
        super().__init__(voices)
        self.said = []
        self.waited = 0

    def say(self, text):
        self.said.append(text)

    def runAndWait(self):
        self.waited += 1

    def stop(self):
        pass


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


def test_has_persian_voice_true(monkeypatch):
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", True)
    monkeypatch.setattr(tts.pyttsx3, "init", lambda: _FakeEngine([_FakeVoice(FA_VOICE)]))
    assert tts.has_persian_voice() is True


def test_has_persian_voice_false(monkeypatch):
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", True)
    monkeypatch.setattr(tts.pyttsx3, "init", lambda: _FakeEngine([_FakeVoice(EN_DAVID)]))
    assert tts.has_persian_voice() is False


def test_has_persian_voice_no_pyttsx3(monkeypatch):
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", False)
    assert tts.has_persian_voice() is False


def test_chunk_text_short_is_single():
    assert tts._chunk_text("hello") == ["hello"]
    assert tts._chunk_text("") == []
    assert tts._chunk_text("   ") == []


def test_chunk_text_long_splits():
    text = " ".join("کلمه%d" % i for i in range(300))
    assert len(text) > tts._ONLINE_CHUNK_MAX
    chunks = tts._chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= tts._ONLINE_CHUNK_MAX for c in chunks)
    # محتوا از بین نرفته است — فاصلهٔ مرزی بین قطعات حذف می‌شود (بی‌ضرر برای گفتار)
    assert sorted(" ".join(chunks).split()) == sorted(text.split())


def test_speak_empty_does_nothing(monkeypatch):
    started = []

    class _FakeThread:
        def __init__(self, *a, **k):
            pass

        def start(self):
            started.append(1)

    monkeypatch.setattr(tts.threading, "Thread", _FakeThread)
    done = []
    tts.speak("", on_done=done.append)
    tts.speak("   ", on_done=done.append)
    assert started == []  # هیچ thread پخش صدایی ساخته نشد
    assert done and done[0]["reason"] == "empty"


def test_speak_no_pyttsx3_quiet(monkeypatch):
    # اگر pyttsx3 نباشد، نباید خطا بدهد
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", False)
    monkeypatch.setattr(tts, "_HAS_EDGE", False)
    done = []
    tts.speak("hello", wait=True, on_done=done.append)
    assert done and done[0]["source"] == "none"


def test_speak_worker_swallows_errors(monkeypatch):
    # اگر engine.init خطا بدهد، worker نباید خطا بالا بیندازد
    def boom(*a, **k):
        raise RuntimeError("no sapi")

    monkeypatch.setattr(tts, "_HAS_PYTTSX3", True)
    monkeypatch.setattr(tts.pyttsx3, "init", boom)
    tts.speak("hello", wait=True)  # نباید exception بدهد


def test_speak_persian_online_when_no_local_voice(monkeypatch):
    """فارسی بدون صدای محلی → صدای آنلاین edge-tts."""
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", False)
    monkeypatch.setattr(tts, "_HAS_EDGE", True)
    online_calls = []
    monkeypatch.setattr(tts, "_speak_online",
                        lambda text: online_calls.append(text) or True)
    done = []
    tts.speak("سلام دنیا", wait=True, on_done=done.append)
    assert online_calls == ["سلام دنیا"]
    assert done and done[0]["source"] == "online"
    assert done[0]["lang"] == "fa"


def test_speak_persian_uses_local_voice_when_available(monkeypatch):
    """اگر صدای فارسی محلی نصب باشد، آنلاین صدا زده نمی‌شود."""
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", True)
    monkeypatch.setattr(tts, "_HAS_EDGE", True)
    engine = _WorkingEngine([_FakeVoice(FA_VOICE)])
    monkeypatch.setattr(tts.pyttsx3, "init", lambda: engine)
    online_calls = []
    monkeypatch.setattr(tts, "_speak_online",
                        lambda text: online_calls.append(text) or True)
    done = []
    tts.speak("سلام دنیا", wait=True, on_done=done.append)
    assert engine.said == ["سلام دنیا"]
    assert engine.set_voice == FA_VOICE
    assert online_calls == []
    assert done and done[0]["source"] == "local"
    assert done[0]["lang"] == "fa"


def test_speak_english_uses_local_en(monkeypatch):
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", True)
    engine = _WorkingEngine([_FakeVoice(EN_DAVID)])
    monkeypatch.setattr(tts.pyttsx3, "init", lambda: engine)
    done = []
    tts.speak("Hello world", wait=True, on_done=done.append)
    assert engine.said == ["Hello world"]
    assert engine.set_voice == EN_DAVID
    assert done and done[0]["source"] == "local"
    assert done[0]["lang"] == "en"


def test_speak_online_failure_reports_none(monkeypatch):
    monkeypatch.setattr(tts, "_HAS_PYTTSX3", False)
    monkeypatch.setattr(tts, "_HAS_EDGE", True)
    monkeypatch.setattr(tts, "_speak_online", lambda text: False)
    done = []
    tts.speak("سلام", wait=True, on_done=done.append)
    assert done and done[0]["source"] == "none"
    assert done[0]["reason"] == "online_failed"


def test_speak_online_synthesizes_and_plays(monkeypatch):
    """_speak_online: ساخت MP3 با edge-tts و پخش با MCI."""
    monkeypatch.setattr(tts, "_HAS_EDGE", True)
    saved = []

    class _FakeComm:
        def __init__(self, text, voice=None):
            self.text = text
            self.voice = voice

        async def save(self, path):
            saved.append((self.text, self.voice, path))
            with open(path, "wb") as f:
                f.write(b"MP3DATA")

    monkeypatch.setattr(tts.edge_tts, "Communicate", _FakeComm)
    monkeypatch.setattr(tts, "_play_mp3", lambda p: True)
    assert tts._speak_online("سلام دنیا") is True
    assert saved and saved[0][0] == "سلام دنیا"
    assert saved[0][1] in tts.PERSIAN_VOICES


def test_speak_online_chunks_long_text(monkeypatch):
    monkeypatch.setattr(tts, "_HAS_EDGE", True)
    saved = []

    class _FakeComm:
        def __init__(self, text, voice=None):
            self.text = text
            self.voice = voice

        async def save(self, path):
            saved.append(self.text)
            with open(path, "wb") as f:
                f.write(b"MP3DATA")

    monkeypatch.setattr(tts.edge_tts, "Communicate", _FakeComm)
    monkeypatch.setattr(tts, "_play_mp3", lambda p: True)
    long_text = " ".join("کلمه%d" % i for i in range(300))
    assert tts._speak_online(long_text) is True
    assert len(saved) > 1
    assert all(len(c) <= tts._ONLINE_CHUNK_MAX for c in saved)


def test_speak_online_play_failure_returns_false(monkeypatch):
    monkeypatch.setattr(tts, "_HAS_EDGE", True)

    class _FakeComm:
        def __init__(self, text, voice=None):
            pass

        async def save(self, path):
            with open(path, "wb") as f:
                f.write(b"MP3DATA")

    monkeypatch.setattr(tts.edge_tts, "Communicate", _FakeComm)
    monkeypatch.setattr(tts, "_play_mp3", lambda p: False)
    assert tts._speak_online("سلام") is False
