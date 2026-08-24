"""تست‌های core/stats.py — ذخیره و بازیابی آمار تایپ صوتی.

از یک فایل stats.json موقت استفاده می‌کند تا فایل اصلی خراب نشود.
"""
import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def _use_temp_stats(tmp_path, monkeypatch):
    """هدایت فایل آمار به یک مسیر موقت در هر تست."""
    from core import stats as _stats
    tmp_file = str(tmp_path / "stats.json")
    monkeypatch.setattr(_stats, "_stats_path", lambda: tmp_file)
    # مسیر app_base_dir را هم هدایت می‌کنیم چون stats از آن استفاده می‌کند
    # ولی ما مستقیماً _stats_path را monkeypatch کرده‌ایم → کافی است
    _stats.save(_stats._DEFAULT)
    yield tmp_file
    # پاک‌سازی بعد از تست
    try:
        os.remove(tmp_file)
    except OSError:
        pass


class TestStatsLoadSave:
    def test_load_empty_returns_default(self, _use_temp_stats):
        from core import stats as _stats
        os.remove(_use_temp_stats)  # فایل وجود ندارد
        data = _stats.load()
        assert data["total_words"] == 0
        assert data["total_recordings"] == 0
        assert data["engine_usage"] == {}

    def test_save_and_load_roundtrip(self, _use_temp_stats):
        from core import stats as _stats
        data = {"total_words": 100, "total_recordings": 5,
                "total_recording_secs": 30.0, "engine_usage": {"google": 3}}
        _stats.save(data)
        loaded = _stats.load()
        assert loaded["total_words"] == 100
        assert loaded["engine_usage"] == {"google": 3}

    def test_load_missing_key_uses_default(self, _use_temp_stats):
        from core import stats as _stats
        # ذخیره فقط با کلیدهای قدیمی (بدون total_recordings)
        _stats.save({"total_words": 42})
        loaded = _stats.load()
        assert loaded["total_words"] == 42
        assert loaded["total_recordings"] == 0  # از default پر شده
        assert loaded["engine_usage"] == {}

    def test_load_corrupt_file_returns_default(self, _use_temp_stats):
        from core import stats as _stats
        with open(_use_temp_stats, "w") as f:
            f.write("not json {{{")
        data = _stats.load()
        assert data["total_words"] == 0


class TestRecordTyping:
    def test_record_typing_accumulates_words(self, _use_temp_stats):
        from core import stats as _stats
        _stats.record_typing("سلام دنیا", engine="google", duration_sec=1.5)
        _stats.record_typing("hello world", engine="local", duration_sec=2.0)
        data = _stats.get_stats()
        assert data["total_words"] == 4  # 2 + 2
        assert data["total_recordings"] == 2
        assert abs(data["total_recording_secs"] - 3.5) < 0.01

    def test_record_typing_tracks_engine_usage(self, _use_temp_stats):
        from core import stats as _stats
        _stats.record_typing("text1", engine="google")
        _stats.record_typing("text2", engine="google")
        _stats.record_typing("text3", engine="local")
        data = _stats.get_stats()
        assert data["engine_usage"] == {"google": 2, "local": 1}

    def test_record_typing_empty_text(self, _use_temp_stats):
        from core import stats as _stats
        _stats.record_typing("", engine="google")
        data = _stats.get_stats()
        assert data["total_words"] == 0
        assert data["total_recordings"] == 1

    def test_record_typing_negative_duration_ignored(self, _use_temp_stats):
        from core import stats as _stats
        _stats.record_typing("test", engine="google", duration_sec=-5.0)
        data = _stats.get_stats()
        assert data["total_recording_secs"] == 0.0


class TestRecordEngineUse:
    def test_record_engine_use(self, _use_temp_stats):
        from core import stats as _stats
        _stats.record_engine_use("Groq Cloud")
        _stats.record_engine_use("Groq Cloud")
        _stats.record_engine_use("local")
        data = _stats.get_stats()
        assert data["engine_usage"] == {"Groq Cloud": 2, "local": 1}


class TestReset:
    def test_reset_clears_all(self, _use_temp_stats):
        from core import stats as _stats
        _stats.record_typing("some text", engine="google", duration_sec=5.0)
        _stats.reset()
        data = _stats.get_stats()
        assert data["total_words"] == 0
        assert data["total_recordings"] == 0
        assert data["total_recording_secs"] == 0.0
        assert data["engine_usage"] == {}
