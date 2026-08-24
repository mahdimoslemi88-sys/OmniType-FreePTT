"""تست‌های مهاجرت چندموتوره و اولویت‌بندی موتورها در core/config.py.

همه تست‌ها از شبکه/دیسک جدا هستند: متغیرهای سراسری (ENV/ENGINES) با
monkeypatch جایگزین می‌شوند و نوشتن روی .env واقعی با یک ضبط‌کننده جعلی
مهار می‌شود که از هرگونه عارضه‌جانبی جلوگیری کند.
"""
import json

import pytest

from core import config
from core.config import (
    ROLE_ASR,
    ROLE_BOTH,
    ROLE_LLM,
)

# ── normalise_engine: تبدیل فرمت قدیمی به جدید (مهاجرت) ──────────────


def test_normalize_new_format_passthrough():
    engine = {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": "k",
        "model": "gpt-oss-20b",
        "role": "llm",
        "active": True,
    }
    result = config._normalize_engine(engine)
    assert result == [engine]


def test_normalize_old_asr_only():
    old = {
        "name": "Groq",
        "active": True,
        "asr_url": "au", "asr_key": "ak", "asr_model": "am",
        "llm_url": "", "llm_key": "", "llm_model": "",
    }
    result = config._normalize_engine(old)
    assert len(result) == 1
    e = result[0]
    assert e["name"] == "Groq"
    assert e["base_url"] == "au"
    assert e["api_key"] == "ak"
    assert e["model"] == "am"
    assert e["role"] == ROLE_ASR
    assert e["active"] is True


def test_normalize_old_llm_only():
    old = {
        "name": "Groq",
        "active": True,
        "asr_url": "", "asr_key": "", "asr_model": "",
        "llm_url": "lu", "llm_key": "lk", "llm_model": "lm",
    }
    result = config._normalize_engine(old)
    assert len(result) == 1
    e = result[0]
    assert e["name"] == "Groq"
    assert e["base_url"] == "lu"
    assert e["api_key"] == "lk"
    assert e["model"] == "lm"
    assert e["role"] == ROLE_LLM
    assert e["active"] is True


def test_normalize_old_both_splits_into_two():
    old = {
        "name": "Groq",
        "active": True,
        "asr_url": "au", "asr_key": "ak", "asr_model": "am",
        "llm_url": "lu", "llm_key": "lk", "llm_model": "lm",
    }
    result = config._normalize_engine(old)
    assert len(result) == 2
    asr, llm = result
    assert asr["name"] == "Groq (ASR)"
    assert asr["role"] == ROLE_ASR
    assert asr["api_key"] == "ak"
    assert llm["name"] == "Groq (LLM)"
    assert llm["role"] == ROLE_LLM
    assert llm["api_key"] == "lk"
    # هیچ‌کدام active نیست؛ بارگذاری نهایی یک موتور را فعال می‌کند
    assert asr["active"] is False and llm["active"] is False


def test_normalize_old_no_fields_falls_back_to_both():
    old = {"name": "Custom", "active": False}
    result = config._normalize_engine(old)
    assert len(result) == 1
    e = result[0]
    assert e["role"] == ROLE_BOTH
    assert e["base_url"] == "https://api.groq.com/openai/v1"
    assert e["model"] == "whisper-large-v3-turbo"


def test_normalize_keeps_explicit_base_url_for_both():
    old = {"name": "Custom", "base_url": "http://localhost:11434",
           "api_key": "x", "model": "llama3"}
    result = config._normalize_engine(old)
    e = result[0]
    assert e["role"] == ROLE_BOTH
    assert e["base_url"] == "http://localhost:11434"
    assert e["model"] == "llama3"


# ── build_default_engines: کلید قدیمی و جایگزینی مدل حذف‌شده گروک ────


def test_default_engines_legacy_key_precedence(monkeypatch):
    monkeypatch.setattr(config, "ENV", {
        "CUSTOM_LLM_API_KEY": "llmkey",
        "CUSTOM_ASR_API_KEY": "asrkey",
    })
    engines = config._build_default_engines()
    assert len(engines) == 2
    # CUSTOM_LLM_API_KEY در اولویت است
    assert engines[0]["api_key"] == "llmkey"
    assert engines[1]["api_key"] == "llmkey"


def test_default_engines_groq_key_fallback(monkeypatch):
    monkeypatch.setattr(config, "ENV", {"GROQ_API_KEY": "gkey"})
    engines = config._build_default_engines()
    assert engines[0]["api_key"] == "gkey"


def test_default_engines_decommissioned_model_replaced(monkeypatch):
    monkeypatch.setattr(config, "ENV", {"CUSTOM_LLM_MODEL": "llama-3.3-70b-versatile"})
    engines = config._build_default_engines()
    assert engines[1]["model"] == "openai/gpt-oss-20b"


def test_default_engines_keeps_custom_llm_model(monkeypatch):
    monkeypatch.setattr(config, "ENV", {"CUSTOM_LLM_MODEL": "openai/gpt-oss-120b"})
    engines = config._build_default_engines()
    assert engines[1]["model"] == "openai/gpt-oss-120b"


def test_default_engines_roles(monkeypatch):
    monkeypatch.setattr(config, "ENV", {})
    engines = config._build_default_engines()
    assert engines[0]["role"] == ROLE_ASR
    assert engines[1]["role"] == ROLE_LLM


# ── load_engines: JSON + اطمینان از یک موتور فعال ────────────────────


def test_load_engines_parses_and_normalizes_json(monkeypatch):
    new_fmt = {"name": "OpenRouter", "base_url": "u", "api_key": "k",
               "model": "m", "role": ROLE_LLM, "active": False}
    monkeypatch.setattr(config, "ENV", {"ENGINES": json.dumps([new_fmt])})
    engines = config._load_engines()
    assert len(engines) == 1
    assert engines[0]["name"] == "OpenRouter"
    assert engines[0]["active"] is True  # فقط یک موتور فعال می‌شود


def test_load_engines_falls_back_to_defaults(monkeypatch):
    monkeypatch.setattr(config, "ENV", {})
    engines = config._load_engines()
    assert len(engines) == 2
    assert sum(1 for e in engines if e["active"]) == 1


def test_load_engines_invalid_json_falls_back(monkeypatch):
    monkeypatch.setattr(config, "ENV", {"ENGINES": "not-json{{{"})
    engines = config._load_engines()
    assert len(engines) >= 1
    assert sum(1 for e in engines if e["active"]) == 1


# ── کاندیداهای ASR/LLM به ترتیب اولویت (فقط با کلید) ──────────────────


@pytest.fixture
def engines(monkeypatch):
    config.ENGINES = [
        {"name": "Both", "api_key": "k1", "role": ROLE_BOTH, "active": True},
        {"name": "AsrNoKey", "api_key": "", "role": ROLE_ASR, "active": False},
        {"name": "AsrKey", "api_key": "k2", "role": ROLE_ASR, "active": False},
        {"name": "Llm", "api_key": "k3", "role": ROLE_LLM, "active": False},
    ]
    yield config.ENGINES


def test_get_asr_candidates_filters_by_role_and_key(engines):
    cands = config.get_asr_candidates()
    names = [c["name"] for c in cands]
    # BOTH با کلید + ASR با کلید؛ ASR بدون کلید حذف می‌شود
    assert names == ["Both", "AsrKey"]


def test_get_llm_candidates_filters_by_role_and_key(engines):
    cands = config.get_llm_candidates()
    names = [c["name"] for c in cands]
    assert names == ["Both", "Llm"]


def test_get_asr_config_returns_first_priority(engines):
    cfg = config.get_asr_config()
    assert cfg["model"] in ("", )  # مدل از موتور Both برداشته می‌شود
    assert "base_url" in cfg and "api_key" in cfg


# ── فعال‌سازی و جابه‌جایی اولویت (بدون نوشتن روی دیسک) ────────────────


def test_set_active_engine(monkeypatch):
    config.ENGINES = [
        {"name": "A", "role": ROLE_ASR, "api_key": "k", "active": True},
        {"name": "B", "role": ROLE_LLM, "api_key": "k", "active": False},
    ]
    saved = {}
    monkeypatch.setattr(config, "save_env_dict", lambda updates: saved.update(updates))
    config.set_active_engine("B")
    assert config.ENGINES[0]["active"] is False
    assert config.ENGINES[1]["active"] is True
    assert "ENGINES" in saved  # روی .env ذخیره شده است (بدون نوشتن واقعی)


def test_move_engine_up(monkeypatch):
    config.ENGINES = [
        {"name": "A", "active": True},
        {"name": "B", "active": False},
        {"name": "C", "active": False},
    ]
    monkeypatch.setattr(config, "save_env_dict", lambda updates: None)
    assert config.move_engine(1, -1) is True
    assert [e["name"] for e in config.ENGINES] == ["B", "A", "C"]


def test_move_engine_down(monkeypatch):
    config.ENGINES = [
        {"name": "A", "active": True},
        {"name": "B", "active": False},
    ]
    monkeypatch.setattr(config, "save_env_dict", lambda updates: None)
    assert config.move_engine(0, 1) is True
    assert [e["name"] for e in config.ENGINES] == ["B", "A"]


def test_move_engine_out_of_range(monkeypatch):
    config.ENGINES = [{"name": "A", "active": True}]
    monkeypatch.setattr(config, "save_env_dict", lambda updates: None)
    assert config.move_engine(0, -1) is False
    assert config.move_engine(0, 1) is False
    assert [e["name"] for e in config.ENGINES] == ["A"]
