"""Android build section."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from core.config_store import get_section
from gui.sections import widgets as W
from core.steps import ANDROID_STEPS


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("android")
    app._shorebird_android = ctk.BooleanVar(value=bool(state.get("shorebird", False)))
    app._register_section_bool_var("android", app._shorebird_android)
    mode = (state.get("shorebird_mode") or "Release")
    app._android_sb_mode = ctk.StringVar(value=mode if mode in ("Release", "Patch") else "Release")

    overrides = W.step_var_overrides(list(ANDROID_STEPS), state)

    c = W.build_card(scroll, row)
    W.build_section_header(
        c, title="Android Build", fonts=app._fonts,
        section_key="android", app=app,
        shorebird_bundle=(app._shorebird_android, app._android_sb_mode),
    )
    W.build_step_rows_from_defs(
        c, app=app, section_key="android", steps=list(ANDROID_STEPS),
        first_grid_row=1, step_var_overrides=overrides,
    )

    def _serialize() -> dict:
        return {
            "shorebird": app._shorebird_android.get(),
            "shorebird_mode": app._android_sb_mode.get(),
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in ANDROID_STEPS},
        }

    app._gui_config_serializers["android"] = _serialize
    return row + 1
