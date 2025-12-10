# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

block_cipher = None

project_root = Path(os.path.abspath('.'))

datas = [
    (str(project_root / 'iheartla' / 'la_grammar'), 'la_grammar'),
    (str(project_root / 'iheartla' / 'la_local_parsers'), 'la_local_parsers'),
]

hiddenimports = [
    'wx.lib.pubsub.core',
    'wx.lib.pdfviewer',
    'wx.lib.pdfviewer.images',
]

a = Analysis(
    ['iheartla/__main__.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='iheartla',
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
    icon=str(project_root / 'docs' / 'favicon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='iheartla',
)
