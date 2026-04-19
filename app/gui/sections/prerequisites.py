"""GUI-only pre-requisite helpers (re-exports core checks + iOS platform)."""

from __future__ import annotations

from core.prerequisites import (
    flutter_project_prereq_status,
    appstore_api_configured,
    drive_creds_configured,
    google_play_configured,
    missing_keys_message,
    has_android_folder,
    gmail_configured,
    has_ios_folder,
)
from gui.sections.contracts import ConfigPanelHost


def ios_prereq_status(app: ConfigPanelHost) -> tuple[bool, str]:
    if not app._show_ios:
        return False, "iOS builds require macOS."
    return flutter_project_prereq_status()
