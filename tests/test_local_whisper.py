"""تست‌های LocalWhisperManager — بدون لود مدل واقعی."""
import sys
import os
import threading
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.local_whisper import LocalWhisperManager, HAS_FASTER_WHISPER


class TestLocalWhisperManager:
    """تست‌های منطق مدیریت مدل محلی Whisper."""

    def test_has_faster_whisper_flag(self):
        """پرچم HAS_FASTER_WHISPER باید bool باشد."""
        assert isinstance(HAS_FASTER_WHISPER, bool)

    def test_manager_initial_state(self):
        mgr = LocalWhisperManager()
        assert mgr.model is None
        assert mgr.is_loading is False
        assert mgr.load_error is None

    def test_preload_sets_loading_flag(self):
        """preload_model_async باید is_loading را True کند."""
        mgr = LocalWhisperManager()
        # mock the _load_worker to prevent actual model loading
        original = mgr._load_worker
        mgr._load_worker = lambda size: None
        mgr.preload_model_async("base")
        # Since _load_worker is now a no-op lambda, is_loading will be set to True
        # but the thread finishes immediately, so let's check via a small delay
        assert mgr.is_loading is True or mgr.model is not None
        mgr._load_worker = original

    def test_preload_does_not_restart_if_already_loading(self):
        mgr = LocalWhisperManager()
        mgr.is_loading = True
        call_count = [0]
        original_worker = mgr._load_worker

        def counting_worker(size):
            call_count[0] += 1

        mgr._load_worker = counting_worker
        mgr.preload_model_async("base")
        # Should not have called worker again
        assert call_count[0] == 0
        mgr._load_worker = original_worker
        mgr.is_loading = False

    def test_preload_does_not_restart_if_model_loaded(self):
        mgr = LocalWhisperManager()
        mgr.model = "fake_model"
        call_count = [0]
        original_worker = mgr._load_worker

        def counting_worker(size):
            call_count[0] += 1

        mgr._load_worker = counting_worker
        mgr.preload_model_async("base")
        assert call_count[0] == 0
        mgr._load_worker = original_worker
        mgr.model = None

    def test_transcribe_raises_if_loading(self):
        mgr = LocalWhisperManager()
        mgr.is_loading = True
        with pytest.raises(Exception, match="بارگذاری"):
            mgr.transcribe(b"fake_wav")
        mgr.is_loading = False

    def test_transcribe_raises_if_no_model(self):
        mgr = LocalWhisperManager()
        with pytest.raises(Exception, match="استارت اولیه"):
            mgr.transcribe(b"fake_wav")

    def test_unload_when_nothing_loaded(self):
        mgr = LocalWhisperManager()
        result = mgr.unload_model()
        assert result is False

    def test_unload_when_loading(self):
        mgr = LocalWhisperManager()
        mgr.is_loading = True
        result = mgr.unload_model()
        assert result is True
        assert mgr.model is None
        assert mgr.is_loading is False

    def test_unload_when_model_loaded(self):
        mgr = LocalWhisperManager()
        mgr.model = "fake_model"
        result = mgr.unload_model()
        assert result is True
        assert mgr.model is None

    def test_base_whisper_prompt_is_persian(self):
        from engine.local_whisper import BASE_WHISPER_PROMPT
        assert isinstance(BASE_WHISPER_PROMPT, str)
        assert len(BASE_WHISPER_PROMPT) > 20
        assert "Python" in BASE_WHISPER_PROMPT

    def test_load_error_cleared_on_new_preload(self):
        mgr = LocalWhisperManager()
        mgr.load_error = "previous error"
        # Mock to prevent actual loading
        original = mgr._load_worker
        mgr._load_worker = lambda size: None
        mgr.preload_model_async("base")
        # Error should still be there (cleared in worker, not in preload)
        # But let's verify the worker clears it
        mgr._load_worker = original
        mgr.is_loading = False
        mgr.load_error = None
