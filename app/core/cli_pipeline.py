"""Build ``PipelineConfig`` for headless CLI using global ``config.json`` + argparse overrides."""

from __future__ import annotations

import argparse

from core.config_store import (
    distribution_recipients_csv_from_config,
    enabled_step_keys_from_config,
    pipeline_section_enabled,
    pub_upgrade_from_config,
    get_app_config,
)

from core.constants import DEFAULT_COMMIT_MESSAGE_RELEASE, DEFAULT_COMMIT_MESSAGE_PRE, DEFAULT_GIT_BRANCH
from core.pipeline_config import (
    build_pipeline_config,
    validate_power_mode,
    parse_step_keys_csv,
    PipelineConfig,
)

from helpers.version import read_version


def _arg_set(args: argparse.Namespace, name: str) -> bool:
    return getattr(args, name, None) is not None


def _cli_bool(base: bool, override: bool | None) -> bool:
    return base if override is None else bool(override)


def resolve_cli_pipeline_config(args: argparse.Namespace, *, include_ios: bool) -> PipelineConfig:
    cfg_file = get_app_config()

    version, build_num = read_version()
    build_num = args.build or build_num
    version = args.version or version

    recipients = args.recipients
    if recipients is None:
        recipients = distribution_recipients_csv_from_config()
    elif isinstance(recipients, str):
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

    git_branch = (
        args.branch
        if _arg_set(args, "branch")
        else cfg_file.get("git_branch", DEFAULT_GIT_BRANCH)
    )

    power_raw = (
        args.power_mode
        if _arg_set(args, "power_mode")
        else str((cfg_file.get("post_build") or {}).get("power_mode", "shutdown")).lower()
    )

    power_mode = validate_power_mode(power_raw)

    quit_after = bool((cfg_file.get("post_build") or {}).get("quit_after_power", False)) or bool(
        args.quit_after_power,
    )

    git_post = pipeline_section_enabled("git_post")
    git_pre = pipeline_section_enabled("git_pre")

    if args.git_on is not None:
        git_pre = git_post = bool(args.git_on)
    else:
        git_post = _cli_bool(git_post, args.post_git_on)
        git_pre = _cli_bool(git_pre, args.pre_git_on)

    android_on = _cli_bool(pipeline_section_enabled("android"), args.android_on)
    common_on = _cli_bool(pipeline_section_enabled("common"), args.common_on)
    
    ios_on = _cli_bool(
        pipeline_section_enabled("ios", include_ios_default=include_ios),
        args.ios_on,
    )
    if not include_ios:
        ios_on = False

    post_on = _cli_bool(pipeline_section_enabled("post"), args.post_on)
    dist_on = _cli_bool(pipeline_section_enabled("distribution"), args.distribution_on)

    enabled_steps = (
        frozenset(parse_step_keys_csv(args.steps))
        if args.steps
        else enabled_step_keys_from_config()
    )

    return build_pipeline_config(
        commit_message_release=str(commit_rel),
        commit_message_pre=str(commit_pre),
        git_post_enabled=git_post,
        quit_after_power=quit_after,
        git_pre_enabled=git_pre,
        android_enabled=android_on,
        common_enabled=common_on,
        enabled_steps=enabled_steps,
        post_enabled=post_on,
        ios_enabled=ios_on,
        pub_upgrade=pub_upgrade,
        power_mode=power_mode,
        recipients=recipients,
        version=version,
        build=build_num,
        git_branch=str(git_branch),
        distribution_enabled=dist_on,
    )
