# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for ARC-20 Explorer
# Compatible Linux / Windows / macOS
# Bitwork Labs

import sys

block_cipher = None

datas = [
    ('i18n', 'i18n'),
]

a = Analysis(
    ['arc20_explorer.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'customtkinter',
        'darkdetect',
        'tkinter',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL.ImageQt',
        'PyQt5',
        'PyQt6',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# UPX solo en Linux (en macOS rompe firma, en Windows da problemas)
use_upx = sys.platform == "linux"

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='arc20-explorer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=use_upx,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
