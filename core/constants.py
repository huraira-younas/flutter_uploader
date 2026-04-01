from pathlib import Path
import os
import re
import sys


APP_TITLE = "Flutter Uploader"
APP_VERSION = "5.4"

IS_WIN = sys.platform == "win32"

UPLOADER_DIR = Path(__file__).resolve().parent.parent


_dotenv_loaded = False


def load_dotenv_files() -> None:
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(UPLOADER_DIR / ".env")
    _dotenv_loaded = True


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


REPORT_ACCENT = "#38bdf8"
REPORT_MUTED = "#64748b"
REPORT_CARD_BORDER = "#1e293b"
REPORT_CARD_BG = "#0f172a"
REPORT_BG = "#020617"
REPORT_SUCCESS = "#34d399"
REPORT_ERROR = "#f87171"
REPORT_SECTION = "#94a3b8"


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


StepDef = tuple[str, str, str, bool]
StepResult = tuple[str, bool, float]

COMMON_STEPS: list[StepDef] = [
    ("clean",   "Flutter Clean", "Remove build cache",     False),
    ("pub_get", "Dependencies",  "pub get or pub upgrade", False),
]

COMMIT_PRE_STEPS: list[StepDef] = [
    ("git_commit_pre", "Pre-release Commit", "git add . && git commit", True),
]

GIT_SYNC_STEPS: list[StepDef] = [
    ("git_pull", "Pull Master", "git pull origin master", True),
]

GIT_PRE_STEPS: list[StepDef] = COMMIT_PRE_STEPS + GIT_SYNC_STEPS

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
