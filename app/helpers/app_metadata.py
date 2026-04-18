from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
import plistlib
import re

def extract_android_pkg_name(project_root: Path) -> str | None:
    """Attempt to find the Android package name (applicationId or namespace) in build.gradle."""
    gradle_path = project_root / "android" / "app" / "build.gradle"
    if not gradle_path.exists():
        return None
    
    try:
        content = gradle_path.read_text(encoding="utf-8")
        # Try applicationId
        match = re.search(r'applicationId\s+["\']([^"\']+)["\']', content)
        if match:
            return match.group(1).strip()
        # Try namespace (modern AGP 7+)
        match = re.search(r'namespace\s+["\']([^"\']+)["\']', content)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return None

def get_current_app_name() -> str:
    """Centralized helper to get the app name with full error handling and fallback."""
    try:
        from core.constants import flutter_project_root
        return _extract_app_name(flutter_project_root())
    except Exception:
        return "Flutter Uploader"

def _extract_app_name(project_root: Path) -> str:
    """
    Unified App Name extraction from Android, iOS or pubspec.yaml.
    Returns "Flutter App" if nothing is found.
    """
    # 1. Try iOS (usually the most reliable for 'Display Name')
    ios_name = _extract_ios_app_name(project_root)
    if ios_name:
        return ios_name

    # 2. Try Android
    android_name = _extract_android_app_name(project_root)
    if android_name:
        return android_name

    # 3. Fallback to pubspec 'name'
    pubspec_name = _extract_pubspec_name(project_root)
    if pubspec_name:
        # Clean up snakeify if needed, but per user request "show AppName only"
        return pubspec_name.replace("_", " ").title()

    return "Flutter App"

def _extract_ios_app_name(project_root: Path) -> str | None:
    plist_path = project_root / "ios" / "Runner" / "Info.plist"
    if not plist_path.exists():
        return None
    try:
        data = plistlib.loads(plist_path.read_bytes())
        return data.get("CFBundleDisplayName") or data.get("CFBundleName")
    except Exception:
        return None

def _extract_android_app_name(project_root: Path) -> str | None:
    manifest_path = project_root / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if not manifest_path.exists():
        return None
    
    try:
        # Namespace handling for Android
        ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        application = root.find("application")
        if application is None:
            return None
        
        label = application.get("{http://schemas.android.com/apk/res/android}label")
        if not label:
            return None

        if label.startswith("@string/"):
            string_name = label.replace("@string/", "")
            return _extract_android_string_resource(project_root, string_name)
        
        return label
    except Exception:
        return None

def _extract_android_string_resource(project_root: Path, name: str) -> str | None:
    strings_path = project_root / "android" / "app" / "src" / "main" / "res" / "values" / "strings.xml"
    if not strings_path.exists():
        return None
    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
        for s in root.findall("string"):
            if s.get("name") == name:
                return s.text
    except Exception:
        pass
    return None

def _extract_pubspec_name(project_root: Path) -> str | None:
    pubspec_path = project_root / "pubspec.yaml"
    if not pubspec_path.exists():
        return None
    try:
        text = pubspec_path.read_text(encoding="utf-8")
        match = re.search(r"^name:\s*(\S+)", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return None
