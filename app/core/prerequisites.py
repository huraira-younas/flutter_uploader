"""Shared prerequisite checks (GUI + CLI) — merged ``env`` from ``secrets/enviroment.json``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config_store import get_app_config


def _merged_env() -> dict[str, Any]:
    block = get_app_config().get("env")
    return block if isinstance(block, dict) else {}


def env_config_str(key: str) -> str:
    """Read from merged ``env`` (``secrets/enviroment.json`` + defaults), not ``os.environ``."""
    return str(_merged_env().get(key, "")).strip()


def missing_keys_message(keys: tuple[str, ...]) -> str | None:
    miss = [k for k in keys if not env_config_str(k)]
    if not miss:
        return None
    lines = "\n".join(f"  • {k}" for k in miss)
    return f"Set in Settings → Environment → Save environment:\n{lines}"


def drive_creds_configured() -> bool:
    return bool(env_config_str("GOOGLE_DRIVE_CREDENTIALS_JSON"))


def google_play_configured() -> bool:
    return bool(env_config_str("GOOGLE_PLAY_JSON_KEY"))


def gmail_configured() -> bool:
    return bool(env_config_str("GMAIL_USER") and env_config_str("GMAIL_APP_PASSWORD"))


def appstore_api_configured() -> bool:
    return bool(env_config_str("APP_STORE_ISSUER_ID") and env_config_str("APP_STORE_API_KEY"))


def flutter_project_prereq_status() -> tuple[bool, str]:
    """Require ``FLUTTER_PROJECT_ROOT`` in merged env and a directory containing ``pubspec.yaml``."""
    raw = env_config_str("FLUTTER_PROJECT_ROOT")
    if not raw:
        return False, (
            "Set FLUTTER_PROJECT_ROOT in Settings → Environment → Save."
        )
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        return False, f"Flutter project path is not a directory:\n{p}"
    if not (p / "pubspec.yaml").is_file():
        return False, f"No pubspec.yaml in:\n{p}"
    return True, ""


def has_android_folder() -> bool:
    raw = env_config_str("FLUTTER_PROJECT_ROOT")
    if not raw:
        return False
    return (Path(raw).expanduser().resolve() / "android").is_dir()


def has_ios_folder() -> bool:
    raw = env_config_str("FLUTTER_PROJECT_ROOT")
    if not raw:
        return False
    return (Path(raw).expanduser().resolve() / "ios").is_dir()
