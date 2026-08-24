"""تست‌های آیکون تسکبار (gui/system_tray.py).

تصویر آیکون، ثبت callbacks، ساخت منو و رفتار بی‌خطر وقتی pystray یا
آیکون در دسترس نیست — بدون اجرای واقعی حلقهٔ تسکبار.
"""
import pytest

from gui import system_tray as st
from gui.system_tray import SystemTray, make_tray_image


def test_make_tray_image_is_rgba_square():
    img = make_tray_image(32)
    assert img.size == (32, 32)
    assert img.mode == "RGBA"
    # حداقل یک پیکسل غیرشفاف (منطقهٔ آیکون) وجود دارد
    assert any(a > 0 for _, _, _, a in img.getdata())


def test_make_tray_image_custom_size():
    img = make_tray_image(64)
    assert img.size == (64, 64)


def test_callbacks_registered():
    tray = SystemTray()
    calls = []
    tray.on("quit", lambda: calls.append("q"))
    tray._callbacks["quit"]()
    assert calls == ["q"]


def test_fire_is_safe_when_callback_not_registered():
    tray = SystemTray()
    # callbacks ابتدا None هستند (با on() تنظیم می‌شوند)
    assert tray._callbacks["dict"] is None
    # _fire نباید خطا دهد وقتی callback ثبت نشده است
    tray._fire("dict")
    tray._fire("nonsense")


def test_fire_invokes_registered_callback():
    tray = SystemTray()
    calls = []
    tray.on("quit", lambda: calls.append("quit"))
    tray._fire("quit")
    assert calls == ["quit"]


def test_build_menu_uses_safe_fire(monkeypatch):
    if not st.HAS_SYSTRAY:
        pytest.skip("pystray not installed")
    tray = SystemTray()
    # ساختن منو با callback ثبت‌نشده نباید کرش کند (قبلاً .get مقدار None را برمی‌گرداند)
    menu = tray._build_menu()
    assert menu is not None


def test_set_auto_pause_state_safe_without_icon():
    tray = SystemTray()
    tray._icon = None
    tray.set_auto_pause_state(False)  # نباید خطا دهد


def test_create_skips_when_no_pystray(monkeypatch):
    monkeypatch.setattr(st, "HAS_SYSTRAY", False)
    tray = SystemTray()
    tray.create()
    assert tray._icon is None


def test_build_menu_builds_with_pystray():
    if not st.HAS_SYSTRAY:
        pytest.skip("pystray not installed")
    tray = SystemTray()
    menu = tray._build_menu()
    assert menu is not None


def test_stop_safe_without_icon():
    tray = SystemTray()
    tray.stop()  # بدون آیکون نباید خطا دهد


def test_stop_safe_with_fake_icon(monkeypatch):
    tray = SystemTray()

    class FakeIcon:
        def __init__(self):
            self.stopped = False

        def stop(self):
            self.stopped = True

    fake = FakeIcon()
    tray._icon = fake
    tray.stop()
    # صفر یا یک thread برای توقف — فقط مطمئن می‌شویم بدون خطا اجرا شد
    tray.stop()
    assert True
