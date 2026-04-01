"""iOS build section (macOS only — mount skipped on other platforms)."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from core.config_store import get_section
from gui.sections import widgets as W
from core.steps import IOS_STEPS


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    if not app._show_ios:
        return row

    state = get_section("ios")
    app._shorebird_ios = ctk.BooleanVar(value=bool(state.get("shorebird", app._shorebird_ok)))
    app._register_section_bool_var("ios", app._shorebird_ios)
    mode = (state.get("shorebird_mode") or "Release")
    app._ios_sb_mode = ctk.StringVar(value=mode if mode in ("Release", "Patch") else "Release")

    overrides = W.step_var_overrides(list(IOS_STEPS), state)

    c = W.build_card(scroll, row)
    W.build_section_header(
        c, title="iOS Build", fonts=app._fonts,
        section_key="ios", app=app,
        shorebird_bundle=(app._shorebird_ios, app._ios_sb_mode),
    )
    W.build_step_rows_from_defs(
        c, app=app, section_key="ios", steps=list(IOS_STEPS),
        first_grid_row=1, step_var_overrides=overrides,
    )

    def _serialize() -> dict:
        return {
            "shorebird": app._shorebird_ios.get(),
            "shorebird_mode": app._ios_sb_mode.get(),
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in IOS_STEPS},
        }

    app._gui_config_serializers["ios"] = _serialize
    return row + 1
