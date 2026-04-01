"""Android build section."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from core.config_store import get_section
from gui.sections import prerequisites as P
from gui.sections import widgets as W
from core.steps import ANDROID_STEPS


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("android")
    app._shorebird_android = ctk.BooleanVar(value=bool(state.get("shorebird", False)))
    app._register_section_bool_var("android", app._shorebird_android)
    mode = (state.get("shorebird_mode") or "Release")
    app._android_sb_mode = ctk.StringVar(value=mode if mode in ("Release", "Patch") else "Release")

    overrides = W.step_var_overrides(list(ANDROID_STEPS), state)

    ok, msg = P.flutter_project_prereq_status()
    off = 1 if not ok else 0
    c = W.build_card(scroll, row)
    if not ok:
        W.build_prereq_banner(c, row=0, message=msg, fonts=app._fonts)
    W.build_section_header(
        c, title="Android Build", fonts=app._fonts,
        section_key="android", app=app,
        shorebird_bundle=(app._shorebird_android, app._android_sb_mode),
        header_row=off,
    )
    W.build_step_rows_from_defs(
        c, app=app, section_key="android", steps=list(ANDROID_STEPS),
        first_grid_row=1 + off, step_var_overrides=overrides,
    )
    if not ok:
        W.disable_section_widgets(app, "android")

    def _serialize() -> dict:
        return {
            "shorebird": app._shorebird_android.get(),
            "shorebird_mode": app._android_sb_mode.get(),
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in ANDROID_STEPS},
        }

    app._gui_config_serializers["android"] = _serialize
    return row + 1
