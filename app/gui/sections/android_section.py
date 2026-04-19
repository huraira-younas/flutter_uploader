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
    overrides = W.step_var_overrides(list(ANDROID_STEPS), state)

    ok_flutter, _ = P.flutter_project_prereq_status()
    has_folder = P.has_android_folder()
    off = 0
    c = W.build_card(scroll, row)

    if ok_flutter and not has_folder:
        W.build_prereq_banner(
            c, row=off, message="No 'android/' folder found in project root. Build steps disabled.",
            fonts=app._fonts, tone="warn"
        )
        off += 1

    W.build_section_header(
        c, title="Android", 
        subtitle="Configure Android compilation for APK and App Bundle formats.",
        fonts=app._fonts, section_key="android", app=app, header_row=off,
    )
    W.build_step_rows_from_defs(
        c, app=app, section_key="android", steps=list(ANDROID_STEPS),
        first_grid_row=1 + off, step_var_overrides=overrides,
    )
    if not ok_flutter or not has_folder:
        W.disable_section_widgets(app, "android")

    def _serialize() -> dict:
        return {
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in ANDROID_STEPS},
        }

    app._gui_config_serializers["android"] = _serialize
    return row + 1
