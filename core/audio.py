"""تنظیمات فنی کارت صدا و ابزار تبدیل فرمت."""
import io
import wave

import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


def pcm_to_wav_bytes(pcm_data, sample_rate=RATE, channels=CHANNELS, sampwidth=2):
    """تبدیل بایت‌های خام PCM به فرمت استاندارد فایل صوتی WAV در حافظه."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()
