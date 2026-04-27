from __future__ import annotations

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
from ..services.transcription import get_transcription_service

router = APIRouter(prefix="/api/transcriptions", tags=["transcriptions"])


@router.post("", response_model=TranscriptionResponse)
async def create_transcription(_: CredentialsDep, payload: TranscriptionRequest) -> TranscriptionResponse:
    service = get_transcription_service()
    try:
        output = await service.transcribe(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

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
    try:
        output, stream_iter = await service.transcribe_stream(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    download_url = f"/api/transcriptions/{output.transcript.id}/download"

    async def event_generator():
        async for chunk in stream_iter:
            event = StreamEvent(type="chunk", data=chunk)
            yield event.model_dump_sse()
        final_event = StreamEvent(
            type="complete",
            data=output.display_text,
            download_url=download_url,
            transcript_id=output.transcript.id,
        )
        yield final_event.model_dump_sse()

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
