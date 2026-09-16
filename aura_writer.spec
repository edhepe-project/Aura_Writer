# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

src_dir = os.path.abspath('src')
conda_dir = os.path.dirname(sys.executable)
if not os.path.exists(os.path.join(conda_dir, 'python313.dll')):
    # If in venv, get base prefix
    conda_dir = sys.base_prefix

extra_binaries = []
dll_names = [
    'zlib.dll',
    'python3.dll',
    'python313.dll',
    'vcruntime140.dll',
    'vcruntime140_1.dll',
    'vcruntime140_threads.dll',
    'msvcp140.dll',
    'msvcp140_1.dll',
    'msvcp140_2.dll',
    'msvcp140_atomic_wait.dll',
    'msvcp140_codecvt_ids.dll',
    'ucrtbase.dll',
]
for dll_name in dll_names:
    dll_path = os.path.join(conda_dir, dll_name)
    if os.path.exists(dll_path):
        extra_binaries.append((dll_path, '.'))

a = Analysis(
    ['launcher.py'],
    pathex=[src_dir, '.'],
    binaries=extra_binaries,
    datas=[
        ('aura_writer.ico', '.'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtMultimedia',
        'qtawesome',
        'Crypto',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'Crypto.Protocol.KDF',
        'Crypto.Random',
        'Crypto.Hash.SHA256',
        'pyotp',
        'qrcode',
        'reportlab',
        'docx',
        'ebooklib',
        'bs4',
        'lxml',
        'networkx',
        'pydantic',
        'markdown',
        'pygame',
        'pygame.mixer',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AuraWriter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='aura_writer.ico',
)
