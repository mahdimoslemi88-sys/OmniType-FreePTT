"""مدیریت مدل Faster-Whisper محلی (Cold-Start & VRAM)."""
import gc
import io
import threading

HAS_FASTER_WHISPER = False
try:
    import ctranslate2
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    pass

BASE_WHISPER_PROMPT = "متن پیاده‌سازی شده صحبت‌های فارسی همراه با اصطلاحات و کلمات انگلیسی مانند Python, Code, Download, VS Code."


class LocalWhisperManager:
    """مدیریت لودینگ پس‌زمینه، اجرای مدل محلی و آزادسازی حافظه VRAM برای گیمینگ."""

    def __init__(self):
        self.model = None
        self.is_loading = False
        self.load_error = None

    def preload_model_async(self, model_size="large-v3-turbo"):
        if self.model is not None or self.is_loading:
            return
        self.is_loading = True
        threading.Thread(target=self._load_worker, args=(model_size,), daemon=True).start()

    def _load_worker(self, model_size):
        try:
            device = "cuda" if (HAS_FASTER_WHISPER and ctranslate2.get_cuda_device_count() > 0) else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            print(f"Loading local Faster-Whisper model '{model_size}' on {device} ({compute_type})...")
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            print("Local Faster-Whisper model loaded successfully!")
        except Exception as e:
            self.load_error = str(e)
            print(f"Error loading local model '{model_size}': {e}. Falling back to 'base'...")
            try:
                device = "cuda" if (HAS_FASTER_WHISPER and ctranslate2.get_cuda_device_count() > 0) else "cpu"
                self.model = WhisperModel("base", device=device, compute_type="int8")
                print("Fallback 'base' model loaded successfully!")
            except Exception as ex:
                self.load_error = str(ex)
        finally:
            self.is_loading = False

    def unload_model(self):
        """آزادسازی ۱۰۰ درصدی حافظه VRAM کارت گرافیک برای بازی و برنامه‌های سنگین."""
        if self.model is not None or self.is_loading:
            print("Unloading local Faster-Whisper model and freeing VRAM...")
            self.model = None
            self.is_loading = False
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            print("VRAM successfully released!")
            return True
        return False

    def transcribe(self, wav_bytes, lang="fa", prompt=None, task="transcribe"):
        if self.model is None:
            if self.is_loading:
                raise Exception("مدل محلی هنوز در حال بارگذاری است، لطفاً چند لحظه صبر کنید...")
            else:
                self.preload_model_async()
                raise Exception("مدل محلی در حال استارت اولیه است...")

        audio_stream = io.BytesIO(wav_bytes)
        segments, info = self.model.transcribe(
            audio_stream,
            language=lang,
            task=task,
            initial_prompt=prompt or BASE_WHISPER_PROMPT,
            beam_size=5,
        )
        text = " ".join([seg.text for seg in segments]).strip()
        return text


LOCAL_WHISPER = LocalWhisperManager()
