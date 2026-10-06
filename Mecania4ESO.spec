# -*- mode: python ; coding: utf-8 -*-
"""Configuración de PyInstaller para MECANIA 4ESO."""
import os, sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Separador según SO
SEP = ";" if sys.platform == "win32" else ":"

datas = [
    ("data", "data"),
    ("assets", "assets"),
]

hidden = collect_submodules("PySide6") + ["sqlite3", "hashlib", "secrets"]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "pandas"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Mecania4ESO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Mecania4ESO",
)

# Si es macOS, generar también .app
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Mecania4ESO.app",
        icon=None,
        bundle_identifier="es.mecania.4eso",
    )
