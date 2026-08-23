"""موتور ترجمه هوشمند (Deep-Translator + Universal LLM Engine)."""
import requests

from core.config import GEMINI_API_KEY, get_llm_candidates

# وارد کردن deep-translator (ترجمه رایگان گوگل)
try:
    from deep_translator import GoogleTranslator
    HAS_DEEP_TRANSLATOR = True
except ImportError:
    HAS_DEEP_TRANSLATOR = False


class LLMTranslatorEngine:
    """ترجمه روان و دقیق با پشتیبانی از موتور فعال (Groq / OpenAI / OpenRouter / محلی)."""

    @classmethod
    def translate(cls, text, mode="fa_to_en", style="tech"):
        if not text or not text.strip():
            return ""

        text = text.strip()

        # ۱. موتور اول: Google Translate رایگان (deep-translator) — دقیق و پایدار
        #    (طبق بازخورد کاربر، ترجمه موتورهایی مثل Groq کیفیت پایینی دارد،
        #     بنابراین ترجمه به‌صورت پیش‌فرض با گوگل انجام می‌شود.)
        try:
            translated = cls._translate_deep_translator(text, mode=mode)
            if translated:
                return translated
        except Exception as e:
            print(f"Deep Translator failed: {e}")

        # ۲. موتور دوم: LLMهای فعال به ترتیب اولویت
        for cfg in get_llm_candidates():
            if cfg["api_key"] or "localhost" in cfg["base_url"] or "127.0.0.1" in cfg["base_url"]:
                try:
                    translated = cls._translate_custom_openai(text, mode=mode, style=style, cfg=cfg)
                    if translated:
                        return translated
                except Exception as e:
                    print(f"Custom LLM translation failed: {e}. Trying next...")

        # ۳. موتور سوم (Google AI Studio Gemini API)
        if GEMINI_API_KEY:
            try:
                translated = cls._translate_gemini(text, mode=mode)
                if translated:
                    return translated
            except Exception as e:
                print(f"Gemini API translation failed: {e}")

        # ۴. موتور چهارم — فریبک گوگل (ممکن است 429 بدهد)
        try:
            translated = cls._translate_google_free(text, mode=mode)
            if translated:
                return translated
        except Exception as e:
            print(f"Google Free Translate failed: {e}")

        return text

    @classmethod
    def _translate_custom_openai(cls, text, mode="fa_to_en", style="tech", cfg=None):
        if cfg is None:
            from core.config import get_llm_config
            cfg = get_llm_config()
        base_url = cfg["base_url"].rstrip('/') or "https://api.groq.com/openai/v1"
        url = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if cfg["api_key"]:
            headers["Authorization"] = f"Bearer {cfg['api_key']}"

        system_prompt = (
            "You are an expert translator. Translate the text accurately and fluently. "
            "Output ONLY the final translated text without any explanation, markdown formatting, or quotes."
        )
        if mode == "fa_to_en":
            system_prompt += " Translate from Persian to English. Preserve technical words like Python, VS Code, Git, Docker, API."
        else:
            system_prompt += " Translate from English to Persian (Farsi)."

        payload = {
            "model": cfg["model"] or "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                content = content[1:-1].strip()
            return content
        raise Exception(f"Custom LLM API status {res.status_code}: {res.text[:200]}")

    @classmethod
    def _translate_deep_translator(cls, text, mode="fa_to_en"):
        """ترجمه با deep-translator (پایدار و رایگان)."""
        if not HAS_DEEP_TRANSLATOR:
            raise Exception("deep-translator not installed")

        src = "fa" if mode == "fa_to_en" else "en"
        dest = "en" if mode == "fa_to_en" else "fa"

        # تقسیم متن‌های طولانی به قطعات ۴۵۰۰ کاراکتری (محدودیت API)
        chunks = []
        while text:
            if len(text) <= 4500:
                chunks.append(text)
                break
            # ترجیح قطع در نقطه جدید خط
            cut = text.rfind("\n", 0, 4500)
            if cut < 1000:
                cut = text.rfind(" ", 0, 4500)
            if cut < 100:
                cut = 4500
            chunks.append(text[:cut])
            text = text[cut:].lstrip("\n")

        translated_chunks = []
        translator = GoogleTranslator(source=src, target=dest)
        for chunk in chunks:
            if not chunk.strip():
                translated_chunks.append("")
                continue
            result = translator.translate(chunk)
            translated_chunks.append(result.strip() if result else "")

        return "\n".join(translated_chunks).strip()

    @classmethod
    def _translate_google_free(cls, text, mode="fa_to_en"):
        """ترجمه با Google Translate Free (ممکن است 429 بدهد)."""
        src = "fa" if mode == "fa_to_en" else "en"
        dest = "en" if mode == "fa_to_en" else "fa"

        # تقسیم متن‌های طولانی به قطعات ۸۰۰ کاراکتری
        chunks = []
        while text:
            if len(text) <= 800:
                chunks.append(text)
                break
            cut = text.rfind("\n", 0, 800)
            if cut < 200:
                cut = text.rfind(" ", 0, 800)
            if cut < 50:
                cut = 800
            chunks.append(text[:cut])
            text = text[cut:].lstrip("\n")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        translated_chunks = []
        for chunk in chunks:
            if not chunk.strip():
                translated_chunks.append("")
                continue

            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={dest}&dt=t&q={requests.utils.quote(chunk)}"
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                result = res.json()
                sentences = result[0]
                chunk_trans = "".join([s[0] for s in sentences if s and len(s) > 0 and s[0]])
                translated_chunks.append(chunk_trans.strip())
            else:
                raise Exception(f"Google translate API status {res.status_code}")

        return "\n".join(translated_chunks).strip()

    @classmethod
    def _translate_gemini(cls, text, mode="fa_to_en"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        prompt_text = f"Translate the following text to {'English' if mode == 'fa_to_en' else 'Persian'}. Return ONLY the translated string without quotes or notes:\n{text}"
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        raise Exception(f"Gemini API status {res.status_code}")
