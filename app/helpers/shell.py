"""Run shell commands and stream output to a log callback."""

from threading import Lock, Thread
from queue import Empty, Queue
from pathlib import Path
import subprocess
import signal
import shutil
import os
import sys

from core.constants import IS_WIN, ORPHAN_PATTERNS
from helpers.types import LogFn, StopCheckFn
from core.config_store import env_value, get_app_config, get_section, save_config

_ACTIVE_PROCS: set[subprocess.Popen[str]] = set()
_PROCS_LOCK = Lock()
_EOF = object()

_CACHED_FLUTTER_BIN: str | None = None
_PERSISTED_FLUTTER_BIN: bool = False
_PATH_SEP = os.pathsep


def _looks_utf8(raw: str) -> bool:
    return "utf-8" in str(raw or "").lower() or "utf8" in str(raw or "").lower()


def _ensure_utf8_locale(env: dict[str, str]) -> None:
    """Force UTF-8 locale for tools like CocoaPods when launched from GUI."""
    if os.name == "nt":
        return
    target = "en_US.UTF-8" if sys.platform == "darwin" else "C.UTF-8"
    lang = env.get("LANG", "")
    lc_all = env.get("LC_ALL", "")
    lc_ctype = env.get("LC_CTYPE", "")
    if not _looks_utf8(lang):
        env["LANG"] = target
    if not lc_all or not _looks_utf8(lc_all):
        env["LC_ALL"] = target
    if not _looks_utf8(lc_ctype):
        env["LC_CTYPE"] = target


def _normalize_path_seg(p: str) -> str:
    """Expand env/user tokens; normalize slashes on Windows."""
    expanded = os.path.expandvars(os.path.expanduser(p)) if IS_WIN else os.path.expanduser(p)
    return os.path.normpath(expanded) if IS_WIN else expanded


def _split_path(raw: str) -> list[str]:
    parts = [p.strip() for p in str(raw or "").split(_PATH_SEP)]
    return [p for p in parts if p]


def _is_executable_file(path: Path) -> bool:
    try:
        return path.is_file() and os.access(path, os.X_OK)
    except OSError:
        return False


def _is_flutter_invokable(path: Path) -> bool:
    """True if *path* can be passed to ``Popen`` as the Flutter CLI (mac + Windows)."""
    try:
        if not path.is_file():
            return False
    except OSError:
        return False
    if IS_WIN:
        suf = path.suffix.lower()
        return suf in (".bat", ".cmd", ".exe") or (suf == "" and _is_executable_file(path))
    return _is_executable_file(path)


def _flutter_filenames_in_bin_dir(bin_dir: Path) -> list[Path]:
    """Ordered candidates inside a Flutter SDK ``bin`` directory."""
    if IS_WIN:
        return [
            bin_dir / "flutter.bat",
            bin_dir / "flutter.cmd",
            bin_dir / "flutter.exe",
            bin_dir / "flutter",
        ]
    return [bin_dir / "flutter"]


def _windows_registry_path_entries() -> list[str]:
    """User + machine PATH from registry (GUI apps often lack the full interactive PATH)."""
    try:
        import winreg
    except ImportError:
        return []
    out: list[str] = []
    for root, subkey in (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, r"Environment"),
    ):
        try:
            with winreg.OpenKey(root, subkey) as k:
                path_val, _ = winreg.QueryValueEx(k, "PATH")
                out.extend(_normalize_path_seg(x) for x in _split_path(str(path_val)))
        except OSError:
            continue
    return out


def _resolve_tool_override(executable: str) -> str | None:
    """Resolve an explicit tool path override for known tools.

    Supported config/env keys:
    - FLUTTER_BIN: absolute path to flutter executable (highest priority)
    """
    exe = str(executable).strip()
    if exe != "flutter":
        return None

    flutter_bin = env_value("FLUTTER_BIN").strip()
    if flutter_bin:
        p = Path(flutter_bin).expanduser().resolve()
        return str(p) if _is_flutter_invokable(p) else None

    return None


def _default_path_entries() -> list[str]:
    """Best-effort PATH for GUI-launched apps (minimal env from Finder / Windows shell)."""
    if IS_WIN:
        home = Path.home()
        la = os.environ.get("LOCALAPPDATA", "").strip()
        candidates: list[str] = _windows_registry_path_entries() + [
            str(home / "flutter" / "bin"),
            str(home / "development" / "flutter" / "bin"),
            str(home / "src" / "flutter" / "bin"),
            str(Path("C:/src/flutter/bin")),
            str(Path("C:/flutter/bin")),
            str(Path("C:/tools/flutter/bin")),
            *( [str(Path(la) / "flutter" / "bin")] if la else [] ),
            r"C:\Program Files\Git\cmd",
            r"C:\Program Files (x86)\Git\cmd",
        ]
        out: list[str] = []
        seen: set[str] = set()
        for p in candidates:
            norm = _normalize_path_seg(p)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            if os.path.isdir(norm):
                out.append(norm)
        return out

    candidates: list[str] = [
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
        "/usr/local/sbin",
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
    ]
    out: list[str] = []
    seen: set[str] = set()
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        if os.path.isdir(p):
            out.append(p)
    return out


def _build_subprocess_env() -> dict[str, str]:
    """Build a stable env for subprocesses, especially for packaged GUI apps."""
    env = {k: str(v) for k, v in os.environ.items()}
    base_path = _split_path(env.get("PATH", ""))
    default_entries = _default_path_entries()

    merged: list[str] = []
    seen: set[str] = set()
    for p in base_path + default_entries:
        seg = _normalize_path_seg(p) if IS_WIN else p
        if not seg or seg in seen:
            continue
        seen.add(seg)
        merged.append(seg)
    env["PATH"] = _PATH_SEP.join(merged)
    _ensure_utf8_locale(env)
    return env


def _flutter_candidate_paths(*, cwd: Path | None = None) -> list[Path]:
    """Common Flutter install locations + FVM project SDK (macOS and Windows)."""
    home = Path.home()
    bin_dirs: list[Path] = [
        home / "flutter" / "bin",
        home / "development" / "flutter" / "bin",
        home / "Developer" / "flutter" / "bin",
        home / "sdk" / "flutter" / "bin",
        home / "Documents" / "flutter" / "bin",
        home / "src" / "flutter" / "bin",
        home / "fvm" / "default" / "bin",
    ]
    if IS_WIN:
        la = os.environ.get("LOCALAPPDATA", "").strip()
        if la:
            bin_dirs.append(Path(la) / "flutter" / "bin")
        bin_dirs.extend(
            [
                Path(r"C:\src\flutter\bin"),
                Path(r"C:\flutter\bin"),
                Path(r"C:\tools\flutter\bin"),
            ]
        )
    else:
        bin_dirs.extend(
            [
                Path("/opt/homebrew/bin"),
                Path("/usr/local/bin"),
                Path("/usr/bin"),
            ]
        )

    candidates: list[Path] = []
    for d in bin_dirs:
        candidates.extend(_flutter_filenames_in_bin_dir(d))

    if not IS_WIN:
        candidates.extend(
            [
                Path("/opt/homebrew/bin/flutter"),
                Path("/usr/local/bin/flutter"),
                Path("/usr/bin/flutter"),
            ]
        )

    if cwd:
        try:
            p = cwd.expanduser().resolve()
        except OSError:
            p = None
        if p:
            for rel in (
                p / ".fvm" / "flutter_sdk" / "bin",
                p / "ios" / ".fvm" / "flutter_sdk" / "bin",
            ):
                candidates.extend(_flutter_filenames_in_bin_dir(rel))
    return candidates


def _autodetect_flutter_bin(*, env: dict[str, str], cwd: Path) -> str | None:
    """Locate flutter without user configuration (session cache)."""
    global _CACHED_FLUTTER_BIN
    if _CACHED_FLUTTER_BIN:
        p = Path(_CACHED_FLUTTER_BIN)
        if _is_flutter_invokable(p):
            return _CACHED_FLUTTER_BIN
        _CACHED_FLUTTER_BIN = None

    path_var = env.get("PATH", "")
    found = shutil.which("flutter", path=path_var)
    if found:
        _CACHED_FLUTTER_BIN = found
        return found
    if IS_WIN:
        found_bat = shutil.which("flutter.bat", path=path_var)
        if found_bat:
            _CACHED_FLUTTER_BIN = found_bat
            return found_bat

    for p in _flutter_candidate_paths(cwd=cwd):
        if _is_flutter_invokable(p):
            _CACHED_FLUTTER_BIN = str(p.resolve())
            return _CACHED_FLUTTER_BIN
    return None


def _persist_detected_flutter_bin(path: str) -> None:
    """Persist the detected flutter path so next launch doesn't need scanning."""
    global _PERSISTED_FLUTTER_BIN
    if _PERSISTED_FLUTTER_BIN:
        return

    if env_value("FLUTTER_BIN").strip():
        _PERSISTED_FLUTTER_BIN = True
        return

    p = Path(path).expanduser()
    if not _is_flutter_invokable(p):
        return

    try:
        merged = {**get_app_config(), "env": {**get_section("env"), "FLUTTER_BIN": str(p.resolve())}}
        save_config(merged)
        _PERSISTED_FLUTTER_BIN = True
    except Exception:
        return


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

    if not cwd.exists():
        log(f"\nError: working directory not found: {cwd}\n")
        return False

    executable = cmd[0]
    env = _build_subprocess_env()
    resolved_executable = _resolve_tool_override(executable) or shutil.which(executable, path=env.get("PATH", ""))
    if resolved_executable is None and executable == "flutter":
        detected = _autodetect_flutter_bin(env=env, cwd=cwd)
        if detected:
            try:
                flutter_bin_dir = str(Path(detected).resolve().parent)
            except OSError:
                flutter_bin_dir = ""
            if flutter_bin_dir:
                env["PATH"] = _PATH_SEP.join([flutter_bin_dir] + _split_path(env.get("PATH", "")))
            resolved_executable = detected
            _persist_detected_flutter_bin(detected)

    if resolved_executable is None:
        if executable == "flutter":
            verify_hint = (
                "You can verify in Command Prompt: `where flutter` then `flutter --version`.\n"
                if IS_WIN
                else "You can verify in Terminal: `which flutter` then `flutter --version`.\n"
            )
            log(
                "\nError: command not found: 'flutter'.\n"
                "Make sure Flutter is installed and on PATH (or use a default install location).\n"
                "Tip: Flutter Uploader auto-detects common installs; for custom locations set FLUTTER_BIN in Settings → Environment.\n"
                + verify_hint
            )
        else:
            verify_hint = (
                f"You can verify in Command Prompt: `where {executable}`.\n"
                if IS_WIN
                else f"You can verify in Terminal: `which {executable}`.\n"
            )
            log(
                f"\nError: command not found: '{executable}'.\n"
                "Make sure required build tools are installed and available on PATH.\n"
                + verify_hint
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
            errors="replace",
            cwd=cwd,
            env=env,
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
