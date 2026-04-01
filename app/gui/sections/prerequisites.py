"""Pre-requisite checks for Config tab sections (paths, platform)."""

from __future__ import annotations

from pathlib import Path

from core.config_store import env_value, get_section, resolved_flutter_project_root_string
from gui.sections.contracts import ConfigPanelHost


def flutter_project_prereq_status() -> tuple[bool, str]:
    """Require a Flutter project directory containing ``pubspec.yaml``."""
    raw = resolved_flutter_project_root_string()
    if not raw:
        return False, "Set Flutter project root in Settings → Environment, then Save environment."
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        return False, f"Flutter project path is not a directory:\n{p}"
    if not (p / "pubspec.yaml").is_file():
        return False, f"No pubspec.yaml in:\n{p}"
    return True, ""


def ios_prereq_status(app: ConfigPanelHost) -> tuple[bool, str]:
    if not app._show_ios:
        return False, "iOS builds require macOS."
    return flutter_project_prereq_status()


def drive_upload_warning() -> str | None:
    """If Drive upload is enabled in saved config but credentials are missing."""
    steps = (get_section("post_build") or {}).get("steps") or {}
    if not isinstance(steps, dict) or not steps.get("drive_upload"):
        return None
    if env_value("GOOGLE_DRIVE_CREDENTIALS_JSON"):
        return None
    return "Post-Build has Drive upload enabled, but Google Drive credentials JSON is not set (Settings → Environment)."
