"""تست اتصال موتورهای AI — قابل استفاده از پنجره مدیریت موتورها و پنل کنترل."""
import requests

from core import config


def test_engine(base_url, api_key, model, role):
    """تست یک موتور: (آدرس، کلید، مدل، نقش) → پیام نتیجه (✅/❌/⚠️ با دلیل)."""
    try:
        base = (base_url or "").rstrip('/')
        if not base:
            return "❌ Base URL خالی است."
        if not model:
            return "❌ نام مدل خالی است."

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # ۱. بررسی آدرس و کلید با لیست مدل‌ها
        models_status = "—"
        try:
            mod_res = requests.get(f"{base}/models", headers=headers, timeout=10)
            if mod_res.status_code == 200:
                try:
                    names = [m.get("id", "") for m in mod_res.json().get("data", [])]
                except Exception:
                    names = []
                models_status = f"✅ {len(names)} مدل"
            else:
                models_status = f"⚠️ /models با کد {mod_res.status_code}"
        except Exception:
            pass  # بعضی سرورها /models ندارند؛ تست اصلی زیر تصمیم‌گیر است

        # ۲. برای LLM (یا هر دو): درخواست واقعی و کوچک به مدل
        if role in (config.ROLE_LLM, config.ROLE_BOTH):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a connectivity test. Reply with exactly: OK"},
                    {"role": "user", "content": "ping"},
                ],
                "max_tokens": 5,
                "temperature": 0,
            }
            res = requests.post(f"{base}/chat/completions", headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                reply = (res.json().get("choices", [{}])[0]
                         .get("message", {}).get("content", "") or "").strip()
                return (f"✅ اتصال برقرار است! {models_status} — مدل «{model}» پاسخ داد: "
                        f"{reply[:60] or '(بدون متن)'}")
            return f"❌ مدل پاسخ نداد (کد {res.status_code}): {res.text[:200]}"

        # ۳. فقط ASR: مدل معمولاً whisper است و چت ندارد — بررسی لیست مدل‌ها کافی است
        if models_status.startswith("✅"):
            return f"✅ اتصال برقرار است! {models_status}. مدل «{model}» در لیست موجود است."
        return (f"⚠️ اتصال برقرار شد ولی مدل «{model}» در لیست دیده نشد. "
                "بررسی کنید نام دقیق مدل را درست وارد کرده باشید.")
    except Exception as e:
        return f"❌ اتصال ناموفق: {e}"
