from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse

from ..dependencies import CredentialsDep
from ..models.api import (
    StreamEvent,
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionResult,
)
from ..services.storage import get_storage
from ..services.transcription import TranscriptionProviderError, get_transcription_service

router = APIRouter(prefix="/api/transcriptions", tags=["transcriptions"])
logger = logging.getLogger(__name__)

STREAM_CHUNK_SIZE = 500
STREAM_HEARTBEAT_INTERVAL_SECONDS = 10


async def _stream_text_chunks(text: str, chunk_size: int = STREAM_CHUNK_SIZE):
    for start in range(0, len(text), chunk_size):
        await asyncio.sleep(0)
        yield text[start : start + chunk_size]


def _build_error_event(message: str) -> str:
    return StreamEvent(type="error", data=message).model_dump_sse()


@router.post("", response_model=TranscriptionResponse)
async def create_transcription(_: CredentialsDep, payload: TranscriptionRequest) -> TranscriptionResponse:
    service = get_transcription_service()
    try:
        output = await service.transcribe(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TranscriptionProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    download_url = f"/api/transcriptions/{output.transcript.id}/download"
    preview = output.display_text
    return TranscriptionResponse(
        result=TranscriptionResult(
            transcript_id=output.transcript.id,
            format=output.transcript.format,
            text_preview=preview,
            download_url=download_url,
        )
    )


@router.post("/stream")
async def stream_transcription(_: CredentialsDep, payload: TranscriptionRequest) -> StreamingResponse:
    if payload.format != "text":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Streaming仅支持文本格式")

    service = get_transcription_service()

    async def event_generator():
        task = asyncio.create_task(service.transcribe(payload))
        try:
            yield StreamEvent(type="chunk", data="").model_dump_sse()

            while True:
                try:
                    output = await asyncio.wait_for(
                        asyncio.shield(task),
                        timeout=STREAM_HEARTBEAT_INTERVAL_SECONDS,
                    )
                    break
                except asyncio.TimeoutError:
                    yield StreamEvent(type="chunk", data="").model_dump_sse()
        except FileNotFoundError as exc:
            yield _build_error_event(str(exc))
            return
        except ValueError as exc:
            yield _build_error_event(str(exc))
            return
        except TranscriptionProviderError as exc:
            yield _build_error_event(str(exc))
            return
        except Exception:
            logger.exception("Streaming transcription failed")
            yield _build_error_event("Transcription failed")
            return
        else:
            download_url = f"/api/transcriptions/{output.transcript.id}/download"
            async for chunk in _stream_text_chunks(output.display_text):
                event = StreamEvent(type="chunk", data=chunk)
                yield event.model_dump_sse()
            final_event = StreamEvent(
                type="complete",
                data=output.display_text,
                download_url=download_url,
                transcript_id=output.transcript.id,
            )
            yield final_event.model_dump_sse()
        finally:
            if not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{transcript_id}/download")
async def download_transcript(_: CredentialsDep, transcript_id: str) -> FileResponse:
    storage = get_storage()
    try:
        transcript = await storage.get_transcript(transcript_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return FileResponse(
        transcript.path,
        media_type="text/plain",
        filename=transcript.original_name,
    )
