# -*- mode: python ; coding: utf-8 -*-

import os.path

block_cipher = None

a = Analysis(['linear_algebra.py'],
             ## pyinstaller iheartla.spec must be run from
             ## next to the 'linear_algebra.py' file and the 'la_grammar' directory.
             pathex=[os.path.abspath(os.getcwd())],
             binaries=[],
             datas=[('la_grammar', 'la_grammar')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='iheartla',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='docs/icon/icon.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='iheartla')
app = BUNDLE(coll,
             name='iheartla.app',
             icon='docs/icon/icon.icns',
             bundle_identifier=None,
             info_plist={'NSHighResolutionCapable': 'True'}
             )
