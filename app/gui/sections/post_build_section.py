"""Post-build section — outputs, Drive, shutdown."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from core.config_store import get_section
from gui.widgets import segmented_button
from gui.sections import prerequisites as P
from gui.sections import widgets as W
from core.steps import POST_STEPS
from gui.theme import PAD


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("post_build")
    pm = (state.get("power_mode") or "Shutdown")
    app._power_mode = ctk.StringVar(
        value=pm if pm in ("Shutdown", "Sleep") else "Shutdown",
    )
    app._quit_after_power = ctk.BooleanVar(value=bool(state.get("quit_after_power", False)))
    app._register_section_bool_var("post", app._quit_after_power)

    overrides = W.step_var_overrides(list(POST_STEPS), state)

    ok, msg = P.flutter_project_prereq_status()
    off = 0
    c = W.build_card(scroll, row)
    if not ok:
        W.build_prereq_banner(c, row=off, message=msg, fonts=app._fonts)
        off += 1
    dw = P.drive_upload_warning()
    if dw:
        W.build_prereq_banner(c, row=off, message=dw, fonts=app._fonts, tone="warn")
        off += 1
    W.build_section_header(
        c, title="Post-Build", fonts=app._fonts,
        section_key="post", app=app, header_row=off,
    )
    W.build_step_rows_from_defs(
        c, app=app, section_key="post", steps=list(POST_STEPS),
        first_grid_row=1 + off, step_var_overrides=overrides,
        trailing_widgets_by_key={"shutdown": _shutdown_controls(app)},
    )
    if not ok:
        W.disable_section_widgets(app, "post")

    def _serialize() -> dict:
        return {
            "power_mode": app._power_mode.get(),
            "quit_after_power": app._quit_after_power.get(),
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in POST_STEPS},
        }

    app._gui_config_serializers["post_build"] = _serialize
    return row + 1


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
