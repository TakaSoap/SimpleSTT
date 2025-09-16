import asyncio
import base64
from typing import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import config
from app.services import openai_client, storage, transcription


class DummyAudioTranscriptions:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, **kwargs):  # noqa: ANN003
        return type("Response", (), {"text": self._text})()


class DummyModels:
    def list(self):  # noqa: ANN001
        return {"data": []}


class DummyClient:
    def __init__(self, text: str) -> None:
        self.audio = type("Audio", (), {"transcriptions": DummyAudioTranscriptions(text)})()
        self.models = DummyModels()


class DummyFactory(openai_client.OpenAIClientFactory):
    def __init__(self, transcript_text: str = "dummy transcript") -> None:
        self.transcript_text = transcript_text

    def create(self, config):  # type: ignore[override]
        return DummyClient(self.transcript_text)

    def validate(self, config) -> None:  # type: ignore[override]
        return None


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APP_USERNAME", "tester")
    monkeypatch.setenv("APP_PASSWORD", "secret")
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("DEFAULT_PROVIDER", "azure")
    monkeypatch.setenv("DEFAULT_MODEL", "gpt-4o-mini-transcribe")
    monkeypatch.setenv("DEFAULT_LANGUAGE", "en")
    monkeypatch.setenv("DEFAULT_STREAM_ENABLED", "false")
    monkeypatch.setenv("DEFAULT_AZURE_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("DEFAULT_AZURE_DEPLOYMENT_ID", "test-deploy")
    monkeypatch.setenv("DEFAULT_AZURE_API_VERSION", "2024-01-01-preview")
    monkeypatch.setenv("DEFAULT_OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("DEFAULT_AZURE_API_KEY", "test-azure-key")
    monkeypatch.setenv("USD_TO_CNY_RATE", "7.2")
    monkeypatch.setenv("USD_TO_HKD_RATE", "7.7")
    config.get_settings.cache_clear()
    storage._storage_instance = None
    transcription._service_instance = None
    openai_client._factory_instance = DummyFactory()
    main_settings = config.get_settings()
    from app import main

    main.settings = main_settings


@pytest.fixture
def app_instance() -> FastAPI:
    from app.main import app

    return app


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = base64.b64encode(b"tester:secret").decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture
async def client(app_instance: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
