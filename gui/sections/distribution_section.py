"""Distribution — Drive email recipients."""

from __future__ import annotations

import os

import customtkinter as ctk

from core.constants import DEFAULT_GMAIL_RECIPIENTS
from gui.sections.contracts import ConfigPanelHost
from gui.widgets import card, section_label
from core.config_store import get_section
from gui.theme import COLORS, PAD, RADIUS


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("distribution")
    frame = card(scroll, row=row, column=0, sticky="ew", pady=(0, 12))
    frame.grid_columnconfigure(0, weight=1)

    section_label(frame, "Distribution", app._fonts["section"]).grid(
        row=0, column=0, sticky="w", padx=PAD["lg"], pady=(PAD["md"], 5),
    )
    ctk.CTkLabel(
        frame, text="Recipient Emails (comma-separated):",
        font=app._fonts["body_sm"], text_color=COLORS["muted"],
    ).grid(row=1, column=0, sticky="w", padx=PAD["lg"], pady=(0, PAD["sm"]))

    saved = (state.get("recipients") or "").strip()
    env_default = os.environ.get("DISTRIBUTION_EMAILS", "").strip()
    default_recipients = saved or env_default or ", ".join(DEFAULT_GMAIL_RECIPIENTS)
    app.recipients_var = ctk.StringVar(value=default_recipients)
    app._track(ctk.CTkEntry(
        frame, textvariable=app.recipients_var,
        corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=2, column=0, sticky="ew", padx=PAD["lg"], pady=(0, PAD["lg"]))

    def _serialize() -> dict:
        return {"recipients": app.recipients_var.get().strip()}

    app._gui_config_serializers["distribution"] = _serialize
    return row + 1
