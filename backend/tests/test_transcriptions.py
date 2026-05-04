from __future__ import annotations

import asyncio
import json
import struct
import wave

import pytest

from app.services import audio, storage, transcription


def _make_audio(path):
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        silence = struct.pack("<h", 0)
        for _ in range(8000):
            wav.writeframes(silence)


async def _upload_sample(client, tmp_path, auth_headers):
    audio_path = tmp_path / "clip.wav"
    _make_audio(audio_path)
    with audio_path.open("rb") as audio_file:
        response = await client.post(
            "/api/files/analyze",
            headers=auth_headers,
            files={"file": ("clip.wav", audio_file, "audio/wav")},
            data={"model": "gpt-4o-transcribe"},
        )
    payload = response.json()
    return payload["file"]["file_id"]


@pytest.mark.asyncio
async def test_transcription_creates_downloadable_file(client, tmp_path, auth_headers):
    file_id = await _upload_sample(client, tmp_path, auth_headers)

    payload = {
        "file_id": file_id,
        "model": "gpt-4o-transcribe",
        "format": "text",
        "language": None,
        "prompt": "",
        "stream": False,
        "provider": {"provider": "openai"},
    }

    response = await client.post(
        "/api/transcriptions",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 200
    result = response.json()["result"]

    download_response = await client.get(result["download_url"], headers=auth_headers)
    assert download_response.status_code == 200
    assert "dummy transcript" in download_response.text


@pytest.mark.asyncio
async def test_streaming_endpoint_provides_events(client, tmp_path, auth_headers):
    file_id = await _upload_sample(client, tmp_path, auth_headers)
    payload = {
        "file_id": file_id,
        "model": "gpt-4o-transcribe",
        "format": "text",
        "language": None,
        "prompt": "",
        "stream": True,
        "provider": {"provider": "openai"},
    }

    async with client.stream(
        "POST",
        "/api/transcriptions/stream",
        headers=auth_headers,
        json=payload,
    ) as stream_response:
        assert stream_response.status_code == 200
        body = ""
        async for chunk in stream_response.aiter_text():
            body += chunk

    events = [line for line in body.splitlines() if line.startswith("data:")]
    assert any("chunk" in line for line in events)
    final_line = events[-1]
    data = json.loads(final_line.replace("data: ", ""))
    assert data["type"] == "complete"
    transcript_id = data["transcript_id"]

    download_response = await client.get(f"/api/transcriptions/{transcript_id}/download", headers=auth_headers)
    assert download_response.status_code == 200
    assert "dummy transcript" in download_response.text


@pytest.mark.asyncio
async def test_streaming_endpoint_sends_heartbeat_before_completion(client, tmp_path, auth_headers, monkeypatch):
    file_id = await _upload_sample(client, tmp_path, auth_headers)

    original_service = transcription.get_transcription_service()

    class SlowService:
        async def transcribe(self, request):  # noqa: ANN001
            await asyncio.sleep(0.05)
            return await original_service.transcribe(request)

        async def transcribe_stream(self, request):  # noqa: ANN001
            raise AssertionError("stream endpoint should call transcribe")

    monkeypatch.setattr(transcription, "_service_instance", SlowService())

    payload = {
        "file_id": file_id,
        "model": "gpt-4o-transcribe",
        "format": "text",
        "language": None,
        "prompt": "",
        "stream": True,
        "provider": {"provider": "openai"},
    }

    async with client.stream(
        "POST",
        "/api/transcriptions/stream",
        headers=auth_headers,
        json=payload,
    ) as stream_response:
        assert stream_response.status_code == 200
        chunks = []
        async for chunk in stream_response.aiter_text():
            chunks.append(chunk)
            if len(chunks) == 1:
                break

    assert chunks
    assert '"type": "chunk"' in chunks[0]


@pytest.mark.asyncio
async def test_provider_bad_request_is_returned_to_client(client, auth_headers, monkeypatch):
    class FailingService:
        async def transcribe(self, request):  # noqa: ANN001
            raise transcription.TranscriptionProviderError(
                "Audio file might be corrupted or unsupported",
                status_code=400,
            )

        async def transcribe_stream(self, request):  # noqa: ANN001
            raise AssertionError("streaming should not be called")

    monkeypatch.setattr(transcription, "_service_instance", FailingService())
    payload = {
        "file_id": "missing",
        "model": "gpt-4o-transcribe",
        "format": "text",
        "language": None,
        "prompt": "",
        "stream": False,
        "provider": {"provider": "openai"},
    }

    response = await client.post(
        "/api/transcriptions",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Audio file might be corrupted or unsupported"


@pytest.mark.asyncio
async def test_long_azure_audio_is_split_into_chunks(client, tmp_path, auth_headers, monkeypatch):
    file_id = await _upload_sample(client, tmp_path, auth_headers)
    await storage.get_storage().attach_metadata(file_id, duration_seconds=1300)

    chunk_a = tmp_path / "chunk-a.wav"
    chunk_b = tmp_path / "chunk-b.wav"
    _make_audio(chunk_a)
    _make_audio(chunk_b)

    def fake_create_transcription_chunks(path, output_dir, *, chunk_duration_seconds, settings=None):  # noqa: ANN001, ARG001
        assert chunk_duration_seconds == 1200
        return [chunk_a, chunk_b]

    monkeypatch.setattr(audio, "create_transcription_chunks", fake_create_transcription_chunks)

    payload = {
        "file_id": file_id,
        "model": "gpt-4o-transcribe",
        "format": "text",
        "language": None,
        "prompt": "",
        "stream": False,
        "provider": {
            "provider": "azure",
            "endpoint": "https://example.openai.azure.com/",
            "deployment_id": "test-deploy",
            "api_version": "2024-01-01-preview",
        },
    }

    response = await client.post(
        "/api/transcriptions",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 200

    result = response.json()["result"]
    assert result["text_preview"] == "dummy transcript\n\ndummy transcript"

    download_response = await client.get(result["download_url"], headers=auth_headers)
    assert download_response.status_code == 200
    assert download_response.text == "dummy transcript\n\ndummy transcript"
