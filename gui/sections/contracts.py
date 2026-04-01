"""Typed interfaces shared by config section modules."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

import customtkinter as ctk


class ConfigPanelHost(Protocol):
    _fonts: dict[str, ctk.CTkFont]
    _shorebird_ok: bool
    _show_ios: bool

    _gui_config_serializers: dict[str, Callable[[], dict[str, Any]]]
    _sb_mode_widgets: dict[str, ctk.CTkSegmentedButton]
    _sb_checkboxes: dict[str, ctk.CTkCheckBox]
    _sb_hint_labels: dict[str, ctk.CTkLabel]

    step_progress_bars: dict[str, ctk.CTkProgressBar]
    step_status_labels: dict[str, ctk.CTkLabel]
    step_switches: dict[str, ctk.CTkSwitch]
    step_vars: dict[str, ctk.BooleanVar]

    _shorebird_android: ctk.BooleanVar | None
    _commit_msg_release: ctk.StringVar | None
    _quit_after_power: ctk.BooleanVar | None
    _android_sb_mode: ctk.StringVar | None
    _shorebird_ios: ctk.BooleanVar | None
    _commit_msg_pre: ctk.StringVar | None
    recipients_var: ctk.StringVar | None
    _ios_sb_mode: ctk.StringVar | None
    _power_mode: ctk.StringVar | None
    version_var: ctk.StringVar | None
    build_var: ctk.StringVar | None
    _pub_mode: ctk.StringVar | None

    def _track(self, widget: Any) -> Any: ...
    def _on_shorebird_toggle(self, section_key: str, var: ctk.BooleanVar) -> None: ...
    def _on_shorebird_mode_changed(self, section_key: str) -> None: ...
