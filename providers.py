"""Provider-neutral access to the optional riddle chat."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProviderId = Literal["openai", "gemini", "deepseek"]


@dataclass(frozen=True)
class ProviderConfig:
    id: ProviderId
    label: str
    key_label: str
    default_model: str
    model_options: tuple[str, ...]
    free_tier_badge: str | None = None


PROVIDERS: dict[ProviderId, ProviderConfig] = {
    "openai": ProviderConfig("openai", "OpenAI", "OpenAI API-Key", "gpt-4.1-mini", ("gpt-4.1-mini",)),
    "gemini": ProviderConfig(
        "gemini",
        "Google Gemini",
        "Gemini API-Key",
        "gemini-2.5-flash-lite",
        ("gemini-2.5-flash-lite", "gemini-2.5-flash"),
        "Kostenlos über Gemini Free Tier möglich – Limits beachten",
    ),
    "deepseek": ProviderConfig(
        "deepseek", "DeepSeek", "DeepSeek API-Key", "deepseek-chat", ("deepseek-chat", "deepseek-reasoner")
    ),
}


def get_provider(provider_id: str) -> ProviderConfig:
    try:
        return PROVIDERS[provider_id]  # type: ignore[index]
    except KeyError as error:
        raise ValueError(f"Unbekannter KI-Anbieter: {provider_id}") from error


def _friendly_error(error: Exception, provider: ProviderConfig, model: str) -> str:
    status_code = getattr(error, "status_code", None)
    if status_code in (401, 403):
        return f"Der {provider.key_label} ist ungültig oder hat keinen Zugriff auf dieses Modell."
    if status_code == 404:
        return f"Das Modell „{model}“ ist bei {provider.label} nicht verfügbar."
    if status_code == 429:
        return f"Bei {provider.label} wurde ein Rate- oder Guthabenlimit erreicht."
    error_text = str(error).lower()
    if "closed" in error_text:
        return "Der Anbieter-Client wurde unerwartet geschlossen. Bitte erneut versuchen."
    if "connect" in error_text or "network" in error_text or "dns" in error_text:
        return f"{provider.label} konnte nicht über das Netzwerk erreicht werden."
    return f"Die Verbindung zu {provider.label} ist fehlgeschlagen: {error}"


def test_connection(provider_id: str, api_key: str, model: str) -> tuple[bool, str]:
    """Test the actual generation endpoint, never a provider-specific model lookup."""

    provider = get_provider(provider_id)
    try:
        if provider.id == "gemini":
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            try:
                response = client.models.generate_content(
                    model=model,
                    contents="Antworte ausschließlich mit OK.",
                    config=types.GenerateContentConfig(max_output_tokens=1),
                )
                if not response.text:
                    raise RuntimeError("Gemini hat keine Textantwort zurückgegeben.")
            finally:
                client.close()
            return True, f"Verbindung zu {provider.label} mit „{model}“ erfolgreich getestet."

        from openai import OpenAI

        if provider.id == "deepseek":
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Antworte ausschließlich mit OK."}],
                max_tokens=1,
            )
            if not response.choices or not response.choices[0].message.content:
                raise RuntimeError("DeepSeek hat keine Textantwort zurückgegeben.")
        else:
            response = OpenAI(api_key=api_key).responses.create(
                model=model,
                input="Antworte ausschließlich mit OK.",
                max_output_tokens=1,
            )
            if not response.output_text:
                raise RuntimeError("OpenAI hat keine Textantwort zurückgegeben.")
    except Exception as error:
        return False, _friendly_error(error, provider, model)
    return True, f"Verbindung zu {provider.label} mit „{model}“ erfolgreich getestet."


def generate_reply(
    provider_id: str,
    api_key: str,
    model: str,
    system_prompt: str,
    history: list[dict[str, str]],
    user_message: str,
) -> str:
    """Send one provider-specific request and return plain assistant text."""

    provider = get_provider(provider_id)
    try:
        if provider.id == "gemini":
            from google import genai
            from google.genai import types

            contents = [
                types.Content(
                    role="model" if message["role"] == "assistant" else "user",
                    parts=[types.Part.from_text(text=message["content"])],
                )
                for message in [*history, {"role": "user", "content": user_message}]
            ]
            client = genai.Client(api_key=api_key)
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                )
            finally:
                client.close()
            if not response.text:
                raise RuntimeError("Gemini hat keine Textantwort zurückgegeben.")
            return response.text

        from openai import OpenAI

        messages = [{"role": "system", "content": system_prompt}, *history]
        messages.append({"role": "user", "content": user_message})
        if provider.id == "deepseek":
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(model=model, messages=messages)
            text = response.choices[0].message.content
            if not text:
                raise RuntimeError("DeepSeek hat keine Textantwort zurückgegeben.")
            return text

        response = OpenAI(api_key=api_key).responses.create(model=model, input=messages)
        if not response.output_text:
            raise RuntimeError("OpenAI hat keine Textantwort zurückgegeben.")
        return response.output_text
    except Exception as error:
        raise RuntimeError(_friendly_error(error, provider, model)) from error
