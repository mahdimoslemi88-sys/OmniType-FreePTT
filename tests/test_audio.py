"""تست‌های core/audio.py — تبدیل PCM به WAV و محاسبهٔ سطح صدا."""
import io
import struct
import wave

from core.audio import CHANNELS, RATE, get_input_level, pcm_to_wav_bytes


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


# ── محاسبهٔ سطح صدا ────────────────────────────────────────────────


def test_input_level_silence_is_zero():
    assert get_input_level(b"\x00\x00" * 64) == 0.0


def test_input_level_empty_is_zero():
    assert get_input_level(b"") == 0.0


def test_input_level_grows_with_amplitude():
    quiet = struct.pack("<64h", *([800] * 64))
    loud = struct.pack("<64h", *([8000] * 64))
    assert get_input_level(quiet) > 0.0
    assert get_input_level(loud) > get_input_level(quiet)
    assert get_input_level(loud) > 0.9


def test_input_level_clamped_to_one():
    full = struct.pack("<64h", *([32000] * 64))
    assert get_input_level(full) == 1.0
