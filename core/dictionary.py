"""مدیریت واژه‌نامه تخصصی اصطلاحات فنی (Custom Dictionary Engine)."""
import json
import os
import re

from core.paths import app_base_dir


class CustomDictionaryManager:
    """مدیریت واژه‌نامه تخصصی اصطلاحات، لغات انگلیسی و جایگزینی هوشمند."""

    def __init__(self, file_path="custom_dictionary.json"):
        self.file_path = os.path.join(app_base_dir(), file_path)
        self.prompts = []
        self.replacements = {}
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.prompts = data.get("prompts", [])
                    self.replacements = data.get("replacements", {})
            except Exception as e:
                print(f"Error loading custom_dictionary.json: {e}")
                self.load_defaults()
        else:
            self.load_defaults()

    def load_defaults(self):
        self.prompts = ['Python', 'VS Code', 'Next.js', 'TailwindCSS', 'PyTorch',
                        'Docker', 'Kubernetes', 'Faster-Whisper', 'Groq', 'API', 'OmniType']
        self.replacements = {
            'پایتون': 'Python',
            'وی اس کد': 'VS Code',
            'نکست جی اس': 'Next.js',
            'تیلویند': 'TailwindCSS',
            'داکر': 'Docker',
            'کوبارنتیس': 'Kubernetes',
            'فست ویسپر': 'Faster-Whisper',
            'گروک': 'Groq',
            'ای پی ای': 'API',
        }
        self.save()

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({"prompts": self.prompts, "replacements": self.replacements},
                          f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving custom_dictionary.json: {e}")

    def get_prompt_string(self):
        if self.prompts:
            return "واژگان تخصصی: " + ", ".join(self.prompts) + "."
        return ""

    def apply_replacements(self, text):
        if not text:
            return text
        for fa_word, en_word in self.replacements.items():
            pattern = re.compile(re.escape(fa_word), re.IGNORECASE)
            text = pattern.sub(en_word, text)
        return text

    def add_term(self, en_term, fa_term=""):
        en_term = en_term.strip()
        fa_term = fa_term.strip()
        if en_term and en_term not in self.prompts:
            self.prompts.append(en_term)
        if fa_term and en_term:
            self.replacements[fa_term] = en_term
        self.save()

    def remove_term(self, en_term):
        if en_term in self.prompts:
            self.prompts.remove(en_term)
        to_delete = [fa for fa, en in self.replacements.items() if en == en_term]
        for fa in to_delete:
            del self.replacements[fa]
        self.save()


CUSTOM_DICT = CustomDictionaryManager()
