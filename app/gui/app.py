"""Main GUI window."""

from __future__ import annotations

from collections.abc import Callable
from threading import Thread
from typing import Any
import tkinter as tk
import atexit
import queue
import time
import sys

from helpers.shell import terminate_active_processes
from helpers.platform_utils import is_macos
from helpers.types import fmt_elapsed

from gui.sections import persist_gui_config, mount_config_panel
from gui.widgets import segmented_button, scrollable_frame
from gui.settings import load_saved_theme, SettingsPanel
from gui.pipeline_runner import PipelineRunner
from gui.theme import COLORS, PAD, RADIUS
from gui.console import ConsolePanel

from core.bootstrap import ensure_dependencies
from core.config_store import (
    pipeline_section_enabled,
    ensure_config_file,
    reload_app_config,
    init_app_config,
)

from core.constants import APP_TITLE, APP_VERSION
from core.pipeline_config import (
    build_pipeline_config,
    step_display_name,
    PipelineConfig,
    ordered_steps,
)
from core.prerequisites import flutter_project_prereq_status
from core.steps import StepDef
from helpers.app_metadata import get_current_app_name
import customtkinter as ctk


PIPELINE_SECTION_KEYS: tuple[str, ...] = (
    "git_pre", "common", "git_post", "android", "ios", "distribution", "post",
)


def _safe_widget_state(widget, state: str) -> None:
    try:
        widget.configure(state=state)
    except Exception:
        pass


class BuildApp(ctk.CTk):
    def __init__(self):
        ensure_config_file()
        init_app_config()

        saved = load_saved_theme()
        if saved:
            from gui.theme import set_theme, available_themes
            if saved in available_themes():
                set_theme(saved)
        super().__init__(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self._show_ios = is_macos()

        self.resizable(False, True)
        self.minsize(700, 750)

        self.ui_queue: queue.Queue = queue.Queue()
        self._stop_requested = False
        self._destroyed = False
        self.is_busy = False

        self._gui_config_serializers: dict[str, Callable[[], Any]] = {}
        self.section_enabled_vars: dict[str, ctk.BooleanVar] = {
            k: ctk.BooleanVar(
                value=pipeline_section_enabled(
                    k,
                    **({"include_ios_default": self._show_ios} if k == "ios" else {}),
                ),
            )
            for k in PIPELINE_SECTION_KEYS
        }
        self._section_widgets: dict[str, list[Any]] = {
            "git_pre": [],
            "common": [],
            "git_post": [],
            "android": [],
            "ios": [],
            "post": [],
            "distribution": [],
        }
        self._section_var_snapshots: dict[str, list[bool]] = {}
        self._section_bool_vars: dict[str, list[ctk.BooleanVar]] = {
            "git_pre": [],
            "common": [],
            "git_post": [],
            "android": [],
            "ios": [],
            "distribution": [],
            "post": [],
        }

        self.step_progress_bars: dict[str, ctk.CTkProgressBar] = {}
        self.step_status_labels: dict[str, ctk.CTkLabel] = {}
        self.step_switches: dict[str, ctk.CTkSwitch] = {}
        self.step_vars: dict[str, ctk.BooleanVar] = {}
        self._steps_disabled_by_prereq: set[str] = set()

        self._step_start_times: dict[str, float] = {}
        self._pipeline_thread: Thread | None = None
        self._last_timer_update: float = 0.0
        self._running_steps: set[str] = set()
        self._lockable_widgets: list = []

        # Populated by section mounts (see ``gui/sections/``).
        self._commit_msg_release: ctk.StringVar | None = None
        self._quit_after_power: ctk.BooleanVar | None = None
        self._commit_msg_pre: ctk.StringVar | None = None
        self.recipients_var: ctk.StringVar | None = None
        self.version_var: ctk.StringVar | None = None
        self._git_branch: ctk.StringVar | None = None
        self._power_mode: ctk.StringVar | None = None
        self._pub_mode: ctk.StringVar | None = None
        self.build_var: ctk.StringVar | None = None

        self._fonts = {
            "mono_sm": ctk.CTkFont(family="Consolas", size=12),
            "mono": ctk.CTkFont(family="Consolas", size=13),
            "status": ctk.CTkFont(size=12, slant="italic"),
            "section": ctk.CTkFont(size=14, weight="bold"),
            "title": ctk.CTkFont(size=26, weight="bold"),
            "btn": ctk.CTkFont(size=14, weight="bold"),
            "body_sm": ctk.CTkFont(size=12),
            "footer": ctk.CTkFont(size=11),
            "body": ctk.CTkFont(size=13),
        }

        self._build_ui()
        self._pipeline_runner = PipelineRunner()
        self._apply_section_enabled_states()
        self._apply_ios_mode_rules()
        self._sync_run_button()
        self._start_queue_polling()

    def _track(self, widget):
        self._lockable_widgets.append(widget)
        return widget

    def _track_section(self, section_key: str, widget):
        self._section_widgets.setdefault(section_key, []).append(widget)
        return self._track(widget)

    def _register_section_bool_var(self, section_key: str, var: ctk.BooleanVar) -> None:
        self._section_bool_vars.setdefault(section_key, []).append(var)

    def _sync_section_enabled_from_disk(self) -> None:
        for k in PIPELINE_SECTION_KEYS:
            self.section_enabled_vars[k].set(
                pipeline_section_enabled(
                    k,
                    **({"include_ios_default": self._show_ios} if k == "ios" else {}),
                ),
            )

    def _clear_config_panel_state(self) -> None:
        self._gui_config_serializers.clear()
        self._steps_disabled_by_prereq.clear()
        for k in self._section_widgets:
            self._section_widgets[k].clear()
        for k in self._section_bool_vars:
            self._section_bool_vars[k].clear()
        self.step_progress_bars.clear()
        self.step_status_labels.clear()
        self._lockable_widgets.clear()
        self.step_switches.clear()
        self.step_vars.clear()

        self._commit_msg_release = None
        self._quit_after_power = None
        self._commit_msg_pre = None
        self.recipients_var = None
        self.version_var = None
        self._power_mode = None
        self._git_branch = None
        self.build_var = None
        self._pub_mode = None

    def rebuild_config_panel(self) -> None:
        """Reload merged config from disk and rebuild the Config tab (prereqs, env, secrets)."""
        if self._destroyed or self.is_busy:
            return
        reload_app_config()
        self._sync_section_enabled_from_disk()
        self._clear_config_panel_state()
        for w in self.config_scroll.winfo_children():
            w.destroy()
        mount_config_panel(self, self.config_scroll)
        self._apply_section_enabled_states()
        self._apply_ios_mode_rules()
        self._sync_run_button()
        self._refresh_app_title()

    def _refresh_app_title(self) -> None:
        """Update the top header title based on current project metadata."""
        if hasattr(self, "hdr_title_lbl"):
            self.hdr_title_lbl.configure(text=get_current_app_name())

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        self._build_header()

        tab_bar = ctk.CTkFrame(self, fg_color="transparent")
        tab_bar.grid(row=1, column=0, sticky="ew", padx=PAD["lg"])

        self._tab_selector = segmented_button(
            tab_bar, values=["Config", "Console", "Settings"],
            command=self._switch_tab, font=self._fonts["body_sm"],
        )
        self._tab_selector.set("Config")
        self._tab_selector.pack(anchor="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=PAD["lg"], pady=(PAD["sm"], 0))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self._tab_frames: dict[str, ctk.CTkFrame] = {}
        for tab_name in ("Config", "Console", "Settings"):
            frame = ctk.CTkFrame(content, fg_color="transparent")
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            self._tab_frames[tab_name] = frame

        self._settings_frame = self._tab_frames["Settings"]
        self._console_frame = self._tab_frames["Console"]
        self._config_frame = self._tab_frames["Config"]

        self.config_scroll = scrollable_frame(
            self._config_frame, row=0, column=0, sticky="nsew",
        )

        mount_config_panel(self, self.config_scroll)

        self._console = ConsolePanel(self._console_frame, self._fonts)
        self._console.grid(row=0, column=0, sticky="nsew")

        self._settings = SettingsPanel(self._settings_frame, self._fonts, app=self)
        self._settings.grid(row=0, column=0, sticky="nsew")

        self._config_frame.tkraise()

        ctk.CTkLabel(
            self, text="Made By Senpai\u2764\ufe0f",
            font=self._fonts["footer"], text_color=COLORS["muted"],
        ).grid(row=3, column=0, pady=(0, 8))

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=PAD["lg"], pady=(PAD["lg"], 15))
        hdr.grid_columnconfigure(0, weight=1)

        self.hdr_title_lbl = ctk.CTkLabel(
            hdr, text=get_current_app_name(), 
            font=self._fonts["title"]
        )
        self.hdr_title_lbl.grid(row=0, column=0, sticky="w")

        self.running_status_lbl = ctk.CTkLabel(
            hdr, font=self._fonts["status"],
            text_color=COLORS["accent"], text="",
        )
        self.running_status_lbl.grid(row=0, column=1, sticky="e", padx=(0, PAD["md"]))

        self.run_btn = ctk.CTkButton(
            hdr, font=self._fonts["btn"],
            hover_color=COLORS["accent_hover"], corner_radius=RADIUS["btn"],
            text="Run Selected Steps", fg_color=COLORS["accent"],
            command=self.on_run_click, height=40,
        )
        self.run_btn.grid(row=0, column=2, sticky="e", padx=(0, PAD["sm"]))

        self.stop_btn = ctk.CTkButton(
            hdr, font=self._fonts["btn"],
            hover_color=COLORS["danger_hover"], corner_radius=RADIUS["btn"],
            command=self.on_stop_click, fg_color=COLORS["danger"],
            text="Stop Build", height=40, width=100,
        )
        self.stop_btn.grid(row=0, column=3, sticky="e")
        self.stop_btn.grid_remove()

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, name: str) -> None:
        self._tab_frames[name].tkraise()
        self._console.visible = (name == "Console")

    def _on_section_enabled_changed(self, section_key: str) -> None:
        vars_list = self._section_bool_vars.get(section_key, [])
        enabling = self._section_enabled(section_key)
        if enabling:
            snapshot = self._section_var_snapshots.pop(section_key, None)
            if snapshot:
                for idx, section_var in enumerate(vars_list):
                    if idx < len(snapshot):
                        section_var.set(bool(snapshot[idx]))
            self._set_section_widget_state(section_key, "normal")
        else:
            self._section_var_snapshots[section_key] = [bool(v.get()) for v in vars_list]
            self._set_section_widget_state(section_key, "disabled")
            for section_var in vars_list:
                section_var.set(False)
        if section_key == "ios":
            self._apply_ios_mode_rules()

    def _section_enabled(self, section_key: str, fallback: bool = True) -> bool:
        var = self.section_enabled_vars.get(section_key)
        return bool(var.get()) if var is not None else fallback

    def _apply_ios_mode_rules(self) -> None:
        """Disable App Store upload when credentials are missing or section is off."""
        if not self._show_ios:
            return

        appstore_sw = self.step_switches.get("appstore_upload")
        appstore_var = self.step_vars.get("appstore_upload")
        if not appstore_sw or not appstore_var:
            return

        ios_enabled = self._section_enabled("ios", self._show_ios)

        if "appstore_upload" in self._steps_disabled_by_prereq:
            appstore_var.set(False)
            appstore_sw.configure(state="disabled")
            return

        if self.is_busy:
            appstore_sw.configure(state="disabled")
            return

        # AppStore upload is allowed if iOS section is enabled OR if prerequisites are satisfied independently
        appstore_sw.configure(state="normal" if ios_enabled else "disabled")

    def _sync_run_button(self) -> None:
        """Disable the Run button when the Flutter project root is not configured."""
        ok, _ = flutter_project_prereq_status()
        if ok:
            self.run_btn.configure(state="normal", fg_color=COLORS["accent"])
        else:
            self.run_btn.configure(state="disabled", fg_color=COLORS["disabled"])

    # ── Queue polling & logging ──────────────────────────────────────────────

    _POLL_IDLE_MS = 200
    _POLL_BUSY_MS = 100
    _MAX_BATCH = 300
    _TIMER_DEBOUNCE_S = 1.0

    def _start_queue_polling(self):
        if self._destroyed:
            return
        processed = 0
        log_items: list[tuple[str, str]] = []
        try:
            while processed < self._MAX_BATCH:
                msg_type, data = self.ui_queue.get_nowait()
                processed += 1
                if msg_type == "log":
                    log_items.append((data, self._console.classify(data)))
                elif msg_type == "log_tagged":
                    log_items.append(data)
                elif msg_type == "status":
                    self._update_step_status(*data)
                elif msg_type == "busy":
                    self._update_busy_state(*data)
                elif msg_type == "quit_delayed":
                    self._schedule_delayed_quit(float(data))
                elif msg_type == "persist_config":
                    try:
                        persist_gui_config(self)
                    except OSError:
                        pass
        except queue.Empty:
            pass
        if log_items:
            self._console.begin_batch()
            self._console.batch_insert(log_items)
            self._console.end_batch()
        if self._running_steps:
            now = time.monotonic()
            if now - self._last_timer_update >= self._TIMER_DEBOUNCE_S:
                self._last_timer_update = now
                for key in self._running_steps:
                    start = self._step_start_times.get(key, now)
                    lbl = self.step_status_labels.get(key)
                    if lbl:
                        lbl.configure(text=fmt_elapsed(now - start))
        interval = self._POLL_BUSY_MS if (self.is_busy or processed) else self._POLL_IDLE_MS
        if self._destroyed:
            return
        try:
            self.after(interval, self._start_queue_polling)
        except (RuntimeError, tk.TclError):
            pass

    def log(self, text: str):
        if not self._destroyed:
            self.ui_queue.put(("log", text))

    def _schedule_delayed_quit(self, delay_s: float) -> None:
        """Main thread: quit after *delay_s* (same as shutdown/sleep countdown)."""
        if self._destroyed:
            return
        ms = max(1, int(delay_s * 1000))

        def _fire_delayed_quit() -> None:
            if self._destroyed:
                return
            self._destroyed = True
            self._stop_requested = True
            terminate_active_processes()
            try:
                self.quit()
            except (RuntimeError, tk.TclError):
                pass
            try:
                self.destroy()
            except (RuntimeError, tk.TclError):
                pass
            sys.exit(0)

        try:
            self.after(ms, _fire_delayed_quit)
        except (RuntimeError, tk.TclError):
            pass

    def _update_step_status(self, step_key: str, status: str):
        if step_key not in self.step_status_labels:
            return
        lbl = self.step_status_labels[step_key]
        pb = self.step_progress_bars[step_key]
        if status == "running":
            self._step_start_times[step_key] = time.monotonic()
            self._running_steps.add(step_key)
            lbl.configure(text="0s", text_color=COLORS["accent"])
            pb.grid()
            pb.start()
            self.running_status_lbl.configure(text=f"Running: {step_display_name(step_key)}...")
        else:
            self._running_steps.discard(step_key)
            pb.stop()
            pb.grid_remove()
            elapsed = time.monotonic() - self._step_start_times.get(step_key, time.monotonic())
            elapsed_str = fmt_elapsed(elapsed)
            if status == "ok":
                lbl.configure(text=f"✓ {elapsed_str}", text_color=COLORS["success"])
            elif status == "error":
                lbl.configure(text=f"✗ {elapsed_str}", text_color=COLORS["error"])
            else:
                lbl.configure(text="-", text_color=COLORS["text_dim"])

    def _update_busy_state(self, is_busy: bool, label_text: str):
        self.is_busy = is_busy
        self._set_widgets_locked(is_busy)
        if is_busy:
            self.run_btn.configure(state="disabled", text="Running...", fg_color=COLORS["disabled"])
            self.running_status_lbl.configure(text=label_text, text_color=COLORS["accent"])
            self.stop_btn.configure(state="normal", text="Stop Build", fg_color=COLORS["danger"])
            self.stop_btn.grid()
        else:
            self.run_btn.configure(state="normal", text="Run Selected Steps", fg_color=COLORS["accent"])
            if label_text:
                color = COLORS["success"] if label_text.startswith("✓") else COLORS["error"]
                self.running_status_lbl.configure(text=label_text, text_color=color)
            else:
                self.running_status_lbl.configure(text="", text_color=COLORS["accent"])
            self.stop_btn.grid_remove()
            self._restore_widget_states()

    def _set_widgets_locked(self, locked: bool):
        state = "disabled" if locked else "normal"
        for w in self._lockable_widgets:
            _safe_widget_state(w, state)

    def _restore_widget_states(self):
        """Re-apply section/prereq UI rules after unlock."""
        self._apply_section_enabled_states()
        self._apply_ios_mode_rules()

    def _set_section_widget_state(self, section_key: str, state: str) -> None:
        """Apply *state* to all tracked widgets in a single section, then
        re-apply prereq overrides for any steps disabled by missing config."""
        for widget in self._section_widgets.get(section_key, []):
            _safe_widget_state(widget, state)
        if state == "normal":
            for step_key in self._steps_disabled_by_prereq:
                sw = self.step_switches.get(step_key)
                var = self.step_vars.get(step_key)
                if sw:
                    _safe_widget_state(sw, "disabled")
                if var:
                    var.set(False)

    def _apply_section_enabled_states(self) -> None:
        """Bulk-apply enabled/disabled across all sections (used after full rebuild)."""
        for section_key in self._section_widgets:
            enabled = self._section_enabled(section_key)
            state = "normal" if enabled and not self.is_busy else "disabled"
            self._set_section_widget_state(section_key, state)

    # ── Step collection (delegates to shared pipeline_config) ────────────────

    def _get_checked_steps(self) -> frozenset[str]:
        """Raw set of step keys whose UI switch is on."""
        return frozenset(key for key, var in self.step_vars.items() if var.get())

    def _build_pipeline_config_from_ui(self) -> PipelineConfig:
        return build_pipeline_config(
            commit_message_release=(
                self._commit_msg_release.get().strip() if self._commit_msg_release else None
            ),
            commit_message_pre=self._commit_msg_pre.get().strip() if self._commit_msg_pre else None,
            git_post_enabled=self._section_enabled("git_post"),
            quit_after_power=self._quit_after_power.get() if self._quit_after_power else False,
            git_pre_enabled=self._section_enabled("git_pre"),
            android_enabled=self._section_enabled("android"),
            common_enabled=self._section_enabled("common"),
            enabled_steps=self._get_checked_steps(),
            post_enabled=self._section_enabled("post"),
            ios_enabled=self._section_enabled("ios", self._show_ios),
            pub_upgrade=self._pub_mode.get() == "pub upgrade" if self._pub_mode else False,
            power_mode=self._power_mode.get() if self._power_mode else "Shutdown",
            recipients=self.recipients_var.get().strip() or None if self.recipients_var else None,
            version=(self.version_var.get().strip() if self.version_var else ""),
            build=(self.build_var.get().strip() if self.build_var else ""),
            git_branch=(self._git_branch.get().strip() if self._git_branch else None),
        )

    # ── Run / Stop ───────────────────────────────────────────────────────────

    def on_stop_click(self):
        self._stop_requested = True
        self.stop_btn.configure(state="disabled", text="Stopping...")
        self.log("\n[User requested stop — cancelling...]\n")
        Thread(target=terminate_active_processes, daemon=True).start()

    def on_run_click(self):
        if self.is_busy:
            return
        self._stop_requested = False
        reload_app_config()
        ok_flutter, flutter_msg = flutter_project_prereq_status()
        if not ok_flutter:
            self._tab_selector.set("Console")
            self._switch_tab("Console")
            self._console.clear()
            self.log(f"\n✗ Pipeline cannot run.\n{flutter_msg}\n")
            self.running_status_lbl.configure(
                text="Flutter project not configured",
                text_color=COLORS["error"],
            )
            return
        cfg = self._build_pipeline_config_from_ui()

        all_steps = ordered_steps(cfg, include_ios=self._show_ios)

        self.ui_queue.put(("busy", (True, "Preparing run...")))
        self._console.clear()
        self._tab_selector.set("Console")
        self._switch_tab("Console")

        self._pipeline_thread = Thread(
            target=self._run_pipeline_worker,
            args=(all_steps, cfg),
            daemon=True,
        )
        self._pipeline_thread.start()

    def _run_pipeline_worker(self, all_steps: list[StepDef], cfg: PipelineConfig) -> None:
        self._pipeline_runner.execute(
            on_persist_request=self._queue_persist_config,
            on_schedule_quit=self._queue_quit_delay,
            on_step_status=self._queue_step_status,
            stop_requested=lambda: self._stop_requested,
            is_destroyed=lambda: self._destroyed,
            on_tagged_log=self._queue_tagged_log,
            steps=all_steps,
            cfg=cfg,
            on_busy=self._queue_busy,
            on_log=self._queue_log,
        )

    def _queue_log(self, text: str) -> None:
        self.ui_queue.put(("log", text))

    def _queue_tagged_log(self, text: str, tag: str) -> None:
        self.ui_queue.put(("log_tagged", (text, tag)))

    def _queue_step_status(self, step_key: str, status: str) -> None:
        self.ui_queue.put(("status", (step_key, status)))

    def _queue_busy(self, busy: bool, label: str) -> None:
        self.ui_queue.put(("busy", (busy, label)))

    def _queue_quit_delay(self, delay: float) -> None:
        if not self._destroyed:
            self.ui_queue.put(("quit_delayed", delay))

    def _queue_persist_config(self) -> None:
        self.ui_queue.put(("persist_config", None))

    def _on_closing(self):
        try:
            persist_gui_config(self)
        except OSError:
            pass
        self._destroyed = True
        self._stop_requested = True
        terminate_active_processes()
        if self._pipeline_thread and self._pipeline_thread.is_alive():
            self._pipeline_thread.join(timeout=3)
        terminate_active_processes()
        try:
            self.quit()
        except (RuntimeError, tk.TclError):
            pass
        try:
            self.destroy()
        except (RuntimeError, tk.TclError):
            pass


def main(run_deps: bool = True) -> None:
    """Start the GUI; *run_deps* runs pip install for ``requirements.txt`` when True."""
    atexit.register(terminate_active_processes)
    if run_deps:
        ensure_dependencies(print)
    app = BuildApp()
    app.mainloop()


if __name__ == "__main__":
    main()
