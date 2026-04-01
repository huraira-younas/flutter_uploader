"""App Info section — version and build fields."""

from __future__ import annotations

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from gui.widgets import card, section_label
from core.config_store import get_section
from helpers.version import read_version
from gui.theme import PAD, RADIUS


def mount(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame, row: int) -> int:
    state = get_section("app_info")
    frame = card(scroll, row=row, column=0, sticky="ew", pady=(0, 12))
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(3, weight=1)

    section_label(frame, "App Info", app._fonts["section"]).grid(
        row=0, column=0, columnspan=4, sticky="w", padx=PAD["lg"], pady=(PAD["md"], PAD["sm"]),
    )

    v_file, b_file = read_version()
    v = (state.get("version") or "").strip() or v_file
    b = (state.get("build") or "").strip() or b_file

    ctk.CTkLabel(frame, text="Version:").grid(
        row=1, column=0, padx=(PAD["lg"], PAD["sm"]), pady=(0, PAD["lg"]), sticky="e",
    )
    app.version_var = ctk.StringVar(value=v)
    app._track(ctk.CTkEntry(
        frame, textvariable=app.version_var, corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=1, column=1, padx=(0, PAD["sm"]), pady=(0, PAD["lg"]), sticky="ew")

    ctk.CTkLabel(frame, text="Build:").grid(
        row=1, column=2, padx=(PAD["sm"], PAD["sm"]), pady=(0, PAD["lg"]), sticky="e",
    )
    app.build_var = ctk.StringVar(value=b)
    app._track(ctk.CTkEntry(
        frame, textvariable=app.build_var, corner_radius=RADIUS["input"], border_width=1,
    )).grid(row=1, column=3, padx=(0, PAD["lg"]), pady=(0, PAD["lg"]), sticky="ew")

    def _serialize_app_info() -> dict:
        chunk = get_section("app_info")
        base = dict(chunk) if isinstance(chunk, dict) else {}
        base.pop("flutter_project_root", None)
        return {
            **base,
            "version": app.version_var.get().strip(),
            "build": app.build_var.get().strip(),
        }

    app._gui_config_serializers["app_info"] = _serialize_app_info
    return row + 1
