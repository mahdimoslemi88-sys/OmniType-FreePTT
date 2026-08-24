"""تست‌های پنجرهٔ واژه‌نامه (gui/dictionary_window.py) با یک stub.

پنجرهٔ Toplevel روی یک ریشهٔ Tk مشترک ساخته می‌شود؛ اگر Tk در دسترس
نباشد تست‌ها skip می‌شوند. مدیر واژه‌نامه با یک stub جایگزین می‌شود تا
چیزی روی دیسک نوشته نشود.
"""
import tkinter as tk

import pytest

from gui import dictionary_window as dw
from gui.dictionary_window import CustomDictionaryWindow


class _FakeDict:
    def __init__(self):
        self.prompts = ["Python", "API"]
        self.replacements = {"پایتون": "Python"}
        self.added = []
        self.removed = []

    def add_term(self, en_term, fa_term=""):
        self.added.append((en_term, fa_term))
        if en_term not in self.prompts:
            self.prompts.append(en_term)
        if fa_term:
            self.replacements[fa_term] = en_term

    def remove_term(self, en_term):
        self.removed.append(en_term)
        if en_term in self.prompts:
            self.prompts.remove(en_term)


class _Parent:
    def __init__(self, root):
        self.root = root


@pytest.fixture
def win(tk_root):
    parent = _Parent(tk_root)
    mgr = _FakeDict()
    w = CustomDictionaryWindow(parent, mgr)
    tk_root.update_idletasks()
    yield w, mgr, tk_root
    try:
        w.destroy()
    except Exception:
        pass


def _row_values(w):
    return [w.tree.item(i, "values") for i in w.tree.get_children()]


def test_window_builds_and_lists_prompts(win):
    w, mgr, _root = win
    # هر واژهٔ داخل prompts در جدول هست
    values = _row_values(w)
    rendered = {v[0] for v in values}
    assert rendered == set(mgr.prompts)


def test_refresh_list_after_add(win):
    w, mgr, _root = win
    mgr.add_term("Docker", "داکر")
    w.refresh_list()
    rendered = {v[0] for v in _row_values(w)}
    assert "Docker" in rendered


def test_add_term_action(win):
    w, mgr, _root = win
    w.entry_en.insert(0, "Next.js")
    w.entry_fa.insert(0, "نکست")
    w.add_term_action()
    assert ("Next.js", "نکست") in mgr.added
    rendered = {v[0] for v in _row_values(w)}
    assert "Next.js" in rendered
    assert w.entry_en.get() == ""  # ورودی پس از افزودن پاک می‌شود


def test_add_term_requires_english(win, monkeypatch):
    w, mgr, _root = win
    # بدون کلمهٔ انگلیسی — هشدار نمایش داده می‌شود و چیزی اضافه نمی‌شود
    monkeypatch.setattr(dw.messagebox, "showwarning", lambda *a, **k: None)
    w.entry_fa.insert(0, "فقط فارسی")
    w.add_term_action()
    assert mgr.added == []


def test_remove_term_action(win):
    w, mgr, _root = win
    first = w.tree.get_children()[0]
    w.tree.selection_set(first)
    en_term = w.tree.item(first, "values")[0]
    w.remove_term_action()
    assert en_term in mgr.removed
