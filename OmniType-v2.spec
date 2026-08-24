# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — OmniType-FreePTT v2.1
# Build: voice_env\Scripts\python -m PyInstaller OmniType-v2.spec --noconfirm

a = Analysis(
    ['OmniType-FreePTT.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.'), ('normalizer.py', '.')],
    hiddenimports=[
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'keyboard',
        'pyperclip',
        'pyaudio',
        'speech_recognition',
        'requests',
        'faster_whisper',
        'ctranslate2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'unittest',
        'pydoc',
        'test',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OmniType-FreePTT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OmniType-FreePTT',
)
