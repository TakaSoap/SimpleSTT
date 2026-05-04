from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import AsyncIterator, Optional

from openai import APIStatusError

from ..config import Settings, get_settings
from ..models.api import ProviderConfig, TranscriptionRequest, ProviderEnum
from .openai_client import (
    OpenAIClientFactory,
    get_client_factory,
    resolve_provider_config,
)
from . import audio
from .storage import StorageManager, TranscriptFile, get_storage


@dataclass
class TranscriptionOutput:
    transcript: TranscriptFile
    display_text: str
    raw_content: str


class TranscriptionProviderError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class TranscriptionService:
    def __init__(
        self,
        *,
        factory: Optional[OpenAIClientFactory] = None,
        storage: Optional[StorageManager] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.factory = factory or get_client_factory()
        self.storage = storage or get_storage()
        self.settings = settings or get_settings()

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

        try:
            return await asyncio.to_thread(_execute)
        except APIStatusError as exc:
            detail = self._extract_provider_error_message(exc)
            status_code = exc.status_code if isinstance(exc.status_code, int) and 400 <= exc.status_code < 500 else 502
            raise TranscriptionProviderError(detail, status_code=status_code) from exc

    def _extract_provider_error_message(self, exc: APIStatusError) -> str:
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            error = body.get("error")
            if isinstance(error, dict):
                message = error.get("message")
                if isinstance(message, str) and message.strip():
                    return message.strip()
            detail = body.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail.strip()
        message = str(exc).strip()
        if message:
            return message
        return "Upstream transcription request failed"

    async def _transcribe_single_file(
        self,
        provider: ProviderConfig,
        request: TranscriptionRequest,
        file_path: Path,
    ) -> tuple[str, str]:
        params = self._build_params(request, file_path)
        response = await self._call_transcription(provider, params)
        return self._parse_response(response, request.format)

    def _should_chunk_request(
        self,
        request: TranscriptionRequest,
        provider: ProviderConfig,
        duration_seconds: Optional[float],
    ) -> bool:
        return (
            provider.provider is ProviderEnum.AZURE
            and request.format == "text"
            and duration_seconds is not None
            and duration_seconds > self.settings.transcription_chunk_duration_seconds
        )

    async def _transcribe_chunked(
        self,
        provider: ProviderConfig,
        request: TranscriptionRequest,
        source_path: Path,
    ) -> tuple[str, str]:
        with TemporaryDirectory(prefix="sst-transcription-") as temp_dir:
            temp_path = Path(temp_dir)
            try:
                chunk_paths = await asyncio.to_thread(
                    audio.create_transcription_chunks,
                    source_path,
                    temp_path,
                    chunk_duration_seconds=self.settings.transcription_chunk_duration_seconds,
                    settings=self.settings,
                )
            except RuntimeError as exc:
                raise ValueError(str(exc)) from exc

            parts: list[str] = []
            for chunk_path in chunk_paths:
                chunk_text, _ = await self._transcribe_single_file(provider, request, chunk_path)
                cleaned_text = chunk_text.strip()
                if cleaned_text:
                    parts.append(cleaned_text)

        combined_text = "\n\n".join(parts).strip()
        return combined_text, combined_text

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

        duration_seconds = stored.duration_seconds or audio.get_duration_seconds(stored.path)
        if self._should_chunk_request(request, resolved_provider, duration_seconds):
            display_text, raw_content = await self._transcribe_chunked(resolved_provider, request, stored.path)
        else:
            display_text, raw_content = await self._transcribe_single_file(resolved_provider, request, stored.path)

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
