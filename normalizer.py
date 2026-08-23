"""نرمال‌ساز فارسی — re-export برای سازگاری با نسخه قدیمی (اکنون در core/normalizer)."""
from core.normalizer import PersianNormalizer  # noqa: F401

if __name__ == "__main__":
    test_cases = [
        "امم می شود کتاب ها را بیاوری؟",
        "علي و كمال به خانه های خود رفتند .",
        "عه این کار نمی شود که انجام داد !",
    ]
    print("--- تست نرمال‌ساز فارسی ---")
    for t in test_cases:
        print(f"اصلی: {t}")
        print(f"اصلاح شده: {PersianNormalizer.normalize(t)}")
        print("-" * 30)
