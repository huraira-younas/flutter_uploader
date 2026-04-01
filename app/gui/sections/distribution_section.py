"""Distribution — Drive email recipients."""

from __future__ import annotations

import customtkinter as ctk

from core.constants import DEFAULT_GMAIL_RECIPIENTS
from gui.sections.contracts import ConfigPanelHost
from gui.widgets import card, section_label
from core.config_store import get_section
from gui.theme import COLORS, PAD, RADIUS


def _parse_emails(raw: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for chunk in raw.split(","):
        email = chunk.strip()
        if not email:
            continue
        lowered = email.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        out.append(email)
    return out


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("distribution")
    frame = card(scroll, row=row, column=0, sticky="ew", pady=(0, 12))
    frame.grid_columnconfigure(0, weight=1)

    section_label(frame, "Distribution", app._fonts["section"]).grid(
        row=0, column=0, sticky="w", padx=PAD["lg"], pady=(PAD["md"], 5),
    )
    ctk.CTkLabel(
        frame, text="Preset Recipient Emails:",
        font=app._fonts["body_sm"], text_color=COLORS["muted"],
    ).grid(row=1, column=0, sticky="w", padx=PAD["lg"], pady=(0, PAD["sm"]))

    current_emails = [str(v).strip() for v in state] if isinstance(state, list) else []
    current_emails = [v for v in current_emails if v]
    current_emails = _parse_emails(",".join(current_emails))
    preset_emails = DEFAULT_GMAIL_RECIPIENTS[:] if DEFAULT_GMAIL_RECIPIENTS else current_emails
    selected_defaults = {email.lower() for email in current_emails} if current_emails else {email.lower() for email in preset_emails}

    row_idx = 2
    preset_vars: list[tuple[str, ctk.BooleanVar]] = []
    app.recipients_var = ctk.StringVar(value="")
    preset_set = {email.lower() for email in preset_emails}
    extra_default = ",".join(email for email in current_emails if email.lower() not in preset_set)
    extra_var = ctk.StringVar(value=extra_default)

    def _refresh_runtime_recipients(*_args) -> None:
        selected = [email for email, var in preset_vars if var.get()]
        selected_set = {v.lower() for v in selected}
        extra = [email for email in _parse_emails(extra_var.get().strip()) if email.lower() not in selected_set]
        app.recipients_var.set(",".join(selected + extra))

    for email in preset_emails:
        var = ctk.BooleanVar(value=email.lower() in selected_defaults)
        preset_vars.append((email, var))
        app._track(ctk.CTkCheckBox(
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

    app._track(ctk.CTkEntry(
        frame, textvariable=extra_var,
        corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=row_idx, column=0, sticky="ew", padx=PAD["lg"], pady=(0, PAD["lg"]))
    extra_var.trace_add("write", _refresh_runtime_recipients)
    _refresh_runtime_recipients()

    def _serialize() -> dict:
        extra_raw = extra_var.get().strip()
        selected = [email for email, var in preset_vars if var.get()]
        selected_set = {v.lower() for v in selected}
        extra = [email for email in _parse_emails(extra_raw) if email.lower() not in selected_set]
        return selected + extra

    app._gui_config_serializers["distribution"] = _serialize
    return row + 1
