"""Build Config section — version, build, and git branch."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from core.constants import DEFAULT_GIT_BRANCH
from core.config_store import get_app_config
from gui.widgets import card, section_label
from gui.theme import COLORS, PAD, RADIUS
from helpers.version import read_version


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    frame = card(scroll, row=row, column=0, sticky="ew", pady=(0, 12))
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(3, weight=1)

    section_label(frame, "Build Config", app._fonts["section"]).grid(
        row=0, column=0, columnspan=4, sticky="w", padx=PAD["lg"], pady=(PAD["md"], 0),
    )
    ctk.CTkLabel(
        frame,
        text="Manage application version, build number, and target Git branch.",
        font=app._fonts["body_sm"],
        text_color=COLORS["text_dim"],
        wraplength=550,
        justify="left",
    ).grid(row=1, column=0, columnspan=4, sticky="w", padx=PAD["lg"], pady=(0, PAD["sm"]))

    v, b = read_version()

    # Version & Build Row
    ctk.CTkLabel(frame, text="Version:").grid(
        row=2, column=0, padx=(PAD["lg"], PAD["sm"]), pady=(0, PAD["sm"]), sticky="w",
    )
    app.version_var = ctk.StringVar(value=v)
    app._track(ctk.CTkEntry(
        frame, textvariable=app.version_var, corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=2, column=1, padx=(0, PAD["sm"]), pady=(0, PAD["sm"]), sticky="ew")

    ctk.CTkLabel(frame, text="Build:").grid(
        row=2, column=2, padx=(PAD["sm"], PAD["sm"]), pady=(0, PAD["sm"]), sticky="w",
    )
    app.build_var = ctk.StringVar(value=b)
    app._track(ctk.CTkEntry(
        frame, textvariable=app.build_var, corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=2, column=3, padx=(0, PAD["lg"]), pady=(0, PAD["sm"]), sticky="ew")

    # Git Branch Row
    ctk.CTkLabel(frame, text="Git Branch:").grid(
        row=3, column=0, padx=(PAD["lg"], PAD["sm"]), pady=(0, PAD["lg"]), sticky="w",
    )
    conf = get_app_config()
    app._git_branch = ctk.StringVar(
        value=str(conf.get("git_branch") or DEFAULT_GIT_BRANCH).strip()
        or DEFAULT_GIT_BRANCH,
    )
    app._track(ctk.CTkEntry(
        frame, textvariable=app._git_branch, corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=3, column=1, columnspan=3, padx=(0, PAD["lg"]), pady=(0, PAD["lg"]), sticky="ew")

    def _serialize() -> dict:
        return {
            "git_branch": app._git_branch.get().strip(),
        }

    app._gui_config_serializers["app_info"] = _serialize
    return row + 1
