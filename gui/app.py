"""Main GUI window."""

from __future__ import annotations

from collections import deque
from threading import Thread
import tkinter as tk
import atexit
import queue
import sys
import time

from core.constants import (
    GIT_PRE_STEPS, ANDROID_STEPS, IOS_STEPS,
    APP_TITLE, APP_VERSION, StepDef, StepResult,
    GIT_POST_STEPS, POST_STEPS,
    MAX_REPORT_LOG_LINES,
)

from core.pipeline_config import (
    ordered_steps, step_enabled_filter,
    PipelineConfig, STEP_TO_SECTION,
    step_display_name,
)

from helpers.platform_utils import is_macos, is_shorebird_available
from helpers.shell import terminate_active_processes
from helpers.build_report import send_build_report
from helpers.types import fmt_elapsed

from gui.widgets import scrollable_frame, segmented_button
from gui.settings import SettingsPanel, load_saved_theme
from helpers.version import write_version
from gui.theme import COLORS, RADIUS, PAD
from gui.cards import CardBuilderMixin
from gui.console import ConsolePanel
from gui.readme import ReadMePanel
from core.run import run_selected
import customtkinter as ctk


class BuildApp(CardBuilderMixin, ctk.CTk):
    def __init__(self):
        saved = load_saved_theme()
        if saved:
            from gui.theme import set_theme, available_themes
            if saved in available_themes():
                set_theme(saved)
        super().__init__(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._shorebird_ok = is_shorebird_available()
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self._show_ios = is_macos()

        self.geometry(f"940x{1080 if self._show_ios else 920}")
        self.minsize(780, 750)

        self.ui_queue: queue.Queue = queue.Queue()
        self._stop_requested = False
        self._destroyed = False
        self.is_busy = False

        self._shorebird_ios = ctk.BooleanVar(value=self._shorebird_ok) if self._show_ios else None
        self._ios_enabled = ctk.BooleanVar(value=True) if self._show_ios else None
        self._shorebird_android = ctk.BooleanVar(value=False)
        self._android_enabled = ctk.BooleanVar(value=True)
        self._common_enabled = ctk.BooleanVar(value=True)
        self._post_enabled = ctk.BooleanVar(value=True)
        self._git_enabled = ctk.BooleanVar(value=True)

        self._power_mode = ctk.StringVar(value="Sleep" if self._show_ios else "Shutdown")
        self._ios_sb_mode = ctk.StringVar(value="Release") if self._show_ios else None
        self._sb_mode_widgets: dict[str, ctk.CTkSegmentedButton] = {}
        self._android_sb_mode = ctk.StringVar(value="Release")
        self._sb_checkboxes: dict[str, ctk.CTkCheckBox] = {}
        self._quit_after_power = ctk.BooleanVar(value=False)
        self._sb_hint_labels: dict[str, ctk.CTkLabel] = {}
        self._pub_mode = ctk.StringVar(value="pub get")
        self._post_sub_widgets: list = []
        self._common_sub_widgets: list = []

        self.step_progress_bars: dict[str, ctk.CTkProgressBar] = {}
        self.step_status_labels: dict[str, ctk.CTkLabel] = {}
        self.step_switches: dict[str, ctk.CTkSwitch] = {}
        self.step_vars: dict[str, ctk.BooleanVar] = {}

        self._section_switches: dict[str, list[ctk.CTkSwitch]] = {}
        self._saved_section_states: dict[str, dict[str, bool]] = {}
        self._section_enable_vars: dict[str, ctk.BooleanVar] = {}
        self._step_start_times: dict[str, float] = {}
        self._pipeline_thread: Thread | None = None
        self._running_steps: set[str] = set()
        self._lockable_widgets: list = []

        self._fonts = {
            "mono_sm": ctk.CTkFont(family="Consolas", size=12),
            "readme_h1": ctk.CTkFont(size=22, weight="bold"),
            "readme_h2": ctk.CTkFont(size=15, weight="bold"),
            "readme_h3": ctk.CTkFont(size=13, weight="bold"),
            "mono": ctk.CTkFont(family="Consolas", size=13),
            "inline_code": ctk.CTkFont(family="Consolas", size=12),
            "status": ctk.CTkFont(size=12, slant="italic"),
            "section": ctk.CTkFont(size=14, weight="bold"),
            "title": ctk.CTkFont(size=26, weight="bold"),
            "btn": ctk.CTkFont(size=14, weight="bold"),
            "body_bold": ctk.CTkFont(size=13, weight="bold"),
            "body_italic": ctk.CTkFont(size=13, slant="italic"),
            "body_bold_italic": ctk.CTkFont(size=13, weight="bold", slant="italic"),
            "body_sm": ctk.CTkFont(size=12),
            "footer": ctk.CTkFont(size=11),
            "body": ctk.CTkFont(size=13),
        }

        self._build_ui()
        self._apply_ios_mode_rules()
        self._start_queue_polling()

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
            tab_bar, values=["Config", "Console", "ReadMe", "Settings"],
            command=self._switch_tab, font=self._fonts["body_sm"],
        )
        self._tab_selector.set("Config")
        self._tab_selector.pack(anchor="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=PAD["lg"], pady=(PAD["sm"], 0))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self._tab_frames: dict[str, ctk.CTkFrame] = {}
        for tab_name in ("Config", "Console", "ReadMe", "Settings"):
            frame = ctk.CTkFrame(content, fg_color="transparent")
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            self._tab_frames[tab_name] = frame

        self._settings_frame = self._tab_frames["Settings"]
        self._console_frame = self._tab_frames["Console"]
        self._readme_frame = self._tab_frames["ReadMe"]
        self._config_frame = self._tab_frames["Config"]

        self.config_scroll = scrollable_frame(
            self._config_frame, row=0, column=0, sticky="nsew",
        )

        row = 0
        self._build_info_card(row); row += 1
        row = self._build_common_card(row)
        row = self._build_section_card(
            "Git", GIT_PRE_STEPS + GIT_POST_STEPS, "git",
            row=row, enable_var=self._git_enabled,
        )
        row = self._build_section_card(
            "Android Build", ANDROID_STEPS, "android",
            row=row, enable_var=self._android_enabled,
            shorebird_var=self._shorebird_android, shorebird_mode_var=self._android_sb_mode,
        )
        if self._show_ios:
            row = self._build_section_card(
                "iOS Build", IOS_STEPS, "ios",
                row=row, enable_var=self._ios_enabled,
                shorebird_var=self._shorebird_ios, shorebird_mode_var=self._ios_sb_mode,
            )
        row = self._build_section_card(
            "Post-Build", POST_STEPS, "post",
            row=row, enable_var=self._post_enabled,
        )
        self._build_dist_card(row)

        self._console = ConsolePanel(self._console_frame, self._fonts)
        self._console.grid(row=0, column=0, sticky="nsew")

        self._readme = ReadMePanel(self._readme_frame, self._fonts)
        self._readme.grid(row=0, column=0, sticky="nsew")

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

        ctk.CTkLabel(hdr, text=APP_TITLE, font=self._fonts["title"]).grid(row=0, column=0, sticky="w")

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

    # ── Section / shorebird toggles ──────────────────────────────────────────

    def _on_section_toggle(self, section_key: str) -> None:
        var = self._section_enable_vars.get(section_key)
        if not var:
            return
        enabled = var.get()
        state = "normal" if enabled else "disabled"

        section_step_keys = [
            k for k, sec in STEP_TO_SECTION.items()
            if sec == section_key and k in self.step_vars
        ]

        if not enabled:
            self._saved_section_states[section_key] = {
                k: self.step_vars[k].get() for k in section_step_keys
            }
            for k in section_step_keys:
                self.step_vars[k].set(False)
        else:
            saved = self._saved_section_states.pop(section_key, {})
            for k in section_step_keys:
                self.step_vars[k].set(saved.get(k, True))

        for switch in self._section_switches.get(section_key, []):
            switch.configure(state=state)

        if section_key == "post":
            for w in self._post_sub_widgets:
                try:
                    w.configure(state=state)
                except Exception:
                    pass
        if section_key == "common":
            for w in self._common_sub_widgets:
                try:
                    w.configure(state=state)
                except Exception:
                    pass

    def _on_shorebird_toggle(self, section_key: str, var: ctk.BooleanVar) -> None:
        if not self._shorebird_ok:
            var.set(False)
            return
        seg = self._sb_mode_widgets.get(section_key)
        if seg:
            seg.configure(state="normal" if var.get() else "disabled")
        if section_key == "ios":
            self._apply_ios_mode_rules()

    def _on_shorebird_mode_changed(self, section_key: str) -> None:
        if section_key == "ios":
            self._apply_ios_mode_rules()

    def _apply_ios_mode_rules(self) -> None:
        """Enforce UI-only rules derived from current iOS build mode selection."""
        if not self._show_ios:
            return

        appstore_sw = self.step_switches.get("appstore_upload")
        appstore_var = self.step_vars.get("appstore_upload")
        if not appstore_sw or not appstore_var:
            return

        shorebird_on = bool(self._shorebird_ios and self._shorebird_ios.get())
        ios_mode = (self._ios_sb_mode.get() if self._ios_sb_mode else "Release").lower()
        ios_enabled = bool(self._ios_enabled and self._ios_enabled.get())

        patch_mode = shorebird_on and ios_mode == "patch"
        if patch_mode:
            appstore_var.set(False)
            appstore_sw.configure(state="disabled")
            return

        if self.is_busy:
            appstore_sw.configure(state="disabled")
            return

        appstore_sw.configure(state="normal" if ios_enabled else "disabled")

    @staticmethod
    def _resolve_build_mode(
        shorebird_var: ctk.BooleanVar | None,
        mode_var: ctk.StringVar | None,
    ) -> str:
        if not shorebird_var or not shorebird_var.get():
            return "flutter"
        return (mode_var.get() if mode_var else "Release").lower()

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
                    log_items.append((data, self._console._classify(data)))
                elif msg_type == "log_tagged":
                    log_items.append(data)
                elif msg_type == "status":
                    self._update_step_status(*data)
                elif msg_type == "busy":
                    self._update_busy_state(*data)
                elif msg_type == "quit_delayed":
                    self._schedule_delayed_quit(float(data))
        except queue.Empty:
            pass
        if log_items:
            self._console.begin_batch()
            self._console.batch_insert(log_items)
            self._console.end_batch()
        if self._running_steps:
            now = time.monotonic()
            last = getattr(self, "_last_timer_update", 0.0)
            if now - last >= self._TIMER_DEBOUNCE_S:
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
            try:
                w.configure(state=state)
            except Exception:
                pass
        for switches in self._section_switches.values():
            for s in switches:
                try:
                    s.configure(state=state)
                except Exception:
                    pass
        for cb in self._sb_checkboxes.values():
            try:
                cb.configure(state=state)
            except Exception:
                pass
        for seg in self._sb_mode_widgets.values():
            try:
                seg.configure(state=state)
            except Exception:
                pass

    def _restore_widget_states(self):
        """Re-apply section/shorebird toggle states after unlock (UI only, no var changes)."""
        for section_key, var in self._section_enable_vars.items():
            state = "normal" if var.get() else "disabled"
            for switch in self._section_switches.get(section_key, []):
                switch.configure(state=state)
            if section_key == "post":
                for w in self._post_sub_widgets:
                    try:
                        w.configure(state=state)
                    except Exception:
                        pass
            if section_key == "common":
                for w in self._common_sub_widgets:
                    try:
                        w.configure(state=state)
                    except Exception:
                        pass
        if self._shorebird_android:
            self._on_shorebird_toggle("android", self._shorebird_android)
        if self._shorebird_ios:
            self._on_shorebird_toggle("ios", self._shorebird_ios)
        self._apply_ios_mode_rules()

    # ── Step collection (delegates to shared pipeline_config) ────────────────

    def _get_checked_steps(self) -> frozenset[str]:
        """Raw set of step keys whose UI switch is on."""
        return frozenset(key for key, var in self.step_vars.items() if var.get())

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

        cfg = PipelineConfig(
            version=self.version_var.get().strip(),
            build=self.build_var.get().strip(),
            recipients=self.recipients_var.get().strip() or None,
            commit_message=self.commit_msg_var.get().strip() or "pre-release cleanup",
            pub_upgrade=self._pub_mode.get() == "pub upgrade",
            android_build_mode=self._resolve_build_mode(self._shorebird_android, self._android_sb_mode),
            ios_build_mode=self._resolve_build_mode(self._shorebird_ios, self._ios_sb_mode),
            power_mode=self._power_mode.get(),
            quit_after_power=self._quit_after_power.get(),
            git_enabled=self._git_enabled.get(),
            common_enabled=self._common_enabled.get(),
            android_enabled=self._android_enabled.get(),
            ios_enabled=bool(self._ios_enabled and self._ios_enabled.get()),
            post_enabled=self._post_enabled.get(),
            enabled_steps=self._get_checked_steps(),
        )

        all_steps = ordered_steps(cfg, include_ios=self._show_ios)

        self.ui_queue.put(("busy", (True, "Preparing run...")))
        self._console.clear()
        self._tab_selector.set("Console")
        self._switch_tab("Console")

        self._pipeline_thread = Thread(
            target=self._run_pipeline_thread,
            args=(all_steps, cfg),
            daemon=True,
        )
        self._pipeline_thread.start()

    def _run_pipeline_thread(self, all_steps: list[StepDef], cfg: PipelineConfig):
        if cfg.version and cfg.build:
            write_version(cfg.version, cfg.build)

        step_filter = step_enabled_filter(cfg)
        for key, _, _, _ in all_steps:
            if step_filter(key):
                self.ui_queue.put(("status", (key, "pending")))

        platforms_str = cfg.platforms_label()

        log_buffer: deque[str] = deque(maxlen=MAX_REPORT_LOG_LINES)
        step_results: list[StepResult] = []

        def tee_log(text: str):
            log_buffer.append(text)
            if not self._destroyed:
                self.ui_queue.put(("log", text))

        def tee_tagged(text: str, tag: str):
            log_buffer.append(text)
            if not self._destroyed:
                self.ui_queue.put(("log_tagged", (text, tag)))

        tee_log(f"{APP_TITLE} — {platforms_str}\n")
        tee_log(f"Android build: {cfg.android_build_mode}  |  iOS build: {cfg.ios_build_mode}\n")
        tee_log(f"version={cfg.version} build={cfg.build}\n\n")

        step_times: dict[str, float] = {}

        def on_start(step_key: str):
            step_times[step_key] = time.monotonic()
            self.ui_queue.put(("status", (step_key, "running")))
            tee_tagged(f"\n▶ {step_display_name(step_key)}\n", "step")

        def on_done(ok: bool, step_key: str):
            elapsed = time.monotonic() - step_times.get(step_key, time.monotonic())
            self.ui_queue.put(("status", (step_key, "ok" if ok else "error")))
            name = step_display_name(step_key)
            elapsed_str = fmt_elapsed(elapsed)
            step_results.append((name, ok, elapsed))
            tag = "ok" if ok else "err"
            mark = "✓" if ok else "✗"
            tee_tagged(f"  {mark} {name} — {elapsed_str}\n", tag)

        def _schedule_quit_ui(delay: float) -> None:
            if not self._destroyed:
                self.ui_queue.put(("quit_delayed", delay))

        pipeline_start = time.monotonic()
        completion_msg = ""
        success = False
        try:
            done = run_selected(
                steps=all_steps,
                step_enabled=step_filter,
                log=tee_log,
                stop_check=lambda: self._stop_requested,
                on_step_start=on_start,
                on_step_done=on_done,
                schedule_quit_after_seconds=_schedule_quit_ui,
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
                    log_lines=log_buffer,
                    step_results=step_results,
                    version=cfg.version,
                    build=cfg.build,
                    platforms=platforms_str,
                    total_elapsed=total_elapsed,
                    success=success,
                    log=tee_log,
                )
            except Exception as exc:
                tee_log(f"Build report error: {exc}\n")
            terminate_active_processes()
            self.ui_queue.put(("busy", (False, completion_msg)))

    def _on_closing(self):
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
        from run import _ensure_deps
        _ensure_deps(print)
    app = BuildApp()
    app.mainloop()


if __name__ == "__main__":
    main()
