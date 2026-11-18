from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from providers import PROVIDERS, generate_reply, get_provider, test_connection


class ProviderConfigurationTests(unittest.TestCase):
    def test_expected_providers_are_available(self) -> None:
        self.assertEqual(set(PROVIDERS), {"openai", "gemini", "deepseek"})

    def test_each_provider_has_models_and_key_label(self) -> None:
        for provider in PROVIDERS.values():
            self.assertTrue(provider.default_model)
            self.assertIn(provider.default_model, provider.model_options)
            self.assertIn("API-Key", provider.key_label)

    def test_gemini_is_marked_as_free_tier_option(self) -> None:
        self.assertIn("Free Tier", get_provider("gemini").free_tier_badge or "")

    @patch("openai.OpenAI")
    def test_deepseek_uses_openai_compatible_chat_endpoint(self, openai_class) -> None:
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **_: SimpleNamespace(
                        choices=[SimpleNamespace(message=SimpleNamespace(content="Antwort"))]
                    )
                )
            )
        )
        openai_class.return_value = fake_client

        reply = generate_reply("deepseek", "test-key", "deepseek-chat", "System", [], "Frage")

        self.assertEqual(reply, "Antwort")
        self.assertEqual(openai_class.call_args.kwargs["base_url"], "https://api.deepseek.com")
        self.assertEqual(openai_class.call_args.kwargs["api_key"], "test-key")

    @patch("google.genai.Client")
    def test_gemini_keeps_client_alive_until_response(self, client_class) -> None:
        fake_client = SimpleNamespace(
            models=SimpleNamespace(generate_content=lambda **_: SimpleNamespace(text="Antwort")),
            close=lambda: None,
        )
        client_class.return_value = fake_client

        reply = generate_reply("gemini", "test-key", "gemini-2.5-flash-lite", "System", [], "Frage")

        self.assertEqual(reply, "Antwort")
        self.assertEqual(client_class.call_args.kwargs["api_key"], "test-key")

    @patch("openai.OpenAI")
    def test_connection_uses_deepseek_chat_not_model_metadata(self, openai_class) -> None:
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **_: SimpleNamespace(
                        choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))]
                    )
                )
            )
        )
        openai_class.return_value = fake_client

        successful, _ = test_connection("deepseek", "test-key", "deepseek-chat")

        self.assertTrue(successful)
        self.assertFalse(hasattr(fake_client, "models"))


if __name__ == "__main__":
    unittest.main()
