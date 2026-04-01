"""Pre-Git section — pre-release commit + message."""

from __future__ import annotations

import customtkinter as ctk

from core.constants import DEFAULT_COMMIT_MESSAGE_PRE
from gui.sections.contracts import ConfigPanelHost
from core.config_store import get_section
from core.steps import COMMIT_PRE_STEPS
from gui.sections import prerequisites as P
from gui.sections import widgets as W


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("pre_git")
    app._commit_msg_pre = ctk.StringVar(
        value=(state.get("commit_message") or DEFAULT_COMMIT_MESSAGE_PRE).strip()
        or DEFAULT_COMMIT_MESSAGE_PRE,
    )
    overrides = W.step_var_overrides(list(COMMIT_PRE_STEPS), state)

    ok, _ = P.flutter_project_prereq_status()
    off = 0
    c = W.build_card(scroll, row)
    W.build_section_header(
        c, title="Pre-Git", fonts=app._fonts,
        section_key="git_pre", app=app, header_row=off,
    )
    W.build_commit_message_row(
        c, row=1 + off, label_text="Commit message:", section_key="git_pre", msg_var=app._commit_msg_pre,
        fonts=app._fonts, app=app,
    )
    W.build_step_rows_from_defs(
        c, app=app, section_key="git_pre", steps=list(COMMIT_PRE_STEPS),
        first_grid_row=2 + off, step_var_overrides=overrides,
    )
    if not ok:
        W.disable_section_widgets(app, "git_pre")

    def _serialize() -> dict:
        return {
            "commit_message": app._commit_msg_pre.get().strip(),
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in COMMIT_PRE_STEPS},
        }

    app._gui_config_serializers["pre_git"] = _serialize
    return row + 1
