"""Settings panel — theme picker with color-swatch previews and instant apply."""

from __future__ import annotations

from tkinter import filedialog
import sys
import os

import customtkinter as ctk

from core.config_store import (
    distribution_recipients_from_config,
    logs_recipients_from_config,
    parse_recipients,
    get_app_config,
    get_section,
    save_config,
)
from core.constants import set_flutter_project_root
from gui.widgets import card, scrollable_frame, section_label
from gui.theme import (
    available_themes, get_theme, set_theme,
    COLORS, RADIUS, PAD, Theme,
)

_SWATCH_KEYS = ("bg", "card_bg", "accent", "success", "danger", "warn", "text", "muted")


def _display_name(name: str) -> str:
    return name.replace("_", " ").title()


def load_saved_theme() -> str | None:
    """Return the saved theme name from config, or ``None``."""
    try:
        theme = get_section("app_info").get("theme")
    except Exception:
        return None
    return theme if isinstance(theme, str) and theme.strip() else None


def _save_theme(name: str) -> None:
    save_config(
        {
            **get_app_config(),
            "app_info": {**get_section("app_info"), "theme": name},
        }
    )


class SettingsPanel(ctk.CTkFrame):
    """Settings: environment (paths, Drive, email) and theme picker."""

    _SWATCH_SIZE = 22
    # Tight vertical rhythm; label+entry share one row — must top-align (see _row).
    _ENV_ROW_PAD = (0, 4)

    def __init__(self, parent: ctk.CTkFrame, fonts: dict, app: ctk.CTk):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._fonts = fonts
        self._app = app
        self._build()

    def _build(self) -> None:
        scroll = scrollable_frame(self, row=0, column=0, sticky="nsew")

        env_outer = card(scroll, row=0, column=0, sticky="ew", pady=(0, 12))
        # Wide enough label column so long labels don’t wrap into sky-tall rows (avoids centered entry gap).
        env_outer.grid_columnconfigure(0, minsize=248, weight=0)
        env_outer.grid_columnconfigure(1, minsize=200, weight=1)
        env_outer.grid_columnconfigure(2, weight=0)

        env_header = ctk.CTkFrame(env_outer, fg_color="transparent")
        env_header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=PAD["lg"], pady=(PAD["md"], 4))
        env_header.grid_columnconfigure(1, weight=1)
        section_label(env_header, "Environment", self._fonts["section"]).grid(row=0, column=0, sticky="w")

        self._env_hint = ctk.CTkLabel(
            env_header, text="", font=self._fonts["body_sm"],
            text_color=COLORS["success"],
        )
        self._env_hint.grid(row=0, column=1, sticky="e", padx=(PAD["sm"], 0))

        env = get_section("env")
        flutter_root = str(env.get("FLUTTER_PROJECT_ROOT") or "").strip()

        self._env_vars: dict[str, ctk.StringVar] = {
            "FLUTTER_PROJECT_ROOT": ctk.StringVar(value=flutter_root),
            "GOOGLE_DRIVE_CREDENTIALS_JSON": ctk.StringVar(value=str(env.get("GOOGLE_DRIVE_CREDENTIALS_JSON") or "")),
            "GOOGLE_DRIVE_TOKEN_JSON": ctk.StringVar(value=str(env.get("GOOGLE_DRIVE_TOKEN_JSON") or "")),
            "GOOGLE_DRIVE_FOLDER_ID": ctk.StringVar(value=str(env.get("GOOGLE_DRIVE_FOLDER_ID") or "")),
            "APP_STORE_ISSUER_ID": ctk.StringVar(value=str(env.get("APP_STORE_ISSUER_ID") or "")),
            "APP_STORE_API_KEY": ctk.StringVar(value=str(env.get("APP_STORE_API_KEY") or "")),
            "GMAIL_USER": ctk.StringVar(value=str(env.get("GMAIL_USER") or "")),
            "GMAIL_APP_PASSWORD": ctk.StringVar(value=str(env.get("GMAIL_APP_PASSWORD") or "")),
        }

        def _list_to_csv(block: object) -> str:
            if not isinstance(block, list):
                return ""
            return ", ".join(str(x).strip() for x in block if str(x).strip())

        self._logs_distribution_var = ctk.StringVar(value=_list_to_csv(logs_recipients_from_config()))
        self._distribution_var = ctk.StringVar(value=_list_to_csv(distribution_recipients_from_config()))

        def _browse_file(key: str, *, title: str) -> None:
            picked = filedialog.askopenfilename(title=title)
            if picked:
                self._env_vars[key].set(picked)

        def _browse_dir(key: str) -> None:
            picked = filedialog.askdirectory(title="Select Flutter project (contains pubspec.yaml)")
            if picked:
                self._env_vars[key].set(picked)

        def _apply_env_to_process(values: dict[str, str]) -> None:
            for k, v in values.items():
                if k == "FLUTTER_PROJECT_ROOT":
                    continue
                raw = str(v).strip()
                if raw:
                    os.environ[k] = raw
                else:
                    os.environ.pop(k, None)

        def _csv_to_email_list(raw: str) -> list[str]:
            parts = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
            return parse_recipients(parts)

        def _save_env() -> None:
            patch = {k: self._env_vars[k].get().strip() for k in self._env_vars}
            patch["LOGS_DISTRIBUTION"] = _csv_to_email_list(self._logs_distribution_var.get())
            patch["DISTRIBUTION"] = _csv_to_email_list(self._distribution_var.get())
            merged = {**get_app_config(), "env": {**get_section("env"), **patch}}
            save_config(merged)
            _apply_env_to_process(patch)
            set_flutter_project_root(patch.get("FLUTTER_PROJECT_ROOT", ""))
            self._app.rebuild_config_panel()
            self._env_hint.configure(text="Saved")
            self._app.after(1500, lambda: self._env_hint.configure(text=""))

        er = 1

        def _subsection(title: str) -> None:
            nonlocal er
            ctk.CTkLabel(
                env_outer, text=title, font=self._fonts["body_sm"],
                text_color=COLORS["muted"],
            ).grid(row=er, column=0, columnspan=3, sticky="w", padx=PAD["lg"], pady=(10, 4))
            er += 1

        def _row(label: str, key: str, *, is_secret: bool = False, browse: str | None = None) -> None:
            nonlocal er
            ctk.CTkLabel(
                env_outer,
                text=label,
                font=self._fonts["body_sm"],
                anchor="w",
                justify="left",
            ).grid(
                row=er, column=0, padx=(PAD["lg"], PAD["sm"]), pady=self._ENV_ROW_PAD, sticky="nw",
            )
            entry = ctk.CTkEntry(
                env_outer,
                textvariable=self._env_vars[key],
                corner_radius=RADIUS["input"],
                border_width=1,
                height=28,
                show="•" if is_secret else None,
            )
            # sticky=new: keep entry top-aligned if label wraps to multiple lines (ew alone centers vertically).
            entry.grid(row=er, column=1, padx=(0, PAD["sm"]), pady=self._ENV_ROW_PAD, sticky="new")
            if browse == "file":
                ctk.CTkButton(
                    env_outer, text="Browse", width=88, corner_radius=RADIUS["btn"],
                    command=lambda k=key, t=label: _browse_file(k, title=t),
                ).grid(row=er, column=2, padx=(0, PAD["lg"]), pady=self._ENV_ROW_PAD, sticky="ne")
            elif browse == "dir":
                ctk.CTkButton(
                    env_outer, text="Browse", width=88, corner_radius=RADIUS["btn"],
                    command=lambda: _browse_dir("FLUTTER_PROJECT_ROOT"),
                ).grid(row=er, column=2, padx=(0, PAD["lg"]), pady=self._ENV_ROW_PAD, sticky="ne")
            else:
                ctk.CTkFrame(env_outer, fg_color="transparent", width=88, height=1).grid(
                    row=er, column=2, padx=(0, PAD["lg"]), pady=self._ENV_ROW_PAD, sticky="nw",
                )
            er += 1

        def _row_var(label: str, var: ctk.StringVar, *, is_secret: bool = False) -> None:
            nonlocal er
            ctk.CTkLabel(
                env_outer,
                text=label,
                font=self._fonts["body_sm"],
                anchor="w",
                justify="left",
            ).grid(
                row=er, column=0, padx=(PAD["lg"], PAD["sm"]), pady=self._ENV_ROW_PAD, sticky="nw",
            )
            entry = ctk.CTkEntry(
                env_outer,
                textvariable=var,
                corner_radius=RADIUS["input"],
                border_width=1,
                height=28,
                show="•" if is_secret else None,
            )
            # Same grid as ``_row`` without Browse: entry only in column 1, spacer column 2.
            entry.grid(row=er, column=1, padx=(0, PAD["sm"]), pady=self._ENV_ROW_PAD, sticky="new")
            ctk.CTkFrame(env_outer, fg_color="transparent", width=88, height=1).grid(
                row=er, column=2, padx=(0, PAD["lg"]), pady=self._ENV_ROW_PAD, sticky="nw",
            )
            er += 1

        _subsection("Project")
        _row("Flutter project root", "FLUTTER_PROJECT_ROOT", browse="dir")
        _subsection("Google Drive")
        _row("OAuth client JSON", "GOOGLE_DRIVE_CREDENTIALS_JSON", browse="file")
        _row("Token JSON (optional)", "GOOGLE_DRIVE_TOKEN_JSON", browse="file")
        _row("Parent folder ID (optional)", "GOOGLE_DRIVE_FOLDER_ID")
        _subsection("iOS / App Store")
        _row("Issuer ID", "APP_STORE_ISSUER_ID")
        _row("API Key ID", "APP_STORE_API_KEY")
        _subsection("Email")
        _row("Gmail address", "GMAIL_USER")
        _row("Gmail app password", "GMAIL_APP_PASSWORD", is_secret=True)
        _subsection("Logs | Distribution")
        _row_var("Logs (build reports, comma-separated)", self._logs_distribution_var)
        _row_var("Distribution (Drive links, comma-separated)", self._distribution_var)

        ctk.CTkButton(
            env_outer,
            text="Save environment",
            corner_radius=RADIUS["btn"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=_save_env,
        ).grid(row=er, column=0, columnspan=3, sticky="e", padx=PAD["lg"], pady=(8, PAD["md"]))

        outer = card(scroll, row=1, column=0, sticky="ew", pady=(0, 12))
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
