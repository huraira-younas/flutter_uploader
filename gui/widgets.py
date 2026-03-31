"""Reusable stateless widget factories for the Flutter Uploader GUI."""

from __future__ import annotations

import customtkinter as ctk

from gui.theme import COLORS, RADIUS, PAD


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


def scrollable_frame(parent: ctk.CTkFrame, **grid_opts) -> ctk.CTkScrollableFrame:
    """Tab-level scrollable frame with themed scrollbar."""
    sf = ctk.CTkScrollableFrame(
        parent, fg_color="transparent",
        scrollbar_button_color=COLORS["card_border"],
        scrollbar_button_hover_color=COLORS["hover"],
    )
    sf.grid(**grid_opts)
    sf.grid_columnconfigure(0, weight=1)
    return sf


def segmented_button(
    parent: ctk.CTkFrame, *, font: ctk.CTkFont, **kwargs,
) -> ctk.CTkSegmentedButton:
    """Segmented button with consistent theme styling."""
    return ctk.CTkSegmentedButton(
        parent, font=font,
        selected_color=COLORS["accent"],
        selected_hover_color=COLORS["accent_hover"],
        height=26, corner_radius=6,
        **kwargs,
    )
