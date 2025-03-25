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
    datas=[
        ('claudeApp/config.json', '.'), 
        ('claudeApp/chinese_mapping.json', '.'), 
        ('claudeApp/champion_mapping.json', '.'), 
        ('claudeApp/local_session.json', '.'), 
        ('images', 'images'), 
        ('data', 'data'), 
        ('champion_images', 'champion_images')
    ],
    hiddenimports=[
        'atexit', 
        'signal', 
        'threading', 
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.font',
        'tkinter.messagebox',
        'multiprocessing'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],  # 移除所有排除項
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 不使用 UPX 壓縮，這是防毒軟體誤判的常見原因
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],  # 不包含二進制文件在 EXE 中
    exclude_binaries=True,  # 排除二進制文件，分開放置
    name=output_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用 UPX 壓縮
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='images/icon.ico',
    uac_admin=False
)

# 使用 COLLECT 創建目錄結構
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=output_name,
)