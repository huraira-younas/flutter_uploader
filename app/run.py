"""GUI/CLI entry: ``python run.py`` · ``--cli`` · ``--list-steps`` · ``--no-install``."""

from collections import deque
import argparse
import threading
import time
import sys

from core.constants import (
    MAX_REPORT_LOG_LINES,
    APP_TITLE,
)
from core.bootstrap import ensure_dependencies
from core.steps import StepResult


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
        "--commit-message", metavar="MSG", default=None,
        help="Pre-Git commit message (default: pre_git.commit_message in config.json).",
    )
    run.add_argument(
        "--release-commit-message", metavar="MSG",
        default=None,
        dest="release_commit_message",
        help="Post-Git release commit template; {version} and {build} are substituted "
        "(default: post_git.commit_message in config.json).",
    )
    run.add_argument(
        "--pub-mode", choices=["pub-get", "pub-upgrade"], default=None,
        help="Dependency resolution mode (default: common.pub_mode in config.json).",
    )
    run.add_argument(
        "--power-mode", choices=["shutdown", "sleep"], default=None,
        help="Power action after pipeline (default: post_build.power_mode in config.json).",
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
        help="Enable Post-Git section (release commit, push).",
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
    print(f"\n{APP_TITLE} - valid step keys:\n")
    print(f"  {'KEY':<20} {'LABEL':<25} SECTION")
    print(f"  {'-' * 20} {'-' * 25} {'-' * 10}")
    for key, label, section in list_steps():
        print(f"  {key:<20} {label:<25} {section}")
    print()


def _run_cli(args: argparse.Namespace) -> None:
    from core.cli_pipeline import resolve_cli_pipeline_config
    from core.config_store import init_app_config
    from core.pipeline_config import (
        parse_step_keys_csv,
        ordered_steps, step_enabled_filter,
        find_invalid_step_keys,
        step_display_name,
    )
    from helpers.platform_utils import is_macos
    from helpers.build_report import send_build_report
    from helpers.version import write_version
    from helpers.shell import terminate_active_processes
    from helpers.types import fmt_elapsed
    from core.run import run_selected

    init_app_config()

    from core.prerequisites import flutter_project_prereq_status

    ok_flutter, flutter_msg = flutter_project_prereq_status()
    if not ok_flutter:
        print(f"\nError: Pipeline cannot run.\n{flutter_msg}\n", file=sys.stderr)
        sys.exit(1)

    if args.steps:
        keys = parse_step_keys_csv(args.steps)
        bad = find_invalid_step_keys(keys)
        if bad:
            print(f"Error: unknown step keys: {', '.join(bad)}", file=sys.stderr)
            print("Run with --list-steps to see valid keys.", file=sys.stderr)
            sys.exit(1)

    include_ios = is_macos()
    cfg = resolve_cli_pipeline_config(args, include_ios=include_ios)

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
    log(f"Flutter builds (Android APK/AAB, iOS IPA)\n")
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
            schedule_quit_after_seconds=schedule_cli_quit,
            step_enabled=step_filter,
            on_step_start=on_start,
            on_step_done=on_done,
            steps=all_steps,
            log=log,
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
                total_elapsed=total_elapsed,
                step_results=step_results,
                platforms=platforms_str,
                log_lines=log_buffer,
                build=cfg.build,
                success=success,
                version=cfg.version,
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
            ensure_dependencies()
        _run_cli(args)
        return

    try:
        if not args.no_install:
            ensure_dependencies()
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
