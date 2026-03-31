"""Pipeline step ordering, ``PipelineConfig``, validation (GUI + CLI)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.constants import (
    COMMON_STEPS, GIT_PRE_STEPS, ANDROID_STEPS, IOS_STEPS,
    GIT_POST_STEPS, POST_STEPS,
    StepDef,
)


_SECTION_DEFS: tuple[tuple[str | None, list[StepDef]], ...] = (
    (None,      COMMON_STEPS),
    ("git",     GIT_PRE_STEPS),
    ("android", ANDROID_STEPS),
    ("ios",     IOS_STEPS),
    ("git",     GIT_POST_STEPS),
    ("post",    POST_STEPS),
)

ALL_STEP_DEFS: dict[str, StepDef] = {
    s[0]: s for _, steps in _SECTION_DEFS for s in steps
}

STEP_TO_SECTION: dict[str, str] = {
    s[0]: section
    for section, steps in _SECTION_DEFS
    if section is not None
    for s in steps
}

VALID_BUILD_MODES: frozenset[str] = frozenset(("flutter", "release", "patch"))
VALID_POWER_MODES: frozenset[str] = frozenset(("shutdown", "sleep"))
VALID_STEP_KEYS: frozenset[str] = frozenset(ALL_STEP_DEFS)


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    commit_message: str = "pre-release cleanup"
    android_build_mode: str = "flutter"
    ios_build_mode: str = "flutter"
    power_mode: str = "Shutdown"
    quit_after_power: bool = False
    version: str = "1.0.0"
    build: str = "1"

    enabled_steps: frozenset[str] | None = None
    recipients: str | None = None

    android_enabled: bool = True
    pub_upgrade: bool = False
    post_enabled: bool = True
    ios_enabled: bool = True
    git_enabled: bool = True

    def run_kwargs(self) -> dict:
        return {
            "android_build_mode": self.android_build_mode,
            "quit_after_power": self.quit_after_power,
            "drive_email_link_to": self.recipients,
            "ios_build_mode": self.ios_build_mode,
            "commit_message": self.commit_message,
            "pub_upgrade": self.pub_upgrade,
            "power_mode": self.power_mode,
            "version": self.version,
            "build": self.build,
        }

    def platforms_label(self) -> str:
        parts: list[str] = []
        if self.android_enabled:
            parts.append("Android")
        if self.ios_enabled:
            parts.append("iOS")
        return " + ".join(parts) if parts else "Common only"


def ordered_steps(cfg: PipelineConfig, *, include_ios: bool = False) -> list[StepDef]:
    active = {
        "git":     cfg.git_enabled,
        "android": cfg.android_enabled,
        "ios":     include_ios and cfg.ios_enabled,
        "post":    cfg.post_enabled,
    }
    return [
        s
        for section, steps in _SECTION_DEFS
        if section is None or active.get(section, False)
        for s in steps
    ]


def step_enabled_filter(cfg: PipelineConfig) -> Callable[[str], bool]:
    appstore_allowed = cfg.ios_build_mode != "patch"

    if cfg.enabled_steps is None:
        return lambda key: appstore_allowed or key != "appstore_upload"

    selected = cfg.enabled_steps
    section_active = {
        "git":     cfg.git_enabled,
        "android": cfg.android_enabled,
        "ios":     cfg.ios_enabled,
        "post":    cfg.post_enabled,
    }

    def _check(key: str) -> bool:
        if not appstore_allowed and key == "appstore_upload":
            return False
        if key not in selected:
            return False
        section = STEP_TO_SECTION.get(key)
        return section is None or section_active.get(section, True)

    return _check


def validate_step_keys(keys: list[str]) -> list[str]:
    return [k for k in keys if k not in VALID_STEP_KEYS]


def validate_build_mode(mode: str, label: str) -> str:
    normalized = mode.lower()
    if normalized not in VALID_BUILD_MODES:
        raise ValueError(
            f"Invalid {label} mode '{mode}'. "
            f"Choose from: {', '.join(sorted(VALID_BUILD_MODES))}"
        )
    return normalized


def validate_power_mode(mode: str) -> str:
    normalized = mode.lower()
    if normalized not in VALID_POWER_MODES:
        raise ValueError(
            f"Invalid power mode '{mode}'. "
            f"Choose from: {', '.join(sorted(VALID_POWER_MODES))}"
        )
    return normalized.capitalize()


def step_display_name(key: str) -> str:
    """Human-readable label for a step key."""
    sd = ALL_STEP_DEFS.get(key)
    return sd[1] if sd else key


def list_steps() -> list[tuple[str, str, str | None]]:
    return [
        (s[0], s[1], STEP_TO_SECTION.get(s[0]))
        for _, steps in _SECTION_DEFS
        for s in steps
    ]
