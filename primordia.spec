# -*- mode: python ; coding: utf-8 -*-
"""One-file PrimORDia workstation. Set PRIMORDIA_BINARY_NAME to choose the output file."""

import os
import sysconfig
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

binary_name = os.environ.get("PRIMORDIA_BINARY_NAME", "PrimORDia")

datas = [("static", "static")]
binaries = []
site = Path(sysconfig.get_path("purelib"))
for libs_dir in sorted(site.glob("*.libs")):
    for lib in sorted(libs_dir.iterdir()):
        if lib.is_file():
            binaries.append((str(lib), libs_dir.name))

hiddenimports = collect_submodules("uvicorn")
hiddenimports += ["RNA", "RNA.RNA", "RNA._RNA", "Bio", "Bio.Align"]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=binary_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
