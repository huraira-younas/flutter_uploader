"""GUI/CLI entry: ``python run.py`` · ``--cli`` · ``--list-steps`` · ``--no-install``."""

from collections import deque
import subprocess
import argparse
import threading
import time
import sys

from core.constants import (
    MAX_REPORT_LOG_LINES,
    UPLOADER_DIR,
    StepResult,
    APP_TITLE,
    DEFAULT_COMMIT_MESSAGE_PRE,
    DEFAULT_COMMIT_MESSAGE_RELEASE,
)


def _load_dotenv() -> None:
    from core.constants import load_dotenv_files

    load_dotenv_files()


def _run_pip(args: list[str], log=print) -> int:
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


def _ensure_deps(log=print) -> None:
    reqs = UPLOADER_DIR / "requirements.txt"
    if not reqs.exists():
        log(">> No requirements.txt found; skipping dependency check.\n")
        return
    log(f">> Verifying dependencies from {reqs.name}…\n")
    code = _run_pip(["install", "-r", str(reqs)], log=log)
    if code != 0:
        log(f">> pip install exited with code {code}\n")
        return
    log(">> Running pip check…\n")
    chk = _run_pip(["check"], log=log)
    if chk == 0:
        log(">> All requirements satisfied (pip check OK).\n")
    else:
        log(f">> pip check exited with {chk}; see messages above.\n")


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 run.py",
        description=f"{APP_TITLE} — automation-friendly CLI for the build & upload pipeline.",
        epilog="Run parameters and section toggles apply only with --cli. "
        "See CLI_REFERENCE.md and ENVIRONMENT.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--cli", action="store_true",
        help="Run headlessly (no GUI).",
    )
    parser.add_argument(
        "--no-install", action="store_true",
        help="Skip automatic pip dependency check.",
    )
    parser.add_argument(
        "--list-steps", action="store_true",
        help="Print all valid step keys and exit.",
    )

    run = parser.add_argument_group("run parameters")
    run.add_argument("--version", metavar="VER", help="App version (default: from pubspec.yaml).")
    run.add_argument("--build", metavar="NUM", help="Build number (default: from pubspec.yaml).")
    run.add_argument("--recipients", metavar="EMAILS", help="Comma-separated email addresses for Drive link.")
    run.add_argument(
        "--commit-message", metavar="MSG", default=DEFAULT_COMMIT_MESSAGE_PRE,
        help="Pre-Git commit message (default: %(default)s).",
    )
    run.add_argument(
        "--release-commit-message", metavar="MSG",
        default=DEFAULT_COMMIT_MESSAGE_RELEASE,
        dest="release_commit_message",
        help="Post-Git release commit template; {version} and {build} are substituted (default: %(default)s).",
    )
    run.add_argument(
        "--pub-mode", choices=["pub-get", "pub-upgrade"], default="pub-get",
        help="Dependency resolution mode (default: pub-get).",
    )
    run.add_argument(
        "--android-mode", choices=["flutter", "release", "patch"], default="flutter",
        help="Android build mode (default: flutter).",
    )
    run.add_argument(
        "--ios-mode", choices=["flutter", "release", "patch"], default="flutter",
        help="iOS build mode (default: flutter).",
    )
    run.add_argument(
        "--power-mode", choices=["shutdown", "sleep"], default="shutdown",
        help="Power action after pipeline (default: shutdown).",
    )
    run.add_argument(
        "--quit-after-power", action="store_true",
        help="After a successful shutdown/sleep step, wait the same delay as that action, then exit.",
    )

    sections = parser.add_argument_group("section toggles")
    for key in ("common", "android", "ios", "post"):
        sections.add_argument(
            f"--{key}", action="store_true", default=None, dest=f"{key}_on",
            help=f"Enable {key} section.",
        )
        sections.add_argument(
            f"--no-{key}", action="store_false", dest=f"{key}_on",
            help=f"Disable {key} section.",
        )

    git_sections = parser.add_argument_group("git section toggles")
    git_sections.add_argument(
        "--pre-git", action="store_true", default=None, dest="pre_git_on",
        help="Enable Pre-Git section (pre-release commit).",
    )
    git_sections.add_argument(
        "--no-pre-git", action="store_false", dest="pre_git_on",
        help="Disable Pre-Git section.",
    )
    git_sections.add_argument(
        "--post-git", action="store_true", default=None, dest="post_git_on",
        help="Enable Post-Git section (pull, release commit, push).",
    )
    git_sections.add_argument(
        "--no-post-git", action="store_false", dest="post_git_on",
        help="Disable Post-Git section.",
    )
    git_sections.add_argument(
        "--git", action="store_true", default=None, dest="git_on",
        help="Enable both Pre-Git and Post-Git sections (overrides --pre-git/--post-git when set).",
    )
    git_sections.add_argument(
        "--no-git", action="store_false", dest="git_on",
        help="Disable both Pre-Git and Post-Git sections (overrides --pre-git/--post-git when set).",
    )

    steps = parser.add_argument_group("step selection")
    steps.add_argument(
        "--steps", metavar="KEYS",
        help="Comma-separated step keys to run (others are disabled). "
             "Use --list-steps to see valid keys.",
    )

    return parser


def _print_steps() -> None:
    from core.pipeline_config import list_steps
    print(f"\n{APP_TITLE} — valid step keys:\n")
    print(f"  {'KEY':<20} {'LABEL':<25} SECTION")
    print(f"  {'─' * 20} {'─' * 25} {'─' * 10}")
    for key, label, section in list_steps():
        print(f"  {key:<20} {label:<25} {section}")
    print()


def _run_cli(args: argparse.Namespace) -> None:
    from core.pipeline_config import (
        PipelineConfig, ordered_steps, step_enabled_filter,
        validate_step_keys, validate_build_mode, validate_power_mode,
        step_display_name,
    )
    from helpers.platform_utils import is_macos
    from helpers.build_report import send_build_report
    from helpers.version import read_version, write_version
    from helpers.shell import terminate_active_processes
    from helpers.types import fmt_elapsed
    from core.run import run_selected

    version, build_num = read_version()
    version = args.version or version
    build_num = args.build or build_num

    android_mode = validate_build_mode(args.android_mode, "android")
    ios_mode = validate_build_mode(args.ios_mode, "ios")
    power_mode = validate_power_mode(args.power_mode)

    enabled_steps: frozenset[str] | None = None
    if args.steps:
        keys = [k.strip() for k in args.steps.split(",") if k.strip()]
        bad = validate_step_keys(keys)
        if bad:
            print(f"Error: unknown step keys: {', '.join(bad)}", file=sys.stderr)
            print("Run with --list-steps to see valid keys.", file=sys.stderr)
            sys.exit(1)
        enabled_steps = frozenset(keys)

    include_ios = is_macos()
    if args.git_on is not None:
        git_pre_enabled = args.git_on
        git_post_enabled = args.git_on
    else:
        git_pre_enabled = args.pre_git_on if args.pre_git_on is not None else True
        git_post_enabled = args.post_git_on if args.post_git_on is not None else True

    cfg = PipelineConfig(
        version=version,
        build=build_num,
        recipients=args.recipients,
        commit_message_pre=args.commit_message,
        commit_message_release=args.release_commit_message,
        pub_upgrade=args.pub_mode == "pub-upgrade",
        android_build_mode=android_mode,
        ios_build_mode=ios_mode,
        power_mode=power_mode,
        quit_after_power=args.quit_after_power,
        git_pre_enabled=git_pre_enabled,
        git_post_enabled=git_post_enabled,
        common_enabled=args.common_on if args.common_on is not None else True,
        android_enabled=args.android_on if args.android_on is not None else True,
        ios_enabled=args.ios_on if args.ios_on is not None else include_ios,
        post_enabled=args.post_on if args.post_on is not None else True,
        enabled_steps=enabled_steps,
    )

    if cfg.version and cfg.build:
        write_version(cfg.version, cfg.build)

    all_steps = ordered_steps(cfg, include_ios=include_ios)
    step_filter = step_enabled_filter(cfg)
    platforms_str = cfg.platforms_label()

    log_buffer: deque[str] = deque(maxlen=MAX_REPORT_LOG_LINES)
    step_results: list[StepResult] = []
    step_times: dict[str, float] = {}

    def log(msg: str) -> None:
        log_buffer.append(msg)
        print(msg, end="", flush=True)

    def on_start(step_key: str):
        step_times[step_key] = time.monotonic()
        log(f"\n▶ {step_display_name(step_key)}\n")

    def on_done(ok: bool, step_key: str):
        elapsed = time.monotonic() - step_times.get(step_key, time.monotonic())
        name = step_display_name(step_key)
        elapsed_str = fmt_elapsed(elapsed)
        step_results.append((name, ok, elapsed))
        mark = "✓" if ok else "✗"
        log(f"  {mark} {name} — {elapsed_str}\n")

    log(f"{APP_TITLE} — {platforms_str}\n")
    log(f"Android build: {cfg.android_build_mode}  |  iOS build: {cfg.ios_build_mode}\n")
    log(f"version={cfg.version} build={cfg.build}\n\n")

    quit_after_timer_scheduled = [False]

    def schedule_cli_quit(delay: float) -> None:
        def _exit_delayed() -> None:
            sys.exit(0)

        threading.Timer(delay, _exit_delayed).start()
        quit_after_timer_scheduled[0] = True

    pipeline_start = time.monotonic()
    success = False
    try:
        done = run_selected(
            steps=all_steps,
            step_enabled=step_filter,
            log=log,
            on_step_start=on_start,
            on_step_done=on_done,
            schedule_quit_after_seconds=schedule_cli_quit,
            **cfg.run_kwargs(),
        )
        total = fmt_elapsed(time.monotonic() - pipeline_start)
        if done:
            log(f"\n✓ All done — total {total}\n")
            success = True
        else:
            log(f"\n✗ Pipeline stopped — {total}\n")
    except Exception as exc:
        total = fmt_elapsed(time.monotonic() - pipeline_start)
        log(f"\nError: {exc}\n")
    finally:
        total_elapsed = fmt_elapsed(time.monotonic() - pipeline_start)
        try:
            send_build_report(
                log_lines=log_buffer,
                step_results=step_results,
                version=cfg.version,
                build=cfg.build,
                platforms=platforms_str,
                total_elapsed=total_elapsed,
                success=success,
                log=log,
            )
        except Exception as exc:
            log(f"Build report error: {exc}\n")
        terminate_active_processes()

    if quit_after_timer_scheduled[0]:
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            sys.exit(130)
    else:
        sys.exit(0 if success else 1)


def main() -> None:
    parser = _build_cli_parser()
    args = parser.parse_args()

    if args.list_steps:
        _print_steps()
        return

    if args.cli:
        if not args.no_install:
            _ensure_deps()
        _load_dotenv()
        _run_cli(args)
        return

    _load_dotenv()
    try:
        if not args.no_install:
            _ensure_deps()
        from gui.app import main as app_main
        app_main(run_deps=False)
    except Exception:
        import traceback
        print("Error launching GUI:", file=sys.stderr)
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        print("Error starting Senpai Build & Send:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
