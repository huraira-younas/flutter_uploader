"""Common section — Flutter clean and dependencies."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from core.config_store import get_section
from gui.widgets import segmented_button
from gui.sections import prerequisites as P
from gui.sections import widgets as W
from core.steps import COMMON_STEPS
from gui.theme import PAD


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("common")
    pub_mode = (state.get("pub_mode") or "pub get").lower()
    app._pub_mode = ctk.StringVar(
        value="pub upgrade" if pub_mode == "pub upgrade" else "pub get",
    )

    overrides = W.step_var_overrides(list(COMMON_STEPS), state)

    ok, _ = P.flutter_project_prereq_status()
    off = 0
    c = W.build_card(scroll, row)
    W.build_section_header(
        c, title="Common", 
        subtitle="Core maintenance tasks like cache cleaning and dependency resolution.",
        fonts=app._fonts, section_key="common", app=app, header_row=off,
    )

    n = len(COMMON_STEPS)
    for offset, (key, label, desc, _def) in enumerate(COMMON_STEPS):
        grid_r = 1 + offset + off
        row_pady = (PAD["sm"], PAD["md"]) if offset == n - 1 else (PAD["sm"], PAD["sm"])
        if key == "pub_get":
            _build_pub_row(
                app, c, grid_row=grid_r, label=label, desc=desc,
                pub_var=overrides[key], pady=row_pady,
            )
        else:
            W.add_step_row(
                c, app=app, key=key, label=label, desc=desc,
                section_key="common",
                grid_row=grid_r, default_on=_def,
                var=overrides[key],
                pady=row_pady,
            )
    if not ok:
        W.disable_section_widgets(app, "common")

    def _serialize() -> dict:
        return {
            "pub_mode": app._pub_mode.get(),
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in COMMON_STEPS},
        }

    app._gui_config_serializers["common"] = _serialize
    return row + 1


def _build_pub_row(
    app: ConfigPanelHost,
    parent: ctk.CTkFrame,
    *,
    grid_row: int,
    label: str,
    desc: str,
    pub_var: ctk.BooleanVar,
    pady: tuple[int, int] | None = None,
) -> None:
    W.add_step_row(
        parent,
        app=app,
        key="pub_get",
        section_key="common",
        label=label,
        desc=desc,
        grid_row=grid_row,
        default_on=False,
        var=pub_var,
        pady=pady,
        trailing_widgets=_pub_mode_controls(app),
    )


def _pub_mode_controls(app: ConfigPanelHost):
    def _build(parent: ctk.CTkFrame, start_col: int) -> int:
        pub_seg = app._track_section("common", segmented_button(
            parent, values=["pub get", "pub upgrade"],
            variable=app._pub_mode, font=app._fonts["body_sm"],
        ))
        pub_seg.grid(row=0, column=start_col, padx=PAD["sm"])
        return start_col + 1

    return _build
