import unittest

from core.pipeline_config import (
    find_invalid_step_keys,
    build_pipeline_config,
    step_enabled_filter,
    PipelineConfig,
)


class PipelineConfigTests(unittest.TestCase):
    def test_find_invalid_step_keys(self) -> None:
        bad = find_invalid_step_keys(["clean", "not_a_step", "build_apk"])
        self.assertEqual(["not_a_step"], bad)

    def test_build_pipeline_config_applies_message_defaults(self) -> None:
        cfg = build_pipeline_config(
            version="1.2.3",
            build="9",
            recipients=None,
            commit_message_pre="",
            commit_message_release="",
        )
        self.assertEqual("pre-release cleanup", cfg.commit_message_pre)
        self.assertEqual("v{version} ({build})", cfg.commit_message_release)

    def test_step_filter_disables_appstore_for_patch_mode(self) -> None:
        cfg = PipelineConfig(
            ios_build_mode="patch",
            enabled_steps=frozenset({"appstore_upload", "build_ipa"}),
        )
        is_enabled = step_enabled_filter(cfg)
        self.assertFalse(is_enabled("appstore_upload"))
        self.assertTrue(is_enabled("build_ipa"))


if __name__ == "__main__":
    unittest.main()
