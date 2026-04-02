from pathlib import Path
import json
import sys
import os
import re


APP_DIR_NAME = "FlutterUploader"
APP_TITLE = "Flutter Uploader"
APP_VERSION = "5.4"

DEFAULT_COMMIT_MESSAGE_PRE = "pre-release cleanup"
# Substituted at run time: ``{version}`` and ``{build}`` from pubspec.
DEFAULT_COMMIT_MESSAGE_RELEASE = "v{version} ({build})"

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


_flutter_project_root: Path | None = None


class ProjectRootNotConfiguredError(FileNotFoundError):
    """Raised when FLUTTER_PROJECT_ROOT is missing or invalid."""


def require_flutter_project_root() -> Path:
    """Resolve FLUTTER_PROJECT_ROOT from env or persisted config (cached after first success).

    Raises ``ProjectRootNotConfiguredError`` when the root is not set or the
    directory does not exist, allowing callers (GUI, CLI) to handle it gracefully.
    """
    global _flutter_project_root
    if _flutter_project_root is not None:
        return _flutter_project_root

    raw = os.environ.get("FLUTTER_PROJECT_ROOT", "").strip()
    if not raw:
        env_path = SECRETS_DIR / "enviroment.json"
        if env_path.is_file():
            try:
                saved = json.loads(env_path.read_text(encoding="utf-8") or "{}")
                if isinstance(saved, dict):
                    raw = str(saved.get("FLUTTER_PROJECT_ROOT", "")).strip()
            except (OSError, json.JSONDecodeError):
                raw = ""

    if not raw:
        raise ProjectRootNotConfiguredError(
            "FLUTTER_PROJECT_ROOT is required. Set Flutter project root in "
            "Settings → Environment."
        )
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        raise ProjectRootNotConfiguredError(
            f"FLUTTER_PROJECT_ROOT '{raw}' resolves to {p}, which is not a directory."
        )
    _flutter_project_root = p
    return p


def flutter_project_root() -> Path:
    return require_flutter_project_root()


def set_flutter_project_root(raw: str) -> None:
    """Update the active project root for the running process."""
    global _flutter_project_root
    s = str(raw).strip()
    if s:
        os.environ["FLUTTER_PROJECT_ROOT"] = s
    else:
        os.environ.pop("FLUTTER_PROJECT_ROOT", None)
    _flutter_project_root = None


def apk_dir() -> Path:
    return require_flutter_project_root() / "build" / "app" / "outputs" / "flutter-apk"


def aab_dir() -> Path:
    return require_flutter_project_root() / "build" / "app" / "outputs" / "bundle" / "release"


def ipa_dir() -> Path:
    return require_flutter_project_root() / "build" / "ios" / "ipa"

CLI_REFERENCE_PATH = BUNDLE_DIR / "CLI_REFERENCE.md"
ENVIRONMENT_PATH = BUNDLE_DIR / "ENVIRONMENT.md"
README_PATH = BUNDLE_DIR / "README.md"

def pubspec_path() -> Path:
    return require_flutter_project_root() / "pubspec.yaml"


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
