"""Reusable config-panel widgets (DRY building blocks for section modules)."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from gui.widgets import card, section_label, segmented_button
from gui.sections.contracts import ConfigPanelHost
from gui.theme import COLORS, RADIUS, PAD


def build_card(parent: ctk.CTkFrame, row: int) -> ctk.CTkFrame:
    c = card(parent, row=row, column=0, sticky="ew", pady=(0, 12))
    c.grid_columnconfigure(0, weight=1)
    return c


def build_prereq_banner(
    parent: ctk.CTkFrame,
    *,
    message: str,
    fonts: dict[str, ctk.CTkFont],
    tone: str = "danger",
    row: int,
) -> None:
    color = COLORS.get(tone, COLORS["danger"])
    ctk.CTkLabel(
        parent,
        text=message,
        font=fonts["body_sm"],
        text_color=color,
        wraplength=720,
        justify="left",
        anchor="w",
    ).grid(row=row, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=(PAD["md"], PAD["sm"]))


def disable_section_widgets(app: ConfigPanelHost, section_key: str) -> None:
    for w in app._section_widgets.get(section_key, []):
        try:
            w.configure(state="disabled")
        except Exception:
            pass


def build_section_header(
    parent: ctk.CTkFrame,
    *,
    title: str,
    fonts: dict[str, ctk.CTkFont],
    section_key: str,
    app: ConfigPanelHost,
    shorebird_bundle: tuple[ctk.BooleanVar, ctk.StringVar | None] | None = None,
    header_row: int = 0,
) -> None:
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.grid(row=header_row, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=(PAD["md"], 5))
    header.grid_columnconfigure(0, weight=1)
    section_label(header, title, fonts["section"]).grid(row=0, column=0, sticky="w")

    col = 1
    if shorebird_bundle is not None:
        sb_var, mode_var = shorebird_bundle
        col = _shorebird_header_controls(header, section_key, sb_var, mode_var, fonts, app, col)

    enabled_var = app.section_enabled_vars.get(section_key)
    if enabled_var is not None:
        app._track_section(section_key, ctk.CTkSwitch(
            header,
            text="Enabled",
            variable=enabled_var,
            font=fonts["body_sm"],
            progress_color=COLORS["accent"],
            command=lambda sk=section_key: app._on_section_enabled_changed(sk),
        )).grid(row=0, column=col, sticky="e", padx=(0, PAD["md"]))


def _shorebird_header_controls(
    header: ctk.CTkFrame,
    section_key: str,
    shorebird_var: ctk.BooleanVar,
    mode_var: ctk.StringVar | None,
    fonts: dict[str, ctk.CTkFont],
    app: ConfigPanelHost,
    start_col: int,
) -> int:
    col = start_col
    mode_seg: ctk.CTkSegmentedButton | None = None
    if mode_var is not None:
        mode_seg = segmented_button(
            header, values=["Release", "Patch"],
            variable=mode_var, font=fonts["body_sm"],
            command=lambda _=None, sk=section_key: app._on_shorebird_mode_changed(sk),
        )
        mode_seg = app._track_section(section_key, mode_seg)
        mode_seg.grid(row=0, column=col, sticky="e", padx=(0, PAD["sm"]))
        app._sb_mode_widgets[section_key] = mode_seg
        col += 1

    cb = app._track_section(section_key, ctk.CTkCheckBox(
        header, variable=shorebird_var, text="Shorebird",
        font=fonts["body_sm"], checkbox_width=18, checkbox_height=18,
        corner_radius=4, border_width=2,
        command=lambda sk=section_key, sv=shorebird_var: app._on_shorebird_toggle(sk, sv),
    ))
    cb.grid(row=0, column=col, sticky="e", padx=(0, PAD["md"]))
    app._sb_checkboxes[section_key] = cb
    col += 1

    if not app._shorebird_ok:
        shorebird_var.set(False)
        cb.configure(state="disabled")
        hint = ctk.CTkLabel(
            header, text="(not installed)",
            font=fonts["body_sm"], text_color=COLORS["danger"],
        )
        hint.grid(row=0, column=col, sticky="e", padx=(0, PAD["sm"]))
        app._sb_hint_labels[section_key] = hint
        col += 1

    if mode_seg is not None:
        mode_seg.configure(state="normal" if shorebird_var.get() else "disabled")
    return col


def build_commit_message_row(
    parent: ctk.CTkFrame,
    *,
    row: int,
    label_text: str,
    section_key: str,
    msg_var: ctk.StringVar,
    fonts: dict[str, ctk.CTkFont],
    app: ConfigPanelHost,
) -> None:
    cm = ctk.CTkFrame(parent, fg_color="transparent")
    cm.grid(row=row, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=(0, PAD["sm"]))
    cm.grid_columnconfigure(1, weight=1)
    lbl = ctk.CTkLabel(cm, text=label_text, font=fonts["body_sm"])
    lbl.grid(row=0, column=0, sticky="w")
    ent = app._track_section(section_key, ctk.CTkEntry(
        cm, textvariable=msg_var, corner_radius=RADIUS["input"], border_width=1,
    ))
    ent.grid(row=0, column=1, sticky="ew", padx=(PAD["sm"], 0))
    # Entry is tracked (locked during pipeline); no section-enable toggling needed.


def add_step_row(
    parent: ctk.CTkFrame,
    *,
    app: ConfigPanelHost,
    key: str,
    label: str,
    desc: str,
    section_key: str,
    grid_row: int,
    default_on: bool = True,
    var: ctk.BooleanVar | None = None,
    trailing_widgets: Callable[[ctk.CTkFrame, int], int] | None = None,
) -> ctk.CTkSwitch:
    row_frame = ctk.CTkFrame(parent, fg_color="transparent")
    row_frame.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=PAD["sm"])
    row_frame.grid_columnconfigure(1, weight=1)

    if var is None:
        var = ctk.BooleanVar(value=default_on)
    app.step_vars[key] = var
    app._register_section_bool_var(section_key, var)
    switch = app._track_section(section_key, ctk.CTkSwitch(
        row_frame, progress_color=COLORS["accent"],
        text=f"{label}  —  {desc}", font=app._fonts["body"], variable=var,
    ))
    switch.grid(row=0, column=0, sticky="w")
    app.step_switches[key] = switch

    status_col = 1
    if trailing_widgets is not None:
        status_col = trailing_widgets(row_frame, status_col)

    add_status_widgets(app, row_frame, key, status_col)
    return switch


def add_status_widgets(app: ConfigPanelHost, parent: ctk.CTkFrame, key: str, column: int) -> None:
    pb = ctk.CTkProgressBar(
        parent, progress_color=COLORS["accent"],
        mode="indeterminate", width=100, height=8,
    )
    pb.grid(row=0, column=column, sticky="e", padx=PAD["sm"])
    pb.grid_remove()
    app.step_progress_bars[key] = pb
    lbl = ctk.CTkLabel(
        parent, text_color=COLORS["text_dim"],
        font=app._fonts["mono_sm"], text="-",
    )
    lbl.grid(row=0, column=column + 1, sticky="e")
    app.step_status_labels[key] = lbl


def build_step_rows_from_defs(
    parent: ctk.CTkFrame,
    *,
    app: ConfigPanelHost,
    section_key: str,
    steps: list[tuple[str, str, str, bool]],
    first_grid_row: int,
    step_var_overrides: dict[str, ctk.BooleanVar] | None = None,
    trailing_widgets_by_key: dict[str, Callable[[ctk.CTkFrame, int], int]] | None = None,
) -> None:
    overrides = step_var_overrides or {}
    trailing = trailing_widgets_by_key or {}
    for offset, (key, label, desc, default_on) in enumerate(steps):
        var = overrides.get(key)
        add_step_row(
            parent, app=app, key=key, label=label, desc=desc,
            section_key=section_key,
            grid_row=first_grid_row + offset,
            default_on=default_on, var=var,
            trailing_widgets=trailing.get(key),
        )


def step_var_overrides(
    steps: list[tuple[str, str, str, bool]],
    section_state: dict[str, object],
) -> dict[str, ctk.BooleanVar]:
    raw_steps = section_state.get("steps")
    saved = raw_steps if isinstance(raw_steps, dict) else {}
    overrides: dict[str, ctk.BooleanVar] = {}
    for key, _lbl, _desc, default_on in steps:
        overrides[key] = ctk.BooleanVar(value=bool(saved.get(key, default_on)))
    return overrides
