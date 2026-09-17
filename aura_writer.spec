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
zlib_path = os.path.join(conda_dir, 'zlib.dll')
if os.path.exists(zlib_path):
    extra_binaries.append((zlib_path, '.'))

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
        'pydantic',
        'markdown',
        'pygame.mixer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'scipy',
        'numpy',
        'matplotlib',
        'networkx',
        'tkinter',
        'unittest',
        'pytest',
        'PIL._avif',
        'PIL.ImageQt',
        'pygame.camera',
        'pygame.cdrom',
        'pygame.font',
        'pygame.ftfont',
        'pygame.joystick',
        'pygame.midi',
        'pygame.movie',
        'pygame.pixelarray',
        'pygame.pixelcopy',
        'pygame.sndarray',
        'pygame.surfarray',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtNetwork',
        'PyQt6.QtSensors',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtXml',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Deduplicar binarios y filtrar DLLs gigantes no requeridas (e.g. software rendering de OpenGL 20MB)
BLOCKED_BINARIES = {'opengl32sw.dll', 'd3dcompiler_47.dll'}
seen_bin_names = set()
unique_binaries = []
for item in a.binaries:
    dest_name = os.path.basename(item[0]).lower()
    if dest_name not in seen_bin_names and dest_name not in BLOCKED_BINARIES:
        seen_bin_names.add(dest_name)
        unique_binaries.append(item)
a.binaries = unique_binaries

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
