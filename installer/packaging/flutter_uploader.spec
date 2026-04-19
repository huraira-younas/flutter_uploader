# PyInstaller spec — builds GUI + CLI executables.
#
# macOS GUI: onedir inside the .app (no per-launch extraction to /tmp — faster cold start).
# Windows GUI: one-file EXE (unchanged).
#
# Build from repo root:
#     pyinstaller -y installer/packaging/flutter_uploader.spec

from pathlib import Path
import sys

# Add app to path so we can import helpers
sys.path.append(str(Path(SPECPATH).parent.parent / "app"))
from helpers.version_info import UPLOADER_APP_VERSION

# SPECPATH is injected by PyInstaller — the directory containing this spec file.
ROOT = Path(SPECPATH).parent.parent
IS_DARWIN = sys.platform == "darwin"

block_cipher = None

# Bundled for _MEIPASS / onedir; build_win.ps1 / build_mac.sh also copy docs next to the
# built binaries because frozen UPLOADER_DIR is the exe directory, not the bundle.
datas = [
    (str(ROOT / "app" / "config.json"), "."),
    (str(ROOT / "app" / "assets"), "assets"),
]

hiddenimports = []

MAC_INFO_PLIST = {
    "CFBundleName": "FlutterUploader",
    "CFBundleDisplayName": "Flutter Uploader",
    "CFBundleShortVersionString": UPLOADER_APP_VERSION,
    "CFBundleVersion": UPLOADER_APP_VERSION,
    "CFBundlePackageType": "APPL",
    "NSHighResolutionCapable": True,
    # Ensure GUI role (not background/agent), required for Tk menu setup.
    "LSBackgroundOnly": False,
    "LSUIElement": False,
}

# ── GUI executable ────────────────────────────────────────────────────────────

gui_a = Analysis(
    [str(ROOT / "installer" / "packaging" / "run_gui.py")],
    pathex=[str(ROOT), str(ROOT / "app")],
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

if IS_DARWIN:
    # Onedir: dependencies live on disk inside the bundle — avoids extracting every launch.
    gui_exe = EXE(
        gui_pyz,
        gui_a.scripts,
        [],
        exclude_binaries=True,
        name="FlutterUploader",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    gui_coll = COLLECT(
        gui_exe,
        gui_a.binaries,
        gui_a.zipfiles,
        gui_a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="FlutterUploader",
    )
    gui_app = BUNDLE(
        gui_coll,
        name="FlutterUploader.app",
        icon=str(ROOT / "app" / "assets" / "icon.icns") if IS_DARWIN else str(ROOT / "app" / "assets" / "icon.ico"),
        bundle_identifier="com.senpai.flutteruploader",
        info_plist=MAC_INFO_PLIST,
    )
else:
    gui_exe = EXE(
        gui_pyz,
        gui_a.scripts,
        gui_a.binaries,
        gui_a.zipfiles,
        gui_a.datas,
        [],
        icon=str(ROOT / "app" / "assets" / "icon.ico"),
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
        icon=str(ROOT / "app" / "assets" / "icon.icns") if IS_DARWIN else str(ROOT / "app" / "assets" / "icon.ico"),
        bundle_identifier="com.senpai.flutteruploader",
        info_plist=MAC_INFO_PLIST,
    )

# ── CLI executable ────────────────────────────────────────────────────────────

cli_a = Analysis(
    [str(ROOT / "installer" / "packaging" / "run_cli.py")],
    pathex=[str(ROOT), str(ROOT / "app")],
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
    icon=str(ROOT / "app" / "assets" / "icon.ico") if not IS_DARWIN else None,
    name="FlutterUploaderCLI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
