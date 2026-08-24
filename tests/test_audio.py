"""تست‌های core/audio.py — تبدیل PCM به WAV معتبر."""
import io
import wave

from core.audio import CHANNELS, RATE, pcm_to_wav_bytes


def _open(data):
    return wave.open(io.BytesIO(data), "rb")


def test_returns_valid_wav_container():
    data = pcm_to_wav_bytes(b"\x00\x01" * 100)
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WAVE"


def test_default_params():
    data = pcm_to_wav_bytes(b"\x00" * 400)
    w = _open(data)
    assert w.getnchannels() == CHANNELS == 1
    assert w.getsampwidth() == 2
    assert w.getframerate() == RATE == 16000


def test_frames_round_trip():
    frames = b"\x01\x02\x03\x04" * 50
    data = pcm_to_wav_bytes(frames)
    w = _open(data)
    assert w.readframes(w.getnframes()) == frames


def test_empty_input_yields_valid_empty_wav():
    data = pcm_to_wav_bytes(b"")
    w = _open(data)
    assert w.getnframes() == 0
    assert data[:4] == b"RIFF"


def test_custom_params_respected():
    data = pcm_to_wav_bytes(b"\x00" * 200, sample_rate=48000, channels=2, sampwidth=2)
    w = _open(data)
    assert w.getnchannels() == 2
    assert w.getframerate() == 48000
