"""Single source of truth for all GUI theme tokens."""

import customtkinter as ctk

ctk.set_default_color_theme("blue")
ctk.set_appearance_mode("Dark")

COLORS: dict[str, str] = {
    "console_border": "#1e293b",
    "console_inner": "#010410",
    "accent_hover": "#7dd3fc",
    "danger_hover": "#f87171",
    "card_border": "#1e293b",
    "console_bg": "#020617",
    "text_dim": "#475569",
    "disabled": "#0f172a",
    "card_bg": "#0f172a",
    "section": "#94a3b8",
    "success": "#34d399",
    "accent": "#38bdf8",
    "danger": "#ef4444",
    "error": "#f87171",
    "hover": "#1e293b",
    "muted": "#64748b",
    "text": "#cbd5e1",
    "warn": "#fbbf24",
    "cmd": "#38bdf8",
    "bg": "#020617",
}

RADIUS: dict[str, int] = {"card": 12, "input": 8, "btn": 10}
PAD: dict[str, int] = {"sm": 8, "md": 15, "lg": 20}

CODE_BG = "#010410"
CODE_BORDER = "#1e293b"
HEADING_COLORS: dict[int, str] = {
    1: COLORS["accent"],
    2: COLORS["section"],
    3: COLORS["accent"],
}
