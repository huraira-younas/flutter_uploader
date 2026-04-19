from __future__ import annotations
from typing import Callable
import shutil
import os

from helpers.platform_utils import open_folder, shutdown_pc, sleep_pc
from helpers.drive_upload import upload_outputs_to_drive
from helpers.types import LogFn, StopCheckFn
from helpers.rename_artifacts import (
    copy_aabs_to_outputs,
    copy_apks_to_outputs,
    copy_ipas_to_outputs,
    clear_outputs,
)

from helpers.google_play_upload import run_google_play_upload as lib_google_play_upload
from helpers.app_metadata import extract_android_pkg_name

from helpers.shell import CommandRunner
from core.config_store import env_value
from core.project_state import (
    flutter_project_root,
    aab_dir,
    apk_dir,
    ipa_dir,
)

from core.constants import (
    OUTPUTS_DIR,
    POWER_DELAY,
)

from core.steps import StepDef


_CMD: CommandRunner | None = None


def _cmd() -> CommandRunner:
    global _CMD
    root = flutter_project_root()
    if _CMD is None or _CMD.project_root != root:
        _CMD = CommandRunner(project_root=root)
    return _CMD


def _log_noop(_: str) -> None:
    pass


def _git_add_and_commit(message: str, log: LogFn) -> bool:
    if not _cmd().run_project(["git", "add", "."], log):
        return False
    _cmd().run_project(["git", "commit", "-m", message], log)
    return True


def _remove_dir_if_exists(path: os.PathLike[str], log: LogFn, label: str) -> bool:
    dir_path = os.fspath(path)
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            log(f"\n>> Deleted {label} output dir: {dir_path}\n")
        except OSError as e:
            log(f"\n>> Failed to delete {label} dir: {e}\n")
            return False
    return True


def _run_project_cmd(
    cmd: list[str],
    log: LogFn,
    *,
    header: str,
    stop_check: StopCheckFn | None = None,
) -> bool:
    return _cmd().run_project(cmd, log, header=header, stop_check=stop_check)


def run_flutter_clean(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["flutter", "clean"], log, header="\n>> flutter clean\n", stop_check=stop_check,
    )


def run_flutter_pub_get(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["flutter", "pub", "get"], log, header="\n>> flutter pub get\n", stop_check=stop_check,
    )


def run_flutter_pub_upgrade(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["flutter", "pub", "upgrade", "--major-versions"], log,
        header="\n>> flutter pub upgrade --major-versions\n", stop_check=stop_check,
    )


def _run_git_commit(message: str, log: LogFn = _log_noop) -> bool:
    log(f'\n>> git add . && git commit -m "{message}"\n')
    _git_add_and_commit(message, log)
    return True


run_git_commit_pre = _run_git_commit
run_git_commit_release = _run_git_commit


def run_git_pull(branch: str = "master", log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["git", "pull", "origin", branch], log,
        header=f"\n>> git pull origin {branch}\n", stop_check=stop_check,
    )


def format_release_commit_message(template: str, version: str, build: str) -> str:
    """Apply ``{version}`` and ``{build}`` placeholders; if empty, use ``v{{version}} ({{build}})``."""
    t = (template or "").strip()
    if not t:
        return f"v{version} ({build})"
    try:
        return t.format(version=version, build=build)
    except (KeyError, ValueError, IndexError):
        return t


def run_git_push(branch: str = "master", log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["git", "push", "origin", branch], log,
        header=f"\n>> git push origin {branch}\n", stop_check=stop_check,
    )


def run_build_apk(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    apk_output_dir = apk_dir()
    if not _remove_dir_if_exists(apk_output_dir, log, "APK"):
        return False
    return _run_project_cmd(
        ["flutter", "build", "apk", "--release", "--split-per-abi"], log,
        header="\n>> flutter build apk --release --split-per-abi\n", stop_check=stop_check,
    )


def run_build_aab(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    bundle_dir = aab_dir()
    if not _remove_dir_if_exists(bundle_dir, log, "App Bundle"):
        return False
    return _run_project_cmd(
        ["flutter", "build", "appbundle", "--release"], log,
        header="\n>> flutter build appbundle --release\n", stop_check=stop_check,
    )


def run_pod_update(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    ios_dir = flutter_project_root() / "ios"
    if not ios_dir.exists():
        log("iOS directory not found. Skipping pod update.\n")
        return False
    if not _cmd().run_in(["pod", "deintegrate"], ios_dir, log, header="\n>> pod deintegrate\n", stop_check=stop_check):
        return False
    if not _cmd().run_in(["pod", "repo", "update"], ios_dir, log, header="\n>> pod repo update\n", stop_check=stop_check):
        return False
    return _cmd().run_in(["pod", "update"], ios_dir, log, header="\n>> pod update\n", stop_check=stop_check)


def run_build_ipa(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    ios_ipa_dir = ipa_dir()
    if not _remove_dir_if_exists(ios_ipa_dir, log, "IPA"):
        return False
    return _run_project_cmd(
        ["flutter", "build", "ipa", "--release"], log,
        header="\n>> flutter build ipa --release\n", stop_check=stop_check,
    )


def run_appstore_upload(
    version: str,
    build: str,
    stop_check: StopCheckFn | None = None,
    log: LogFn = _log_noop,
) -> bool:
    """Upload the first IPA found to AppStore Connect via xcrun altool."""
    issuer_id = env_value("APP_STORE_ISSUER_ID")
    api_key = env_value("APP_STORE_API_KEY")
    if (
        not issuer_id
        or not api_key
        or issuer_id.startswith("YOUR_")
        or api_key.startswith("YOUR_")
    ):
        log("AppStore Connect credentials not configured. Skipping upload.\n")
        return True

    ipa_files = sorted(ipa_dir().glob("*.ipa"))
    if not ipa_files:
        log("No IPA files found to upload.\n")
        return False

    ipa_path = ipa_files[0]
    return _cmd().run_project(
        [
            "xcrun", "altool", "--upload-app", "--type", "ios",
            "-f", str(ipa_path),
            "--apiKey", api_key,
            "--apiIssuer", issuer_id,
        ],
        log,
        header=f"\n>> Uploading {ipa_path.name} to AppStore Connect\n",
        stop_check=stop_check,
    )


def run_google_play_upload(
    version: str,
    build: str,
    track: str = "production",
    log: LogFn = _log_noop,
    stop_check: StopCheckFn | None = None,
) -> bool:
    """Auto-detect package name and upload AAB to Google Play."""
    project_root = flutter_project_root()
    packageName = env_value("GOOGLE_PLAY_PACKAGE_NAME") or extract_android_pkg_name(project_root)
    if not packageName:
        log("Google Play: Could not auto-detect Package Name from build.gradle and no override found. Skipping.\n")
        return False
    
    json_key_path_str = env_value("GOOGLE_PLAY_JSON_KEY")
    if not json_key_path_str:
        log("Google Play: GOOGLE_PLAY_JSON_KEY not set in Environment. Skipping.\n")
        return True
    
    # Use helper's path resolver if needed, or just standard path
    from helpers.drive_upload import _resolve_env_path
    json_key_path = _resolve_env_path(json_key_path_str)
    
    aab_files = sorted(aab_dir().glob("*.aab"))
    if not aab_files:
        log("Google Play: No AAB files found to upload.\n")
        return False
    
    aab_path = aab_files[0]
    return lib_google_play_upload(
        aab_path=aab_path,
        packageName=packageName,
        json_key_path=json_key_path,
        track=track,
        log=log,
        stop_check=stop_check,
    )


def run_open_outputs(log: LogFn) -> bool:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    log("\n>> Open outputs folder\n")
    return open_folder(OUTPUTS_DIR, log)


def _build_runners(
    version: str,
    build: str,
    recipients: str | None,
    stop_check: StopCheckFn | None,
    *,
    commit_message: str = "pre-release cleanup",
    commit_message_release: str = "v{version} ({build})",
    pub_upgrade: bool = False,
    power_mode: str = "Shutdown",
    git_branch: str = "master",
    google_play_track: str = "production",
) -> dict[str, Callable[[LogFn], bool]]:
    """Build step_key -> runner function mapping."""
    def with_stop(fn: Callable) -> Callable[[LogFn], bool]:
        return lambda log: fn(log, stop_check=stop_check)

    pub_fn = run_flutter_pub_upgrade if pub_upgrade else run_flutter_pub_get
    power_fn = sleep_pc if power_mode == "Sleep" else shutdown_pc

    def _appstore_runner(log: LogFn) -> bool:
        return run_appstore_upload(
            version=version,
            stop_check=stop_check,
            build=build,
            log=log,
        )

    def _build_apk_and_collect(log: LogFn) -> bool:
        ok = run_build_apk(log, stop_check=stop_check)
        if ok:
            copy_apks_to_outputs(version, build, log)
        return ok

    def _build_aab_and_collect(log: LogFn) -> bool:
        ok = run_build_aab(log, stop_check=stop_check)
        if ok:
            copy_aabs_to_outputs(version, build, log)
        return ok

    def _build_ipa_and_collect(log: LogFn) -> bool:
        ok = run_build_ipa(log, stop_check=stop_check)
        if ok:
            copy_ipas_to_outputs(version, build, log)
        return ok

    release_msg = format_release_commit_message(commit_message_release, version, build)

    return {
        "drive_upload":    lambda l: upload_outputs_to_drive(recipients, l, version=version, build=build, stop_check=stop_check),
        "git_push":        lambda l: run_git_push(git_branch, log=l, stop_check=stop_check),
        "git_pull":        lambda l: run_git_pull(git_branch, log=l, stop_check=stop_check),
        "git_commit_rel":  lambda l: run_git_commit_release(release_msg, l),
        "git_commit_pre":  lambda l: run_git_commit_pre(commit_message, l),
        "open_folders":    lambda l: run_open_outputs(l),
        "shutdown":        lambda l: power_fn(l),

        "clean":           with_stop(run_flutter_clean),
        "pod_update":      with_stop(run_pod_update),
        "pub_get":         with_stop(pub_fn),

        "build_aab":       _build_aab_and_collect,
        "build_apk":       _build_apk_and_collect,
        "build_ipa":       _build_ipa_and_collect,
        "appstore_upload": _appstore_runner,
        "google_play_upload": lambda l: run_google_play_upload(
            version=version, build=build, track=google_play_track, log=l, stop_check=stop_check,
        ),
    }


def run_selected(
    *,
    steps: list[StepDef],
    step_enabled: Callable[[str], bool],
    log: LogFn,
    version: str = "1.0.0",
    build: str = "1",
    drive_email_link_to: str | None = None,
    stop_check: StopCheckFn | None = None,
    on_step_start: Callable[[str], None] | None = None,
    on_step_done: Callable[[bool, str], None] | None = None,
    commit_message: str = "pre-release cleanup",
    commit_message_release: str = "v{version} ({build})",
    pub_upgrade: bool = False,
    power_mode: str = "Shutdown",
    git_branch: str = "master",
    google_play_track: str = "production",
    quit_after_power: bool = False,
    schedule_quit_after_seconds: Callable[[float], None] | None = None,
) -> bool:
    should_clear_outputs = any(
        key in {"build_aab", "build_apk", "build_ipa"} and step_enabled(key)
        for key, _label, _desc, _critical in steps
    )
    if should_clear_outputs:
        clear_outputs()
    runners = _build_runners(
        commit_message_release=commit_message_release,
        commit_message=commit_message,
        pub_upgrade=pub_upgrade,
        recipients=drive_email_link_to,
        stop_check=stop_check,
        power_mode=power_mode,
        version=version,
        build=build,
        git_branch=git_branch,
        google_play_track=google_play_track,
    )

    shutdown_step_ok = False
    for key, _label, _desc, critical in steps:
        if stop_check and stop_check():
            log("\nStopped by user.\n")
            return False
        if not step_enabled(key):
            continue
        runner = runners.get(key)
        if runner is None:
            log(f"Unknown step: {key}\n")
            continue
        if on_step_start:
            on_step_start(key)
        ok = runner(log)
        if on_step_done:
            on_step_done(ok, key)
        if key == "shutdown" and ok:
            shutdown_step_ok = True
        if critical and not ok:
            return False

    if (
        quit_after_power
        and shutdown_step_ok
        and schedule_quit_after_seconds is not None
    ):
        log(
            f"\nQuitting application in {POWER_DELAY} seconds "
            f"(same delay as shutdown/sleep).\n"
        )
        schedule_quit_after_seconds(float(POWER_DELAY))
    return True
