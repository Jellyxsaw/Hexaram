# -*- mode: python ; coding: utf-8 -*-
import time

# 生成帶時間戳的檔案名
timestamp = time.strftime("%m%d_%H%M")
output_name = f'Hexaram_{timestamp}'

block_cipher = None

a = Analysis(
    ['claudeApp/mainApp.py'],
    pathex=['C:\SideProject\Hexaram'],
    binaries=[],
    datas=[('claudeApp/config.yml', '.'), ('claudeApp/chinese_mapping.json', '.'), ('claudeApp/champion_mapping.json', '.'), ('claudeApp/local_session.json', '.'), ('images', 'images'), ('data', 'data'), ('champion_images', 'champion_images')],
    hiddenimports=['atexit', 'signal', 'threading', 'PIL._tkinter_finder'],
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
    name=output_name,  # 使用帶時間戳的檔案名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 設置為 False 以隱藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='images/icon.ico',
    uac_admin=False  # 不需要管理員權限
)
