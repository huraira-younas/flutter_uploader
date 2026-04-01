"""Pipeline step declarations and typed tuples."""

from __future__ import annotations

StepDef = tuple[str, str, str, bool]
StepResult = tuple[str, bool, float]

COMMON_STEPS: list[StepDef] = [
    ("clean", "Flutter Clean", "Remove build cache", False),
    ("pub_get", "Dependencies", "pub get or pub upgrade", False),
]

COMMIT_PRE_STEPS: list[StepDef] = [
    ("git_commit_pre", "Pre-release Commit", "git add . && git commit", True),
]

GIT_SYNC_STEPS: list[StepDef] = [
    ("git_pull", "Pull Master", "git pull origin master", True),
]

ANDROID_STEPS: list[StepDef] = [
    ("build_apk", "Build APK", "Release, split-per-abi", True),
]

IOS_STEPS: list[StepDef] = [
    ("pod_install", "Pod Install", "Deintegrate + repo update + install", False),
    ("build_ipa", "Build IPA", "Release archive", True),
    ("appstore_upload", "App Store Upload", "Upload to App Store Connect", True),
]

GIT_POST_STEPS: list[StepDef] = [
    ("git_commit_rel", "Release Commit", "git add . && git commit v{ver}", True),
    ("git_push", "Push Master", "git push origin master", True),
]

# Pull + release commit + push (Post-Git UI card; pipeline runs pull before builds, rest after).
GIT_POST_SECTION_STEPS: list[StepDef] = GIT_SYNC_STEPS + GIT_POST_STEPS

POST_STEPS: list[StepDef] = [
    ("open_folders", "Open Outputs", "Open outputs folder", False),
    ("drive_upload", "Upload to Drive", "Upload outputs + email link", True),
    ("shutdown", "Power Off/Sleep", "Shutdown or sleep when done", False),
]
