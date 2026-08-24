"""نرمال‌ساز متون فارسی — اصلاح حروف عربی، نیم‌فاصله‌ها، علائم و کلمات پرکننده."""
import re

# جدول تبدیل تلفظ فارسی حروف انگلیسی → حرف اصلی انگلیسی
# وقتی کاربر در حالت فارسی حرف انگلیسی را با تلفظ فارسی می‌گوید
# (مثلاً «پی» به جای «P»)، گوگل آن را به فارسی تبدیل می‌کند.
# این جدول آن را به حرف اصلی برمی‌گرداند.
_PERSIAN_LETTER_MAP = {
    'پی': 'P', 'بی': 'B', 'سی': 'C', 'دی': 'D',
    'جی': 'G', 'ایچ': 'H', 'جِی': 'J', 'کِی': 'K',    'ال': 'L', 'اِل': 'L', 'ام': 'M', 'اِم': 'M',
    'ان': 'N', 'اِن': 'N', 'اس': 'S', 'اِس': 'S',
    'تی': 'T', 'وی': 'V', 'دابلیو': 'W', 'ایکس': 'X',
    'وای': 'Y', 'زی': 'Z', 'کیو': 'Q', 'آر': 'R',
    'ار': 'R', 'اَر': 'R', 'اف': 'F', 'اِف': 'F',
    'ای': 'I', 'آی': 'I', 'اِی': 'I',
    'اُ': 'O', 'او': 'O', 'اوه': 'O',
    'جی‌آی': 'GI', 'دات': '.',
    'کاما': ',', 'اسپیس': ' ', 'اینتر': '\n', ' Space': ' ',
    'space': ' ', 'Enter': '\n', 'enter': '\n',
}

# واژه‌های رایج فارسی که با تلفظ یک حرف انگلیسی هم‌نویسه‌اند
# (مثل «بی»=بدون، «وی»=او، «ان»=آن، «او»=او، «ام»=هستم، «ار»/«سی»/«دی»=پسوند یا عدد).
# این‌ها نباید به‌تنهایی به حرف تبدیل شوند مگر اینکه متن به‌وضوح تلفظِ
# یک «رشته حروف» باشد (چند نام حرف پشت‌سرهم، مثل «بی سی دی اف»).
_PERSIAN_HOMOGRAPH_STOPLIST = {'بی', 'وی', 'او', 'ان', 'ام', 'ار', 'سی', 'دی', 'ای', 'آی'}
# حداقل تعداد نام حرف فارسی برای در نظر گرفتن متن به عنوان «تلفظ رشته حروف»
_LETTER_DICTATION_MIN = 3

# الگوهای regex برای الگوهای متداول ترکیبی حروف
_LETTER_PATTERNS = [
    (r'\b(\S+?)\s+و\s+(\S+?)\b', None),  # «A و B» → تک‌تک بررسی می‌شود
]


def convert_persian_letters_to_english(text):
    """
    تبدیل تلفظ فارسی حروف انگلیسی به حرف اصلی.
    مثال: «من می‌خوام پی‌تایپ کنم» → «من می‌خوام P تایپ کنم»
    «بی‌سی‌دی‌اف» → "BCDF"
    """
    if not text:
        return text

    # فقط اگر متن حاوی حروف/کلمات فارسی باشد اعمال کن
    if not re.search(r'[آ-ی]', text):
        return text

    # مرحله ۱: تبدیل کلمات تکی (مثل «پی» → «P»)
    words = text.split()
    # شمارش نام‌های حرف فارسی در کل متن برای تشخیص تلفظِ رشته حروف
    dictation_count = sum(1 for w in words if w.strip('.,;:!?،؛؟!') in _PERSIAN_LETTER_MAP)
    is_letter_dictation = dictation_count >= _LETTER_DICTATION_MIN

    result_words = []
    for word in words:
        # حذف علائم نگارشی از ابتدا/انتهای کلمه برای تطبیق
        clean = word.strip('.,;:!?،؛؟!')
        prefix = word[:len(word) - len(word.lstrip('.,;:!?،؛؟!'))]
        suffix = word[len(word.rstrip('.,;:!?،؛؟!')):]

        if clean in _PERSIAN_LETTER_MAP:
            # واژهٔ فارسیِ هم‌نویس با نام حرف، به‌تنهایی نباید تبدیل شود
            if clean in _PERSIAN_HOMOGRAPH_STOPLIST and not is_letter_dictation:
                result_words.append(word)
                continue
            replacement = _PERSIAN_LETTER_MAP[clean]
            result_words.append(prefix + replacement + suffix)
        else:
            result_words.append(word)

    text = ' '.join(result_words)

    # مرحله ۲: تبدیل رشته‌های ترکیبی (مثل «بی‌سی‌دی‌اف» → "BCDF")
    # فقط اگر کلمه‌ای کاملاً از حروف فارسی مشتق از حروف انگلیسی باشد
    def _replace_combo(match):
        word = match.group(0)
        if re.search(r'[آ-ی]', word) and not re.search(r'[a-zA-Z]', word):
            result = ''
            for char_word in re.split(r'[\u200c\-\s]', word):  # نیم‌فاصله یا خط تیره
                if char_word in _PERSIAN_LETTER_MAP:
                    result += _PERSIAN_LETTER_MAP[char_word]
                else:
                    return word  # اگر هر بخشی قابل تبدیل نبود، اصل را برگردان
            if result and len(result) >= 2:
                return result
        return word

    # (خط تیره هم جزو رشتهٔ ترکیبی است تا «بی-سی-دی» مثل «بی‌سی‌دی‌اف» تبدیل شود)
    text = re.sub(r'[\w\u200c-]+', _replace_combo, text)

    return text


class PersianNormalizer:
    """نرمال‌ساز قطعی متون فارسی جهت اصلاح حروف عربی، علائم نگارشی،
    نیم‌فاصله‌ها و حذف کلمات پرکننده."""

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
    def normalize_characters(cls, text):
        """اصلاح حروف عربی به فارسی"""
        for src, dst in cls.CHAR_MAP.items():
            text = text.replace(src, dst)
        return text

    @classmethod
    def fix_half_spaces(cls, text):
        """اعمال نیم‌فاصله‌های استاندارد بر اساس قواعد Regex"""
        zwnj = '\u200c'  # Zero-width non-joiner (نیم‌فاصله)

        # پیشوند «می» و «نمی»
        text = re.sub(r'\b(می|نمی)\s+([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی]+)',
                      r'\1' + zwnj + r'\2', text)

        # پسوندهای متداول (ها، های، هایی، تر، ترین)
        text = re.sub(r'([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی]+)\s+(ها|های|هایی|تر|ترین)\b',
                      r'\1' + zwnj + r'\2', text)

        # پسوند «شناسه ها» برای کلمات مختوم به «ه» (خانه ام -> خانه‌ام)
        text = re.sub(r'([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی]+ه)\s+(ام|ات|اش|ایم|اید|اند)\b',
                      r'\1' + zwnj + r'\2', text)

        return text

    @classmethod
    def fix_punctuations(cls, text):
        """اصلاح فاصله‌گذاری علائم نگارشی"""
        # حذف فاصله قبل از علائم نگارشی
        # (شامل کاما فارسی ، U+060C که قبلاً در کلاس نبود و فضابندی نمی‌شد)
        text = re.sub(r'\s+([.,،!؟:؛])', r'\1', text)

        # افزودن فاصله بعد از علائم نگارشی در صورتی که فاصله وجود نداشته باشد
        # (نقطه استثناست: lookbehind مانع خراب شدن ایمیل/URL/اعشار می‌شود:
        #  gmail.com و 3.14 دست‌نخورده می‌مانند، ولی «سلام.دنیا» → «سلام. دنیا»)
        text = re.sub(r'([،!؟:؛,])([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیa-zA-Z])', r'\1 \2', text)
        text = re.sub(r'(?<![A-Za-z0-9_.-])(\.)([آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیa-zA-Z])', r'\1 \2', text)

        # جایگزینی فاصله‌های متوالی با یک فاصله
        text = re.sub(r'[ \t]+', ' ', text)

        return text.strip()

    @classmethod
    def remove_fillers(cls, text):
        """حذف کلمات پرکننده گفتاری"""
        for pattern in cls.FILLER_WORDS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', text).strip()

    @classmethod
    def normalize(cls, text):
        """اجرای تمامی مراحل نرمال‌سازی به ترتیب قطعی"""
        if not text:
            return ""
        text = cls.normalize_characters(text)
        text = cls.remove_fillers(text)
        text = cls.fix_half_spaces(text)
        text = cls.fix_punctuations(text)
        return text
