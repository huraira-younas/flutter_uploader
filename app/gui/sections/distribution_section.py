"""Distribution — Drive email recipients."""

from __future__ import annotations

import customtkinter as ctk

from core.config_store import distribution_recipients_from_config, parse_recipients
from gui.sections.contracts import ConfigPanelHost
from gui.sections import prerequisites as P
from gui.widgets import card, section_label
from gui.sections import widgets as W
from gui.theme import COLORS, PAD, RADIUS


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    preset_emails = distribution_recipients_from_config()
    frame = card(scroll, row=row, column=0, sticky="ew", pady=(0, 12))
    frame.grid_columnconfigure(0, weight=1)

    r = 0
    gmail_ok = P.gmail_configured()
    if not gmail_ok:
        miss = P.missing_keys_message(("GMAIL_USER", "GMAIL_APP_PASSWORD"))
        if miss:
            W.build_prereq_banner(
                frame, row=r, message=miss, fonts=app._fonts, tone="warn",
            )
            r += 1

    section_label(frame, "Distribution", app._fonts["section"]).grid(
        row=r, column=0, sticky="w", padx=PAD["lg"], pady=(PAD["md"], 5),
    )
    r += 1
    ctk.CTkLabel(
        frame, text="Preset Recipient Emails:",
        font=app._fonts["body_sm"], text_color=COLORS["muted"],
    ).grid(row=r, column=0, sticky="w", padx=PAD["lg"], pady=(0, PAD["sm"]))
    r += 1

    selected_defaults = {email.lower() for email in preset_emails}

    row_idx = r
    preset_vars: list[tuple[str, ctk.BooleanVar]] = []
    app.recipients_var = ctk.StringVar(value="")
    extra_var = ctk.StringVar(value="")

    def _refresh_runtime_recipients(*_args) -> None:
        selected = [email for email, var in preset_vars if var.get()]
        selected_set = {v.lower() for v in selected}
        extra_parsed = parse_recipients([e.strip() for e in extra_var.get().split(",") if e.strip()])
        extra = [email for email in extra_parsed if email.lower() not in selected_set]
        app.recipients_var.set(",".join(selected + extra))

    for email in preset_emails:
        var = ctk.BooleanVar(value=email.lower() in selected_defaults)
        preset_vars.append((email, var))
        app._track_section("distribution", ctk.CTkCheckBox(
            frame,
            text=email,
            variable=var,
            command=_refresh_runtime_recipients,
            corner_radius=4,
            border_width=2,
            checkbox_width=18,
            checkbox_height=18,
            font=app._fonts["body_sm"],
        )).grid(row=row_idx, column=0, sticky="w", padx=PAD["lg"], pady=(0, 4))
        row_idx += 1

    ctk.CTkLabel(
        frame, text="Additional Emails (comma-separated):",
        font=app._fonts["body_sm"], text_color=COLORS["muted"],
    ).grid(row=row_idx, column=0, sticky="w", padx=PAD["lg"], pady=(PAD["sm"], PAD["sm"]))
    row_idx += 1

    app._track_section("distribution", ctk.CTkEntry(
        frame, textvariable=extra_var,
        corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=row_idx, column=0, sticky="ew", padx=PAD["lg"], pady=(0, PAD["lg"]))
    extra_var.trace_add("write", _refresh_runtime_recipients)
    _refresh_runtime_recipients()

    if not gmail_ok:
        W.disable_section_widgets(app, "distribution")

    def _serialize() -> list:
        selected = [email for email, var in preset_vars if var.get()]
        selected_set = {v.lower() for v in selected}
        extra_parsed = parse_recipients([e.strip() for e in extra_var.get().split(",") if e.strip()])
        extra = [email for email in extra_parsed if email.lower() not in selected_set]
        return selected + extra

    app._gui_config_serializers["distribution"] = _serialize
    return row + 1
