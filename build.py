import PyInstaller.__main__
import os
import shutil

def build_app():
    # 獲取當前目錄
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定義需要包含的資源文件夾和文件
    resources = [
        ('claudeApp/config.json', '.'),  # 將配置文件放在根目錄
        ('claudeApp/chinese_mapping.json', '.'),  # 將映射文件放在根目錄
        ('claudeApp/champion_mapping.json', '.'),
        ('claudeApp/local_session.json', '.'),
        ('images', 'images'),
        ('data', 'data'),
        ('champion_images', 'champion_images')  # 添加英雄圖片目錄
    ]
    
    # 創建 spec 文件
    spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['claudeApp/mainApp.py'],
    pathex=['{current_dir}'],
    binaries=[],
    datas={resources},
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
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
    name='Hexaram',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 暫時改為 True 以便查看錯誤信息
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='images/icon.ico'
)
'''
    
    # 寫入 spec 文件
    with open('Hexaram.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # 使用 PyInstaller 打包
    PyInstaller.__main__.run([
        'Hexaram.spec',
        '--clean',
        '--noconfirm'
    ])
    
    # 清理臨時文件
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('Hexaram.spec'):
        os.remove('Hexaram.spec')
    
    print("打包完成！可執行檔位於 dist 目錄中。")

if __name__ == '__main__':
    build_app() 