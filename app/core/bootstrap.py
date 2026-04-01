"""Runtime bootstrap helpers for CLI and GUI entrypoints."""

from __future__ import annotations

from collections.abc import Callable
from core.constants import UPLOADER_DIR
import subprocess
import sys


def _run_pip(args: list[str], log: Callable[[str], None]) -> int:
    proc = subprocess.Popen(
        [sys.executable, "-m", "pip"] + args,
        cwd=UPLOADER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    try:
        for line in proc.stdout:
            log(line)
    finally:
        if proc.stdout:
            proc.stdout.close()
        proc.wait()
    return proc.returncode


def ensure_dependencies(log: Callable[[str], None] = print) -> None:
    """Install requirements and run pip check if requirements.txt is present."""
    reqs = UPLOADER_DIR / "requirements.txt"
    if not reqs.exists():
        log(">> No requirements.txt found; skipping dependency check.\n")
        return
    log(f">> Verifying dependencies from {reqs.name}...\n")
    code = _run_pip(["install", "-r", str(reqs)], log=log)
    if code != 0:
        log(f">> pip install exited with code {code}\n")
        return
    log(">> Running pip check...\n")
    chk = _run_pip(["check"], log=log)
    if chk == 0:
        log(">> All requirements satisfied (pip check OK).\n")
    else:
        log(f">> pip check exited with {chk}; see messages above.\n")
