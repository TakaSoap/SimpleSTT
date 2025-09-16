from fastapi import APIRouter, Depends

from ..dependencies import CredentialsDep

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(_: CredentialsDep) -> dict[str, str]:
    return {"status": "authenticated"}
