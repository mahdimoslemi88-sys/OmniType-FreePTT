"""تنظیمات برنامه — خواندن/نوشتن .env و موتورهای چندگانه AI."""
import json
import os

from core.paths import app_base_dir


def load_env():
    """خواندن فایل .env به صورت dict."""
    env_vars = {}
    env_path = os.path.join(app_base_dir(), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars


ENV = load_env()

GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")

# ── موتورهای سفارشی چندگانه (Multi-Engine) ─────────────────────
# هر موتور یک dict است:
#   name, base_url, api_key, model, role, active
#   role: "asr" (فقط تبدیل صوت) | "llm" (فقط ترجمه/پرامپت) | "both"
# ترتیب لیست = اولویت استفاده (موتور اول با اولویت بالاتر امتحان می‌شود)

ROLE_ASR = "asr"
ROLE_LLM = "llm"
ROLE_BOTH = "both"


def _normalize_engine(e):
    """تبدیل فرمت قدیمی (asr_*/llm_*) به فرمت جدید (base_url/api_key/model/role)."""
    if "model" in e and "role" in e:
        return [e]

    name = e.get("name", "Custom")
    active = bool(e.get("active"))
    has_asr = bool(e.get("asr_url") or e.get("asr_key") or e.get("asr_model"))
    has_llm = bool(e.get("llm_url") or e.get("llm_key") or e.get("llm_model"))

    engines = []
    if has_asr:
        engines.append({
            "name": f"{name} (ASR)" if has_llm else name,
            "base_url": e.get("asr_url") or e.get("llm_url") or "https://api.groq.com/openai/v1",
            "api_key": e.get("asr_key") or e.get("llm_key") or "",
            "model": e.get("asr_model") or "whisper-large-v3-turbo",
            "role": ROLE_ASR,
            "active": active and not has_llm,
        })
    if has_llm:
        engines.append({
            "name": f"{name} (LLM)" if has_asr else name,
            "base_url": e.get("llm_url") or e.get("asr_url") or "https://api.groq.com/openai/v1",
            "api_key": e.get("llm_key") or e.get("asr_key") or "",
            "model": e.get("llm_model") or "openai/gpt-oss-20b",
            "role": ROLE_LLM,
            "active": active and not has_asr,
        })
    if not engines:
        engines = [{
            "name": name,
            "base_url": e.get("base_url", "https://api.groq.com/openai/v1"),
            "api_key": e.get("api_key", ""),
            "model": e.get("model", "whisper-large-v3-turbo"),
            "role": ROLE_BOTH,
            "active": active,
        }]
    return engines


def _build_default_engines():
    """ساخت موتور پیش‌فرض از مقادیر قدیمی CUSTOM_* (سازگاری با نسخه‌های قبل)."""
    legacy_key = (ENV.get("CUSTOM_LLM_API_KEY") or ENV.get("CUSTOM_ASR_API_KEY")
                  or ENV.get("GROQ_API_KEY") or "")
    # مدل llama-3.3-70b-versatile در آگوست ۲۰۲۶ از گروک حذف شده؛
    # به‌جای آن از gpt-oss-20b (مدل فعال فعلی) استفاده می‌کنیم.
    legacy_llm_model = ENV.get("CUSTOM_LLM_MODEL", "")
    if legacy_llm_model in ("llama-3.3-70b-versatile", ""):
        legacy_llm_model = "openai/gpt-oss-20b"
    legacy_url = ENV.get("CUSTOM_ASR_BASE_URL", "https://api.groq.com/openai/v1")
    return [
        {
            "name": "Groq Cloud (ASR)",
            "base_url": legacy_url,
            "api_key": legacy_key,
            "model": ENV.get("CUSTOM_ASR_MODEL", "whisper-large-v3-turbo"),
            "role": ROLE_ASR,
            "active": False,
        },
        {
            "name": "Groq Cloud (LLM)",
            "base_url": ENV.get("CUSTOM_LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            "api_key": legacy_key,
            "model": legacy_llm_model,
            "role": ROLE_LLM,
            "active": False,
        },
    ]


def _load_engines():
    """بارگذاری لیست موتورها از .env (کلید ENGINES به صورت JSON) و نرمال‌سازی."""
    raw = ENV.get("ENGINES", "")
    engines = []
    if raw:
        try:
            parsed = json.loads(raw)
            for e in parsed:
                engines.extend(_normalize_engine(e))
        except Exception:
            engines = []
    if not engines:
        engines = _build_default_engines()
    # اطمینان از اینکه فقط یک موتور active است
    if not any(e.get("active") for e in engines):
        engines[0]["active"] = True
    return engines


ENGINES = _load_engines()


def get_active_engine():
    """برگرداندن موتور فعال (اولین موتور دارای active=True)."""
    global ENGINES
    if not ENGINES:
        ENGINES = _load_engines()
    for e in ENGINES:
        if e.get("active"):
            return e
    ENGINES[0]["active"] = True
    return ENGINES[0]


def get_asr_candidates():
    """لیست موتورهای ASR به ترتیب اولویت (فقط موتورهای دارای کلید)."""
    return [e for e in ENGINES if e.get("role") in (ROLE_ASR, ROLE_BOTH) and e.get("api_key")]


def get_llm_candidates():
    """لیست موتورهای LLM به ترتیب اولویت (فقط موتورهای دارای کلید)."""
    return [e for e in ENGINES if e.get("role") in (ROLE_LLM, ROLE_BOTH) and e.get("api_key")]


def get_asr_config():
    """تنظیمات اولین موتور ASR در اولویت."""
    cands = get_asr_candidates()
    if not cands:
        return {"base_url": "", "api_key": "", "model": ""}
    e = cands[0]
    return {"base_url": e.get("base_url", ""), "api_key": e.get("api_key", ""), "model": e.get("model", "")}


def get_llm_config():
    """تنظیمات اولین موتور LLM در اولویت."""
    cands = get_llm_candidates()
    if not cands:
        return {"base_url": "", "api_key": "", "model": ""}
    e = cands[0]
    return {"base_url": e.get("base_url", ""), "api_key": e.get("api_key", ""), "model": e.get("model", "")}


def set_active_engine(name):
    """فعال‌سازی یک موتور با نام مشخص و ذخیره آن."""
    global ENGINES
    for e in ENGINES:
        e["active"] = (e.get("name") == name)
    save_engines(ENGINES)


def move_engine(index, direction):
    """جابه‌جایی یک موتور در لیست اولویت (direction: -1 بالا، +1 پایین)."""
    global ENGINES
    new_index = index + direction
    if not (0 <= new_index < len(ENGINES)):
        return False
    ENGINES[index], ENGINES[new_index] = ENGINES[new_index], ENGINES[index]
    save_engines(ENGINES)
    return True


def save_engines(engines):
    """ذخیره لیست موتورها در .env (کلید ENGINES)."""
    global ENGINES
    if not any(e.get("active") for e in engines):
        engines[0]["active"] = True
    ENGINES = engines
    save_env_dict({"ENGINES": json.dumps(engines, ensure_ascii=False)})


# برای سازگاری با کدهای قدیمی که از CUSTOM_* استفاده می‌کنند
CUSTOM_ASR_BASE_URL = ENV.get("CUSTOM_ASR_BASE_URL", "https://api.groq.com/openai/v1")
CUSTOM_ASR_API_KEY = ENV.get("CUSTOM_ASR_API_KEY", "")
CUSTOM_ASR_MODEL = ENV.get("CUSTOM_ASR_MODEL", "whisper-large-v3-turbo")

CUSTOM_LLM_BASE_URL = ENV.get("CUSTOM_LLM_BASE_URL", "https://api.groq.com/openai/v1")
CUSTOM_LLM_API_KEY = ENV.get("CUSTOM_LLM_API_KEY", "")
CUSTOM_LLM_MODEL = ENV.get("CUSTOM_LLM_MODEL", "llama-3.3-70b-versatile")


def save_env_dict(updates):
    """ذخیره/به‌روزرسانی کلیدهای .env و اعمال آن‌ها در حافظه."""
    global ENV, CUSTOM_ASR_BASE_URL, CUSTOM_ASR_API_KEY, CUSTOM_ASR_MODEL
    global CUSTOM_LLM_BASE_URL, CUSTOM_LLM_API_KEY, CUSTOM_LLM_MODEL, GEMINI_API_KEY

    for k, v in updates.items():
        ENV[k] = v

    CUSTOM_ASR_BASE_URL = ENV.get("CUSTOM_ASR_BASE_URL", "https://api.groq.com/openai/v1")
    CUSTOM_ASR_API_KEY = ENV.get("CUSTOM_ASR_API_KEY", "")
    CUSTOM_ASR_MODEL = ENV.get("CUSTOM_ASR_MODEL", "whisper-large-v3-turbo")

    CUSTOM_LLM_BASE_URL = ENV.get("CUSTOM_LLM_BASE_URL", "https://api.groq.com/openai/v1")
    CUSTOM_LLM_API_KEY = ENV.get("CUSTOM_LLM_API_KEY", "")
    CUSTOM_LLM_MODEL = ENV.get("CUSTOM_LLM_MODEL", "llama-3.3-70b-versatile")

    GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")

    env_path = os.path.join(app_base_dir(), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    key_indices = {}
    for i, line in enumerate(lines):
        if "=" in line and not line.strip().startswith("#"):
            k = line.split("=", 1)[0].strip()
            key_indices[k] = i

    for k, v in updates.items():
        if k in key_indices:
            lines[key_indices[k]] = f"{k}={v}\n"
        else:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(f"{k}={v}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
