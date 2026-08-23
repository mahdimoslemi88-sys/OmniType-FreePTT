"""تبدیل درخواست‌های گفتاری یا متنی به پرامپت‌های مهندسی‌شده AI."""
import requests

from core.config import GEMINI_API_KEY, get_llm_candidates


class AIPromptEngineer:
    """تبدیل درخواست‌های گفتاری یا متنی فارسی به پرامپت‌های مهندسی‌شده و ساختاریافته انگلیسی."""

    @classmethod
    def generate_engineered_prompt(cls, user_text):
        if not user_text or not user_text.strip():
            return ""

        user_text = user_text.strip()
        system_prompt = (
            "You are an elite AI Prompt Engineer. The user will provide a raw request or idea in Persian or English. "
            "Your task is to transform their raw input into a world-class, highly structured, clear, and professional AI Prompt in English. "
            "Format the prompt with clear sections:\n"
            "- **Role / Persona**\n"
            "- **Task Objective & Context**\n"
            "- **Key Requirements & Steps**\n"
            "- **Output Format & Constraints**\n"
            "Output ONLY the final engineered prompt text in English without any meta commentary, intro text, or quotes."
        )

        # ۱. LLMهای فعال به ترتیب اولویت
        candidates = get_llm_candidates()
        last_err = None
        for cfg in candidates:
            has_llm = bool(cfg["api_key"]) or "localhost" in cfg["base_url"] or "127.0.0.1" in cfg["base_url"]
            if not has_llm:
                continue
            try:
                url = f"{cfg['base_url'].rstrip('/')}/chat/completions"
                headers = {"Content-Type": "application/json"}
                if cfg["api_key"]:
                    headers["Authorization"] = f"Bearer {cfg['api_key']}"
                payload = {
                    "model": cfg["model"] or "openai/gpt-oss-20b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text},
                    ],
                    "temperature": 0.3,
                }
                res = requests.post(url, headers=headers, json=payload, timeout=15)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"].strip()
                last_err = f"LLM API status {res.status_code}: {res.text[:200]}"
            except Exception as e:
                last_err = str(e)
                print(f"Custom Prompt Engineer ({cfg.get('name')}) failed: {e}")

        # ۲. Google Gemini
        if GEMINI_API_KEY:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
                headers = {"Content-Type": "application/json"}
                prompt = f"{system_prompt}\n\nUser Request: {user_text}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = requests.post(url, headers=headers, json=payload, timeout=8)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                raise Exception(f"Gemini status {res.status_code}")
            except Exception as e:
                print(f"Gemini Prompt Engineer failed: {e}")
                raise

        raise RuntimeError(
            f"هیچ موتور LLM پاسخ نداد ({last_err or 'پیکربندی نشده'}). "
            "لطفاً از «مدیریت موتورها» یک موتور با کلید و مدل معتبر اضافه کنید."
        )
