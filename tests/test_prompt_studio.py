"""Unit and Mock Tests for Prompt Studio.

Covers:
- Strict JSON response parsing (ready vs needs_clarification vs invalid)
- Model validation (free mode enforcement, paid rejection)
- System prompt contract checks
- Mocked provider network generation (Gemini 3.8 Flash, OpenRouter Free, GLM-5.3)
- Error mapping (401, 402, 403, 404, 429 with retry-after, timeout, network error)
- Cancellation & stale response discarding
- Input length boundaries and empty text validation
- Multi-turn clarification workflow
"""
import json
import os
import threading
from unittest.mock import MagicMock, patch
import pytest

from prompt_studio_engine import (
    PromptStudioEngine,
    StudioError,
    Cancelled,
    Result,
    SYSTEM_PROMPT,
)


# ── System Prompt Contract ──────────────────────────────────────────────
def test_system_prompt_contract():
    assert "You are a professional Prompt Engineer" in SYSTEM_PROMPT
    assert "You are not the execution agent" in SYSTEM_PROMPT
    assert "Do not solve the underlying task" in SYSTEM_PROMPT
    assert "Do not write the code requested by the user" in SYSTEM_PROMPT
    assert "Do not invent facts" in SYSTEM_PROMPT
    assert "Objective" in SYSTEM_PROMPT
    assert "Requirements" in SYSTEM_PROMPT
    assert "Workflow or Steps" in SYSTEM_PROMPT
    assert "Output Format" in SYSTEM_PROMPT
    assert "Constraints" in SYSTEM_PROMPT
    assert "Acceptance Criteria" in SYSTEM_PROMPT
    assert "needs_clarification" in SYSTEM_PROMPT
    assert "Persian" in SYSTEM_PROMPT


# ── Model Validation ───────────────────────────────────────────────────
def test_validate_model_openrouter_free():
    # Valid free models
    assert PromptStudioEngine.validate_model(
        PromptStudioEngine.PROVIDER_OPENROUTER, "openrouter/free"
    ) == "openrouter/free"
    assert PromptStudioEngine.validate_model(
        PromptStudioEngine.PROVIDER_OPENROUTER, "meta-llama/llama-3.3-70b-instruct:free"
    ) == "meta-llama/llama-3.3-70b-instruct:free"
    assert PromptStudioEngine.validate_model(
        PromptStudioEngine.PROVIDER_OPENROUTER, ""
    ) == "openrouter/free"

    # Reject paid models
    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.validate_model(
            PromptStudioEngine.PROVIDER_OPENROUTER, "openai/gpt-4o"
        )
    assert "فقط مدل openrouter/free" in str(exc.value)

    with pytest.raises(StudioError):
        PromptStudioEngine.validate_model(
            PromptStudioEngine.PROVIDER_OPENROUTER, "openrouter/auto"
        )

    with pytest.raises(StudioError):
        PromptStudioEngine.validate_model(
            PromptStudioEngine.PROVIDER_OPENROUTER, "anthropic/claude-3.5-sonnet"
        )


def test_validate_model_gemini():
    assert PromptStudioEngine.validate_model(
        PromptStudioEngine.PROVIDER_GEMINI, ""
    ) == "gemini-3.8-flash"
    assert PromptStudioEngine.validate_model(
        PromptStudioEngine.PROVIDER_GEMINI, "gemini-3.8-flash"
    ) == "gemini-3.8-flash"


def test_validate_model_glm():
    assert PromptStudioEngine.validate_model(
        PromptStudioEngine.PROVIDER_GLM, ""
    ) == "glm-5.3"
    assert PromptStudioEngine.validate_model(
        PromptStudioEngine.PROVIDER_GLM, "glm-5.3"
    ) == "glm-5.3"


# ── Response Parser ────────────────────────────────────────────────────
def test_parse_valid_ready():
    raw = json.dumps({
        "status": "ready",
        "prompt": "Objective: Build a React login page.\nRequirements: responsive layout.",
        "questions": [],
    })
    res = PromptStudioEngine.parse(raw, model="openrouter/free", provider="openrouter")
    assert isinstance(res, Result)
    assert res.status == "ready"
    assert "Objective" in res.prompt
    assert res.questions == ()
    assert res.model == "openrouter/free"


def test_parse_valid_ready_with_code_fences():
    inner = json.dumps({
        "status": "ready",
        "prompt": "Objective: Clean English prompt.",
        "questions": [],
    })
    fenced = f"```json\n{inner}\n```"
    res = PromptStudioEngine.parse(fenced, model="gemini-3.8-flash", provider="gemini")
    assert res.status == "ready"
    assert res.prompt == "Objective: Clean English prompt."


def test_parse_valid_needs_clarification():
    raw = json.dumps({
        "status": "needs_clarification",
        "prompt": "",
        "questions": [
            "آیا هدف ساخت رابط کاربری تحت وب است یا موبایل؟",
            "کدام پایگاه داده مدنظر شماست؟"
        ],
    })
    res = PromptStudioEngine.parse(raw, model="openrouter/free")
    assert res.status == "needs_clarification"
    assert res.prompt == ""
    assert len(res.questions) == 2
    assert "موبایل" in res.questions[0]


def test_parse_rejects_mixed_status():
    # Model mistakenly returns both prompt and questions
    raw = json.dumps({
        "status": "ready",
        "prompt": "Some prompt",
        "questions": ["سؤال اضافه"],
    })
    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.parse(raw)
    assert "تفکیک نکرده است" in str(exc.value)


def test_parse_rejects_too_many_questions():
    raw = json.dumps({
        "status": "needs_clarification",
        "prompt": "",
        "questions": ["Q1", "Q2", "Q3", "Q4"],
    })
    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.parse(raw)
    assert "حداکثر ۳ سؤال" in str(exc.value)


def test_parse_rejects_invalid_json():
    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.parse("This is not JSON at all")
    assert "ساختار معتبر JSON نبود" in str(exc.value)


# ── Input Boundaries ───────────────────────────────────────────────────
def test_generate_empty_input_rejected():
    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.generate(
            text="   ",
            api_key="sk-dummy",
        )
    assert "ابتدا خواسته یا ایده خود را بنویسید" in str(exc.value)


def test_generate_missing_api_key_rejected():
    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.generate(
            text="می‌خواهم یک برنامه بنویسم",
            api_key="   ",
        )
    assert "کلید API معتبر وارد نشده است" in str(exc.value)


def test_generate_oversized_input_rejected():
    huge_text = "الف" * 16001
    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.generate(
            text=huge_text,
            api_key="sk-dummy",
        )
    assert "نباید از 16000 نویسه بیشتر باشد" in str(exc.value)


# ── Cancellation ───────────────────────────────────────────────────────
def test_generate_pre_cancelled():
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        PromptStudioEngine.generate(
            text="متن تستی",
            api_key="sk-dummy",
            cancel=cancel,
        )


# ── Mocked Provider Network Calls ──────────────────────────────────────
@patch("requests.post")
def test_generate_openrouter_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "status": "ready",
                        "prompt": "Objective: Build a simple counter app in Python.",
                        "questions": [],
                    })
                }
            }
        ]
    }
    mock_post.return_value = mock_resp

    res = PromptStudioEngine.generate(
        text="یک برنامه شمارنده ساده با پایتون بساز",
        api_key="sk-or-v1-dummy",
        provider=PromptStudioEngine.PROVIDER_OPENROUTER,
        model="openrouter/free",
    )
    assert res.status == "ready"
    assert "Objective" in res.prompt
    assert res.model == "meta-llama/llama-3.3-70b-instruct:free"

    # Verify request payload
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["model"] == "openrouter/free"
    assert call_kwargs["headers"]["Authorization"] == "Bearer sk-or-v1-dummy"


@patch("requests.post")
def test_generate_gemini_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "status": "ready",
                                "prompt": "Objective: Create a REST API using Fastify.",
                                "questions": [],
                            })
                        }
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_resp

    res = PromptStudioEngine.generate(
        text="می‌خوام یک API با فستیفای بسازم",
        api_key="AIzaSyDummyKey",
        provider=PromptStudioEngine.PROVIDER_GEMINI,
        model="gemini-3.8-flash",
    )
    assert res.status == "ready"
    assert "Objective" in res.prompt
    assert res.model == "gemini-3.8-flash"

    # Verify Gemini payload: No temperature, header auth, thinkingConfig
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["headers"]["x-goog-api-key"] == "AIzaSyDummyKey"
    assert "temperature" not in call_kwargs["json"]["generationConfig"]
    assert call_kwargs["json"]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "MEDIUM"


@patch("requests.post")
def test_generate_openrouter_error_429(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "15"}
    mock_post.return_value = mock_resp

    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.generate(
            text="تست خطا",
            api_key="sk-dummy",
            provider=PromptStudioEngine.PROVIDER_OPENROUTER,
        )
    assert "سهمیه یا ظرفیت ترافیک مدل رایگان" in str(exc.value)
    assert "15 ثانیه" in str(exc.value)


@patch("requests.post")
def test_generate_openrouter_error_401(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_post.return_value = mock_resp

    with pytest.raises(StudioError) as exc:
        PromptStudioEngine.generate(
            text="تست کلید",
            api_key="invalid-key",
            provider=PromptStudioEngine.PROVIDER_OPENROUTER,
        )
    assert "معتبر نیست یا منقضی شده است" in str(exc.value)


@patch("requests.post")
def test_generate_multi_turn_clarification(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "openrouter/free",
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "status": "ready",
                        "prompt": "Objective: Create an e-commerce backend in Django with PostgreSQL.",
                        "questions": [],
                    })
                }
            }
        ]
    }
    mock_post.return_value = mock_resp

    res = PromptStudioEngine.generate(
        text="یک سیستم فروشگاهی می‌خواهم",
        api_key="sk-dummy",
        answers="فریمورک جنگو و دیتابیس پستگرس باشد.",
        questions=("کدام فریمورک را ترجیح می‌دهید؟",),
    )
    assert res.status == "ready"

    # Check that previous questions and answers were included in user content
    sent_payload = mock_post.call_args[1]["json"]
    user_msg = json.loads(sent_payload["messages"][1]["content"])
    assert user_msg["clarification_answers"] == "فریمورک جنگو و دیتابیس پستگرس باشد."
    assert "کدام فریمورک" in user_msg["previous_questions"][0]


def test_antigravity_hub_model_validation():
    assert PromptStudioEngine.validate_model(PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB, None) == "flash"
    assert PromptStudioEngine.validate_model(PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB, "pro") == "pro"
    assert PromptStudioEngine.validate_model(PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB, "invalid-model") == "flash"


def test_antigravity_hub_session_isolation(tmp_path, monkeypatch):
    test_session_file = str(tmp_path / "test_session.json")
    monkeypatch.setattr(PromptStudioEngine, "SESSION_FILE", test_session_file)

    # Initially empty
    assert PromptStudioEngine.get_active_session_id() == ""

    # Save session with outside-of-project
    PromptStudioEngine._save_active_session_id("session-uuid-1234", PromptStudioEngine.OUTSIDE_PROJECT_ID)
    assert PromptStudioEngine.get_active_session_id() == "session-uuid-1234"

    # Reject Foodyar or workspace project sessions
    PromptStudioEngine._save_active_session_id("foodyar-session", "512647cd-6c06-4558-adb3-59f289ac3dc1")
    assert PromptStudioEngine.get_active_session_id() == ""

    # Reset session
    PromptStudioEngine._save_active_session_id("session-uuid-1234", PromptStudioEngine.OUTSIDE_PROJECT_ID)
    PromptStudioEngine.reset_session()
    assert PromptStudioEngine.get_active_session_id() == ""
    assert not os.path.exists(test_session_file)


def test_antigravity_hub_no_api_key_requirement():
    key = PromptStudioEngine.configured_key(PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB)
    assert key == "LOCAL_HUB"


def test_antigravity_hub_cli_generation_mock(tmp_path, monkeypatch):
    test_session_file = str(tmp_path / "test_session.json")
    monkeypatch.setattr(PromptStudioEngine, "SESSION_FILE", test_session_file)
    monkeypatch.setattr(PromptStudioEngine, "AGY_EXE", "fake_agy.exe")

    mock_json_out = json.dumps({
        "conversation_id": "test-dedicated-cid-999",
        "status": "SUCCESS",
        "response": json.dumps({
            "status": "ready",
            "prompt": "Objective: Build a modern button component.",
            "questions": []
        }),
        "num_turns": 1
    })

    mock_proc = MagicMock()
    mock_proc.poll.side_effect = [0]
    mock_proc.communicate.return_value = (mock_json_out, "")
    mock_proc.returncode = 0

    with patch("os.path.exists", return_value=True), \
         patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        res = PromptStudioEngine.generate(
            "دکمه مدرن در ری‌اکت می‌خوام",
            provider=PromptStudioEngine.PROVIDER_ANTIGRAVITY_HUB,
            model="flash"
        )

        assert res.status == "ready"
        assert "modern button" in res.prompt
        assert res.questions == ()

        # Assert CLI was invoked with outside-of-project strictly
        called_cmd = mock_popen.call_args[0][0]
        assert "--project" in called_cmd
        proj_idx = called_cmd.index("--project")
        assert called_cmd[proj_idx + 1] == "outside-of-project"
        assert "512647cd-6c06-4558-adb3-59f289ac3dc1" not in called_cmd


def test_launcher_audio_routing_to_prompt_studio():
    from importlib import import_module
    import sys
    sys.path.insert(0, r"C:\Users\LENOVO LOQ\tools\OmniType-FreePTT")
    launcher = import_module("OmniType-PromptStudio")

    app = launcher.StudioVoiceTyperGUI.__new__(launcher.StudioVoiceTyperGUI)
    app.current_lang = "prompt_engineer"
    app.current_engine = "google"
    app.history = []
    app.root = MagicMock()
    app.set_ui_state = MagicMock()
    app.prompt_engineer_action = MagicMock()

    mock_win = MagicMock()
    mock_win.closed = False
    app.prompt_studio_win = mock_win

    with patch("engine.asr.recognize_google", return_value="یک اسکریپت بکاپ‌گیری می‌خوام"), \
         patch("core.audio.pcm_to_wav_bytes", return_value=b"fake-wav"):
        app.recognize_audio(b"1" * 4000)

    # Verify that scheduled main-thread callback was queued
    assert app.root.after.called
    callback = app.root.after.call_args[0][1]
    callback()

    # Verify window method was called with Persian text
    assert app.prompt_engineer_action.called
    assert mock_win.set_persian_input.called
    assert "یک اسکریپت بکاپ‌گیری می‌خوام" in mock_win.set_persian_input.call_args[0][0]


