"""Local, git-ignored application settings and API-key storage."""

from __future__ import annotations

import json
import os
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from providers import PROVIDERS, ProviderId, get_provider


DEFAULT_PROVIDER_ID: ProviderId = "openai"


@dataclass
class ProviderSettings:
    api_key: str = ""
    model: str = ""


@dataclass
class AppSettings:
    active_provider: ProviderId = DEFAULT_PROVIDER_ID
    providers: dict[ProviderId, ProviderSettings] = field(default_factory=dict)

    def provider_settings(self, provider_id: ProviderId) -> ProviderSettings:
        if provider_id not in self.providers:
            self.providers[provider_id] = ProviderSettings(model=get_provider(provider_id).default_model)
        settings = self.providers[provider_id]
        if not settings.model:
            settings.model = get_provider(provider_id).default_model
        return settings


def default_settings() -> AppSettings:
    settings = AppSettings()
    for provider_id, provider in PROVIDERS.items():
        settings.providers[provider_id] = ProviderSettings(model=provider.default_model)
    return settings


def load_settings(path: str | Path) -> AppSettings:
    """Load settings; a missing file simply means an unconfigured app."""

    settings_path = Path(path)
    settings = default_settings()
    if not settings_path.exists():
        return settings

    with settings_path.open("rb") as settings_file:
        raw = tomllib.load(settings_file)

    app_section = raw.get("app", {})
    active_provider = app_section.get("active_provider", DEFAULT_PROVIDER_ID)
    if active_provider in PROVIDERS:
        settings.active_provider = active_provider

    provider_section = raw.get("providers", {})
    for provider_id in PROVIDERS:
        values = provider_section.get(provider_id, {})
        if not isinstance(values, dict):
            continue
        current = settings.provider_settings(provider_id)
        api_key = values.get("api_key", "")
        model = values.get("model", current.model)
        current.api_key = api_key if isinstance(api_key, str) else ""
        current.model = model if isinstance(model, str) and model.strip() else current.model
    return settings


def _toml_string(value: str) -> str:
    """JSON quoting is valid TOML basic-string quoting for our scalar values."""

    return json.dumps(value, ensure_ascii=False)


def save_settings(settings: AppSettings, path: str | Path) -> None:
    """Atomically write a private local TOML file with restrictive Unix permissions."""

    settings_path = Path(path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["[app]", f"active_provider = {_toml_string(settings.active_provider)}", ""]
    for provider_id in PROVIDERS:
        provider = settings.provider_settings(provider_id)
        lines.extend(
            [
                f"[providers.{provider_id}]",
                f"api_key = {_toml_string(provider.api_key)}",
                f"model = {_toml_string(provider.model)}",
                "",
            ]
        )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix="secrets-", suffix=".toml", dir=settings_path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
            temporary_file.write("\n".join(lines))
        os.chmod(temporary_name, 0o600)
        Path(temporary_name).replace(settings_path)
    finally:
        temporary_path = Path(temporary_name)
        if temporary_path.exists():
            temporary_path.unlink()


def masked_key(api_key: str) -> str:
    if not api_key:
        return "Kein Key gespeichert"
    suffix = api_key[-4:] if len(api_key) >= 4 else api_key
    return f"••••••••{suffix}"
