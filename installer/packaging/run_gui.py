"""PyInstaller GUI entry-point — launches the graphical interface."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import traceback
import sys
import os

# app/run.py uses bare imports (``from core.xxx``, ``from gui.xxx``).
# Ensure the ``app/`` directory is on sys.path so they resolve at runtime.
_app_dir = str(Path(__file__).resolve().parent.parent.parent / "app")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)


def _startup_log_path() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "FlutterUploader" / "startup.log"
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", "").strip()
        root = Path(base).expanduser() if base else (Path.home() / "AppData" / "Local")
        return root / "FlutterUploader" / "startup.log"
    return Path.home() / ".cache" / "FlutterUploader" / "startup.log"


def _append_startup_log(message: str) -> None:
    path = _startup_log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(message.rstrip() + "\n")
    except OSError:
        pass


def _runtime_snapshot() -> str:
    lines = [
        f"[{datetime.now().isoformat(timespec='seconds')}] FlutterUploader startup",
        f"platform={sys.platform}",
        f"python={sys.version.split()[0]}",
        f"executable={sys.executable}",
        f"frozen={getattr(sys, 'frozen', False)}",
        f"argv={sys.argv}",
    ]
    try:
        import tkinter as tk
        lines.append(f"tk={getattr(tk, 'TkVersion', '?')} tcl={getattr(tk, 'TclVersion', '?')}")
    except Exception as exc:
        lines.append(f"tk_import_error={exc}")
    return "\n".join(lines)


from app.run import main

if __name__ == "__main__":
    _append_startup_log(_runtime_snapshot())
    try:
        main()
    except Exception:
        _append_startup_log("startup_exception:\n" + traceback.format_exc())
        raise
