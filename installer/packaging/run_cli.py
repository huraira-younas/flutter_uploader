"""PyInstaller CLI entry-point — forces headless mode."""

from __future__ import annotations

import sys

from app.run import main

if __name__ == "__main__":
    if "--cli" not in sys.argv:
        sys.argv.insert(1, "--cli")
    main()
