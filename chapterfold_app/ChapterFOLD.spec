# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_dir = Path.cwd().resolve()
repo_root = project_dir.parent

a = Analysis(
    ['app.py'],
    pathex=[str(project_dir), str(repo_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'core',
        'core.epub_service',
    ],
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
    name='ChapterFOLD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=['assets\\icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChapterFOLD',
)
