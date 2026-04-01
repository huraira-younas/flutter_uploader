"""PyInstaller GUI entry-point — launches the graphical interface."""

from __future__ import annotations

from pathlib import Path
import sys

# app/run.py uses bare imports (``from core.xxx``, ``from gui.xxx``).
# Ensure the ``app/`` directory is on sys.path so they resolve at runtime.
_app_dir = str(Path(__file__).resolve().parent.parent.parent / "app")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from app.run import main

if __name__ == "__main__":
    main()
