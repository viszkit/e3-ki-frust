from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from settings import default_settings, load_settings, masked_key, save_settings


class SettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings_path = Path(self.temp_dir.name) / ".streamlit" / "secrets.toml"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_saved_configuration_round_trips_without_exposing_key(self) -> None:
        settings = default_settings()
        settings.active_provider = "gemini"
        gemini = settings.provider_settings("gemini")
        gemini.api_key = "gemini-secret-1234"
        gemini.model = "gemini-2.5-flash"
        save_settings(settings, self.settings_path)

        loaded = load_settings(self.settings_path)

        self.assertEqual(loaded.active_provider, "gemini")
        self.assertEqual(loaded.provider_settings("gemini").api_key, "gemini-secret-1234")
        self.assertEqual(loaded.provider_settings("gemini").model, "gemini-2.5-flash")
        self.assertEqual(masked_key("gemini-secret-1234"), "••••••••1234")

    def test_missing_file_uses_safe_defaults(self) -> None:
        settings = load_settings(self.settings_path)

        self.assertEqual(settings.active_provider, "openai")
        self.assertEqual(settings.provider_settings("deepseek").api_key, "")
        self.assertEqual(settings.provider_settings("deepseek").model, "deepseek-chat")


if __name__ == "__main__":
    unittest.main()
