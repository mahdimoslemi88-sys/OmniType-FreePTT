"""تست‌های به‌روزرسانی خودکار (core/updater.py).

نسخه‌محلی، پارس برچسب، و منطق مقایسه/انتخاب asset با API گیت‌هاب mockشده
بررسی می‌شود — بدون تماس شبکهٔ واقعی.
"""
from core import updater


def test_parse_version():
    assert updater._parse_version("v2.3.0") == (2, 3, 0)
    assert updater._parse_version("v1.0.0-beta") == (1, 0, 0)
    assert updater._parse_version("2.2") is None  # سه عدد لازم است
    assert updater._parse_version("") is None
    assert updater._parse_version("abc") is None


def test_read_current_version_is_valid_triple():
    v = updater._read_current_version()
    assert len(v) == 3
    assert all(isinstance(x, int) for x in v)


def test_check_for_update_finds_newer(monkeypatch):
    class FakeRes:
        status_code = 200

        def json(self):
            return {
                "tag_name": "v2.4.0",
                "html_url": "https://github.com/x/y/releases/tag/v2.4.0",
                "assets": [{
                    "name": "OmniType-FreePTT-v2.4.0.zip",
                    "browser_download_url": "https://github.com/x/y/omni.zip",
                }],
            }

    monkeypatch.setattr(updater.requests, "get", lambda *a, **k: FakeRes())
    info = updater.check_for_update()
    assert info["available"] is True
    assert info["latest"] == "v2.4.0"
    assert info["asset_name"].endswith(".zip")
    assert info["download_url"]


def test_check_for_update_not_newer(monkeypatch):
    class FakeRes:
        status_code = 200

        def json(self):
            return {"tag_name": "v2.1.0", "html_url": "/r", "assets": []}

    monkeypatch.setattr(updater.requests, "get", lambda *a, **k: FakeRes())
    info = updater.check_for_update()
    assert info["available"] is False


def test_check_for_update_non_200_returns_none(monkeypatch):
    monkeypatch.setattr(updater.requests, "get",
                        lambda *a, **k: type("R", (), {"status_code": 403})())
    assert updater.check_for_update() is None


def test_check_for_update_network_error_returns_none(monkeypatch):
    def boom(*a, **k):
        raise Exception("offline")

    monkeypatch.setattr(updater.requests, "get", boom)
    assert updater.check_for_update() is None
