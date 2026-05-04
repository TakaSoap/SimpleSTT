from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile

from ..config import Settings, get_settings


TRANSCRIPTION_SAMPLE_RATE_HZ = 16_000
TRANSCRIPTION_BITRATE = "48k"


def get_duration_seconds(path: Path) -> Optional[float]:
    try:
        audio = MutagenFile(path)
        if audio is None:
            return None
        return float(getattr(audio.info, "length", None) or 0.0) or None
    except Exception:
        return None


def _resolve_ffmpeg_binary(settings: Optional[Settings] = None) -> Optional[Path]:
    settings = settings or get_settings()
    candidates: list[Path] = []

    if settings.ffmpeg_binary:
        candidates.append(settings.ffmpeg_binary)

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        candidates.append(Path(system_ffmpeg))

    for parent in Path(__file__).resolve().parents:
        shared_tools = parent / "shared" / "tools"
        if not shared_tools.is_dir():
            continue
        candidates.extend(sorted(shared_tools.glob("ffmpeg-*-static/ffmpeg"), reverse=True))

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def create_transcription_chunks(
    path: Path,
    output_dir: Path,
    *,
    chunk_duration_seconds: int,
    settings: Optional[Settings] = None,
) -> list[Path]:
    if chunk_duration_seconds <= 0:
        raise ValueError("chunk_duration_seconds must be greater than 0")

    settings = settings or get_settings()
    ffmpeg_binary = _resolve_ffmpeg_binary(settings)
    if ffmpeg_binary is None:
        raise RuntimeError("ffmpeg is required to split long audio files before transcription")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / "chunk-%03d.mp3"
    command = [
        str(ffmpeg_binary),
        "-v",
        "error",
        "-y",
        "-i",
        str(path),
        "-map",
        "0:a:0",
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(TRANSCRIPTION_SAMPLE_RATE_HZ),
        "-c:a",
        "libmp3lame",
        "-b:a",
        TRANSCRIPTION_BITRATE,
        "-f",
        "segment",
        "-segment_time",
        str(chunk_duration_seconds),
        "-reset_timestamps",
        "1",
        str(output_pattern),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "ffmpeg failed to split the uploaded audio"
        raise RuntimeError(message)

    chunk_paths = sorted(output_dir.glob("chunk-*.mp3"))
    if not chunk_paths:
        raise RuntimeError("ffmpeg did not produce any audio chunks")
    return chunk_paths
