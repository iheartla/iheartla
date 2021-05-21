# -*- mode: python ; coding: utf-8 -*-

import os.path

# print("Did you forget to re-generate the cached parsers first with `poetry run python la_local_parsers.py`?")

'''
from pathlib import Path
## Create the default parsers if needed.
# import la_parser.parser
# la_parser.parser.create_parser()
# TODO: Wait for the saving thread to finish.
## Copy the parsers from the cache folder.
from appdirs import user_cache_dir
cached_parsers = Path(user_cache_dir())/'iheartla'
import shutil, tempfile
tmpdir = tempfile.TemporaryDirectory()
for f in cached_parsers.glob('*.py'): shutil.copy( f, tmpdir.name )
## Change below to `datas=[...,(tmpdir.name, 'la_local_parsers')]`
'''

block_cipher = None

a = Analysis(['app.py'],
             ## pyinstaller iheartla.spec must be run from
             ## next to the 'linear_algebra.py' file and the 'la_grammar' directory.
             pathex=[os.path.abspath(os.getcwd())],
             binaries=[],
             datas=[],
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
          console=False , icon='extras/icon/icon.icns')
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
             icon='extras/icon/icon.icns',
             bundle_identifier=None,
             info_plist={'NSHighResolutionCapable': 'True'}
             )
