"""PyInstaller spec — builds GUI + CLI one-file executables.

Build from repo root:
    pyinstaller -y installer/packaging/flutter_uploader.spec
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

block_cipher = None

datas = [
    (str(ROOT / "README.md"), "."),
    (str(ROOT / "app" / "config.json"), "."),
    (str(ROOT / "app" / "ENVIRONMENT.md"), "."),
    (str(ROOT / "app" / "CLI_REFERENCE.md"), "."),
]

hiddenimports = []

# ── GUI executable ────────────────────────────────────────────────────────────

gui_a = Analysis(
    [str(ROOT / "installer" / "packaging" / "run_gui.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

gui_pyz = PYZ(gui_a.pure, gui_a.zipped_data, cipher=block_cipher)

gui_exe = EXE(
    gui_pyz,
    gui_a.scripts,
    gui_a.binaries,
    gui_a.zipfiles,
    gui_a.datas,
    [],
    name="FlutterUploader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

gui_app = BUNDLE(
    gui_exe,
    name="FlutterUploader.app",
    icon=None,
    bundle_identifier="com.senpai.flutteruploader",
)

# ── CLI executable ────────────────────────────────────────────────────────────

cli_a = Analysis(
    [str(ROOT / "installer" / "packaging" / "run_cli.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

cli_pyz = PYZ(cli_a.pure, cli_a.zipped_data, cipher=block_cipher)

cli_exe = EXE(
    cli_pyz,
    cli_a.scripts,
    cli_a.binaries,
    cli_a.zipfiles,
    cli_a.datas,
    [],
    name="FlutterUploaderCLI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
