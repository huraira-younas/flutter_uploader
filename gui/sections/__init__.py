"""Config tab sections — one module per panel (single responsibility)."""

from __future__ import annotations

from collections.abc import Callable
import customtkinter as ctk

from core.config_store import (
    deep_merge,
    get_app_config,
    save_config,
    PIPELINE_SECTION_TO_CONFIG_SECTION,
)
from gui.sections.contracts import ConfigPanelHost
from . import android_section, app_info, common_section, distribution_section, ios_section, post_build_section, post_git, pre_git


_SECTION_MOUNTS: tuple[tuple[str, Callable[[ConfigPanelHost, ctk.CTkScrollableFrame, int], int]], ...] = (
    ("pre_git", pre_git.mount),
    ("common", common_section.mount),
    ("post_git", post_git.mount),
    ("android", android_section.mount),
    ("ios", ios_section.mount),
    ("post_build", post_build_section.mount),
)


def mount_config_panel(app: ConfigPanelHost, scroll: ctk.CTkScrollableFrame) -> None:
    app._gui_config_serializers.clear()
    row = 0
    row = app_info.mount(app, scroll, row)
    for section_key, mount_fn in _SECTION_MOUNTS:
        row = mount_fn(app, scroll, row)
    row = distribution_section.mount(app, scroll, row)


def collect_gui_config(app: ConfigPanelHost) -> dict:
    parts: dict[str, object] = {}
    for key, fn in app._gui_config_serializers.items():
        parts[key] = fn()
    for section_alias, section_var in app.section_enabled_vars.items():
        config_key = PIPELINE_SECTION_TO_CONFIG_SECTION.get(section_alias, section_alias)
        section_patch = parts.setdefault(config_key, {})
        section_patch["enabled"] = bool(section_var.get())
    return deep_merge(get_app_config(), parts)


def persist_gui_config(app: ConfigPanelHost) -> None:
    save_config(collect_gui_config(app))
