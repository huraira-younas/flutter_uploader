"""Single source of truth for all GUI theme tokens.

Supports multiple themes.  Change the active theme by calling
``set_theme("theme_name")`` **before** any widget is created, or edit
``_DEFAULT_THEME`` below.

All consumers keep using the same top-level names (``COLORS``, ``RADIUS``,
``PAD``, ``CODE_BG``, ``CODE_BORDER``, ``HEADING_COLORS``) — they are
module-level dicts/values that update in-place on theme switch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import customtkinter as ctk

ctk.set_default_color_theme("blue")
ctk.set_appearance_mode("Dark")

# ── Theme dataclass ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Theme:
    name: str
    colors: dict[str, str]
    radius: dict[str, int] = field(default_factory=lambda: {"card": 12, "input": 8, "btn": 10})
    pad: dict[str, int] = field(default_factory=lambda: {"sm": 8, "md": 15, "lg": 20})

    @property
    def code_bg(self) -> str:
        return self.colors["console_inner"]

    @property
    def code_border(self) -> str:
        return self.colors["console_border"]

    @property
    def heading_colors(self) -> dict[int, str]:
        return {
            1: self.colors["accent"],
            2: self.colors["section"],
            3: self.colors["accent"],
        }

    _registry: ClassVar[dict[str, "Theme"]] = {}

    def __init_subclass__(cls, **kw: object) -> None:
        super().__init_subclass__(**kw)

    def __post_init__(self) -> None:
        Theme._registry[self.name] = self


# ── Theme presets ─────────────────────────────────────────────────────────────

Theme(
    name="catppuccin_mocha",
    colors={
        "console_border": "#313244",
        "console_inner": "#11111b",
        "accent_hover": "#b4befe",
        "danger_hover": "#f38ba8",
        "card_border": "#313244",
        "console_bg": "#181825",
        "text_dim": "#6c7086",
        "disabled": "#1e1e2e",
        "card_bg": "#1e1e2e",
        "section": "#a6adc8",
        "success": "#a6e3a1",
        "accent": "#89b4fa",
        "danger": "#f38ba8",
        "error": "#f38ba8",
        "hover": "#313244",
        "muted": "#7f849c",
        "text": "#cdd6f4",
        "warn": "#f9e2af",
        "cmd": "#89dceb",
        "bg": "#1e1e2e",
    },
)

Theme(
    name="dracula",
    colors={
        "console_border": "#44475a",
        "console_inner": "#191a21",
        "accent_hover": "#bd93f9",
        "danger_hover": "#ff6e6e",
        "card_border": "#44475a",
        "console_bg": "#21222c",
        "text_dim": "#6272a4",
        "disabled": "#282a36",
        "card_bg": "#282a36",
        "section": "#f8f8f2",
        "success": "#50fa7b",
        "accent": "#bd93f9",
        "danger": "#ff5555",
        "error": "#ff5555",
        "hover": "#44475a",
        "muted": "#6272a4",
        "text": "#f8f8f2",
        "warn": "#f1fa8c",
        "cmd": "#8be9fd",
        "bg": "#282a36",
    },
)

Theme(
    name="tokyo_night",
    colors={
        "console_border": "#292e42",
        "console_inner": "#16161e",
        "accent_hover": "#89ddff",
        "danger_hover": "#ff7a93",
        "card_border": "#292e42",
        "console_bg": "#1a1b26",
        "text_dim": "#565f89",
        "disabled": "#1a1b26",
        "card_bg": "#1a1b26",
        "section": "#a9b1d6",
        "success": "#9ece6a",
        "accent": "#7aa2f7",
        "danger": "#f7768e",
        "error": "#f7768e",
        "hover": "#292e42",
        "muted": "#565f89",
        "text": "#c0caf5",
        "warn": "#e0af68",
        "cmd": "#7dcfff",
        "bg": "#1a1b26",
    },
)

Theme(
    name="gruvbox",
    colors={
        "console_border": "#3c3836",
        "console_inner": "#1d2021",
        "accent_hover": "#83a598",
        "danger_hover": "#fb4934",
        "card_border": "#3c3836",
        "console_bg": "#1d2021",
        "text_dim": "#665c54",
        "disabled": "#282828",
        "card_bg": "#282828",
        "section": "#d5c4a1",
        "success": "#b8bb26",
        "accent": "#83a598",
        "danger": "#cc241d",
        "error": "#fb4934",
        "hover": "#3c3836",
        "muted": "#928374",
        "text": "#ebdbb2",
        "warn": "#fabd2f",
        "cmd": "#8ec07c",
        "bg": "#282828",
    },
)

Theme(
    name="nord",
    colors={
        "console_border": "#3b4252",
        "console_inner": "#242933",
        "accent_hover": "#88c0d0",
        "danger_hover": "#d08770",
        "card_border": "#3b4252",
        "console_bg": "#2e3440",
        "text_dim": "#616e88",
        "disabled": "#2e3440",
        "card_bg": "#3b4252",
        "section": "#e5e9f0",
        "success": "#a3be8c",
        "accent": "#81a1c1",
        "danger": "#bf616a",
        "error": "#bf616a",
        "hover": "#434c5e",
        "muted": "#7b88a1",
        "text": "#eceff4",
        "warn": "#ebcb8b",
        "cmd": "#88c0d0",
        "bg": "#2e3440",
    },
)

Theme(
    name="one_dark",
    colors={
        "console_border": "#3e4452",
        "console_inner": "#1b1d23",
        "accent_hover": "#61afef",
        "danger_hover": "#e06c75",
        "card_border": "#3e4452",
        "console_bg": "#21252b",
        "text_dim": "#5c6370",
        "disabled": "#21252b",
        "card_bg": "#21252b",
        "section": "#abb2bf",
        "success": "#98c379",
        "accent": "#61afef",
        "danger": "#e06c75",
        "error": "#e06c75",
        "hover": "#3e4452",
        "muted": "#5c6370",
        "text": "#abb2bf",
        "warn": "#e5c07b",
        "cmd": "#56b6c2",
        "bg": "#282c34",
    },
)

Theme(
    name="solarized_dark",
    colors={
        "console_border": "#073642",
        "console_inner": "#00212b",
        "accent_hover": "#268bd2",
        "danger_hover": "#dc322f",
        "card_border": "#073642",
        "console_bg": "#002b36",
        "text_dim": "#586e75",
        "disabled": "#002b36",
        "card_bg": "#073642",
        "section": "#93a1a1",
        "success": "#859900",
        "accent": "#268bd2",
        "danger": "#dc322f",
        "error": "#dc322f",
        "hover": "#073642",
        "muted": "#657b83",
        "text": "#fdf6e3",
        "warn": "#b58900",
        "cmd": "#2aa198",
        "bg": "#002b36",
    },
)

# ── Active theme + public API ─────────────────────────────────────────────────

_DEFAULT_THEME = "one_dark"

_active: Theme = Theme._registry[_DEFAULT_THEME]


def _build_colors(theme: Theme) -> dict[str, str]:
    """Return colors dict with synthetic code_bg / code_border keys."""
    merged = dict(theme.colors)
    merged.setdefault("code_bg", theme.code_bg)
    merged.setdefault("code_border", theme.code_border)
    return merged


COLORS: dict[str, str] = _build_colors(_active)
RADIUS: dict[str, int] = dict(_active.radius)
PAD: dict[str, int] = dict(_active.pad)
HEADING_COLORS: dict[int, str] = dict(_active.heading_colors)

# Keep legacy names for any external scripts; they mirror COLORS values.
CODE_BG: str = COLORS["code_bg"]
CODE_BORDER: str = COLORS["code_border"]


def set_theme(name: str) -> None:
    """Switch the active theme.  Call before building the UI."""
    global _active, CODE_BG, CODE_BORDER
    if name not in Theme._registry:
        available = ", ".join(sorted(Theme._registry))
        raise ValueError(f"Unknown theme {name!r}. Available: {available}")

    _active = Theme._registry[name]
    COLORS.clear()
    COLORS.update(_build_colors(_active))
    RADIUS.clear()
    RADIUS.update(_active.radius)
    PAD.clear()
    PAD.update(_active.pad)
    HEADING_COLORS.clear()
    HEADING_COLORS.update(_active.heading_colors)
    CODE_BG = COLORS["code_bg"]
    CODE_BORDER = COLORS["code_border"]


def get_theme() -> str:
    """Return the name of the active theme."""
    return _active.name


def available_themes() -> list[str]:
    """Return sorted list of registered theme names."""
    return sorted(Theme._registry)
