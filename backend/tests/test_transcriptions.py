from __future__ import annotations

import json
import struct
import wave

import pytest


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
