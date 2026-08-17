import sys
import re

# تنظیم کدینگ خروجی ترمینال
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class PersianNormalizer:
    """
    نرمالساز قطعی متون فارسی جهت اصلاح حروف عربی، علائم نگارشی، نیم‌فاصله‌ها و حذف کلمات پرکننده.
    """
    
    # جدول جایگزینی حروف عربی به فارسی
    CHAR_MAP = {
        'ي': 'ی',
        'ى': 'ی',
        'ك': 'ک',
        'ئ': 'ئ',
        'إ': 'ا',
        'أ': 'ا',
        'آ': 'آ',
        'ة': 'ه',
    }
    
    # کلمات پرکننده متداول جهت پاکسازی
    FILLER_WORDS = [
        r'\bامم+\b',
        r'\bعه+\b',
        r'\bاهم+\b',
        r'\bاووم+\b',
    ]

    @classmethod
    def normalize_characters(cls, text: str) -> str:
        """اصلاح حروف عربی به فارسی"""
        for src, dst in cls.CHAR_MAP.items():
            text = text.replace(src, dst)
        return text

    @classmethod
    def fix_half_spaces(cls, text: str) -> str:
        """اعمال نیم‌فاصله‌های استاندارد بر اساس قواعد Regex"""
        zwnj = '\u200c' # Zero-width non-joiner (نیم‌فاصله)
        
        # پیشوند «می» و «نمی»
        text = re.sub(r'\b(می|نمی)\s+([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی]+)', r'\1' + zwnj + r'\2', text)
        
        # پسوندهای متداول (ها، های، هایی، تر، ترین)
        text = re.sub(r'([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی]+)\s+(ها|های|هایی|تر|ترین)\b', r'\1' + zwnj + r'\2', text)
        
        # پسوند «شناسه ها» برای کلمات مختوم به «ه» (خانه ام -> خانه‌ام)
        text = re.sub(r'([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی]+ه)\s+(ام|ات|اش|ایم|اید|اند)\b', r'\1' + zwnj + r'\2', text)
        
        return text

    @classmethod
    def fix_punctuations(cls, text: str) -> str:
        """اصلاح فاصله‌گذاری علائم نگارشی"""
        # حذف فاصله قبل از علائم نگارشی
        text = re.sub(r'\s+([.,!؟:؛])', r'\1', text)
        
        # افزودن فاصله بعد از علائم نگارشی در صورتی که فاصله وجود نداشته باشد
        text = re.sub(r'([.,!؟:؛])([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیa-zA-Z])', r'\1 \2', text)
        
        # جایگزینی فاصله‌های متوالی با یک فاصله
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()

    @classmethod
    def remove_fillers(cls, text: str) -> str:
        """حذف کلمات پرکننده گفتاری"""
        for pattern in cls.FILLER_WORDS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', text).strip()

    @classmethod
    def normalize(cls, text: str) -> str:
        """اجرای تمامی مراحل نرمالسازی به ترتیب قطعی"""
        if not text:
            return ""
        
        text = cls.normalize_characters(text)
        text = cls.remove_fillers(text)
        text = cls.fix_half_spaces(text)
        text = cls.fix_punctuations(text)
        
        return text

if __name__ == "__main__":
    test_cases = [
        "امم می شود کتاب ها را بیاوری؟",
        "علي و كمال به خانه های خود رفتند .",
        "عه این کار نمی شود که انجام داد !",
    ]
    print("--- تست نرمالساز فارسی ---")
    for t in test_cases:
        print(f"اصلی: {t}")
        print(f"اصلاح شده: {PersianNormalizer.normalize(t)}")
        print("-" * 30)
