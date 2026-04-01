"""Config tab sections — one module per panel (single responsibility)."""

from __future__ import annotations

from collections.abc import Callable
import customtkinter as ctk

from core.config_store import (
    PIPELINE_SECTION_TO_CONFIG_SECTION,
    deep_merge,
    get_app_config,
    resolved_flutter_project_root_string,
    save_config,
)
from core.prerequisites import flutter_project_prereq_status
from core.constants import set_flutter_project_root
from gui.sections.contracts import ConfigPanelHost

from . import android_section, app_info, common_section, distribution_section, ios_section, post_build_section, post_git, pre_git
from . import widgets as W


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
    ok_flutter, flutter_msg = flutter_project_prereq_status()
    if not ok_flutter:
        top = W.build_card(scroll, row)
        W.build_prereq_banner(top, row=0, message=flutter_msg, fonts=app._fonts)
        row += 1
    row = app_info.mount(app, scroll, row)
    for _, mount_fn in _SECTION_MOUNTS:
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
    dist_list = parts.pop("distribution", None)
    merged = deep_merge(get_app_config(), parts)
    if dist_list is not None:
        env_block = merged.get("env")
        if not isinstance(env_block, dict):
            env_block = {}
        merged["env"] = {**env_block, "DISTRIBUTION": dist_list}
    return merged


def persist_gui_config(app: ConfigPanelHost) -> None:
    save_config(collect_gui_config(app))
    set_flutter_project_root(resolved_flutter_project_root_string())
