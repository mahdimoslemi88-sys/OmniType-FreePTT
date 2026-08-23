"""توقف/ادامه خودکار ویدیو و موزیک هنگام صحبت (Media Auto-Pause).

با ارسال کلید Media Play/Pause (VK_MEDIA_PLAY_PAUSE) به ویندوز —
روی YouTube، Spotify، VLC، مرورگرها و اکثر پلیرها کار می‌کند.
"""
import ctypes

VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long), ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_ushort)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT), ("hi", _HARDWAREINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", _INPUTUNION)]


def send_media_play_pause():
    """ارسال کلید Media Play/Pause (toggle) به سیستم."""
    try:
        extra = ctypes.c_ulong(0)
        inputs = (_INPUT * 2)()
        for i in range(2):
            inputs[i].type = INPUT_KEYBOARD
            inputs[i].ki.wVk = VK_MEDIA_PLAY_PAUSE
            inputs[i].ki.wScan = 0
            inputs[i].ki.dwFlags = KEYEVENTF_KEYUP if i == 1 else 0
            inputs[i].ki.time = 0
            inputs[i].ki.dwExtraInfo = ctypes.pointer(extra)
        ctypes.windll.user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(_INPUT))
    except Exception:
        pass


class MediaController:
    """مدیریت توقف/ادامه رسانه هنگام ضبط.

    فقط اگر خود برنامه رسانه را متوقف کرده باشد آن را ادامه می‌دهد
    (بنابراین موزیکی که از قبل متوقف بود، پخش نمی‌شود).
    """

    def __init__(self, enabled=True):
        self._enabled = bool(enabled)
        self._paused = False

    @property
    def is_enabled(self):
        return self._enabled

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)

    def pause(self):
        if not self._enabled:
            return
        self._paused = True
        send_media_play_pause()

    def resume(self):
        if not self._enabled or not self._paused:
            return
        self._paused = False
        send_media_play_pause()

    def reset(self):
        self._paused = False
