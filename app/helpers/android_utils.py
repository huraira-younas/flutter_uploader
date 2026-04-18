from __future__ import annotations
from pathlib import Path
import re

def extract_package_name(project_root: Path) -> str | None:
    """Attempt to find the Android package name (applicationId or namespace) in build.gradle."""
    gradle_path = project_root / "android" / "app" / "build.gradle"
    if not gradle_path.exists():
        return None
    
    try:
        content = gradle_path.read_text(encoding="utf-8")
        
        # 1. Try applicationId (standard for many projects)
        match = re.search(r'applicationId\s+["\']([^"\']+)["\']', content)
        if match:
            return match.group(1).strip()
            
        # 2. Try namespace (modern AGP 7+ standard)
        match = re.search(r'namespace\s+["\']([^"\']+)["\']', content)
        if match:
            return match.group(1).strip()
            
    except Exception:
        pass
        
    return None
