import unittest

from core import config_store


class ConfigStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_cache = config_store._cache

    def tearDown(self) -> None:
        config_store._cache = self._orig_cache

    def test_pipeline_section_aliases(self) -> None:
        config_store._cache = {
            "pre_git": {"enabled": False},
            "post_git": {"enabled": True},
            "post_build": {"enabled": False},
            "ios": {"enabled": True},
            "common": {"enabled": True},
            "android": {"enabled": True},
        }
        self.assertFalse(config_store.pipeline_section_enabled("git_pre"))
        self.assertTrue(config_store.pipeline_section_enabled("git_post"))
        self.assertFalse(config_store.pipeline_section_enabled("post"))
        self.assertTrue(config_store.pipeline_section_enabled("ios", include_ios_default=False))

    def test_shorebird_build_modes(self) -> None:
        config_store._cache = {
            "android": {"shorebird": True, "shorebird_mode": "Patch"},
            "ios": {"shorebird": True, "shorebird_mode": "Release"},
        }
        self.assertEqual("patch", config_store.android_build_mode_from_config())
        self.assertEqual("release", config_store.ios_build_mode_from_config())

    def test_get_section_returns_mutation_safe_copy(self) -> None:
        config_store._cache = {
            "common": {"enabled": True, "steps": {"clean": True}},
        }
        section = config_store.get_section("common")
        section["steps"]["clean"] = False
        self.assertTrue(config_store._cache["common"]["steps"]["clean"])


if __name__ == "__main__":
    unittest.main()
