"""Tests for VAD (voice-activity detection) auto-stop recording logic."""
import time

import pytest


# ── standalone VAD tracker (mirrors record_worker logic) ──────

class _VADTracker:
    """Minimal state machine that mirrors the VAD logic inside record_worker."""

    def __init__(self, threshold=0.02, silence_timeout=1.5):
        self.threshold = threshold
        self.silence_timeout = silence_timeout
        self.speech_started = False
        self.silence_start = None
        self.should_stop = False

    def feed(self, level: float, now: float | None = None):
        """Process one audio chunk level.  Returns True when auto-stop triggers."""
        now = now or time.time()
        if level >= self.threshold:
            self.speech_started = True
            self.silence_start = None
        else:
            if self.speech_started:
                if self.silence_start is None:
                    self.silence_start = now
                elif (now - self.silence_start) >= self.silence_timeout:
                    self.should_stop = True
                    return True
        return False


# ── tests ─────────────────────────────────────────────────────

class TestVADTracker:
    def test_no_stop_without_speech(self):
        """Before any speech, long silence should NOT trigger stop."""
        t = _VADTracker(threshold=0.02, silence_timeout=1.0)
        for i in range(100):
            assert t.feed(0.0, now=float(i)) is False
        assert t.should_stop is False

    def test_stop_after_speech_and_silence(self):
        """Speech then silence exceeding timeout should trigger stop."""
        t = _VADTracker(threshold=0.02, silence_timeout=1.5)
        t.feed(0.5, now=0.0)   # speech
        t.feed(0.6, now=0.1)   # speech
        assert t.speech_started is True
        t.feed(0.0, now=0.2)   # silence begins
        t.feed(0.0, now=1.0)   # still silent
        assert t.should_stop is False
        assert t.feed(0.0, now=1.71) is True  # exceeds 1.5s
        assert t.should_stop is True

    def test_silence_resets_when_speech_resumes(self):
        """If speech resumes before timeout, silence timer resets."""
        t = _VADTracker(threshold=0.02, silence_timeout=1.0)
        t.feed(0.5, now=0.0)   # speech
        t.feed(0.0, now=0.2)   # silence starts
        t.feed(0.0, now=0.8)   # still silent (0.6s)
        t.feed(0.3, now=0.9)   # speech resumes → timer resets
        assert t.silence_start is None
        t.feed(0.0, now=1.5)   # new silence
        assert t.should_stop is False
        assert t.feed(0.0, now=2.5) is True  # 1.0s from silence_start=1.5
        assert t.should_stop is True

    def test_threshold_boundary(self):
        """Level exactly at threshold counts as speech."""
        t = _VADTracker(threshold=0.02, silence_timeout=1.0)
        t.feed(0.02, now=0.0)
        assert t.speech_started is True
        assert t.silence_start is None
        # now drop to just below
        t.feed(0.019, now=0.1)
        assert t.silence_start is not None

    def test_zero_level_immediately_after_speech(self):
        """Zero level right after speech starts silence timer."""
        t = _VADTracker(threshold=0.02, silence_timeout=1.0)
        t.feed(0.1, now=0.0)
        t.feed(0.0, now=0.05)
        assert t.silence_start == 0.05
        assert t.feed(0.0, now=1.06) is True

    def test_long_speech_then_short_silence_no_stop(self):
        """Long speech followed by silence shorter than timeout should not stop."""
        t = _VADTracker(threshold=0.02, silence_timeout=2.0)
        for i in range(50):
            t.feed(0.5, now=float(i) * 0.02)  # 1 second of speech
        t.feed(0.0, now=1.0)
        t.feed(0.0, now=1.5)
        assert t.should_stop is False

    def test_exact_timeout_triggers_stop(self):
        """Level exactly at silence_timeout triggers stop."""
        t = _VADTracker(threshold=0.02, silence_timeout=1.0)
        t.feed(0.5, now=0.0)
        t.feed(0.0, now=0.5)  # silence starts at 0.5
        assert t.feed(0.0, now=1.5) is True  # exactly 1.0s later


class TestVADSettings:
    def test_default_values(self):
        """VAD defaults are reasonable."""
        t = _VADTracker()
        assert t.threshold == 0.02
        assert t.silence_timeout == 1.5
        assert t.speech_started is False
        assert t.should_stop is False

    def test_custom_settings(self):
        """Custom threshold and timeout are respected."""
        t = _VADTracker(threshold=0.1, silence_timeout=0.5)
        t.feed(0.09, now=0.0)   # below custom threshold → silence
        assert t.speech_started is False
        t.feed(0.1, now=0.0)    # at custom threshold → speech
        assert t.speech_started is True
        t.feed(0.0, now=0.6)
        assert t.feed(0.0, now=1.11) is True  # 0.51s from silence_start=0.6 > 0.5s timeout
