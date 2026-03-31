"""Settings panel — theme picker with color-swatch previews and instant apply."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import os

import customtkinter as ctk

from gui.widgets import card, scrollable_frame, section_label
from gui.theme import (
    available_themes, get_theme, set_theme,
    COLORS, RADIUS, PAD, Theme,
)

_PREFS_PATH = Path(__file__).resolve().parent.parent / ".gui_prefs.json"

_SWATCH_KEYS = ("bg", "card_bg", "accent", "success", "danger", "warn", "text", "muted")


def _display_name(name: str) -> str:
    return name.replace("_", " ").title()


def load_saved_theme() -> str | None:
    """Return the saved theme name from disk, or ``None``."""
    try:
        data = json.loads(_PREFS_PATH.read_text(encoding="utf-8"))
        return data.get("theme")
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def _save_theme(name: str) -> None:
    prefs: dict = {}
    try:
        prefs = json.loads(_PREFS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    prefs["theme"] = name
    _PREFS_PATH.write_text(json.dumps(prefs, indent=2), encoding="utf-8")


class SettingsPanel(ctk.CTkFrame):
    """Theme selection grid with live color swatch previews."""

    _SWATCH_SIZE = 22

    def __init__(self, parent: ctk.CTkFrame, fonts: dict, app: ctk.CTk):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._fonts = fonts
        self._app = app
        self._build()

    def _build(self) -> None:
        scroll = scrollable_frame(self, row=0, column=0, sticky="nsew")

        outer = card(scroll, row=0, column=0, sticky="ew", pady=(0, 12))
        outer.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD["lg"], pady=(PAD["md"], PAD["sm"]))
        header.grid_columnconfigure(1, weight=1)
        section_label(header, "Theme", self._fonts["section"]).grid(row=0, column=0, sticky="w")

        self._hint = ctk.CTkLabel(
            header, text="", font=self._fonts["body_sm"],
            text_color=COLORS["success"],
        )
        self._hint.grid(row=0, column=1, sticky="e", padx=(PAD["sm"], 0))

        grid = ctk.CTkFrame(outer, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="ew", padx=PAD["sm"], pady=(0, PAD["md"]))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_columnconfigure(2, weight=1)

        current = get_theme()
        themes = available_themes()
        for idx, name in enumerate(themes):
            r, c = divmod(idx, 3)
            self._theme_card(grid, name, is_active=(name == current), grid_row=r, grid_col=c)

    def _theme_card(
        self, parent: ctk.CTkFrame, name: str, *,
        is_active: bool, grid_row: int, grid_col: int,
    ) -> None:
        theme = Theme._registry[name]
        colors = theme.colors
        display = _display_name(name)

        border_color = COLORS["accent"] if is_active else colors.get("card_border", "#333")
        border_w = 2 if is_active else 1

        frame = ctk.CTkFrame(
            parent,
            fg_color=colors["card_bg"],
            border_color=border_color,
            border_width=border_w,
            corner_radius=RADIUS["card"],
        )
        frame.grid(
            row=grid_row, column=grid_col, sticky="nsew",
            padx=PAD["sm"], pady=PAD["sm"],
        )
        frame.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(frame, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_row, text=display,
            font=self._fonts["body"] if not is_active else self._fonts["section"],
            text_color=colors["accent"] if is_active else colors["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        if is_active:
            ctk.CTkLabel(
                title_row, text="Active",
                font=self._fonts["body_sm"],
                text_color=colors.get("success", COLORS["success"]),
                anchor="e",
            ).grid(row=0, column=1, sticky="e")

        swatch_row = ctk.CTkFrame(frame, fg_color="transparent")
        swatch_row.grid(row=1, column=0, sticky="w", padx=12, pady=(2, 4))

        for i, key in enumerate(_SWATCH_KEYS):
            color = colors.get(key, "#555")
            swatch = ctk.CTkFrame(
                swatch_row,
                fg_color=color,
                width=self._SWATCH_SIZE,
                height=self._SWATCH_SIZE,
                corner_radius=4,
                border_width=1,
                border_color=colors.get("card_border", "#444"),
            )
            swatch.grid(row=0, column=i, padx=(0, 3))
            swatch.grid_propagate(False)

        preview_bar = ctk.CTkFrame(
            frame, fg_color=colors["bg"],
            corner_radius=6, height=28,
        )
        preview_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 4))
        preview_bar.grid_propagate(False)
        preview_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_bar,
            text=f"  Sample text in {display}",
            font=self._fonts["body_sm"],
            text_color=colors["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=6)

        if not is_active:
            btn = ctk.CTkButton(
                frame, text="Apply",
                font=self._fonts["body_sm"],
                fg_color=colors.get("accent", COLORS["accent"]),
                hover_color=colors.get("accent_hover", COLORS["accent_hover"]),
                text_color=colors.get("bg", "#000"),
                corner_radius=6, height=28, width=70,
                command=lambda n=name: self._apply_theme(n),
            )
            btn.grid(row=3, column=0, sticky="e", padx=12, pady=(2, 10))
        else:
            ctk.CTkFrame(frame, fg_color="transparent", height=10).grid(row=3, column=0)

    def _apply_theme(self, name: str) -> None:
        _save_theme(name)
        set_theme(name)
        self._hint.configure(
            text=f"Restarting with {_display_name(name)}...",
            text_color=COLORS["accent"],
        )
        self._app.after(400, self._restart)

    @staticmethod
    def _restart() -> None:
        os.execv(sys.executable, [sys.executable] + sys.argv)
