from __future__ import annotations

import asyncio
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from fastapi import UploadFile

from ..config import Settings, get_settings


@dataclass
class StoredFile:
    id: str
    path: Path
    original_name: str
    size_bytes: int
    content_type: Optional[str]
    created_at: datetime
    duration_seconds: Optional[float] = None


@dataclass
class TranscriptFile(StoredFile):
    format: str = "text"


class StorageManager:
    def __init__(self, base_dir: Path, ttl_seconds: int) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(seconds=ttl_seconds)
        self._files: Dict[str, StoredFile] = {}
        self._transcripts: Dict[str, TranscriptFile] = {}
        self._lock = asyncio.Lock()

    async def save_upload(self, file: UploadFile) -> StoredFile:
        file_id = uuid.uuid4().hex
        created_at = datetime.now(timezone.utc)
        destination = self.base_dir / f"{file_id}_{file.filename}"
        size = 0
        destination.parent.mkdir(parents=True, exist_ok=True)

        with destination.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                buffer.write(chunk)

        stored = StoredFile(
            id=file_id,
            path=destination,
            original_name=file.filename or "audio",
            size_bytes=size,
            content_type=file.content_type,
            created_at=created_at,
        )
        async with self._lock:
            self._files[file_id] = stored
        await file.close()
        return stored

    async def attach_metadata(self, file_id: str, *, duration_seconds: Optional[float]) -> None:
        async with self._lock:
            if file_id in self._files:
                self._files[file_id].duration_seconds = duration_seconds

    async def get_upload(self, file_id: str) -> StoredFile:
        async with self._lock:
            stored = self._files.get(file_id)
        if not stored:
            raise FileNotFoundError(file_id)
        return stored

    async def delete_upload(self, file_id: str) -> None:
        async with self._lock:
            stored = self._files.pop(file_id, None)
        if stored and stored.path.exists():
            stored.path.unlink(missing_ok=True)

    async def save_transcript(self, *, source: StoredFile, extension: str, content: str, format_name: str) -> TranscriptFile:
        transcript_id = uuid.uuid4().hex
        destination = source.path.with_suffix(extension)
        destination.write_text(content, encoding="utf-8")
        transcript = TranscriptFile(
            id=transcript_id,
            path=destination,
            original_name=destination.name,
            size_bytes=destination.stat().st_size,
            content_type="text/plain",
            created_at=datetime.now(timezone.utc),
            duration_seconds=source.duration_seconds,
            format=format_name,
        )
        async with self._lock:
            self._transcripts[transcript_id] = transcript
        return transcript

    async def get_transcript(self, transcript_id: str) -> TranscriptFile:
        async with self._lock:
            stored = self._transcripts.get(transcript_id)
        if not stored:
            raise FileNotFoundError(transcript_id)
        return stored

    async def delete_transcript(self, transcript_id: str) -> None:
        async with self._lock:
            stored = self._transcripts.pop(transcript_id, None)
        if stored and stored.path.exists():
            stored.path.unlink(missing_ok=True)

    async def cleanup(self) -> None:
        cutoff = datetime.now(timezone.utc) - self.ttl
        async with self._lock:
            file_items = list(self._files.items())
            transcript_items = list(self._transcripts.items())
        for file_id, stored in file_items:
            if stored.created_at < cutoff:
                await self.delete_upload(file_id)
        for transcript_id, stored in transcript_items:
            if stored.created_at < cutoff:
                await self.delete_transcript(transcript_id)

    async def purge_all(self) -> None:
        async with self._lock:
            self._files.clear()
            self._transcripts.clear()
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)


_storage_instance: Optional[StorageManager] = None


def get_storage(settings: Optional[Settings] = None) -> StorageManager:
    global _storage_instance
    if _storage_instance is None:
        settings = settings or get_settings()
        _storage_instance = StorageManager(settings.storage_dir, settings.storage_ttl_seconds)
    return _storage_instance


def trigger_cleanup() -> None:
    storage = get_storage()
    asyncio.create_task(storage.cleanup())
