from __future__ import annotations

from typing import Any, Optional

from openai import AzureOpenAI, OpenAI

from ..config import Settings, get_settings
from ..models.api import AzureProviderConfig, OpenAIProviderConfig, ProviderConfig, ProviderEnum


class OpenAIClientFactory:
    def create(self, config: ProviderConfig) -> Any:
        if config.provider is ProviderEnum.OPENAI:
            assert isinstance(config, OpenAIProviderConfig)
            return OpenAI(api_key=config.api_key)
        if config.provider is ProviderEnum.AZURE:
            assert isinstance(config, AzureProviderConfig)
            return AzureOpenAI(
                api_key=config.api_key,
                api_version=config.api_version,
                azure_endpoint=str(config.endpoint),
            )
        raise ValueError("Unsupported provider")

    def validate(self, config: ProviderConfig) -> None:
        client = self.create(config)
        client.models.list()


_factory_instance: Optional[OpenAIClientFactory] = None


def get_client_factory() -> OpenAIClientFactory:
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = OpenAIClientFactory()
    return _factory_instance


def resolve_provider_config(
    config: ProviderConfig,
    settings: Settings | None = None,
) -> tuple[ProviderConfig, bool]:
    """Ensure provider config contains an API key, applying defaults if available."""

    settings = settings or get_settings()
    used_default = False
    data = config.model_dump()

    if config.provider is ProviderEnum.OPENAI:
        api_key = data.get("api_key") or settings.default_openai_api_key
        if not api_key:
            raise ValueError("Missing OpenAI API key")
        used_default = not data.get("api_key")
        data["api_key"] = api_key
        return OpenAIProviderConfig(**data), used_default

    if config.provider is ProviderEnum.AZURE:
        api_key = data.get("api_key") or settings.default_azure_api_key
        if not api_key:
            raise ValueError("Missing Azure API key")
        used_default = not data.get("api_key")
        data["api_key"] = api_key
        return AzureProviderConfig(**data), used_default

    raise ValueError("Unsupported provider")
