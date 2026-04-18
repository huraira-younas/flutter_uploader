"""Post-Git section — release commit message, release commit, push."""

from __future__ import annotations

import customtkinter as ctk

from core.constants import DEFAULT_COMMIT_MESSAGE_RELEASE
from gui.sections.contracts import ConfigPanelHost
from core.steps import GIT_POST_STEPS
from core.config_store import get_section
from gui.sections import prerequisites as P
from gui.sections import widgets as W


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("post_git")
    app._commit_msg_release = ctk.StringVar(
        value=(state.get("commit_message") or DEFAULT_COMMIT_MESSAGE_RELEASE).strip()
        or DEFAULT_COMMIT_MESSAGE_RELEASE,
    )
    overrides = W.step_var_overrides(list(GIT_POST_STEPS), state)

    ok, _ = P.flutter_project_prereq_status()
    off = 0
    c = W.build_card(scroll, row)
    W.build_section_header(
        c, title="Post-Git", 
        subtitle="Finalize the release with version tagging and remote synchronization.",
        fonts=app._fonts, section_key="git_post", app=app, header_row=off,
    )
    
    W.build_commit_message_row(
        c, row=1 + off, label_text="Release commit message:", section_key="git_post",
        msg_var=app._commit_msg_release, fonts=app._fonts, app=app,
    )

    W.build_step_rows_from_defs(
        c, app=app, section_key="git_post", steps=list(GIT_POST_STEPS),
        first_grid_row=2 + off, step_var_overrides=overrides,
    )
    if not ok:
        W.disable_section_widgets(app, "git_post")

    def _serialize() -> dict:
        return {
            "commit_message": app._commit_msg_release.get().strip(),
            "steps": {k: app.step_vars[k].get() for k, _, _, _ in GIT_POST_STEPS},
        }

    app._gui_config_serializers["post_git"] = _serialize
    return row + 1
