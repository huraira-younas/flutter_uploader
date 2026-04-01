from typing import Callable
import shutil
import os

from core.constants import (
    flutter_project_root,
    OUTPUTS_DIR,
    POWER_DELAY,
    apk_dir,
    ipa_dir,
)
from core.steps import StepDef
from helpers.platform_utils import open_folder, shutdown_pc, sleep_pc
from helpers.drive_upload import upload_outputs_to_drive
from helpers.types import LogFn, StopCheckFn
from helpers.shell import CommandRunner
from helpers.rename_artifacts import (
    copy_apks_to_outputs, 
    copy_ipas_to_outputs, 
    clear_outputs,
)


_CMD: CommandRunner | None = None


def _cmd() -> CommandRunner:
    global _CMD
    if _CMD is None:
        _CMD = CommandRunner(project_root=flutter_project_root())
    return _CMD


def _log_noop(_: str) -> None:
    pass


def _git_add_and_commit(message: str, log: LogFn) -> bool:
    if not _cmd().run_project(["git", "add", "."], log):
        return False
    return _cmd().run_project(["git", "commit", "-m", message], log)


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


def run_git_commit_pre(message: str, log: LogFn = _log_noop) -> bool:
    log(f'\n>> git add . && git commit -m "{message}"\n')
    return _git_add_and_commit(message, log)


def run_git_pull(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["git", "pull", "origin", "master"], log,
        header="\n>> git pull origin master\n", stop_check=stop_check,
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


def run_git_commit_release(message: str, log: LogFn = _log_noop) -> bool:
    log(f'\n>> git add . && git commit -m "{message}"\n')
    return _git_add_and_commit(message, log)


def run_git_push(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return _run_project_cmd(
        ["git", "push", "origin", "master"], log,
        header="\n>> git push origin master\n", stop_check=stop_check,
    )


def run_build_apk(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    apk_output_dir = apk_dir()
    if not _remove_dir_if_exists(apk_output_dir, log, "APK"):
        return False
    return _run_project_cmd(
        ["flutter", "build", "apk", "--release", "--split-per-abi"], log,
        header="\n>> flutter build apk --release --split-per-abi\n", stop_check=stop_check,
    )


def run_pod_install(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    ios_dir = flutter_project_root() / "ios"
    if not ios_dir.exists():
        log("iOS directory not found. Skipping pod install.\n")
        return False
    if not _cmd().run_in(["pod", "deintegrate"], ios_dir, log, header="\n>> pod deintegrate\n", stop_check=stop_check):
        return False
    if not _cmd().run_in(["pod", "repo", "update"], ios_dir, log, header="\n>> pod repo update\n", stop_check=stop_check):
        return False
    return _cmd().run_in(["pod", "install"], ios_dir, log, header="\n>> pod install\n", stop_check=stop_check)


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
    return run_shorebird_patch_android_for_release("", log=log, stop_check=stop_check)


def run_shorebird_patch_android_for_release(
    release_version: str,
    log: LogFn = _log_noop,
    stop_check: StopCheckFn | None = None,
) -> bool:
    cmd = ["shorebird", "patch", "android"]
    if release_version:
        log(f">> Auto-target Shorebird release: {release_version}\n")
        cmd += ["--release-version", release_version]
    return _run_project_cmd(
        cmd, log,
        header="\n>> shorebird patch android\n",
        stop_check=stop_check,
    )


def run_shorebird_patch_ios(log: LogFn = _log_noop, stop_check: StopCheckFn | None = None) -> bool:
    return run_shorebird_patch_ios_for_release("", log=log, stop_check=stop_check)


def run_shorebird_patch_ios_for_release(
    release_version: str,
    log: LogFn = _log_noop,
    stop_check: StopCheckFn | None = None,
) -> bool:
    cmd = ["shorebird", "patch", "ios"]
    if release_version:
        log(f">> Auto-target Shorebird release: {release_version}\n")
        cmd += ["--release-version", release_version]
    return _run_project_cmd(
        cmd, log,
        header="\n>> shorebird patch ios\n",
        stop_check=stop_check,
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
    commit_message_release: str = "v{version} ({build})",
    pub_upgrade: bool = False,
    power_mode: str = "Shutdown",
) -> dict[str, Callable[[LogFn], bool]]:
    """Build step_key -> runner function mapping."""
    def with_stop(fn: Callable) -> Callable[[LogFn], bool]:
        return lambda log: fn(log, stop_check=stop_check)

    release_version = f"{version}+{build}".strip("+")
    pub_fn = run_flutter_pub_upgrade if pub_upgrade else run_flutter_pub_get
    apk_builder = _APK_BUILDERS.get(android_build_mode, run_build_apk)
    ipa_builder = _IPA_BUILDERS.get(ios_build_mode, run_build_ipa)
    power_fn = sleep_pc if power_mode == "Sleep" else shutdown_pc

    if android_build_mode == "patch":
        apk_builder = lambda log, stop_check=None: run_shorebird_patch_android_for_release(
            release_version, log=log, stop_check=stop_check,
        )
    if ios_build_mode == "patch":
        ipa_builder = lambda log, stop_check=None: run_shorebird_patch_ios_for_release(
            release_version, log=log, stop_check=stop_check,
        )

    def _appstore_runner(log: LogFn) -> bool:
        if ios_build_mode == "patch":
            log("Skipping App Store upload: Shorebird patch mode selected.\n")
            return True
        return run_appstore_upload(
            version=version,
            stop_check=stop_check,
            build=build,
            log=log,
        )

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

    release_msg = format_release_commit_message(commit_message_release, version, build)

    return {
        "drive_upload":    lambda l: run_drive_upload(recipients, version, build, l, stop_check=stop_check),
        "appstore_upload": _appstore_runner,
        "git_commit_rel":  lambda l: run_git_commit_release(release_msg, l),
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
    commit_message_release: str = "v{version} ({build})",
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
        commit_message_release=commit_message_release,
        android_build_mode=android_build_mode,
        commit_message=commit_message,
        ios_build_mode=ios_build_mode,
        pub_upgrade=pub_upgrade,
        recipients=drive_email_link_to,
        stop_check=stop_check,
        power_mode=power_mode,
        version=version,
        build=build,
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
