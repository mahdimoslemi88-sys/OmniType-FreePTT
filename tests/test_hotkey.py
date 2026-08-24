"""تست‌های core/hotkey.py — نگاشت کلید، نرمال‌سازی و تشخیص ترکیب کلیدها.

وضعیت واقعی کلیدها با monkeypatch مهار می‌شود تا تست قطعی (غیروابسته به
صفحه‌کلید واقعی) باشد.
"""
import pytest

from core import hotkey


def test_vk_map_has_expected_codes():
    assert hotkey.VK_MAP["capslock"] == 0x14
    assert hotkey.VK_MAP["f2"] == 0x71
    assert hotkey.VK_MAP["ctrl"] == 0x11
    assert hotkey.VK_MAP["shift"] == 0x10
    assert hotkey.VK_MAP["alt"] == 0x12


def test_is_hotkey_held_single_normalizes(monkeypatch):
    seen = []

    def fake_is_down(k):
        seen.append(k)
        return True

    monkeypatch.setattr(hotkey, "is_down", fake_is_down)
    assert hotkey.is_hotkey_held("Caps Lock") is True
    # حروف کوچک و بدون فاصله شده و به "capslock" نگاشت می‌شود
    assert seen == ["capslock"]


def test_is_hotkey_held_combo_queries_each_key(monkeypatch):
    seen = []

    def fake_is_down(k):
        seen.append(k)
        return False

    monkeypatch.setattr(hotkey, "is_down", fake_is_down)
    hotkey.is_hotkey_held("Ctrl+Shift")
    assert "ctrl" in seen and "shift" in seen


def test_combo_returns_true_if_any_held(monkeypatch):
    # رفتار فعلی: if هر کدام از کلیدهای ترکیب پایین باشد True
    monkeypatch.setattr(hotkey, "is_down", lambda k: k == "ctrl")
    assert hotkey.is_hotkey_held("ctrl+alt") is True


def test_combo_returns_false_when_none_held(monkeypatch):
    monkeypatch.setattr(hotkey, "is_down", lambda k: False)
    assert hotkey.is_hotkey_held("ctrl+alt") is False


def test_is_down_known_key_uses_getasync(monkeypatch):
    # کلید شناخته‌شده از VK_MAP و GetAsyncKeyState استفاده می‌کند
    def fake_get(vk):
        return 0x8000  # بیت «پایین» فعال

    fake_user32 = type("U", (), {"GetAsyncKeyState": staticmethod(fake_get)})()
    monkeypatch.setattr(hotkey.ctypes, "windll", type("W", (), {"user32": fake_user32})())
    assert hotkey.is_down("f2") is True


def test_is_down_known_key_not_pressed(monkeypatch):
    def fake_get(vk):
        return 0  # پایین نیست

    fake_user32 = type("U", (), {"GetAsyncKeyState": staticmethod(fake_get)})()
    monkeypatch.setattr(hotkey.ctypes, "windll", type("W", (), {"user32": fake_user32})())
    assert hotkey.is_down("f2") is False


def test_is_down_unknown_key_falls_back_to_keyboard(monkeypatch):
    class FakeKeyboard:
        def is_pressed(self, k):
            return k == "a"

    monkeypatch.setattr(hotkey, "keyboard", FakeKeyboard())
    assert hotkey.is_down("a") is True
    assert hotkey.is_down("b") is False


def test_is_down_no_keyboard_returns_false(monkeypatch):
    monkeypatch.setattr(hotkey, "keyboard", None)
    assert hotkey.is_down("x") is False
