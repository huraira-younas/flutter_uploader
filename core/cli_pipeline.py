"""Build ``PipelineConfig`` for headless CLI using global ``config.json`` + argparse overrides."""

from __future__ import annotations

import argparse

from core.config_store import (
    android_build_mode_from_config,
    enabled_step_keys_from_config,
    ios_build_mode_from_config,
    pipeline_section_enabled,
    pub_upgrade_from_config,
    get_app_config,
)

from core.constants import DEFAULT_COMMIT_MESSAGE_RELEASE, DEFAULT_COMMIT_MESSAGE_PRE
from core.pipeline_config import (
    parse_step_keys_csv,
    build_pipeline_config,
    validate_build_mode,
    validate_power_mode,
    PipelineConfig,
)

from helpers.version import read_version


def _arg_set(args: argparse.Namespace, name: str) -> bool:
    return getattr(args, name, None) is not None


def resolve_cli_pipeline_config(args: argparse.Namespace, *, include_ios: bool) -> PipelineConfig:
    cfg_file = get_app_config()
    version, build_num = read_version()
    build_num = args.build or build_num
    version = args.version or version

    recipients = args.recipients
    if recipients is None:
        recipients = (cfg_file.get("distribution") or {}).get("recipients") or None
    if isinstance(recipients, str):
        recipients = recipients.strip() or None

    commit_pre = (
        args.commit_message
        if _arg_set(args, "commit_message")
        else (cfg_file.get("pre_git") or {}).get("commit_message", DEFAULT_COMMIT_MESSAGE_PRE)
    )
    commit_rel = (
        args.release_commit_message
        if _arg_set(args, "release_commit_message")
        else (cfg_file.get("post_git") or {}).get("commit_message", DEFAULT_COMMIT_MESSAGE_RELEASE)
    )

    pub_upgrade = (
        args.pub_mode == "pub-upgrade"
        if _arg_set(args, "pub_mode")
        else pub_upgrade_from_config()
    )

    android_mode = (
        validate_build_mode(args.android_mode, "android")
        if _arg_set(args, "android_mode")
        else validate_build_mode(android_build_mode_from_config(), "android")
    )
    ios_mode = (
        validate_build_mode(args.ios_mode, "ios")
        if _arg_set(args, "ios_mode")
        else validate_build_mode(ios_build_mode_from_config(), "ios")
    )

    power_raw = (
        args.power_mode
        if _arg_set(args, "power_mode")
        else str((cfg_file.get("post_build") or {}).get("power_mode", "shutdown")).lower()
    )
    power_mode = validate_power_mode(power_raw)

    quit_after = bool((cfg_file.get("post_build") or {}).get("quit_after_power", False))
    if args.quit_after_power:
        quit_after = True

    git_pre = pipeline_section_enabled("git_pre")
    git_post = pipeline_section_enabled("git_post")
    if args.git_on is not None:
        git_pre = git_post = bool(args.git_on)
    else:
        if args.pre_git_on is not None:
            git_pre = bool(args.pre_git_on)
        if args.post_git_on is not None:
            git_post = bool(args.post_git_on)

    common_on = pipeline_section_enabled("common")
    if args.common_on is not None:
        common_on = bool(args.common_on)

    android_on = pipeline_section_enabled("android")
    if args.android_on is not None:
        android_on = bool(args.android_on)

    ios_on = pipeline_section_enabled("ios", include_ios_default=include_ios)
    if args.ios_on is not None:
        ios_on = bool(args.ios_on)
    if not include_ios:
        ios_on = False

    post_on = pipeline_section_enabled("post")
    if args.post_on is not None:
        post_on = bool(args.post_on)

    enabled_steps = None
    if args.steps:
        keys = parse_step_keys_csv(args.steps)
        enabled_steps = frozenset(keys)
    else:
        enabled_steps = enabled_step_keys_from_config()

    return build_pipeline_config(
        commit_message_release=str(commit_rel),
        commit_message_pre=str(commit_pre),
        android_build_mode=android_mode,
        quit_after_power=quit_after,
        git_post_enabled=git_post,
        git_pre_enabled=git_pre,
        common_enabled=common_on,
        android_enabled=android_on,
        ios_build_mode=ios_mode,
        enabled_steps=enabled_steps,
        ios_enabled=ios_on,
        recipients=recipients,
        pub_upgrade=pub_upgrade,
        power_mode=power_mode,
        post_enabled=post_on,
        version=version,
        build=build_num,
    )
