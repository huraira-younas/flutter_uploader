from typing import Callable
import shutil
import os

from core.constants import StepDef, FLUTTER_PROJECT_ROOT, OUTPUTS_DIR, APK_DIR, IPA_DIR, POWER_DELAY
from helpers.platform_utils import open_folder, shutdown_pc, sleep_pc
from helpers.drive_upload import upload_outputs_to_drive
from helpers.types import LogFn, StopCheckFn
from helpers.shell import CommandRunner
from helpers.rename_artifacts import (
    copy_apks_to_outputs, 
    copy_ipas_to_outputs, 
    clear_outputs,
)


_CMD = CommandRunner(project_root=FLUTTER_PROJECT_ROOT)


def _log_noop(_: str) -> None:
    pass


def _run_project_cmd(
    cmd: list[str],
    log: LogFn,
    *,
    header: str,
    stop_check: StopCheckFn | None = None,
) -> bool:
    return _CMD.run_project(cmd, log, header=header, stop_check=stop_check)


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


def run_git_commit_pre(message: str, log: LogFn = _log_noop) -> bool:
    log(f'\n>> git add . && git commit -m "{message}"\n')
    if not _CMD.run_project(["git", "add", "."], log):
        return False
    _CMD.run_project(["git", "commit", "-m", message], log)
    return True


def run_git_pull(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["git", "pull", "origin", "master"], log,
        header="\n>> git pull origin master\n", stop_check=stop_check,
    )


def run_git_commit_release(version: str, build: str, log: LogFn = _log_noop) -> bool:
    msg = f"v{version} ({build})"
    log(f'\n>> git add . && git commit -m "{msg}"\n')
    if not _CMD.run_project(["git", "add", "."], log):
        return False
    return _CMD.run_project(["git", "commit", "-m", msg], log)


def run_git_push(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["git", "push", "origin", "master"], log,
        header="\n>> git push origin master\n", stop_check=stop_check,
    )


def run_build_apk(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    if APK_DIR.exists():
        try:
            shutil.rmtree(APK_DIR)
            log(f"\n>> Deleted APK output dir: {APK_DIR}\n")
        except OSError as e:
            log(f"\n>> Failed to delete APK dir: {e}\n")
            return False
    return _run_project_cmd(
        ["flutter", "build", "apk", "--release", "--split-per-abi"], log,
        header="\n>> flutter build apk --release --split-per-abi\n", stop_check=stop_check,
    )


def run_pod_install(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    ios_dir = FLUTTER_PROJECT_ROOT / "ios"
    if not ios_dir.exists():
        log("iOS directory not found. Skipping pod install.\n")
        return False
    if not _CMD.run_in(["pod", "deintegrate"], ios_dir, log, header="\n>> pod deintegrate\n", stop_check=stop_check):
        return False
    if not _CMD.run_in(["pod", "repo", "update"], ios_dir, log, header="\n>> pod repo update\n", stop_check=stop_check):
        return False
    return _CMD.run_in(["pod", "install"], ios_dir, log, header="\n>> pod install\n", stop_check=stop_check)


def run_build_ipa(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    if IPA_DIR.exists():
        try:
            shutil.rmtree(IPA_DIR)
            log(f"\n>> Deleted IPA output dir: {IPA_DIR}\n")
        except OSError as e:
            log(f"\n>> Failed to delete IPA dir: {e}\n")
            return False
    return _run_project_cmd(
        ["flutter", "build", "ipa", "--release"], log,
        header="\n>> flutter build ipa --release\n", stop_check=stop_check,
    )


def run_appstore_upload(
    version: str,
    build: str,
    log: LogFn = _log_noop,
    stop_check: StopCheckFn | None = None,
) -> bool:
    """Upload the first IPA found to App Store Connect via xcrun altool."""
    issuer_id = os.environ.get("APP_STORE_ISSUER_ID", "").strip()
    api_key = os.environ.get("APP_STORE_API_KEY", "").strip()
    if (
        not issuer_id
        or not api_key
        or issuer_id.startswith("YOUR_")
        or api_key.startswith("YOUR_")
    ):
        log("App Store Connect credentials not configured. Skipping upload.\n")
        return True

    ipa_files = sorted(IPA_DIR.glob("*.ipa"))
    if not ipa_files:
        log("No IPA files found to upload.\n")
        return False

    ipa_path = ipa_files[0]
    return _CMD.run_project(
        [
            "xcrun", "altool", "--upload-app", "--type", "ios",
            "-f", str(ipa_path),
            "--apiKey", api_key,
            "--apiIssuer", issuer_id,
        ],
        log,
        header=f"\n>> Uploading {ipa_path.name} to App Store Connect\n",
        stop_check=stop_check,
    )


def run_shorebird_release_android(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["shorebird", "release", "android", "--artifact", "apk"], log,
        header="\n>> shorebird release android --artifact apk\n", stop_check=stop_check,
    )


def run_shorebird_release_ios(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["shorebird", "release", "ios"], log,
        header="\n>> shorebird release ios\n", stop_check=stop_check,
    )


def run_shorebird_patch_android(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["shorebird", "patch", "android"], log,
        header="\n>> shorebird patch android\n", stop_check=stop_check,
    )


def run_shorebird_patch_ios(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["shorebird", "patch", "ios"], log,
        header="\n>> shorebird patch ios\n", stop_check=stop_check,
    )


def run_drive_upload(
    recipients: str | None, version: str, build: str, log: LogFn,
    stop_check: StopCheckFn | None = None,
) -> bool:
    return upload_outputs_to_drive(
        recipients, log, version=version, build=build, stop_check=stop_check,
    )


def run_open_outputs(log: LogFn) -> bool:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    log("\n>> Open outputs folder\n")
    return open_folder(OUTPUTS_DIR, log)


_APK_BUILDERS = {
    "release":  run_shorebird_release_android,
    "patch":    run_shorebird_patch_android,
    "flutter":  run_build_apk,
}

_IPA_BUILDERS = {
    "release":  run_shorebird_release_ios,
    "patch":    run_shorebird_patch_ios,
    "flutter":  run_build_ipa,
}


def _build_runners(
    version: str,
    build: str,
    recipients: str | None,
    stop_check: StopCheckFn | None,
    *,
    android_build_mode: str = "release",
    ios_build_mode: str = "release",
    commit_message: str = "pre-release cleanup",
    pub_upgrade: bool = False,
    power_mode: str = "Shutdown",
) -> dict[str, Callable[[LogFn], bool]]:
    """Build step_key -> runner function mapping."""
    def with_stop(fn: Callable) -> Callable[[LogFn], bool]:
        return lambda log: fn(log, stop_check=stop_check)

    pub_fn = run_flutter_pub_upgrade if pub_upgrade else run_flutter_pub_get
    apk_builder = _APK_BUILDERS.get(android_build_mode, run_build_apk)
    ipa_builder = _IPA_BUILDERS.get(ios_build_mode, run_build_ipa)
    power_fn = sleep_pc if power_mode == "Sleep" else shutdown_pc

    def _build_apk_and_collect(log: LogFn) -> bool:
        ok = apk_builder(log, stop_check=stop_check)
        if ok:
            copy_apks_to_outputs(version, build, log)
        return ok

    def _build_ipa_and_collect(log: LogFn) -> bool:
        ok = ipa_builder(log, stop_check=stop_check)
        if ok:
            copy_ipas_to_outputs(version, build, log)
        return ok

    return {
        "drive_upload":    lambda l: run_drive_upload(recipients, version, build, l, stop_check=stop_check),
        "appstore_upload": lambda l: run_appstore_upload(version, build, l, stop_check=stop_check),
        "git_commit_rel":  lambda l: run_git_commit_release(version, build, l),
        "git_commit_pre":  lambda l: run_git_commit_pre(commit_message, l),
        "open_folders":    lambda l: run_open_outputs(l),
        "shutdown":        lambda l: power_fn(l),

        "clean":           with_stop(run_flutter_clean),
        "pod_install":     with_stop(run_pod_install),
        "git_push":        with_stop(run_git_push),
        "git_pull":        with_stop(run_git_pull),
        "pub_get":         with_stop(pub_fn),
        
        "build_apk":       _build_apk_and_collect,
        "build_ipa":       _build_ipa_and_collect,
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
    android_build_mode: str = "release",
    ios_build_mode: str = "release",
    commit_message: str = "pre-release cleanup",
    pub_upgrade: bool = False,
    power_mode: str = "Shutdown",
    quit_after_power: bool = False,
    schedule_quit_after_seconds: Callable[[float], None] | None = None,
) -> bool:
    should_clear_outputs = any(
        key in {"build_apk", "build_ipa"} and step_enabled(key)
        for key, _label, _desc, _critical in steps
    )
    if should_clear_outputs:
        clear_outputs()
    runners = _build_runners(
        version, build, drive_email_link_to, stop_check,
        android_build_mode=android_build_mode,
        commit_message=commit_message,
        ios_build_mode=ios_build_mode,
        pub_upgrade=pub_upgrade,
        power_mode=power_mode,
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
