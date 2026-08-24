"""تست‌های سیستم تم رنگی ( tema.py )."""
import sys
import os
import pytest

# مسیر پروژه را به sys.path اضافه کن
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestThemeSwitching:
    """تست‌های سوئیچ تم بین Catppuccin و Midnight."""

    def setup_method(self):
        """بازگرداندن تم به حالت پیش‌فرض قبل از هر تست."""
        import gui.theme as theme
        theme.set_theme("catppuccin")

    def test_default_theme_is_catppuccin(self):
        import gui.theme as theme
        assert theme.get_theme_name() == "catppuccin"
        assert theme.BG_DARK == "#181825"

    def test_switch_to_midnight(self):
        import gui.theme as theme
        theme.set_theme("midnight")
        assert theme.get_theme_name() == "midnight"
        assert theme.BG_DARK == "#0d1117"
        assert theme.ACCENT_CYAN == "#58a6ff"

    def test_switch_back_to_catppuccin(self):
        import gui.theme as theme
        theme.set_theme("midnight")
        theme.set_theme("catppuccin")
        assert theme.get_theme_name() == "catppuccin"
        assert theme.BG_DARK == "#181825"

    def test_invalid_theme_defaults_to_catppuccin(self):
        import gui.theme as theme
        theme.set_theme("nonexistent_theme")
        assert theme.get_theme_name() == "catppuccin"

    def test_theme_names_dict_has_both_themes(self):
        import gui.theme as theme
        assert "catppuccin" in theme.THEME_NAMES
        assert "midnight" in theme.THEME_NAMES
        assert len(theme.THEME_NAMES) == 2

    def test_get_palette_returns_dict(self):
        import gui.theme as theme
        pal = theme.get_palette("midnight")
        assert isinstance(pal, dict)
        assert pal["BG_DARK"] == "#0d1117"
        assert "ACCENT_RED" in pal

    def test_get_palette_invalid_returns_catppuccin(self):
        import gui.theme as theme
        pal = theme.get_palette("bogus")
        assert pal["BG_DARK"] == "#181825"

    def test_all_palette_colors_exist_after_switch(self):
        """پس از سوئیچ، همه ثابت‌های رنگ باید مقدار hex معتبر داشته باشند."""
        import gui.theme as theme
        theme.set_theme("midnight")
        for name in ("BG_DARK", "BG_DARKER", "BG_MID", "BG_SURFACE",
                      "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_BRIGHT",
                      "ACCENT_CYAN", "ACCENT_GREEN", "ACCENT_RED",
                      "ACCENT_BLUE", "ACCENT_YELLOW", "ACCENT_PURPLE", "ACCENT_ORANGE"):
            val = getattr(theme, name)
            assert val.startswith("#"), f"{name} = {val!r} does not start with #"
            assert len(val) == 7, f"{name} = {val!r} is not 7 chars"

    def test_fonts_unchanged_after_switch(self):
        """فونت‌ها نباید با تغییر تم عوض شوند."""
        import gui.theme as theme
        theme.set_theme("midnight")
        assert theme.FONT_EN == ("Segoe UI", 9)
        assert theme.FONT_FA == ("Tahoma", 9)
