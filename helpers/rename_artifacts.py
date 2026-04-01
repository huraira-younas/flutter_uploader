"""Copy APK/IPA into ``outputs/`` with versioned names (Flutter ``build/`` untouched)."""

from pathlib import Path
import shutil
import re

from core.constants import OUTPUTS_DIR, ABI_PATTERN, PLAIN_RELEASE, apk_dir, ipa_dir
from helpers.types import LogFn


def _sanitize(s: str) -> str:
    return re.sub(r"[^\w.+\-]", "", (s or "").strip()) or "0"


def clear_outputs() -> None:
    """Wipe outputs/ for a fresh pipeline run."""
    if OUTPUTS_DIR.exists():
        shutil.rmtree(OUTPUTS_DIR)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _apk_dest_name(name: str, v: str, b: str) -> str | None:
    """Derive versioned filename for an APK, or None to skip."""
    m = ABI_PATTERN.match(name)
    if m:
        return f"v{v}+{b}.{m.group(1)}.apk"
    if PLAIN_RELEASE.match(name):
        return f"v{v}+{b}.apk"
    return None


def _copy_apks(v: str, b: str, log: LogFn, dest: Path) -> bool:
    apks = sorted(apk_dir().glob("*.apk"))
    if not apks:
        log("No APK files found to copy.\n")
        return True

    log(f"Copying APKs to outputs …\n")
    for apk in apks:
        new_name = _apk_dest_name(apk.name, v, b)
        if not new_name:
            log(f"  Skip: {apk.name}\n")
            continue
        try:
            shutil.copy2(str(apk), str(dest / new_name))
            log(f"  {apk.name} → {new_name}\n")
        except OSError as e:
            log(f"  Copy failed: {e}\n")
            return False
    return True


def _copy_ipas(v: str, b: str, log: LogFn, dest: Path) -> bool:
    ipas = sorted(ipa_dir().glob("*.ipa"))
    if not ipas:
        log("No IPA files found to copy.\n")
        return True

    log(f"Copying IPAs → v{v}+{b}.ipa\n")
    for idx, ipa in enumerate(ipas):
        suffix = f".{idx}" if idx > 0 else ""
        new_name = f"v{v}+{b}{suffix}.ipa"
        try:
            shutil.copy2(str(ipa), str(dest / new_name))
            log(f"  {ipa.name} → {new_name}\n")
        except OSError as e:
            log(f"  Copy failed: {e}\n")
            return False
    return True


def copy_apks_to_outputs(version: str, build: str, log: LogFn) -> bool:
    """Copy APK artifacts to outputs/ immediately after build."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    v, b = _sanitize(version), _sanitize(build)
    if not v or not b:
        return True
    return _copy_apks(v, b, log, OUTPUTS_DIR)


def copy_ipas_to_outputs(version: str, build: str, log: LogFn) -> bool:
    """Copy IPA artifacts to outputs/ immediately after build."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    v, b = _sanitize(version), _sanitize(build)
    if not v or not b:
        return True
    return _copy_ipas(v, b, log, OUTPUTS_DIR)


