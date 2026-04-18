from __future__ import annotations
from pathlib import Path
import sys
import os
import re


APP_DIR_NAME = "FlutterUploader"
APP_TITLE = "Flutter Uploader"
APP_VERSION = "5.5"

# Substituted at run time: ``{version}`` and ``{build}`` from pubspec.
DEFAULT_COMMIT_MESSAGE_RELEASE = "v{version} ({build})"
DEFAULT_COMMIT_MESSAGE_PRE = "pre-release cleanup"
DEFAULT_GIT_BRANCH = "master"

IS_WIN = sys.platform == "win32"

if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys.executable).resolve().parent
    if IS_WIN:
        appdata = os.environ.get("APPDATA", "").strip()
        base_dir = Path(appdata).expanduser() if appdata else (Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path.home() / ".config"
    UPLOADER_DIR = (base_dir / APP_DIR_NAME).resolve()
else:
    # Dev: keep config/logs/outputs under ./app/
    BUNDLE_DIR = Path(__file__).resolve().parents[1]
    UPLOADER_DIR = BUNDLE_DIR

SECRETS_DIR = UPLOADER_DIR / "secrets"
OUTPUTS_DIR = UPLOADER_DIR / "outputs"
LOGS_DIR = UPLOADER_DIR / "logs"

REPORT_CARD_BORDER = "#1e293b"
REPORT_CARD_BG = "#0f172a"
REPORT_SECTION = "#94a3b8"
REPORT_SUCCESS = "#34d399"
REPORT_ACCENT = "#38bdf8"
REPORT_MUTED = "#64748b"
REPORT_ERROR = "#f87171"
REPORT_BG = "#020617"

POWER_DELAY = 30

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
LINK_PREFIX = "https://drive.google.com/drive/folders/"
FOLDER_MIME = "application/vnd.google-apps.folder"
MIME_MAP: dict[str, str] = {
    ".aab": "application/octet-stream",
    ".apk": "application/vnd.android.package-archive",
    ".ipa": "application/octet-stream",
}

ABI_PATTERN = re.compile(r"^app-(.+)-release\.apk$", re.IGNORECASE)
PLAIN_RELEASE = re.compile(r"^app-release\.apk$", re.IGNORECASE)
VERSION_RE = re.compile(r"^(version:\s*)(\S+)", re.MULTILINE)

ORPHAN_PATTERNS: list[str] = [
    "org.gradle.launcher.daemon.bootstrap.GradleDaemon",
    "org.jetbrains.kotlin.daemon.KotlinCompileDaemon",
    "com.android.tools.idea.gradle",
    "xcdevice observe",
    "dart.*snapshot",
    "flutter_tools",
    "xcodebuild",
]

REPORT_BODY_OPEN = (
    '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"></head>'
    f'<body style="margin:0;padding:0;background-color:{REPORT_BG};'
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,"
    "Helvetica,Arial,sans-serif;\">"
    '<div style="max-width:600px;margin:0 auto;padding:16px 8px;">'
)

REPORT_BODY_CLOSE = "</div></body></html>"

REPORT_BORDER_LR = f"border-left:1px solid {REPORT_CARD_BORDER};border-right:1px solid {REPORT_CARD_BORDER};"
REPORT_SECTION_H2 = (
    f'style="margin:0;font-size:13px;color:{REPORT_SECTION};font-weight:600;'
    'text-transform:uppercase;letter-spacing:0.8px;"'
)
REPORT_TH_STYLE = (
    f'style="padding:5px 12px;text-align:{{align}};color:{REPORT_MUTED};font-size:11px;'
    'font-weight:600;text-transform:uppercase;letter-spacing:0.4px;"'
)

MAX_REPORT_LOG_LINES = 20000
