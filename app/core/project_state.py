"""Active Flutter project state: root path management and path resolution logic."""

from __future__ import annotations
from .constants import SECRETS_DIR
from pathlib import Path
import json
import os

_flutter_project_root: Path | None = None
_CACHE_CLEANERS: list[callable] = []

class ProjectRootNotConfiguredError(FileNotFoundError):
    """Raised when FLUTTER_PROJECT_ROOT is missing or invalid."""

def register_cache_cleaner(fn: callable) -> None:
    """Register a callback to be called when the project root changes."""
    if fn not in _CACHE_CLEANERS:
        _CACHE_CLEANERS.append(fn)

def require_flutter_project_root() -> Path:
    """Resolve FLUTTER_PROJECT_ROOT from env or persisted config (cached after first success)."""
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
    
    # Trigger all registered cache cleaners
    for cleaner in _CACHE_CLEANERS:
        try:
            cleaner()
        except Exception:
            pass

def apk_dir() -> Path:
    return require_flutter_project_root() / "build" / "app" / "outputs" / "flutter-apk"

def aab_dir() -> Path:
    return require_flutter_project_root() / "build" / "app" / "outputs" / "bundle" / "release"

def ipa_dir() -> Path:
    return require_flutter_project_root() / "build" / "ios" / "ipa"

def pubspec_path() -> Path:
    return require_flutter_project_root() / "pubspec.yaml"
