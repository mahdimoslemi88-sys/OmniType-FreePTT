"""تست‌های پنل کنترل (gui/control_panel.py) با یک stub parent.

پنل با یک parent جعلی ساخته می‌شود تا بدون بالا آوردن کل برنامه (صدا/هوک)
بتوان ساختار تب‌ها، انتخاب موتور، زبان و نشانگر وضعیت را بررسی کرد.

یک ریشهٔ Tk مشترک در سطح ماژول ساخته و در همهٔ تست‌ها بازاستفاده می‌شود
(فقط یک بار tk.Tk()) تا از شکستِ ساخت ریشهٔ دوم جلوگیری شود. اگر Tk
در محیط در دسترس نباشد، تست‌ها به‌جای خطا، skip می‌شوند.
"""
import tkinter as tk

import pytest

from gui.control_panel import ControlPanel
from gui.theme import ACCENT_GREEN


class _StubParent:
    """واسط حداقلی موردنیاز ControlPanel، بدون عارضه‌جانبی واقعی."""

    def __init__(self, root):
        self.root = root
        self.current_engine = "google"
        self.current_lang = "fa"
        self.current_hotkey = "caps lock"
        self.history = []
        self.auto_pause_media = True
        self.change_calls = []

    def change_engine(self, name):
        self.current_engine = name
        self.change_calls.append(name)

    def change_engine_language(self, code):
        self.current_lang = code

    def _noop(self, *a, **k):
        pass

    translate_peek_action = _noop
    open_document_translator_window = _noop
    prompt_engineer_action = _noop
    open_custom_dict_window = _noop
    open_api_keys_window = _noop
    open_custom_hotkey_window = _noop
    change_global_hotkey = _noop
    copy_history_item = _noop
    clear_history_action = _noop
    toggle_auto_pause_media = _noop
    free_vram_action = _noop
    quit_app = _noop

    def translate_manual_action(self, mode):
        pass


@pytest.fixture
def panel(tk_root):
    """ساخت پنل روی ریشهٔ مشترک (tk_root از conftest) و پاک‌سازی پس از هر تست."""
    stub = _StubParent(tk_root)
    cp = ControlPanel(stub)
    tk_root.update_idletasks()
    yield cp, stub, tk_root
    try:
        cp.destroy()
    except Exception:
        pass


def _tab_texts(cp):
    return [cp.notebook.tab(i, "text") for i in range(len(cp.notebook.tabs()))]


def test_panel_has_six_tabs(panel):
    cp, _stub, _root = panel
    tabs = _tab_texts(cp)
    assert len(tabs) == 6
    assert any("موتور" in t for t in tabs)
    assert any("زبان" in t for t in tabs)
    assert any("تنظیمات" in t for t in tabs)


def test_engine_buttons_include_google_and_local(panel):
    cp, _stub, _root = panel
    keys = [k for k, _ in cp.engine_btns]
    assert "google" in keys
    assert "local" in keys


def test_google_is_active_by_default(panel):
    cp, stub, _root = panel
    assert stub.current_engine == "google"
    btn = [b for k, b in cp.engine_btns if k == "google"][0]
    assert btn.cget("bg") == ACCENT_GREEN


def test_pick_engine_calls_parent_and_activates_button(panel):
    cp, stub, _root = panel
    cp._pick_engine("local")
    assert stub.current_engine == "local"
    assert stub.change_calls == ["local"]
    btn = [b for k, b in cp.engine_btns if k == "local"][0]
    assert btn.cget("bg") == ACCENT_GREEN  # موتور فعال سبز است
    google_btn = [b for k, b in cp.engine_btns if k == "google"][0]
    assert google_btn.cget("bg") != ACCENT_GREEN


def test_lang_tab_has_modes(panel):
    cp, _stub, _root = panel
    # fa, en, auto, prompt_engineer, translate_fa_en, translate_en_fa
    assert len(cp.lang_btns) == 6


def test_pick_language_updates_parent(panel):
    cp, stub, _root = panel
    cp._pick_lang("en")
    assert stub.current_lang == "en"


def test_settings_pause_checkbox_reflects_parent(panel):
    cp, stub, _root = panel
    assert cp.pause_var.get() is True
    stub.auto_pause_media = False
    cp.pause_var.set(stub.auto_pause_media)
    assert cp.pause_var.get() is False


def test_status_shows_green_for_google(panel):
    cp, _stub, _root = panel
    # گوگل رایگان → سبز، بدون تست شبکه
    cp._set_status(ACCENT_GREEN, "🌐 Google Speech — رایگان و پیش‌فرض")
    assert cp.status_label.cget("text").startswith("🌐")
    assert cp.status_dot.find_all()  # نقطهٔ رنگی رسم شده است


def test_close_is_safe(panel):
    cp, _stub, _root = panel
    cp.close()
    cp.close()  # دوبار باید بی‌خطر باشد
