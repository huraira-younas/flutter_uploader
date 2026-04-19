"""Global app configuration: ``config.json`` + ``secrets/enviroment.json`` + in-process cache.

Pipeline/UI state lives in ``config.json``.  Secrets and paths live in
``secrets/enviroment.json`` (git-ignored) and are merged into the in-memory ``env`` section.

All consumers use ``get_app_config()`` / ``get_section()`` — do not thread config dicts
through UI or pipeline call chains.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import json
import sys
import os

from core.constants import (
    DEFAULT_COMMIT_MESSAGE_RELEASE,
    DEFAULT_COMMIT_MESSAGE_PRE,
    UPLOADER_DIR,
    SECRETS_DIR,
)

# Canonical mapping between pipeline section aliases and persisted config keys.
PIPELINE_SECTION_TO_CONFIG_SECTION: dict[str, str] = {
    "distribution": "distribution",
    "git_post": "post_git",
    "android": "android",
    "git_pre": "pre_git",
    "post": "post_build",
    "common": "common",
    "ios": "ios",
}


CONFIG_PATH: Path = UPLOADER_DIR / "config.json"
# Local secrets + paths (not committed); merged into the in-memory ``env`` section.
ENVIRONMENT_JSON_PATH: Path = SECRETS_DIR / "enviroment.json"

# Top-level keys in ``config.json`` / ``default_app_config()``.
CONFIG_SECTION_KEYS: tuple[str, ...] = (
    "distribution",
    "git_branch",
    "post_build",
    "post_git",
    "android",
    "pre_git",
    "common",
    "theme",
    "env",
    "ios",
)

_cache: dict[str, Any] | None = None
_section_cache: dict[str, Any] = {}


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
        "theme": "catppuccin_mocha",
        "git_branch": "master",
        "env": {
            "GOOGLE_DRIVE_CREDENTIALS_JSON": "",
            "GOOGLE_DRIVE_TOKEN_JSON": "",
            "GOOGLE_DRIVE_FOLDER_ID": "",
            "FLUTTER_PROJECT_ROOT": "",
            "APP_STORE_ISSUER_ID": "",
            "GMAIL_APP_PASSWORD": "",
            "APP_STORE_API_KEY": "",
            "LOGS_DISTRIBUTION": [],
            "DISTRIBUTION": [],
            "FLUTTER_BIN": "",
            "GMAIL_USER": "",
        },
        "pre_git": {
            "steps": {"git_commit_pre": True, "git_pull": True},
            "commit_message": DEFAULT_COMMIT_MESSAGE_PRE,
            "enabled": True,
        },
        "common": {
            "steps": {"clean": False, "pub_get": False},
            "pub_mode": "pub get",
            "enabled": True,
        },
        "post_git": {
            "steps": {"git_commit_rel": True, "git_push": True},
            "commit_message": DEFAULT_COMMIT_MESSAGE_RELEASE,
            "enabled": True,
        },
        "android": {
            "steps": {"build_apk": True, "build_aab": False},
            "enabled": True,
        },
        "ios": {
            "steps": {"pod_update": False, "build_ipa": True},
            "enabled": True,
        },
        "distribution": {
            "steps": {"google_play_upload": False, "appstore_upload": False, "drive_upload": True},
            "google_play_track": "production",
            "enabled": True,
        },
        "post_build": {
            "steps": {"open_folders": False, "shutdown": False},
            "power_mode": "Sleep" if sys.platform == "darwin" else "Shutdown",
            "quit_after_power": False,
            "enabled": True,
        },
    }


def parse_recipients(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in items:
        email = str(raw).strip()
        if not email:
            continue
        lowered = email.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        out.append(email)
    return out


def _load_json_object_file(path: Path) -> dict[str, Any]:
    """Read a JSON object from *path*; missing file, invalid JSON, or non-object root → ``{}``."""
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}

def _read_merged_from_disk() -> dict[str, Any]:
    base = default_app_config()
    merged = deep_merge(base, _load_json_object_file(CONFIG_PATH))
    file_env = _load_json_object_file(ENVIRONMENT_JSON_PATH)
    merged["env"] = deep_merge(merged.get("env") or {}, file_env)
    return merged


def init_app_config(*, force_reload: bool = False) -> dict[str, Any]:
    """Ensure ``config.json`` exists and populate the process-wide config cache.

    Safe to call multiple times; only reads from disk on the first call (or when forced).
    """
    global _cache
    ensure_config_file()
    if force_reload or _cache is None:
        _cache = _read_merged_from_disk()
    return _cache


def reload_app_config() -> dict[str, Any]:
    """Re-read ``config.json`` and ``secrets/enviroment.json`` from disk into the cache."""
    global _cache, _section_cache
    _section_cache.clear()
    _cache = _read_merged_from_disk()
    return _cache


def get_app_config() -> dict[str, Any]:
    """Return merged app config (defaults + file). Initializes cache if needed."""
    if _cache is None:
        return init_app_config()
    return _cache


def get_section(name: str) -> Any:
    """Return a deep copy of one top-level section (cached)."""
    global _section_cache
    if name in _section_cache:
        return copy.deepcopy(_section_cache[name])

    full = get_app_config()
    base_chunk = default_app_config().get(name, {})
    chunk = full.get(name, {})
    
    res = None
    if isinstance(chunk, dict):
        res = deep_merge(copy.deepcopy(base_chunk), copy.deepcopy(chunk))
    elif isinstance(base_chunk, list) and isinstance(chunk, list):
        res = copy.deepcopy(chunk)
    else:
        res = copy.deepcopy(base_chunk)
    
    _section_cache[name] = res
    return copy.deepcopy(res)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def save_config(data: dict[str, Any]) -> None:
    """Persist merged config: pipeline/UI state → ``config.json``; ``env`` → ``secrets/enviroment.json``."""
    global _cache, _section_cache
    _section_cache.clear()
    merged = deep_merge(default_app_config(), data)
    _cache = merged
    env_block = merged.get("env")
    if isinstance(env_block, dict):
        try:
            _atomic_write_json(ENVIRONMENT_JSON_PATH, env_block)
        except OSError:
            pass
    try:
        config_only = {k: v for k, v in merged.items() if k != "env"}
        _atomic_write_json(CONFIG_PATH, config_only)
    except OSError:
        pass


def ensure_config_file() -> None:
    """Create ``config.json`` (defaults snapshot) if missing. Does not write ``secrets/enviroment.json``."""
    if CONFIG_PATH.is_file():
        return
    try:
        config_only = {k: v for k, v in default_app_config().items() if k != "env"}
        _atomic_write_json(CONFIG_PATH, config_only)
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
    """Whether a pipeline section alias is enabled per persisted config.
    Defaults to True only if prerequisites are met (folders/keys exist)."""
    cfg = get_app_config()
    block = cfg.get("env")
    env = block if isinstance(block, dict) else {}
    root_raw = str(env.get("FLUTTER_PROJECT_ROOT") or "").strip()
    config_key = PIPELINE_SECTION_TO_CONFIG_SECTION.get(name, name)

    # Calculate smart default based on readiness
    if config_key == "android":
        default_enabled = bool(root_raw and (Path(root_raw).expanduser().resolve() / "android").is_dir())
    elif config_key == "ios":
        on_mac = sys.platform == "darwin"
        default_enabled = on_mac and include_ios_default and bool(
            root_raw and (Path(root_raw).expanduser().resolve() / "ios").is_dir()
        )
    elif config_key == "distribution":
        has_play = bool(env.get("GOOGLE_PLAY_JSON_KEY"))
        has_apple = bool(env.get("APP_STORE_ISSUER_ID") and env.get("APP_STORE_API_KEY"))
        has_drive = bool(env.get("GOOGLE_DRIVE_CREDENTIALS_JSON"))
        default_enabled = has_play or has_apple or has_drive
    else:
        default_enabled = True

    return default_enabled


def pub_upgrade_from_config() -> bool:
    pm = str((get_app_config().get("common") or {}).get("pub_mode", "pub get")).lower()
    return pm == "pub upgrade"


def _env_email_list(key: str) -> list[str]:
    env = get_app_config().get("env")
    if not isinstance(env, dict) or key not in env:
        return []
    block = env.get(key)
    if isinstance(block, list):
        return parse_recipients([str(v) for v in block])
    return []


def distribution_recipients_from_config() -> list[str]:
    return _env_email_list("DISTRIBUTION")


def logs_recipients_from_config() -> list[str]:
    """Emails that receive the HTML build report (``env.LOGS_DISTRIBUTION``)."""
    return _env_email_list("LOGS_DISTRIBUTION")


def distribution_recipients_csv_from_config() -> str | None:
    recipients = distribution_recipients_from_config()
    return ",".join(recipients) if recipients else None


def env_value(key: str, *, default: str = "") -> str:
    """Read an environment value from ``os.environ``, then merged ``env`` (``secrets/enviroment.json``)."""
    raw = os.environ.get(key, "").strip()
    if raw:
        return raw
    cfg = get_app_config()
    block = cfg.get("env")
    if isinstance(block, dict):
        v = str(block.get(key, "")).strip()
        if v:
            return v
    return default


def resolved_flutter_project_root_string() -> str:
    """Flutter project directory: ``FLUTTER_PROJECT_ROOT`` from process env or ``secrets/enviroment.json`` (merged ``env``)."""
    raw = os.environ.get("FLUTTER_PROJECT_ROOT", "").strip()
    if raw:
        return raw
    block = get_app_config().get("env")
    if isinstance(block, dict):
        return str(block.get("FLUTTER_PROJECT_ROOT", "")).strip()
    return ""
