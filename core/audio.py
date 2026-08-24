"""تنظیمات فنی کارت صدا، لیست دستگاه‌ها و محاسبهٔ سطح صدا."""
import io
import math
import struct
import wave

import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# آستانه‌ای که RMS به آن می‌رسد تا سطح=۱ گزارش شود (حساسیت نشانگر)
_LEVEL_FULL_RMS = 8000.0


def pcm_to_wav_bytes(pcm_data, sample_rate=RATE, channels=CHANNELS, sampwidth=2):
    """تبدیل بایت‌های خام PCM به فرمت استاندارد فایل صوتی WAV در حافظه."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def list_input_devices(pa=None):
    """لیست دستگاه‌های دارای ورودی صدا: [(index, name), ...].

    اگر نمونهٔ pyaudio داده نشود، یکی به‌صورت موقت ساخته و بسته می‌شود.
    """
    close = False
    if pa is None:
        try:
            pa = pyaudio.PyAudio()
            close = True
        except Exception:
            return []
    try:
        result = []
        for i in range(pa.get_device_count()):
            try:
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    name = info.get("name", f"Device {i}")
                    result.append((i, name))
            except Exception:
                continue
        return result
    finally:
        if close:
            try:
                pa.terminate()
            except Exception:
                pass


def get_input_level(pcm_data):
    """سطح حجم صدای یک بافر PCM-16 (مونو) به صورت 0..1 بر اساس RMS."""
    if not pcm_data:
        return 0.0
    n = len(pcm_data) // 2
    if n == 0:
        return 0.0
    samples = struct.unpack("<%dh" % n, pcm_data[: n * 2])
    rms = math.sqrt(sum((s * s) for s in samples) / n)
    level = min(1.0, rms / _LEVEL_FULL_RMS)
    return level
