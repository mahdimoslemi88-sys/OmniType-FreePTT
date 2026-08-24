"""تست‌های engine/voice_commands.py — فرمان‌های صوتی فارسی."""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.voice_commands import (
    normalize_persian,
    match_command,
    COMMANDS,
)


class TestNormalizePersian:
    """تست نرمال‌سازی متن فارسی."""

    def test_strip_whitespace(self):
        assert normalize_persian("  پاک کن  ") == "پاک کن"

    def test_strip_punctuation(self):
        assert normalize_persian("پاک کن!") == "پاک کن"
        assert normalize_persian("پاک کن؟") == "پاک کن"
        assert normalize_persian("پاک کن.") == "پاک کن"

    def test_arabic_to_persian_digits(self):
        assert normalize_persian("٣") == "۳"

    def test_multiple_spaces_collapsed(self):
        assert normalize_persian("پاک    کن") == "پاک کن"


class TestMatchCommand:
    """تست تطبیق فرمان‌ها."""

    def test_exact_match_delete(self):
        result = match_command("پاک کن")
        assert result is not None
        pattern, actions = result
        assert pattern == "پاک کن"
        assert actions == [("press", "backspace")]

    def test_exact_match_select_all(self):
        result = match_command("انتخاب کن")
        assert result is not None
        _, actions = result
        assert actions == [("combo", "ctrl+a")]

    def test_exact_match_copy(self):
        result = match_command("کپی")
        assert result is not None

    def test_exact_match_paste(self):
        result = match_command("پیست")
        assert result is not None

    def test_exact_match_undo(self):
        result = match_command("برگرد")
        assert result is not None
        _, actions = result
        assert actions == [("combo", "ctrl+z")]

    def test_exact_match_save(self):
        result = match_command("ذخیره کن")
        assert result is not None

    def test_exact_match_enter(self):
        result = match_command("انتر")
        assert result is not None
        _, actions = result
        assert actions == [("press", "enter")]

    def test_exact_match_tab(self):
        result = match_command("تب")
        assert result is not None

    def test_exact_match_period(self):
        result = match_command("نقطه")
        assert result is not None
        _, actions = result
        assert actions == [("type", ".")]

    def test_exact_match_comma(self):
        result = match_command("کاما")
        assert result is not None
        _, actions = result
        assert actions == [("type", ",")]

    def test_exact_match_open_paren(self):
        result = match_command("پرانتز باز")
        assert result is not None
        _, actions = result
        assert actions == [("type", "(")]

    def test_exact_match_close_paren(self):
        result = match_command("پرانتز بسته")
        assert result is not None
        _, actions = result
        assert actions == [("type", ")")]

    def test_exact_match_up(self):
        result = match_command("بالا")
        assert result is not None
        _, actions = result
        assert actions == [("press", "up")]

    def test_exact_match_down(self):
        result = match_command("پایین")
        assert result is not None

    def test_exact_match_space(self):
        result = match_command("فاصله")
        assert result is not None
        _, actions = result
        assert actions == [("press", "space")]

    def test_no_match_for_random_text(self):
        result = match_command("سلام دنیا")
        assert result is None

    def test_no_match_for_empty(self):
        result = match_command("")
        assert result is None

    def test_match_with_trailing_period(self):
        """فرمان با نقطه انتهایی هم باید تطبیق پیدا کند."""
        result = match_command("پاک کن.")
        assert result is not None

    def test_double_delete(self):
        result = match_command("دو تا پاک کن")
        assert result is not None
        _, actions = result
        assert len(actions) == 2

    def test_triple_delete(self):
        result = match_command("سه تا پاک کن")
        assert result is not None
        _, actions = result
        assert len(actions) == 3

    def test_number_match(self):
        for num, digit in [("صفر", "0"), ("یک", "1"), ("دو", "2"),
                           ("سه", "3"), ("نه", "9")]:
            result = match_command(num)
            assert result is not None, f"Failed to match: {num}"
            _, actions = result
            assert actions == [("type", digit)], f"Wrong action for {num}"


class TestCommandsCompleteness:
    """بررسی کامل بودن فهرست فرمان‌ها."""

    def test_commands_is_nonempty(self):
        assert len(COMMANDS) > 0

    def test_each_command_has_patterns_and_actions(self):
        for patterns, actions in COMMANDS:
            assert isinstance(patterns, list)
            assert len(patterns) > 0
            assert isinstance(actions, list)
            assert len(actions) > 0
            for action in actions:
                assert action[0] in ("press", "combo", "type")
