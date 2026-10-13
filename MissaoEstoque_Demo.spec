# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller one-folder para o playtest Windows."""

import os
from pathlib import Path


root = Path(SPECPATH)
asset_data = [
    (str(root / "missao_estoque" / "assets"), "missao_estoque/assets"),
    (str(root / "Som"), "Som"),
]

a = Analysis(
    [str(root / "missao_estoque" / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=asset_data,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "unittest"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MissaoEstoque_Demo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=os.environ.get("MISSAO_DEMO_CONSOLE") == "1",
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MissaoEstoque_Demo",
)
