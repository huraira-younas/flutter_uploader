"""Read / write the version+build from pubspec.yaml (single source of truth)."""

from pathlib import Path
import tempfile
import os

from core.project_state import ProjectRootNotConfiguredError, pubspec_path, register_cache_cleaner
from core.constants import VERSION_RE

_version_cache: tuple[str, str] | None = None
_FALLBACK_VERSION = ("0.0.0", "1")


def clear_version_cache() -> None:
    """Wipe the version cache (call this when project root changes or version is written)."""
    global _version_cache
    _version_cache = None

register_cache_cleaner(clear_version_cache)


def read_version() -> tuple[str, str]:
    """Return (version, build) from pubspec.yaml, e.g. ('1.0.6', '65').
    
    Cached in-memory to avoid repeated disk reads.
    """
    global _version_cache
    if _version_cache:
        return _version_cache
    try:
        pubspec = pubspec_path()
        text = pubspec.read_text(encoding="utf-8")
    except (ProjectRootNotConfiguredError, OSError):
        return _FALLBACK_VERSION
    m = VERSION_RE.search(text)
    if not m:
        return _FALLBACK_VERSION
    raw = m.group(2)
    if "+" in raw:
        ver, build = raw.split("+", 1)
    else:
        ver, build = raw, "1"
    
    _version_cache = (ver.strip(), build.strip())
    return _version_cache


def write_version(version: str, build: str) -> None:
    """Atomically update pubspec.yaml with the given version+build."""
    clear_version_cache()
    pubspec = pubspec_path()
    text = pubspec.read_text(encoding="utf-8")
    new_text = VERSION_RE.sub(rf"\g<1>{version}+{build}", text)
    fd, tmp_path = tempfile.mkstemp(dir=pubspec.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new_text)
        Path(tmp_path).replace(pubspec)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
