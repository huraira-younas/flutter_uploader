"""Pipeline step declarations and typed tuples."""

from __future__ import annotations

StepDef = tuple[str, str, str, bool]
StepResult = tuple[str, bool, float]

COMMON_STEPS: list[StepDef] = [
    ("clean", "Flutter Clean", "Remove build cache", False),
    ("pub_get", "Pub", "Install dependencies", False),
]

ANDROID_STEPS: list[StepDef] = [
    ("build_apk", "Build APK", "flutter build apk --release --split-per-abi", True),
    ("build_aab", "Build App Bundle", "flutter build appbundle --release", True),
]

IOS_STEPS: list[StepDef] = [
    ("pod_update", "Pod Update", "Deintegrate + repo update + update", False),
    ("build_ipa", "Build IPA", "Release archive", True),
]

DISTRIBUTION_STEPS: list[StepDef] = [
    ("google_play_upload", "PlayStore Upload", "Upload AAB", True),
    ("appstore_upload", "AppStore Upload", "Upload IPA", True),
    ("drive_upload", "Upload to Drive", "Upload outputs + email link", True),
]


COMMIT_PRE_STEPS: list[StepDef] = [
    ("git_commit_pre", "Pre-release Commit", "git add . && git commit", True),
    ("git_pull", "Pull Branch", "git pull origin {branch}", True),
]

GIT_POST_STEPS: list[StepDef] = [
    ("git_commit_rel", "Release Commit", "git add . && git commit v{ver}", True),
    ("git_push", "Push Branch", "git push origin {branch}", True),
]

POST_STEPS: list[StepDef] = [
    ("open_folders", "Open Outputs", "Open outputs folder", False),
    ("shutdown", "Power", "Shutdown or sleep", False),
]
