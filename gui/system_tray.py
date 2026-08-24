"""آیکون System Tray ویندوز — در ناحیه هیدن‌آیکون‌های تسک‌بار با منوی کامل."""
import threading
import time

from PIL import Image, ImageDraw

from core.paths import find_icon_path

HAS_SYSTRAY = False
try:
    import pystray
    HAS_SYSTRAY = True
except ImportError:
    pass


def make_tray_image(size=32):
    """ساخت تصویر آیکون tray — از icon.ico یا لوگوی پیش‌فرض گوی سبز."""
    icon_path = find_icon_path()
    if icon_path:
        try:
            img = Image.open(icon_path)
            return img.resize((size, size), Image.LANCZOS).convert("RGBA")
        except Exception:
            pass
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([4, 4, size - 4, size - 4], fill="#10b981", outline="#059669", width=2)
    draw.ellipse([9, 8, 15, 14], fill="#ffffff")
    return image


class SystemTray:
    """آیکون در ناحیه هیدن‌آیکون‌های تسک‌بار با منوی کامل و tooltip وضعیت."""

    def __init__(self):
        self._icon = None
        self._callbacks = {
            "dict": None,
            "api_settings": None,
            "doc_translator": None,
            "toggle_pause": None,
            "vram": None,
            "quit": None,
        }
        self._auto_pause_state = True

    @property
    def is_available(self):
        return HAS_SYSTRAY

    def on(self, name, cb):
        self._callbacks[name] = cb

    def set_auto_pause_state(self, enabled):
        self._auto_pause_state = bool(enabled)
        if self._icon:
            try:
                self._icon.menu = self._build_menu()
                self._icon.update_menu()
            except Exception:
                pass

    def _build_menu(self):
        check = "✓ " if self._auto_pause_state else "   "
        return pystray.Menu(
            pystray.MenuItem("📚 واژه‌نامه تخصصی", lambda: self._callbacks.get("dict", lambda: None)()),
            pystray.MenuItem("📄 ترجمه اسناد و متن طولانی", lambda: self._callbacks.get("doc_translator", lambda: None)()),
            pystray.MenuItem("⚙️ تنظیمات هوش مصنوعی (API)", lambda: self._callbacks.get("api_settings", lambda: None)()),
            pystray.MenuItem(
                check + "توقف خودکار ویدیو/موزیک هنگام صحبت",
                lambda: self._callbacks.get("toggle_pause", lambda: None)(),
            ),
            pystray.MenuItem("🧹 آزادسازی VRAM", lambda: self._callbacks.get("vram", lambda: None)()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ خروج کامل از برنامه", lambda: self._callbacks.get("quit", lambda: None)()),
        )

    def create(self):
        if not HAS_SYSTRAY:
            print("[SystemTray] pystray not installed — skipping")
            return
        try:
            image = make_tray_image(32)
            self._icon = pystray.Icon("OmniType-FreePTT", image, "OmniType v2.2 — آماده", self._build_menu())
            threading.Thread(target=self._icon.run, daemon=True).start()
        except Exception as e:
            print(f"[SystemTray] Error creating icon: {e}")
            self._icon = None

    def update_tooltip(self, text):
        if self._icon:
            try:
                self._icon.title = text
            except Exception:
                pass

    def stop(self):
        icon = self._icon
        self._icon = None
        if icon:
            def _stop():
                time.sleep(0.15)
                try:
                    icon.stop()
                except Exception:
                    pass
            threading.Thread(target=_stop, daemon=True).start()
