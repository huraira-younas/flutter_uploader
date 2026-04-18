"""Reusable config-panel widgets (DRY building blocks for section modules)."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from gui.sections.contracts import ConfigPanelHost
from gui.theme import COLORS, PAD, RADIUS
from gui.widgets import section_label, card


def _configure_state(widget, state: str) -> None:
    try:
        widget.configure(state=state)
    except Exception:
        pass


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
        wraplength=550,
        justify="left",
        anchor="w",
    ).grid(row=row, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=(PAD["md"], PAD["sm"]))


def disable_section_widgets(app: ConfigPanelHost, section_key: str) -> None:
    for w in app._section_widgets.get(section_key, []):
        _configure_state(w, "disabled")


def build_section_header(
    parent: ctk.CTkFrame,
    *,
    title: str,
    subtitle: str | None = None,
    fonts: dict[str, ctk.CTkFont],
    section_key: str,
    app: ConfigPanelHost,
    header_row: int = 0,
) -> None:
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.grid(
        row=header_row, column=0, columnspan=2, sticky="ew",
        padx=PAD["lg"], pady=(PAD["md"], PAD["sm"]),
    )
    header.grid_columnconfigure(0, weight=1)
    
    title_frame = ctk.CTkFrame(header, fg_color="transparent")
    title_frame.grid(row=0, column=0, sticky="w")
    
    section_label(title_frame, title, fonts["section"]).grid(row=0, column=0, sticky="w")
    
    if subtitle:
        ctk.CTkLabel(
            title_frame,
            text=subtitle,
            font=fonts["body_sm"],
            text_color=COLORS["text_dim"],
            wraplength=550,
            justify="left",
        ).grid(row=1, column=0, sticky="w")

    col = 1
    enabled_var = app.section_enabled_vars.get(section_key)
    if enabled_var is not None:
        # Use ``_track`` only — never ``_track_section``: the Enabled switch must stay
        # clickable so the user can turn a section back on after disabling it.
        sw = ctk.CTkSwitch(
            header,
            text="Enabled",
            variable=enabled_var,
            font=fonts["body_sm"],
            progress_color=COLORS["accent"],
            command=lambda sk=section_key: app._on_section_enabled_changed(sk),
        )
        app._track(sw).grid(row=0, column=col, sticky="e", padx=(0, PAD["md"]))


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
    pady: tuple[int, int] | None = None,
    trailing_widgets: Callable[[ctk.CTkFrame, int], int] | None = None,
) -> ctk.CTkSwitch:
    row_frame = ctk.CTkFrame(parent, fg_color="transparent")
    pad_y = pady if pady is not None else (PAD["sm"], PAD["sm"])
    row_frame.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=pad_y)
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
    n = len(steps)
    for offset, (key, label, desc, default_on) in enumerate(steps):
        var = overrides.get(key)
        last = offset == n - 1
        row_pady = (PAD["sm"], PAD["md"]) if last else (PAD["sm"], PAD["sm"])
        add_step_row(
            parent, app=app, key=key, label=label, desc=desc,
            section_key=section_key,
            grid_row=first_grid_row + offset,
            default_on=default_on, var=var,
            pady=row_pady,
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
