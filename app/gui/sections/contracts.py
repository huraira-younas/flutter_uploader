"""Typed interfaces shared by config section modules."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

import customtkinter as ctk


class ConfigPanelHost(Protocol):
    _commit_msg_pre: ctk.StringVar | None
    _commit_msg_release: ctk.StringVar | None
    _fonts: dict[str, ctk.CTkFont]
    _gui_config_serializers: dict[str, Callable[[], Any]]
    _power_mode: ctk.StringVar | None
    _pub_mode: ctk.StringVar | None
    _quit_after_power: ctk.BooleanVar | None
    _section_bool_vars: dict[str, list[ctk.BooleanVar]]
    _section_widgets: dict[str, list[Any]]
    _show_ios: bool
    _steps_disabled_by_prereq: set[str]
    build_var: ctk.StringVar | None
    recipients_var: ctk.StringVar | None
    section_enabled_vars: dict[str, ctk.BooleanVar]
    step_progress_bars: dict[str, ctk.CTkProgressBar]
    step_status_labels: dict[str, ctk.CTkLabel]
    step_switches: dict[str, ctk.CTkSwitch]
    step_vars: dict[str, ctk.BooleanVar]
    version_var: ctk.StringVar | None

    def _on_section_enabled_changed(self, section_key: str) -> None: ...
    def _register_section_bool_var(self, section_key: str, var: ctk.BooleanVar) -> None: ...
    def _track(self, widget: Any) -> Any: ...
    def _track_section(self, section_key: str, widget: Any) -> Any: ...
    def rebuild_config_panel(self) -> None: ...
