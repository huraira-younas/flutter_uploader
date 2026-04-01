"""Global app configuration: ``config.json`` + in-process cache (GUI + CLI).

All consumers use ``get_app_config()`` / ``get_section()`` — do not thread config dicts
through UI or pipeline call chains.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from core.constants import (
    DEFAULT_COMMIT_MESSAGE_RELEASE,
    DEFAULT_COMMIT_MESSAGE_PRE,
    UPLOADER_DIR,
)
# Canonical mapping between pipeline section aliases and persisted config keys.
PIPELINE_SECTION_TO_CONFIG_SECTION: dict[str, str] = {
    "git_pre": "pre_git",
    "git_post": "post_git",
    "post": "post_build",
    "common": "common",
    "android": "android",
    "ios": "ios",
}


CONFIG_PATH: Path = UPLOADER_DIR / "config.json"

# Top-level keys in ``config.json`` / ``default_app_config()``.
CONFIG_SECTION_KEYS: tuple[str, ...] = (
    "app_info",
    "pre_git",
    "common",
    "post_git",
    "android",
    "ios",
    "post_build",
    "distribution",
)

_cache: dict[str, Any] | None = None


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* onto *base* (dicts only)."""
    out: dict[str, Any] = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def default_app_config() -> dict[str, Any]:
    """Code defaults; user file overlays this."""
    return {
        "app_info": {"version": "", "build": ""},
        "pre_git": {
            "enabled": True,
            "commit_message": DEFAULT_COMMIT_MESSAGE_PRE,
            "steps": {"git_commit_pre": True},
        },
        "common": {
            "enabled": True,
            "pub_mode": "pub get",
            "steps": {"clean": False, "pub_get": False},
        },
        "post_git": {
            "enabled": True,
            "commit_message": DEFAULT_COMMIT_MESSAGE_RELEASE,
            "steps": {"git_pull": True, "git_commit_rel": True, "git_push": True},
        },
        "android": {
            "enabled": True,
            "shorebird": False,
            "shorebird_mode": "Release",
            "steps": {"build_apk": True},
        },
        "ios": {
            "enabled": True,
            "shorebird": False,
            "shorebird_mode": "Release",
            "steps": {"pod_install": False, "build_ipa": True, "appstore_upload": True},
        },
        "post_build": {
            "enabled": True,
            "power_mode": "Sleep" if sys.platform == "darwin" else "Shutdown",
            "quit_after_power": False,
            "steps": {"open_folders": False, "drive_upload": True, "shutdown": False},
        },
        "distribution": {"recipients": ""},
    }


def _read_merged_from_disk() -> dict[str, Any]:
    base = default_app_config()
    if not CONFIG_PATH.is_file():
        return base
    try:
        raw = CONFIG_PATH.read_text(encoding="utf-8")
        saved = json.loads(raw) if raw.strip() else {}
    except (OSError, json.JSONDecodeError):
        return base
    if not isinstance(saved, dict):
        return base
    return deep_merge(base, saved)


def init_app_config(*, force_reload: bool = False) -> dict[str, Any]:
    """Ensure ``config.json`` exists and populate the process-wide config cache.

    Call once after env (``.env``) is loaded; safe to call multiple times.
    """
    global _cache
    ensure_config_file()
    if force_reload or _cache is None:
        _cache = _read_merged_from_disk()
    return _cache


def reload_app_config() -> dict[str, Any]:
    """Re-read ``config.json`` from disk into the cache."""
    global _cache
    _cache = _read_merged_from_disk()
    return _cache


def get_app_config() -> dict[str, Any]:
    """Return merged app config (defaults + file). Initializes cache if needed."""
    if _cache is None:
        return init_app_config()
    return _cache


def get_section(name: str) -> dict[str, Any]:
    """Return a deep copy of one top-level section (safe for mutation)."""
    full = get_app_config()
    base_chunk = default_app_config().get(name, {})
    chunk = full.get(name, {})
    if isinstance(chunk, dict):
        return deep_merge(copy.deepcopy(base_chunk), copy.deepcopy(chunk))
    return copy.deepcopy(base_chunk)


def save_config(data: dict[str, Any]) -> None:
    """Persist a full or partial snapshot; merge with defaults; update cache."""
    global _cache
    merged = deep_merge(default_app_config(), data)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(CONFIG_PATH)
    _cache = merged


def ensure_config_file() -> None:
    """Create ``config.json`` (defaults snapshot) if missing."""
    if CONFIG_PATH.is_file():
        return
    try:
        save_config(default_app_config())
    except OSError:
        pass


# ── Pipeline helpers (read from global config; no dict passing) ──────────────

_STEP_CONFIG_SECTIONS: tuple[str, ...] = (
    "pre_git", "common", "post_git", "android", "ios", "post_build",
)


def enabled_step_keys_from_config() -> frozenset[str]:
    """Step keys the user left enabled in ``config.json`` (union of all sections)."""
    cfg = get_app_config()
    out: set[str] = set()
    for sec in _STEP_CONFIG_SECTIONS:
        block = cfg.get(sec)
        if not isinstance(block, dict):
            continue
        steps = block.get("steps")
        if not isinstance(steps, dict):
            continue
        for k, v in steps.items():
            if v:
                out.add(str(k))
    return frozenset(out)


def pipeline_section_enabled(name: str, *, include_ios_default: bool = True) -> bool:
    """Whether a pipeline section alias is enabled per persisted config."""
    cfg = get_app_config()
    config_key = PIPELINE_SECTION_TO_CONFIG_SECTION.get(name, name)
    default_enabled = include_ios_default if config_key == "ios" else True
    return bool((cfg.get(config_key) or {}).get("enabled", default_enabled))


def pub_upgrade_from_config() -> bool:
    pm = str((get_app_config().get("common") or {}).get("pub_mode", "pub get")).lower()
    return pm == "pub upgrade"


def _shorebird_build_mode(block: dict[str, Any]) -> str:
    if block.get("shorebird"):
        return "patch" if str(block.get("shorebird_mode", "")).lower() == "patch" else "release"
    return "flutter"


def android_build_mode_from_config() -> str:
    return _shorebird_build_mode(get_app_config().get("android") or {})


def ios_build_mode_from_config() -> str:
    return _shorebird_build_mode(get_app_config().get("ios") or {})
