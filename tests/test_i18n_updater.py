"""
Tests for i18n and updater modules.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from safekid.i18n import t, set_lang, get_lang, t_all, SUPPORTED_LANGS


class TestI18n(unittest.TestCase):
    def setUp(self):
        set_lang("id")  # reset to ID before each test

    def test_default_lang_is_id(self):
        self.assertEqual(get_lang(), "id")

    def test_translate_welcome_id(self):
        set_lang("id")
        result = t("welcome", name="Budi")
        self.assertEqual(result, "Halo, Budi!")

    def test_translate_welcome_en(self):
        set_lang("en")
        result = t("welcome", name="Budi")
        self.assertEqual(result, "Hello, Budi!")

    def test_translate_with_integer(self):
        set_lang("id")
        result = t("time_added", mins=10)
        self.assertIn("10", result)

    def test_missing_key_returns_key(self):
        result = t("totally_nonexistent_key_xyz")
        self.assertEqual(result, "totally_nonexistent_key_xyz")

    def test_set_unsupported_lang_fallback(self):
        set_lang("fr")   # French not supported
        self.assertEqual(get_lang(), "id")  # Falls back to ID

    def test_t_all_returns_all_langs(self):
        result = t_all("time_left")
        self.assertIn("id", result)
        self.assertIn("en", result)
        self.assertEqual(result["id"], "Sisa Waktu")
        self.assertEqual(result["en"], "Time Left")

    def test_lang_override_per_call(self):
        set_lang("id")
        # Override to EN for single call
        result = t("time_left", lang="en")
        self.assertEqual(result, "Time Left")
        # Global still ID
        self.assertEqual(get_lang(), "id")

    def test_all_keys_exist_in_both_langs(self):
        """Ensure no translation key is missing in any language."""
        from safekid.i18n import TRANSLATIONS
        id_keys = set(TRANSLATIONS["id"].keys())
        en_keys = set(TRANSLATIONS["en"].keys())
        missing_en = id_keys - en_keys
        missing_id = en_keys - id_keys
        self.assertEqual(len(missing_en), 0,
            f"Keys in ID but not EN: {missing_en}")
        self.assertEqual(len(missing_id), 0,
            f"Keys in EN but not ID: {missing_id}")


class TestUpdater(unittest.TestCase):
    def test_version_format(self):
        from safekid.updater import CURRENT_VERSION
        parts = CURRENT_VERSION.split(".")
        self.assertEqual(len(parts), 3)
        for p in parts:
            self.assertTrue(p.isdigit(), f"'{p}' is not a digit")

    def test_check_update_returns_dict(self):
        from safekid.updater import check_update
        res = check_update.__wrapped__ if hasattr(check_update, "__wrapped__") else check_update
        # Just call with force but allow network error
        from safekid.updater import check_update as cu
        result = cu()  # May fail if offline — that's OK
        self.assertIn("update_available", result)
        self.assertIn("current_version", result)
        self.assertIn("message", result)
        # update_available must be bool
        self.assertIsInstance(result["update_available"], bool)

    def test_version_comparison(self):
        from safekid.updater import _is_newer
        self.assertTrue(_is_newer("1.0.0", "0.9.0"))
        self.assertFalse(_is_newer("0.5.0", "0.6.0"))
        self.assertFalse(_is_newer("0.6.0", "0.6.0"))

    def test_version_tuple(self):
        from safekid.updater import _version_tuple
        self.assertEqual(_version_tuple("1.2.3"), (1, 2, 3))
        self.assertEqual(_version_tuple("v0.6.0"), (0, 6, 0))


if __name__ == "__main__":
    unittest.main()
