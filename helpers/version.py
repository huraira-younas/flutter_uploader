"""Read / write the version+build from pubspec.yaml (single source of truth)."""

import os
import tempfile
from pathlib import Path

from uploader.core.constants import PUBSPEC, VERSION_RE


def read_version() -> tuple[str, str]:
    """Return (version, build) from pubspec.yaml, e.g. ('1.0.6', '65')."""
    text = PUBSPEC.read_text(encoding="utf-8")
    m = VERSION_RE.search(text)
    if not m:
        return ("0.0.0", "1")
    raw = m.group(2)
    if "+" in raw:
        ver, build = raw.split("+", 1)
    else:
        ver, build = raw, "1"
    return (ver.strip(), build.strip())


def write_version(version: str, build: str) -> None:
    """Atomically update pubspec.yaml with the given version+build."""
    text = PUBSPEC.read_text(encoding="utf-8")
    new_text = VERSION_RE.sub(rf"\g<1>{version}+{build}", text)
    fd, tmp_path = tempfile.mkstemp(dir=PUBSPEC.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new_text)
        Path(tmp_path).replace(PUBSPEC)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
