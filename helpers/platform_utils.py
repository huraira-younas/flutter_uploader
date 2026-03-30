"""Platform detection and shutdown / sleep helpers."""

import os
import platform
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from uploader.core.constants import POWER_DELAY
from uploader.helpers.types import LogFn


def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_shorebird_available() -> bool:
    """Return True if the `shorebird` CLI is reachable on PATH and exits cleanly."""
    try:
        result = subprocess.run(
            ["shorebird", "--version"],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _schedule_power_action(label: str, action: Callable[[], None], log: LogFn) -> bool:
    log(f"{label} scheduled in {POWER_DELAY} seconds.\n")
    def _deferred():
        try:
            action()
        except Exception as e:
            log(f"{label} failed: {e}\n")
    timer = threading.Timer(POWER_DELAY, _deferred)
    timer.daemon = False
    timer.start()
    return True


def _shutdown_cmd() -> list[str]:
    system = platform.system()
    if system == "Windows":
        return ["shutdown", "/s", "/t", str(POWER_DELAY)]
    if system == "Darwin":
        return ["osascript", "-e", 'tell application "System Events" to shut down']
    return ["systemctl", "poweroff"]


def _sleep_cmd() -> list[str]:
    system = platform.system()
    if system == "Windows":
        return ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"]
    if system == "Darwin":
        return ["pmset", "sleepnow"]
    return ["systemctl", "suspend"]


def _run_power_cmd(cmd: list[str], log: LogFn | None = None, what: str = "command") -> None:
    kw: dict = {"capture_output": True, "check": True, "text": True, "timeout": 120}
    if platform.system() == "Windows" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        subprocess.run(cmd, **kw)
    except FileNotFoundError as e:
        if log:
            log(f"{what}: not found ({cmd[0]}): {e}\n")
        raise
    except subprocess.CalledProcessError as e:
        err = (e.stderr or "").strip()
        if log:
            log(f"{what} failed (exit {e.returncode}): {err or e}\n")
        raise
    except subprocess.TimeoutExpired as e:
        if log:
            log(f"{what} timed out: {e}\n")
        raise


def _run_macos_sleep(log: LogFn) -> None:
    """Put the Mac to sleep via ``pmset sleepnow`` (kernel). Tries common binary paths."""
    candidates = (
        ["/usr/bin/pmset", "sleepnow"],
        ["/usr/sbin/pmset", "sleepnow"],
    )
    last: Exception | None = None
    for cmd in candidates:
        try:
            _run_power_cmd(cmd, log=log, what="Sleep (pmset)")
            log("Sleep command finished (machine should sleep now).\n")
            return
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            last = e
    log(
        "Sleep failed: `pmset sleepnow` did not succeed. "
        "Confirm in Terminal: `/usr/bin/pmset sleepnow`. "
        "Energy settings or another app may be preventing sleep.\n"
    )
    if last:
        raise last


def shutdown_pc(log: LogFn) -> bool:
    """Schedule a shutdown after POWER_DELAY seconds."""
    if platform.system() == "Windows":
        try:
            _run_power_cmd(_shutdown_cmd(), log=log, what="Shutdown")
            log(f"Shutdown scheduled in {POWER_DELAY} seconds.\n")
            return True
        except Exception as e:
            log(f"Shutdown failed: {e}\n")
            return False
    return _schedule_power_action(
        "Shutdown",
        lambda: _run_power_cmd(_shutdown_cmd(), log=log, what="Shutdown"),
        log,
    )


def sleep_pc(log: LogFn) -> bool:
    """Schedule sleep after POWER_DELAY seconds."""
    if platform.system() == "Darwin":
        return _schedule_power_action("Sleep", lambda: _run_macos_sleep(log), log)
    return _schedule_power_action(
        "Sleep",
        lambda: _run_power_cmd(_sleep_cmd(), log=log, what="Sleep"),
        log,
    )


def open_folder(path: Path, log: LogFn) -> bool:
    """Open the given folder in the system file manager. Return True on success."""
    if not path.exists():
        log(f"Folder not found: {path}\n")
        return False
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)
        return True
    except Exception as e:
        log(f"{e}\n")
        return False
