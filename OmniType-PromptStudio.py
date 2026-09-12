"""Launch the existing OmniType app plus Prompt Studio, without modifying its source.

Run ONLY this launcher, not both apps simultaneously (global microphone/hotkey conflict).
Open the studio with Ctrl+Alt+P or the existing AI prompt button in Quick Actions.
This action no longer automatically reads/replaces selected text: use explicit paste/copy.
The old voice-mode prompt_engineer remains legacy and is NOT free-only.

The accompanying HTML contains install, privacy and Windows verification instructions.
"""
import sys
import ctypes

# Preserve windowed-exe safety for print statements in the original app.
class _NullOutput:
    def write(self, _text):
        pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = _NullOutput()
if sys.stderr is None:
    sys.stderr = _NullOutput()

if sys.platform == 'win32':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

from gui.app import VoiceTyperGUI
from prompt_studio_window import PromptStudioWindow

class StudioVoiceTyperGUI(VoiceTyperGUI):
    def prompt_engineer_action(self):
        win = getattr(self, 'prompt_studio_win', None)
        if win is not None and not win.closed:
            win.deiconify()
            win.lift()
            win.focus_force()
            return
        self.prompt_studio_win = PromptStudioWindow(self)

    def start_recording(self, mode='hotkey'):
        if getattr(self, '_prompt_studio_audio_busy', False):
            return
        return super().start_recording(mode)

    def recognize_audio(self, raw_data):
        if self.current_lang == "prompt_engineer":
            if not raw_data or len(raw_data) < 2000:
                self.set_ui_state("idle")
                return
            try:
                from core.audio import pcm_to_wav_bytes
                from core.dictionary import CUSTOM_DICT
                from core.normalizer import PersianNormalizer
                from engine.asr import recognize_google, transcribe_custom_api
                from engine.local_whisper import LOCAL_WHISPER

                wav_bytes = pcm_to_wav_bytes(raw_data)

                if self.current_engine == "local":
                    text = LOCAL_WHISPER.transcribe(wav_bytes, lang="fa", prompt="", task="transcribe")
                elif self.current_engine in ("google", ""):
                    text = recognize_google(raw_data, lang="fa")
                else:
                    try:
                        text = transcribe_custom_api(wav_bytes, lang_code="fa", prompt="", preferred_engine=self.current_engine)
                    except Exception:
                        text = recognize_google(raw_data, lang="fa")

                if text:
                    text = PersianNormalizer.normalize(text)
                    text = CUSTOM_DICT.apply_replacements(text)
                    self.history.append(f"🎯 [Prompt Studio] {text}")

                    def _open_studio_with_text(t):
                        self.prompt_engineer_action()
                        win = getattr(self, 'prompt_studio_win', None)
                        if win is not None and not win.closed:
                            win.set_persian_input(t)
                            win.deiconify()
                            win.lift()
                            win.focus_force()

                    self.root.after(0, lambda: _open_studio_with_text(text))
                    self.set_ui_state("success")
                else:
                    self.set_ui_state("idle")
            except Exception:
                self.set_ui_state("idle")
            return

        return super().recognize_audio(raw_data)

    def quit_app(self):
        win = getattr(self, 'prompt_studio_win', None)
        if win is not None:
            win.close()
        return super().quit_app()

if __name__ == '__main__':
    StudioVoiceTyperGUI().run()
