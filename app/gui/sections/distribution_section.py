"""Distribution — Store uploads, cloud copies, and email notification."""

from __future__ import annotations

import customtkinter as ctk

from core.config_store import distribution_recipients_from_config, get_app_config, parse_recipients
from core.steps import DISTRIBUTION_STEPS
from gui.sections.contracts import ConfigPanelHost
from gui.sections import prerequisites as P
from gui.widgets import card, section_label, segmented_button
from gui.sections import widgets as W
from gui.theme import COLORS, PAD, RADIUS


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    preset_emails = distribution_recipients_from_config()
    off = 0
    c = W.build_card(scroll, row)
    
    # 1. Prerequisite Banners
    if not P.google_play_configured():
        W.build_prereq_banner(
            c, row=off, message=P.missing_keys_message(("GOOGLE_PLAY_JSON_KEY",)),
            fonts=app._fonts, tone="warn"
        )
        off += 1
        app._steps_disabled_by_prereq.add("google_play_upload")

    if not P.appstore_api_configured():
        W.build_prereq_banner(
            c, row=off, message=P.missing_keys_message(("APP_STORE_ISSUER_ID", "APP_STORE_API_KEY")),
            fonts=app._fonts, tone="warn"
        )
        off += 1
        app._steps_disabled_by_prereq.add("appstore_upload")

    if not P.drive_creds_configured():
        W.build_prereq_banner(
            c, row=off, message=P.missing_keys_message(("GOOGLE_DRIVE_CREDENTIALS_JSON",)),
            fonts=app._fonts, tone="warn"
        )
        off += 1
        app._steps_disabled_by_prereq.add("drive_upload")

    # 2. Section Header
    W.build_section_header(
        c, title="Distribution", 
        subtitle="Deploy builds to app stores, cloud storage, and notify recipients.",
        fonts=app._fonts, section_key="distribution", app=app, header_row=off,
    )
    off += 1

    # 3. Google Play Upload + Track Selector
    conf = get_app_config()
    dist_conf = conf.get("distribution") or {}
    app._google_play_track = ctk.StringVar(value=str(dist_conf.get("google_play_track") or "production"))

    def _track_selector(parent: ctk.CTkFrame, start_col: int) -> int:
        track_seg = app._track_section("distribution", segmented_button(
            parent, 
            values=["production", "beta", "alpha", "internal"],
            variable=app._google_play_track,
            font=app._fonts["body_sm"],
        ))
        track_seg.grid(row=0, column=start_col, padx=PAD["sm"])
        return start_col + 1

    play_step = DISTRIBUTION_STEPS[0] # google_play_upload
    W.add_step_row(
        c, app=app, key=play_step[0], label=play_step[1], desc=play_step[2],
        section_key="distribution", grid_row=off, default_on=play_step[3],
        trailing_widgets=_track_selector
    )
    off += 1

    # 4. Remaining Upload Steps (AppStore, Drive)
    for other_step in DISTRIBUTION_STEPS[1:]:
        W.add_step_row(
            c, app=app, key=other_step[0], label=other_step[1], desc=other_step[2],
            section_key="distribution", grid_row=off, default_on=other_step[3]
        )
        off += 1
    
    # 5. Email Recipients List
    app._track_section("distribution", ctk.CTkLabel(
        c, text="Preset Recipient Emails:",
        font=app._fonts["body_sm"], text_color=COLORS["muted"],
    )).grid(row=off, column=0, sticky="w", padx=PAD["lg"], pady=(PAD["sm"], PAD["sm"]))
    off += 1

    selected_defaults = {email.lower() for email in preset_emails}

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
            c,
            text=email,
            variable=var,
            command=_refresh_runtime_recipients,
            corner_radius=4,
            border_width=2,
            checkbox_width=18,
            checkbox_height=18,
            font=app._fonts["body_sm"],
        )).grid(row=off, column=0, columnspan=2, sticky="w", padx=PAD["lg"], pady=(0, 4))
        off += 1

    app._track_section("distribution", ctk.CTkLabel(
        c, text="Additional Emails (comma-separated):",
        font=app._fonts["body_sm"], text_color=COLORS["muted"],
    )).grid(row=off, column=0, sticky="w", padx=PAD["lg"], pady=(PAD["sm"], PAD["sm"]))
    off += 1

    app._track_section("distribution", ctk.CTkEntry(
        c, textvariable=extra_var,
        corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=off, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=(0, PAD["lg"]))
    extra_var.trace_add("write", _refresh_runtime_recipients)
    _refresh_runtime_recipients()

    def _serialize() -> dict:
        selected = [email for email, var in preset_vars if var.get()]
        selected_set = {v.lower() for v in selected}
        extra_parsed = parse_recipients([e.strip() for e in extra_var.get().split(",") if e.strip()])
        extra = [email for email in extra_parsed if email.lower() not in selected_set]
        
        return {
            "google_play_track": app._google_play_track.get(),
            "recipients_list": selected + extra,
        }

    app._gui_config_serializers["distribution"] = _serialize
    return row + 1
