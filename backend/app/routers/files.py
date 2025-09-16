from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..dependencies import CredentialsDep
from ..models.api import AnalyzeFileResponse, CostEstimate, FileMetadata
from ..services import audio, cost
from ..services.storage import get_storage, trigger_cleanup

router = APIRouter(prefix="/api/files", tags=["files"])


def _format_duration(seconds: Optional[float]) -> Optional[str]:
    if seconds is None:
        return None
    delta = timedelta(seconds=round(seconds))
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


@router.post("/analyze", response_model=AnalyzeFileResponse)
async def analyze_file(
    _: CredentialsDep,
    file: UploadFile = File(...),
    model: str = Form("gpt-4o-transcribe"),
) -> AnalyzeFileResponse:
    storage = get_storage()
    stored = await storage.save_upload(file)

    duration_seconds = audio.get_duration_seconds(stored.path)
    await storage.attach_metadata(stored.id, duration_seconds=duration_seconds)

    estimate = None
    if duration_seconds is not None:
        estimation = cost.estimate_cost(model=model, duration_seconds=duration_seconds)
        if estimation:
            estimate = CostEstimate(
                usd=round(estimation.usd, 4),
                hkd=round(estimation.hkd, 3),
                cny=round(estimation.cny, 3),
                duration_minutes=round(estimation.duration_minutes, 2),
            )

    trigger_cleanup()

    metadata = FileMetadata(
        file_id=stored.id,
        name=stored.original_name,
        size_bytes=stored.size_bytes,
        duration_seconds=duration_seconds,
        duration_text=_format_duration(duration_seconds),
        cost=estimate,
    )
    return AnalyzeFileResponse(file=metadata)


@router.delete("/{file_id}")
async def delete_file(_: CredentialsDep, file_id: str) -> dict[str, str]:
    storage = get_storage()
    await storage.delete_upload(file_id)
    return {"status": "deleted"}
