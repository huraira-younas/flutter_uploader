"""GUI-agnostic pipeline execution service."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
import time

from core.constants import APP_TITLE, MAX_REPORT_LOG_LINES
from core.pipeline_config import step_enabled_filter, step_display_name, PipelineConfig
from core.run import run_selected
from core.steps import StepResult, StepDef
from helpers.build_report import send_build_report
from helpers.shell import terminate_active_processes
from helpers.types import fmt_elapsed
from helpers.version import write_version


class PipelineRunner:
    """Runs a configured pipeline and reports events through callbacks."""

    def execute(
        self,
        *,
        on_persist_request: Callable[[], None],
        on_schedule_quit: Callable[[float], None],
        on_step_status: Callable[[str, str], None],
        stop_requested: Callable[[], bool],
        steps: list[StepDef],
        is_destroyed: Callable[[], bool],
        on_tagged_log: Callable[[str, str], None],
        cfg: PipelineConfig,
        on_busy: Callable[[bool, str], None],
        on_log: Callable[[str], None],
    ) -> None:
        if cfg.version and cfg.build:
            write_version(cfg.version, cfg.build)

        step_filter = step_enabled_filter(cfg)
        for key, _, _, _ in steps:
            if step_filter(key):
                on_step_status(key, "pending")

        platforms_str = cfg.platforms_label()
        log_buffer: deque[str] = deque(maxlen=MAX_REPORT_LOG_LINES)
        step_results: list[StepResult] = []
        step_times: dict[str, float] = {}

        def tee_log(text: str) -> None:
            log_buffer.append(text)
            if not is_destroyed():
                on_log(text)

        def tee_tagged(text: str, tag: str) -> None:
            log_buffer.append(text)
            if not is_destroyed():
                on_tagged_log(text, tag)

        tee_log(f"{APP_TITLE} — {platforms_str}\n")
        tee_log(f"Android build: {cfg.android_build_mode}  |  iOS build: {cfg.ios_build_mode}\n")
        tee_log(f"version={cfg.version} build={cfg.build}\n\n")

        def on_start(step_key: str) -> None:
            step_times[step_key] = time.monotonic()
            on_step_status(step_key, "running")
            tee_tagged(f"\n▶ {step_display_name(step_key)}\n", "step")

        def on_done(ok: bool, step_key: str) -> None:
            elapsed = time.monotonic() - step_times.get(step_key, time.monotonic())
            on_step_status(step_key, "ok" if ok else "error")
            name = step_display_name(step_key)
            elapsed_str = fmt_elapsed(elapsed)
            step_results.append((name, ok, elapsed))
            tee_tagged(f"  {'✓' if ok else '✗'} {name} — {elapsed_str}\n", "ok" if ok else "err")

        pipeline_start = time.monotonic()
        completion_msg = ""
        success = False
        try:
            done = run_selected(
                schedule_quit_after_seconds=on_schedule_quit,
                step_enabled=step_filter,
                on_step_start=on_start,
                on_step_done=on_done,
                stop_check=stop_requested,
                steps=steps,
                log=tee_log,
                **cfg.run_kwargs(),
            )
            total = fmt_elapsed(time.monotonic() - pipeline_start)
            if done:
                tee_tagged(f"\n✓ All done — total {total}\n", "ok")
                completion_msg = f"✓ Completed — {total}"
                success = True
            else:
                tee_tagged(f"\n✗ Stopped — {total}\n", "err")
                completion_msg = f"✗ Stopped — {total}"
        except Exception as exc:
            total = fmt_elapsed(time.monotonic() - pipeline_start)
            tee_log(f"\nError: {exc}\n")
            completion_msg = f"✗ Error — {total}"
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
                    log=tee_log,
                )
            except Exception as exc:
                tee_log(f"Build report error: {exc}\n")
            terminate_active_processes()
            on_busy(False, completion_msg)
            if success:
                on_persist_request()
