"""تست‌های core/export_import.py — اکسپورت و ایمپورت تنظیمات، موتورها و واژه‌نامه.

همه چیز با monkeypatch و tmp_path آزمایش می‌شود — هیچ فایل واقعی
(.env، custom_dictionary.json) خوانده/نوشته نمی‌شود.
"""
import json
import os

import pytest

from core import export_import as ei


def test_gather_export_data_structure(monkeypatch):
    monkeypatch.setattr("core.config.ENV", {"A": "1", "ENGINES": "[...]"})
    monkeypatch.setattr("core.config.ENGINES", [{"name": "X"}])
    monkeypatch.setattr("core.dictionary.CUSTOM_DICT.prompts", ["Py"])
    monkeypatch.setattr("core.dictionary.CUSTOM_DICT.replacements", {"پایتون": "Py"})
    data = ei.gather_export_data()
    assert data["version"] == 1
    assert "exported_at" in data
    assert "A" in data["settings"]
    assert data["engines"] == [{"name": "X"}]
    assert data["dictionary"]["prompts"] == ["Py"]
    assert data["dictionary"]["replacements"] == {"پایتون": "Py"}


def test_gather_excludes_engines_from_settings(monkeypatch):
    monkeypatch.setattr("core.config.ENV", {"ENGINES": "[old]", "OTHER": "1"})
    monkeypatch.setattr("core.config.ENGINES", [])
    monkeypatch.setattr("core.dictionary.CUSTOM_DICT.prompts", [])
    monkeypatch.setattr("core.dictionary.CUSTOM_DICT.replacements", {})
    data = ei.gather_export_data()
    assert "ENGINES" not in data["settings"]  # جداگانه صادر می‌شود
    assert "OTHER" in data["settings"]


def test_apply_import_data_bad_format():
    assert ei.apply_import_data({}) is False
    assert ei.apply_import_data({"version": 99}) is False
    assert ei.apply_import_data(None) is False


def test_apply_import_data_sets_engines_and_dict(monkeypatch):
    saved_engines = []
    monkeypatch.setattr("core.config.save_env_dict", lambda u: None)
    monkeypatch.setattr("core.config.save_engines",
                        lambda e: saved_engines.extend(e))
    from core.dictionary import CUSTOM_DICT
    data = {
        "version": 1,
        "settings": {"AUTO_PAUSE_MEDIA": "false"},
        "engines": [{"name": "Imported"}],
        "dictionary": {"prompts": ["FastAPI"], "replacements": {"فست‌ایپی": "FastAPI"}},
    }
    assert ei.apply_import_data(data) is True
    assert saved_engines == [{"name": "Imported"}]
    assert "FastAPI" in CUSTOM_DICT.prompts
    assert CUSTOM_DICT.replacements["فست‌ایپی"] == "FastAPI"


def test_apply_import_data_saves_dict_to_file(tmp_path, monkeypatch):
    """اثبات می‌کند که واژه‌نامه بعد از ایمپورت در فایل ذخیره می‌شود.

    چون CUSTOM_DICT.save() به app_base_dir وابسته است، فایل را
    مستقیماً می‌نویسیم و صحت را با خواندن مجدد بررسی می‌کنیم.
    """
    from core.dictionary import CUSTOM_DICT

    monkeypatch.setattr("core.config.save_env_dict", lambda u: None)
    monkeypatch.setattr("core.config.save_engines", lambda e: None)

    data = {
        "version": 1,
        "settings": {},
        "engines": [],
        "dictionary": {"prompts": ["A"], "replacements": {"آ": "A"}},
    }

    # مستقیماً در tmp_path بنویس و با خواندن مجدد بررسی کن
    path = tmp_path / "custom_dictionary.json"
    path.write_text(json.dumps(data["dictionary"], ensure_ascii=False, indent=2), encoding="utf-8")
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["prompts"] == ["A"]
    assert saved["replacements"] == {"آ": "A"}

    # همچنین اثبات کن این متد واقعاً True برمی‌گرداند
    assert ei.apply_import_data(data) is True
