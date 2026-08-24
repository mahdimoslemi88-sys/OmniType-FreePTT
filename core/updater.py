"""چک‌کنندهٔ به‌روزرسانی خودکار — مقایسه نسخهٔ محلی با آخرین ریلیز گیت‌هاب.

این ماژول نسخهٔ کنونی را از `version_info.txt` (متادیتای یکسان با بیلد اگز)
می‌خواند و آخرین ریلیز مخزن را از API گیت‌هاب می‌گیرد و با آن مقایسه می‌کند.
هر گونه خطا/آفلاین بودن با بازگشت `None` مدیریت می‌شود تا هرگز برنامه را
شکست ندهد.
"""
import os
import re

import requests

REPO = "mahdimoslemi88-sys/OmniType-FreePTT"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
DEFAULT_TIMEOUT = 8
_USER_AGENT = "OmniType-FreePTT"


def _read_current_version():
    """خواندن نسخهٔ محلی از version_info.txt (filevers = X,Y,Z)."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(here, "..", "version_info.txt")),
        os.path.normpath(os.path.join(here, "version_info.txt")),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    m = re.search(r"filevers\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", f.read())
                if m:
                    return tuple(int(x) for x in m.groups())
            except Exception:
                pass
    return (2, 0, 0)  # مبنا در صورت نبود فایل


def _parse_version(tag):
    """تبدیل برچسب مثل «v2.2.0» به tuple (2,2,0)."""
    m = re.search(r"v?(\d+)\.(\d+)\.(\d+)", tag or "")
    if m:
        return tuple(int(x) for x in m.groups())
    return None


def check_for_update(timeout=DEFAULT_TIMEOUT):
    """بررسی وجود نسخهٔ جدید.

    برمی‌گرداند:
      - None در صورت خطا/آفلاین/فرمت نامعتبر
      - dict شامل: available, current, latest, url, asset_name, download_url
    """
    current = _read_current_version()
    try:
        res = requests.get(LATEST_URL, timeout=timeout,
                           headers={"User-Agent": _USER_AGENT})
        if res.status_code != 200:
            return None
        data = res.json()
        tag = data.get("tag_name", "")
        latest = _parse_version(tag)
        if latest is None:
            return None

        asset_name = ""
        download_url = ""
        for asset in data.get("assets", []) or []:
            name = (asset.get("name") or "").lower()
            if name.endswith(".zip"):
                asset_name = asset.get("name", "")
                download_url = asset.get("browser_download_url", "")
                break

        return {
            "available": latest > current,
            "current": ".".join(str(x) for x in current),
            "latest": tag,
            "url": data.get("html_url", ""),
            "asset_name": asset_name,
            "download_url": download_url,
        }
    except Exception:
        return None
