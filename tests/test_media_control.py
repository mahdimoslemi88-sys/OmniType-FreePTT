"""تست‌های core/media_control.py — منطق توقف/ادامهٔ رسانه.

فرستادن واقعی کلید Media Play/Pause با monkeypatch مهار می‌شود تا تست
حالت صفحه‌کلید/رسانهٔ واقعی را تغییر ندهد.
"""
from core import media_control as mc
from core.media_control import MediaController


def test_media_play_pause_vk():
    assert mc.VK_MEDIA_PLAY_PAUSE == 0xB3


def test_disabled_controller_sends_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(mc, "send_media_play_pause", lambda: calls.append(1))
    c = MediaController(enabled=False)
    c.pause()
    c.resume()
    assert calls == []


def test_enabled_pause_then_resume_toggles_twice(monkeypatch):
    calls = []
    monkeypatch.setattr(mc, "send_media_play_pause", lambda: calls.append(1))
    c = MediaController(enabled=True)
    c.pause()
    c.resume()
    assert len(calls) == 2


def test_resume_without_pause_sends_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(mc, "send_media_play_pause", lambda: calls.append(1))
    c = MediaController(enabled=True)
    # بدون pause قبلی، ادامه نباید رسانه‌ای که از قبل متوقف بود را پخش کند
    c.resume()
    assert calls == []


def test_pause_then_enable_requires_repeat(monkeypatch):
    calls = []
    monkeypatch.setattr(mc, "send_media_play_pause", lambda: calls.append(1))
    c = MediaController(enabled=False)
    c.set_enabled(True)
    c.pause()
    c.resume()
    assert len(calls) == 2  # پس از فعال‌سازی، پخش/توقف کار می‌کند


def test_reset_prevents_resume(monkeypatch):
    calls = []
    monkeypatch.setattr(mc, "send_media_play_pause", lambda: calls.append(1))
    c = MediaController(enabled=True)
    c.pause()          # ۱ ارسال
    c.reset()          # paused را پاک می‌کند
    c.resume()         # دیگر نباید ارسال کند
    assert len(calls) == 1


def test_is_enabled_property():
    assert MediaController(True).is_enabled is True
    assert MediaController(False).is_enabled is False
