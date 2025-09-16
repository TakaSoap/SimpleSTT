from __future__ import annotations

from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile


def get_duration_seconds(path: Path) -> Optional[float]:
    try:
        audio = MutagenFile(path)
        if audio is None:
            return None
        return float(getattr(audio.info, "length", None) or 0.0) or None
    except Exception:
        return None
