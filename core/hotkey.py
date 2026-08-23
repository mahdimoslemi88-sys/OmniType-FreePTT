"""ابزارهای کلید میانبر — تشخیص نگه‌داشته شدن کلیدها با Win32 GetAsyncKeyState."""
import ctypes

try:
    import keyboard
except ImportError:
    keyboard = None

# نگاشت به کدهای مجازی ویندوز
VK_MAP = {
    "ctrl": 0x11, "control": 0x11, "leftctrl": 0xA2, "rightctrl": 0xA3,
    "shift": 0x10, "leftshift": 0xA0, "rightshift": 0xA1,
    "alt": 0x12, "leftalt": 0xA4, "rightalt": 0xA5,
    "windows": 0x5B, "win": 0x5B, "leftwindows": 0x5B, "rightwindows": 0x5C,
    "capslock": 0x14, "caps_lock": 0x14,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74,
    "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79,
    "f11": 0x7A, "f12": 0x7B,
    "space": 0x20, "tab": 0x09, "insert": 0x2D, "delete": 0x2E, "`": 0xC0,
}


def is_down(k):
    """آیا کلید k در حال حاضر پایین است؟"""
    vk = VK_MAP.get(k)
    if vk:
        try:
            return (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000) != 0
        except Exception:
            return False
    try:
        return keyboard.is_pressed(k) if keyboard else False
    except Exception:
        return False


def is_hotkey_held(hotkey):
    """تشخیص پایدار نگه داشته شدن کلید یا ترکیب کلیدها در ویندوز."""
    hk = hotkey.lower().replace(" ", "")
    keys = hk.split("+")
    if len(keys) == 1:
        return is_down(keys[0])
    # برای ترکیبات، تا زمانی که کلیدها نگه داشته شده‌اند ضبط ادامه دارد
    return any(is_down(k) for k in keys)
