"""Pipeline step ordering, ``PipelineConfig``, validation (GUI + CLI)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypedDict

from core.constants import (
    DEFAULT_COMMIT_MESSAGE_RELEASE,
    DEFAULT_COMMIT_MESSAGE_PRE,
)
from core.steps import (
    GIT_POST_STEPS, COMMIT_PRE_STEPS, COMMON_STEPS, GIT_SYNC_STEPS,
    ANDROID_STEPS, POST_STEPS, IOS_STEPS,
    StepDef,
)


# Execution order: pre-commit → clean/pub → pull → builds → release commit + push → post-build.
# ``git_post`` appears twice so pull runs before Android/iOS; release/push run after (same section flag).
_SECTION_DEFS: tuple[tuple[str, list[StepDef]], ...] = (
    ("git_pre", COMMIT_PRE_STEPS),
    ("common",  COMMON_STEPS),
    ("git_post", GIT_SYNC_STEPS),
    ("android", ANDROID_STEPS),
    ("ios", IOS_STEPS),
    ("git_post", GIT_POST_STEPS),
    ("post", POST_STEPS),
)

ALL_STEP_DEFS: dict[str, StepDef] = {
    s[0]: s for _, steps in _SECTION_DEFS for s in steps
}

STEP_TO_SECTION: dict[str, str] = {
    s[0]: section for section, steps in _SECTION_DEFS for s in steps
}

VALID_BUILD_MODES: frozenset[str] = frozenset(("flutter", "release", "patch"))
VALID_POWER_MODES: frozenset[str] = frozenset(("shutdown", "sleep"))
VALID_STEP_KEYS: frozenset[str] = frozenset(ALL_STEP_DEFS)


class RunSelectedArgs(TypedDict):
    commit_message_release: str
    android_build_mode: str
    drive_email_link_to: str | None
    quit_after_power: bool
    commit_message: str
    ios_build_mode: str
    pub_upgrade: bool
    power_mode: str
    version: str
    build: str


def _section_flags(cfg: PipelineConfig, *, ios_resolved: bool) -> dict[str, bool]:
    """Per-step gating uses ``ios_resolved`` = ``cfg.ios_enabled``; pipeline ordering uses
    ``include_ios and cfg.ios_enabled`` (pass that as *ios_resolved*)."""
    return {
        "common": cfg.common_enabled,
        "git_pre": cfg.git_pre_enabled,
        "git_post": cfg.git_post_enabled,
        "android": cfg.android_enabled,
        "ios": ios_resolved,
        "post": cfg.post_enabled,
    }


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    commit_message_pre: str = DEFAULT_COMMIT_MESSAGE_PRE
    commit_message_release: str = DEFAULT_COMMIT_MESSAGE_RELEASE
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
    git_pre_enabled: bool = True
    git_post_enabled: bool = True
    common_enabled: bool = True

    def run_kwargs(self) -> RunSelectedArgs:
        return {
            "commit_message_release": self.commit_message_release,
            "android_build_mode": self.android_build_mode,
            "drive_email_link_to": self.recipients,
            "quit_after_power": self.quit_after_power,
            "commit_message": self.commit_message_pre,
            "ios_build_mode": self.ios_build_mode,
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
    active = _section_flags(cfg, ios_resolved=include_ios and cfg.ios_enabled)
    return [
        s
        for section, steps in _SECTION_DEFS
        if active.get(section, False)
        for s in steps
    ]


def step_enabled_filter(cfg: PipelineConfig) -> Callable[[str], bool]:
    appstore_allowed = cfg.ios_build_mode != "patch"

    if cfg.enabled_steps is None:
        return lambda key: appstore_allowed or key != "appstore_upload"

    selected = cfg.enabled_steps
    section_active = _section_flags(cfg, ios_resolved=cfg.ios_enabled)

    def _check(key: str) -> bool:
        if not appstore_allowed and key == "appstore_upload":
            return False
        if key not in selected:
            return False
        section = STEP_TO_SECTION.get(key)
        return section is None or section_active.get(section, True)

    return _check


def build_pipeline_config(
    *,
    commit_message_release: str | None = None,
    commit_message_pre: str | None = None,
    android_build_mode: str = "flutter",
    quit_after_power: bool = False,
    git_post_enabled: bool = True,
    git_pre_enabled: bool = True,
    common_enabled: bool = True,
    android_enabled: bool = True,
    ios_build_mode: str = "flutter",
    enabled_steps: frozenset[str] | None = None,
    ios_enabled: bool = True,
    recipients: str | None = None,
    pub_upgrade: bool = False,
    power_mode: str = "Shutdown",
    post_enabled: bool = True,
    version: str = "1.0.0",
    build: str = "1",
) -> PipelineConfig:
    return PipelineConfig(
        commit_message_release=(commit_message_release or "").strip() or DEFAULT_COMMIT_MESSAGE_RELEASE,
        commit_message_pre=(commit_message_pre or "").strip() or DEFAULT_COMMIT_MESSAGE_PRE,
        android_build_mode=android_build_mode,
        quit_after_power=quit_after_power,
        git_post_enabled=git_post_enabled,
        git_pre_enabled=git_pre_enabled,
        common_enabled=common_enabled,
        android_enabled=android_enabled,
        ios_build_mode=ios_build_mode,
        enabled_steps=enabled_steps,
        ios_enabled=ios_enabled,
        recipients=recipients,
        pub_upgrade=pub_upgrade,
        power_mode=power_mode,
        post_enabled=post_enabled,
        version=version,
        build=build,
    )


def find_invalid_step_keys(keys: list[str]) -> list[str]:
    return [k for k in keys if k not in VALID_STEP_KEYS]


def parse_step_keys_csv(steps_arg: str) -> list[str]:
    return [k.strip() for k in steps_arg.split(",") if k.strip()]


def validate_step_keys(keys: list[str]) -> list[str]:
    """Backward-compatible alias for ``find_invalid_step_keys``."""
    return find_invalid_step_keys(keys)


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


def list_steps() -> list[tuple[str, str, str]]:
    return [
        (s[0], s[1], STEP_TO_SECTION[s[0]])
        for _, steps in _SECTION_DEFS
        for s in steps
    ]
