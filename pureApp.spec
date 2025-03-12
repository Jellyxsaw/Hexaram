# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pureApp.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('champion_mapping.json', '.'),
        ('chinese_mapping.json', '.'),
        ('local_session.json', '.'),
        ('champion_images/*', 'champion_images'),
        ('advanced_aram_model_v2.h5', '.'),
        ('champion_to_idx_v2.pkl', '.'),
        ('scaler_v2.pkl', '.'),
        ('champion_stats_dict_v2.pkl', '.')
    ],
    hiddenimports=[
        'requests',
        'urllib3',
        'certifi',
        'sklearn.utils._weight_vector',
        'sklearn.neighbors._partition_nodes'
    ],
    hookspath=['.'],
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
    name='deepApp1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 設定為 True 可顯示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='deepApp1'
)