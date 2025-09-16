from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from ..config import get_settings


_PRICE_PER_MINUTE: Final[dict[str, float]] = {
    "gpt-4o-transcribe": 0.006,
    "gpt-4o-mini-transcribe": 0.003,
    "whisper-1": 0.006,
}


@dataclass
class CostEstimate:
    usd: float
    hkd: float
    cny: float
    duration_minutes: float


def estimate_cost(model: str, duration_seconds: Optional[float]) -> Optional[CostEstimate]:
    if duration_seconds is None:
        return None
    price = _PRICE_PER_MINUTE.get(model)
    if price is None:
        return None
    settings = get_settings()
    duration_minutes = duration_seconds / 60
    usd = price * duration_minutes
    hkd = usd * settings.usd_to_hkd_rate
    cny = usd * settings.usd_to_cny_rate
    return CostEstimate(usd=usd, hkd=hkd, cny=cny, duration_minutes=duration_minutes)
