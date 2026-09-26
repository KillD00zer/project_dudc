# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['d:/Work/certi_processing_tools/project_dudc/src/app_server.py'],
    pathex=[],
    binaries=[],
    datas=[('d:/Work/certi_processing_tools/project_dudc/src/شهادة.docx', '.'), ('d:/Work/certi_processing_tools/project_dudc/src/Google Maps Satellite.lyr', '.'), ('d:/Work/certi_processing_tools/project_dudc/src/ف.xls', '.'), ('d:/Work/certi_processing_tools/project_dudc/src/index.html', '.'), ('d:/Work/certi_processing_tools/project_dudc/src/core', 'core')],
    hiddenimports=['openpyxl', 'xlrd', 'pyproj', 'shapely', 'PIL', 'matplotlib', 'docx', 'cryptography', 'security_overlay', 'encoder_api', 'arabic_reshaper', 'bidi', 'bidi.algorithm'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Certificate_Generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Certificate_Generator',
)
