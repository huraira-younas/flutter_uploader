"""iOS build section (macOS only — mount skipped on other platforms)."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from core.config_store import get_section
from gui.sections import prerequisites as P
from gui.sections import widgets as W
from core.steps import IOS_STEPS


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    if not app._show_ios:
        return row

    state = get_section("ios")
    overrides = W.step_var_overrides(list(IOS_STEPS), state)

    ok_flutter, _ = P.flutter_project_prereq_status()
    off = 0
    c = W.build_card(scroll, row)
    if ok_flutter and not P.appstore_api_configured():
        W.build_prereq_banner(
            c,
            row=off,
            message=(
                "App Store upload requires APP_STORE_ISSUER_ID and APP_STORE_API_KEY in "
                "app/secrets/enviroment.json (Settings → Save environment)."
            ),
            fonts=app._fonts,
            tone="warn",
        )
        off += 1
        app._steps_disabled_by_prereq.add("appstore_upload")
    W.build_section_header(
        c, title="iOS Build", fonts=app._fonts,
        section_key="ios", app=app,
        header_row=off,
    )
    W.build_step_rows_from_defs(
        c, app=app, section_key="ios", steps=list(IOS_STEPS),
        first_grid_row=1 + off, step_var_overrides=overrides,
    )
    if "appstore_upload" in app._steps_disabled_by_prereq:
        app.step_vars["appstore_upload"].set(False)
        app.step_switches["appstore_upload"].configure(state="disabled")
    if not ok_flutter:
        W.disable_section_widgets(app, "ios")

    def _serialize() -> dict:
        return {
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in IOS_STEPS},
        }

    app._gui_config_serializers["ios"] = _serialize
    return row + 1
