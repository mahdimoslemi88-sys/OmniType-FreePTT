@echo off
:: ============================================================================
:: OmniType v2.1 — اجرای تستی از سورس (با کنسول برای مشاهده خطاها)
:: پیش‌نیاز: پوشه voice_env (دستور: python -m venv voice_env)
:: ============================================================================
cd /d "%~dp0"
if exist "voice_env\Scripts\python.exe" (
    "voice_env\Scripts\python.exe" OmniType-FreePTT.py
) else (
    echo [ERROR] voice_env not found. Create it first:
    echo   python -m venv voice_env
    echo   voice_env\Scripts\pip install -r requirements.txt
    pause
)
