from pathlib import Path
import os
import re
import sys


APP_TITLE = "Flutter Uploader"
APP_VERSION = "5.4"

IS_WIN = sys.platform == "win32"

UPLOADER_DIR = Path(__file__).resolve().parent.parent


def load_dotenv_files() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(UPLOADER_DIR / ".env")


load_dotenv_files()


def _require_flutter_project_root() -> Path:
    raw = os.environ.get("FLUTTER_PROJECT_ROOT", "").strip()
    if not raw:
        print(
            "Error: FLUTTER_PROJECT_ROOT is required. In .env set it to the directory that "
            "contains pubspec.yaml — where builds and git commands should run.\n",
            file=sys.stderr,
        )
        raise SystemExit(1)
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        print(
            f"Error: FLUTTER_PROJECT_ROOT '{raw}' resolves to {p}, which is not a directory.\n",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return p


FLUTTER_PROJECT_ROOT = _require_flutter_project_root()

APK_DIR = FLUTTER_PROJECT_ROOT / "build" / "app" / "outputs" / "flutter-apk"
IPA_DIR = FLUTTER_PROJECT_ROOT / "build" / "ios" / "ipa"

CLI_REFERENCE_PATH = UPLOADER_DIR / "CLI_REFERENCE.md"
ENVIRONMENT_PATH = UPLOADER_DIR / "ENVIRONMENT.md"
README_PATH = UPLOADER_DIR / "README.md"

PUBSPEC = FLUTTER_PROJECT_ROOT / "pubspec.yaml"
OUTPUTS_DIR = UPLOADER_DIR / "outputs"
LOGS_DIR = UPLOADER_DIR / "logs"


COLORS: dict[str, str] = {
    "console_border": "#1e293b",
    "console_inner": "#010410",
    "accent_hover": "#7dd3fc",
    "danger_hover": "#f87171",
    "card_border": "#1e293b",
    "console_bg": "#020617",
    "text_dim": "#475569",
    "disabled": "#0f172a",
    "card_bg": "#0f172a",
    "section": "#94a3b8",
    "success": "#34d399",
    "accent": "#38bdf8",
    "danger": "#ef4444",
    "error": "#f87171",
    "hover": "#1e293b",
    "muted": "#64748b",
    "text": "#cbd5e1",
    "warn": "#fbbf24",
    "cmd": "#38bdf8",
    "bg": "#020617",
}

RADIUS: dict[str, int] = {"card": 12, "input": 8, "btn": 10}
PAD: dict[str, int] = {"sm": 8, "md": 15, "lg": 20}

CODE_BG = "#010410"
CODE_BORDER = "#1e293b"
HEADING_COLORS: dict[int, str] = {
    1: COLORS["accent"],
    2: COLORS["section"],
    3: COLORS["accent"],
}


POWER_DELAY = 30


DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
DEFAULT_GMAIL_RECIPIENTS: list[str] = []
LINK_PREFIX = "https://drive.google.com/drive/folders/"
FOLDER_MIME = "application/vnd.google-apps.folder"
MIME_MAP: dict[str, str] = {
    ".apk": "application/vnd.android.package-archive",
    ".ipa": "application/octet-stream",
}


ABI_PATTERN = re.compile(r"^app-(.+)-release\.apk$", re.IGNORECASE)
PLAIN_RELEASE = re.compile(r"^app-release\.apk$", re.IGNORECASE)
VERSION_RE = re.compile(r"^(version:\s*)(\S+)", re.MULTILINE)
RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
RE_CODE = re.compile(r"`(.+?)`")


ORPHAN_PATTERNS: list[str] = [
    "org.gradle.launcher.daemon.bootstrap.GradleDaemon",
    "org.jetbrains.kotlin.daemon.KotlinCompileDaemon",
    "com.android.tools.idea.gradle",
    "xcdevice observe",
    "dart.*snapshot",
    "flutter_tools",
    "xcodebuild",
    "shorebird",
]


REPORT_BODY_OPEN = (
    '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"></head>'
    '<body style="margin:0;padding:0;background-color:#020617;'
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,"
    "Helvetica,Arial,sans-serif;\">"
    '<div style="max-width:600px;margin:0 auto;padding:16px 8px;">'
)

REPORT_BODY_CLOSE = "</div></body></html>"

REPORT_BORDER_LR = "border-left:1px solid #1e293b;border-right:1px solid #1e293b;"
REPORT_SECTION_H2 = (
    'style="margin:0;font-size:13px;color:#94a3b8;font-weight:600;'
    'text-transform:uppercase;letter-spacing:0.8px;"'
)
REPORT_TH_STYLE = (
    'style="padding:5px 12px;text-align:{align};color:#64748b;font-size:11px;'
    'font-weight:600;text-transform:uppercase;letter-spacing:0.4px;"'
)

MAX_REPORT_LOG_LINES = 20000


StepDef = tuple[str, str, str, bool]
StepResult = tuple[str, bool, float]

COMMON_STEPS: list[StepDef] = [
    ("clean",   "Flutter Clean", "Remove build cache",     False),
    ("pub_get", "Dependencies",  "pub get or pub upgrade", False),
]

GIT_PRE_STEPS: list[StepDef] = [
    ("git_commit_pre", "Pre-release Commit", "git add . && git commit", True),
    ("git_pull",       "Pull Master",        "git pull origin master",  True),
]

ANDROID_STEPS: list[StepDef] = [
    ("build_apk", "Build APK", "Release, split-per-abi", True),
]

IOS_STEPS: list[StepDef] = [
    ("pod_install",     "Pod Install",      "Deintegrate + repo update + install", False),
    ("build_ipa",       "Build IPA",        "Release archive",                     True),
    ("appstore_upload", "App Store Upload", "Upload to App Store Connect",         True),
]

GIT_POST_STEPS: list[StepDef] = [
    ("git_commit_rel", "Release Commit", "git add . && git commit v{ver}", True),
    ("git_push",       "Push Master",    "git push origin master",         True),
]

POST_STEPS: list[StepDef] = [
    ("open_folders",  "Open Outputs",    "Open outputs folder",         False),
    ("drive_upload",  "Upload to Drive", "Upload outputs + email link", True),
    ("shutdown",      "Power Off/Sleep", "Shutdown or sleep when done", False),
]
