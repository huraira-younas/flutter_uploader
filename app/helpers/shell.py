"""Run shell commands and stream output to a log callback."""

from threading import Lock, Thread
from queue import Empty, Queue
from pathlib import Path
import subprocess
import signal
import shutil
import os

from core.constants import IS_WIN, ORPHAN_PATTERNS
from helpers.types import LogFn, StopCheckFn

_ACTIVE_PROCS: set[subprocess.Popen[str]] = set()
_PROCS_LOCK = Lock()
_EOF = object()


def _register_process(proc: subprocess.Popen[str]) -> None:
    with _PROCS_LOCK:
        _ACTIVE_PROCS.add(proc)


def _unregister_process(proc: subprocess.Popen[str]) -> None:
    with _PROCS_LOCK:
        _ACTIVE_PROCS.discard(proc)


def _force_kill_tree(pid: int) -> None:
    """Immediately force-kill process and all children. Cross-platform."""
    if IS_WIN:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True, timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            pass
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def _terminate_proc(
    proc: subprocess.Popen[str],
    *,
    log: LogFn | None = None,
) -> None:
    """Force-kill a process and its entire child tree. Always unregisters."""
    if proc.poll() is not None:
        _unregister_process(proc)
        return
    try:
        _force_kill_tree(proc.pid)
        proc.kill()
        proc.wait(timeout=2)
    except Exception:
        pass
    finally:
        _unregister_process(proc)
    if log:
        log("Force-killed subprocess.\n")


def _kill_orphaned_build_daemons() -> None:
    """Kill build tool daemons that escape process-group kill (e.g., Gradle daemon).

    The Gradle daemon does double-fork + setsid, landing in its own session.
    os.killpg() cannot reach it, so we pattern-match and SIGKILL directly.
    Safe because Gradle auto-starts a new daemon on the next build.
    """
    if IS_WIN:
        for pattern in ORPHAN_PATTERNS:
            try:
                subprocess.run(
                    ["wmic", "process", "where",
                     f"commandline like '%{pattern}%'",
                     "call", "terminate"],
                    capture_output=True, timeout=5,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except Exception:
                pass
    else:
        for pattern in ORPHAN_PATTERNS:
            try:
                subprocess.run(
                    ["pkill", "-9", "-f", pattern],
                    capture_output=True, timeout=5,
                )
            except Exception:
                pass


def terminate_active_processes(log: LogFn | None = None) -> None:
    """Terminate any still-running child processes started by run_cmd()."""
    with _PROCS_LOCK:
        dead = [p for p in _ACTIVE_PROCS if p.poll() is not None]
        for p in dead:
            _ACTIVE_PROCS.discard(p)
        procs = list(_ACTIVE_PROCS)
    for proc in procs:
        _terminate_proc(proc, log=log)
    _kill_orphaned_build_daemons()


def run_cmd(
    cmd: list[str],
    cwd: Path,
    log: LogFn,
    *,
    header: str | None = None,
    stop_check: StopCheckFn | None = None,
) -> bool:
    """Run a command; log stdout/stderr via log() in real time. Return True if returncode is 0."""
    if not cmd:
        log("Error: empty command.\n")
        return False

    if header:
        log(header)

    executable = cmd[0]
    resolved_executable = shutil.which(executable)

    if resolved_executable is None:
        log(
            f"\nError: command not found: '{executable}'.\n"
            "Make sure Flutter is installed and available in PATH.\n"
            "You can verify in terminal with: flutter --version\n"
        )
        return False

    run_args = list(cmd)
    run_args[0] = resolved_executable

    proc: subprocess.Popen[str] | None = None
    try:
        # GUI apps on Windows have no console; without CREATE_NO_WINDOW, child
        # console programs (e.g. flutter.bat) get a new cmd window.
        _no_win = (
            {"creationflags": subprocess.CREATE_NO_WINDOW}
            if IS_WIN and hasattr(subprocess, "CREATE_NO_WINDOW")
            else {}
        )
        proc = subprocess.Popen(
            run_args,
            start_new_session=not IS_WIN,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            bufsize=1,
            text=True,
            cwd=cwd,
            **_no_win,
        )
        _register_process(proc)
    except FileNotFoundError as exc:
        log(
            f"\nError: failed to start command: {exc}\n"
            "Make sure required tools are installed and in PATH.\n"
        )
        return False
    except Exception as exc:
        log(f"\nError running command {' '.join(run_args)}: {exc}\n")
        return False

    def reader(out, q: Queue) -> None:
        try:
            buf = ""
            while True:
                chunk = out.read(512)
                if not chunk:
                    if buf.strip():
                        q.put(buf.strip() + "\n")
                    break
                buf += chunk
                while "\n" in buf or "\r" in buf:
                    ni, ri = buf.find("\n"), buf.find("\r")
                    if ni == -1:
                        idx = ri
                    elif ri == -1:
                        idx = ni
                    else:
                        idx = min(ni, ri)
                    line = buf[:idx].strip()
                    buf = buf[idx + 1:]
                    if line:
                        q.put(line + "\n")
        except Exception:
            pass
        finally:
            q.put(_EOF)

    stopped_by_user = False
    reader_thread: Thread | None = None
    try:
        if proc.stdout:
            q: Queue = Queue()
            reader_thread = Thread(target=reader, args=(proc.stdout, q), daemon=True)
            reader_thread.start()
            while True:
                if stop_check and stop_check():
                    log("\nStopped by user.\n")
                    stopped_by_user = True
                    _terminate_proc(proc, log=log)
                    break
                try:
                    item = q.get(timeout=0.25)
                except Empty:
                    if not reader_thread.is_alive() and q.empty():
                        break
                    continue
                if item is _EOF:
                    break
                log(item)
            if proc.poll() is None and not stopped_by_user:
                proc.wait()
        else:
            proc.wait()
        return proc.returncode == 0 and not stopped_by_user
    except Exception as exc:
        log(f"\nError while reading process output: {exc}\n")
        _terminate_proc(proc, log=log)
        return False
    finally:
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
        if reader_thread is not None:
            reader_thread.join(timeout=2)
        if proc.poll() is None:
            _terminate_proc(proc)
        else:
            _unregister_process(proc)


class CommandRunner:
    """Bound command runner that avoids passing cwd throughout the call graph."""

    def __init__(self, *, project_root: Path):
        self.project_root = project_root

    def run_in(
        self,
        cmd: list[str],
        cwd: Path,
        log: LogFn,
        *,
        header: str | None = None,
        stop_check: StopCheckFn | None = None,
    ) -> bool:
        return run_cmd(cmd, cwd, log, header=header, stop_check=stop_check)

    def run_project(
        self,
        cmd: list[str],
        log: LogFn,
        *,
        header: str | None = None,
        stop_check: StopCheckFn | None = None,
    ) -> bool:
        return self.run_in(cmd, self.project_root, log, header=header, stop_check=stop_check)
