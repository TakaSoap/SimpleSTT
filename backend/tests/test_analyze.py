from __future__ import annotations

import struct
import wave

import pytest


def _create_wave_file(path):
    sample_rate = 16000
    duration_seconds = 1
    total_frames = sample_rate * duration_seconds
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        silence_frame = struct.pack("<h", 0)
        for _ in range(total_frames):
            wav.writeframes(silence_frame)


@pytest.mark.asyncio
async def test_analyze_file_returns_metadata(client, tmp_path, auth_headers):
    audio_path = tmp_path / "sample.wav"
    _create_wave_file(audio_path)

    with audio_path.open("rb") as audio_file:
        response = await client.post(
            "/api/files/analyze",
            headers=auth_headers,
            files={"file": ("sample.wav", audio_file, "audio/wav")},
            data={"model": "gpt-4o-transcribe"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["file"]["file_id"]
    assert payload["file"]["size_bytes"] > 0
    assert payload["file"]["duration_seconds"] is not None
    assert payload["file"]["cost"]["usd"] > 0
    assert payload["file"]["cost"]["hkd"] > 0
    assert payload["file"]["cost"]["cny"] > 0
