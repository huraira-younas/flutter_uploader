"""Post-build section — outputs, Drive, shutdown."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from core.constants import OUTPUTS_DIR
from core.config_store import get_section
from gui.widgets import segmented_button
from gui.sections import prerequisites as P
from gui.sections import widgets as W
from core.steps import POST_STEPS
from gui.theme import PAD
from helpers.platform_utils import open_folder


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("post_build")
    pm = (state.get("power_mode") or "Shutdown")
    app._power_mode = ctk.StringVar(
        value=pm if pm in ("Shutdown", "Sleep") else "Shutdown",
    )
    app._quit_after_power = ctk.BooleanVar(value=bool(state.get("quit_after_power", False)))
    app._register_section_bool_var("post", app._quit_after_power)

    overrides = W.step_var_overrides(list(POST_STEPS), state)

    ok_flutter, _ = P.flutter_project_prereq_status()
    off = 0
    c = W.build_card(scroll, row)
    if ok_flutter and not P.drive_creds_configured():
        W.build_prereq_banner(
            c,
            row=off,
            message=(
                "Upload to Drive requires GOOGLE_DRIVE_CREDENTIALS_JSON in "
                "Settings → Environment (Save environment)."
            ),
            fonts=app._fonts,
            tone="warn",
        )
        off += 1
        app._steps_disabled_by_prereq.add("drive_upload")
    W.build_section_header(
        c, title="Post Build", 
        subtitle="Automation for distribution, cloud uploads, and system power management.",
        fonts=app._fonts, section_key="post", app=app, header_row=off,
    )
    W.build_step_rows_from_defs(
        c, app=app, section_key="post", steps=list(POST_STEPS),
        first_grid_row=1 + off, step_var_overrides=overrides,
        trailing_widgets_by_key={
            "open_folders": _open_outputs_now_button(app),
            "shutdown": _shutdown_controls(app),
        },
    )
    if "drive_upload" in app._steps_disabled_by_prereq:
        app.step_vars["drive_upload"].set(False)
        app.step_switches["drive_upload"].configure(state="disabled")
    if not ok_flutter:
        W.disable_section_widgets(app, "post")

    def _serialize() -> dict:
        return {
            "power_mode": app._power_mode.get(),
            "quit_after_power": app._quit_after_power.get(),
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in POST_STEPS},
        }

    app._gui_config_serializers["post_build"] = _serialize
    return row + 1


def _open_outputs_now_button(app: ConfigPanelHost):
    def _build(parent: ctk.CTkFrame, start_col: int) -> int:
        def _open_now() -> None:
            log = getattr(app, "log", None)
            sink = log if callable(log) else (lambda _m: None)
            try:
                OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                sink(f"Failed to create outputs folder: {exc}\n")
                return
            sink(f"\n>> Open outputs folder: {OUTPUTS_DIR}\n")
            open_folder(OUTPUTS_DIR, sink)

        btn = app._track_section("post", ctk.CTkButton(
            parent,
            text="Open now",
            font=app._fonts["body_sm"],
            command=_open_now,
            width=88,
        ))
        btn.grid(row=0, column=start_col, padx=(0, PAD["sm"]), sticky="e")
        return start_col + 1

    return _build


def _shutdown_controls(app: ConfigPanelHost):
    def _build(parent: ctk.CTkFrame, start_col: int) -> int:
        app._track_section("post", segmented_button(
            parent, values=["Shutdown", "Sleep"],
            variable=app._power_mode, font=app._fonts["body_sm"],
        )).grid(row=0, column=start_col, padx=PAD["sm"])
        qcb = app._track_section("post", ctk.CTkCheckBox(
            parent,
            text="Quit app after countdown",
            variable=app._quit_after_power,
            font=app._fonts["body_sm"],
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
            border_width=2,
        ))
        qcb.grid(row=0, column=start_col + 1, padx=(0, PAD["sm"]), sticky="w")
        return start_col + 2

    return _build
