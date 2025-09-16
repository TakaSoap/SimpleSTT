from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional

from ..models.api import ProviderConfig, TranscriptionRequest, ProviderEnum
from .openai_client import (
    OpenAIClientFactory,
    get_client_factory,
    resolve_provider_config,
)
from .storage import StorageManager, TranscriptFile, get_storage


@dataclass
class TranscriptionOutput:
    transcript: TranscriptFile
    display_text: str
    raw_content: str


class TranscriptionService:
    def __init__(self, *, factory: Optional[OpenAIClientFactory] = None, storage: Optional[StorageManager] = None) -> None:
        self.factory = factory or get_client_factory()
        self.storage = storage or get_storage()

    def _build_params(self, request: TranscriptionRequest, file_path: Path) -> dict[str, object]:
        params: dict[str, object] = {
            "model": request.model,
            "response_format": request.format,
        }
        if request.prompt:
            params["prompt"] = request.prompt
        if request.language:
            params["language"] = request.language
        params["file"] = file_path.open("rb")
        return params

    async def _call_transcription(self, provider: ProviderConfig, params: dict[str, object]) -> object:
        client = self.factory.create(provider)

        def _execute() -> object:
            with params["file"] as file_handle:  # type: ignore[abstract]
                params_copy = params.copy()
                params_copy["file"] = file_handle
                return client.audio.transcriptions.create(**params_copy)

        return await asyncio.to_thread(_execute)

    def _parse_response(self, response: object, response_format: str) -> tuple[str, str]:
        if response_format == "text":
            text = getattr(response, "text", None)
            if isinstance(response, str):
                text = response
            if text is None:
                text = str(response)
            return text, text

        if response_format in {"json", "verbose_json"}:
            model_dump_fn = getattr(response, "model_dump", None)
            if callable(model_dump_fn):
                data = model_dump_fn()
                raw = json.dumps(data, ensure_ascii=False, indent=2)
                text_from_data = data.get("text") if isinstance(data, dict) else None
                text = text_from_data or getattr(response, "text", None) or raw
                return str(text), raw
            model_dump_json_fn = getattr(response, "model_dump_json", None)
            if callable(model_dump_json_fn):
                raw = model_dump_json_fn(indent=2)
                text = getattr(response, "text", None) or raw
                return text, raw
            if hasattr(response, "to_dict"):
                data = response.to_dict()
                raw = json.dumps(data, ensure_ascii=False, indent=2)
                text = data.get("text") if isinstance(data, dict) else raw
                text = text or raw
                return str(text), raw
            if isinstance(response, (dict, list)):
                raw = json.dumps(response, ensure_ascii=False, indent=2)
                return raw, raw
            raw = str(response)
            return raw, raw

        if response_format in {"srt", "vtt"}:
            if isinstance(response, str):
                return response, response
            text = getattr(response, "text", None) or str(response)
            return text, text

        return str(response), str(response)

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionOutput:
        stored = await self.storage.get_upload(request.file_id)
        resolved_provider, _ = resolve_provider_config(request.provider)
        if resolved_provider.provider is ProviderEnum.AZURE and request.format != "text":
            raise ValueError("Azure OpenAI currently supports only plain text output")
        params = self._build_params(request, stored.path)
        response = await self._call_transcription(resolved_provider, params)
        display_text, raw_content = self._parse_response(response, request.format)

        extension_map = {
            "text": ".txt",
            "json": ".json",
            "verbose_json": ".json",
            "srt": ".srt",
            "vtt": ".vtt",
        }
        extension = extension_map.get(request.format, ".txt")
        transcript = await self.storage.save_transcript(
            source=stored,
            extension=extension,
            content=raw_content,
            format_name=request.format,
        )
        return TranscriptionOutput(transcript=transcript, display_text=display_text, raw_content=raw_content)

    async def transcribe_stream(self, request: TranscriptionRequest) -> tuple[TranscriptionOutput, AsyncIterator[str]]:
        output = await self.transcribe(request)

        async def _chunked_stream(text: str, chunk_size: int = 500) -> AsyncIterator[str]:
            for start in range(0, len(text), chunk_size):
                await asyncio.sleep(0)
                yield text[start : start + chunk_size]

        return output, _chunked_stream(output.display_text)


_service_instance: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    global _service_instance
    if _service_instance is None:
        _service_instance = TranscriptionService()
    return _service_instance
