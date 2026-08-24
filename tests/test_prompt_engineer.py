"""تست‌های مهندسی پرامپت (engine/prompt_engineer.py).

همه‌چیز با mock انجام می‌شود — بدون تماس شبکه واقعی. رفتار زنجیرهٔ
fallback (LLM → Gemini) و مدیریت خطا بررسی می‌شود.
"""
import pytest

from engine import prompt_engineer as pe
from engine.prompt_engineer import AIPromptEngineer


def test_empty_input_returns_empty():
    assert AIPromptEngineer.generate_engineered_prompt("") == ""
    assert AIPromptEngineer.generate_engineered_prompt("   ") == ""


def test_raises_when_no_llm_or_gemini(monkeypatch):
    monkeypatch.setattr(pe, "get_llm_candidates", lambda: [])
    monkeypatch.setattr(pe, "GEMINI_API_KEY", "")
    with pytest.raises(RuntimeError):
        AIPromptEngineer.generate_engineered_prompt("write a poem")


def test_uses_first_llm_candidate(monkeypatch):
    cfg = {"base_url": "https://api.groq.com/openai/v1", "api_key": "k", "model": "m1"}
    monkeypatch.setattr(pe, "get_llm_candidates", lambda: [cfg])

    class FakeRes:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": " EngineeredPrompt "}}]}

    recorded = {}

    def fake_post(url, headers, json, timeout):
        recorded["url"] = url
        recorded["headers"] = headers
        recorded["json"] = json
        return FakeRes()

    monkeypatch.setattr(pe.requests, "post", fake_post)

    out = AIPromptEngineer.generate_engineered_prompt("write a poem about cats")
    assert out == "EngineeredPrompt"  # trimmed
    assert recorded["url"].endswith("/chat/completions")
    assert recorded["headers"]["Authorization"] == "Bearer k"
    assert recorded["json"]["model"] == "m1"
    assert recorded["json"]["temperature"] == 0.3


def test_skips_candidate_without_api_key(monkeypatch):
    cfgs = [
        {"base_url": "https://x", "api_key": "k", "model": "real"},
        {"base_url": "https://x", "api_key": "", "model": "noskip"},  # بدون کلید → رد می‌شود
    ]
    called_models = []

    class FakeRes:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": "X"}}]}

    def fake_post(url, headers, json, timeout):
        called_models.append(json["model"])
        return FakeRes()

    monkeypatch.setattr(pe, "get_llm_candidates", lambda: cfgs)
    monkeypatch.setattr(pe.requests, "post", fake_post)
    AIPromptEngineer.generate_engineered_prompt("hi")
    assert called_models == ["real"]


def test_second_candidate_used_when_first_fails(monkeypatch):
    cfgs = [
        {"base_url": "https://x", "api_key": "k", "model": "bad"},
        {"base_url": "https://x", "api_key": "k", "model": "good"},
    ]
    called = []

    class FakeRes:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": "OK"}}]}

    def fake_post(url, headers, json, timeout):
        model = json["model"]
        called.append(model)
        if model == "bad":
            raise Exception("boom")
        return FakeRes()

    monkeypatch.setattr(pe, "get_llm_candidates", lambda: cfgs)
    monkeypatch.setattr(pe.requests, "post", fake_post)
    assert AIPromptEngineer.generate_engineered_prompt("hi") == "OK"
    assert called == ["bad", "good"]


def test_falls_back_to_gemini_when_llm_fails(monkeypatch):
    monkeypatch.setattr(pe, "get_llm_candidates",
                       lambda: [{"base_url": "u", "api_key": "k", "model": "m"}])
    monkeypatch.setattr(pe, "GEMINI_API_KEY", "gkey")

    class FakeRes:
        status_code = 200

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": " GeminiPrompt "}]}}]}

    def fake_post(url, **kw):
        if "generativelanguage" in url:
            return FakeRes()
        raise Exception("LLM down")

    monkeypatch.setattr(pe.requests, "post", fake_post)
    assert AIPromptEngineer.generate_engineered_prompt("hi") == "GeminiPrompt"


def test_non_200_llm_and_no_gemini_raises(monkeypatch):
    monkeypatch.setattr(pe, "get_llm_candidates",
                       lambda: [{"base_url": "u", "api_key": "k", "model": "m"}])
    monkeypatch.setattr(pe, "GEMINI_API_KEY", "")

    class FakeRes:
        status_code = 429
        text = "rate limited"

        def json(self):
            return {}

    monkeypatch.setattr(pe.requests, "post", lambda *a, **k: FakeRes())
    with pytest.raises(RuntimeError):
        AIPromptEngineer.generate_engineered_prompt("hi")
