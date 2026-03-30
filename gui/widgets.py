"""Reusable stateless widget factories for the Flutter Uploader GUI."""

from __future__ import annotations

import customtkinter as ctk

from gui.theme import COLORS, RADIUS


def card(parent: ctk.CTkFrame, **grid_opts) -> ctk.CTkFrame:
    f = ctk.CTkFrame(
        parent,
        border_color=COLORS["card_border"],
        corner_radius=RADIUS["card"],
        fg_color=COLORS["card_bg"],
        border_width=1,
    )
    f.grid(**grid_opts)
    return f


def section_label(parent: ctk.CTkFrame, text: str, font: ctk.CTkFont, **grid_opts) -> ctk.CTkLabel:
    lbl = ctk.CTkLabel(parent, text_color=COLORS["section"], text=text, font=font)
    lbl.grid(**grid_opts)
    return lbl
