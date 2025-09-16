from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import CredentialsDep
from ..models.api import ValidateKeyRequest, ValidateKeyResponse
from ..services.openai_client import get_client_factory, resolve_provider_config

router = APIRouter(prefix="/api/keys", tags=["keys"])


@router.post("/validate", response_model=ValidateKeyResponse)
async def validate_key(_: CredentialsDep, payload: ValidateKeyRequest) -> ValidateKeyResponse:
    factory = get_client_factory()
    try:
        resolved_provider, used_default = resolve_provider_config(payload.provider)
        factory.validate(resolved_provider)
        message = "Key is valid"
        if used_default:
            message = "Using server default API key"
        return ValidateKeyResponse(
            ok=True,
            provider=payload.provider.provider,
            message=message,
            used_default=used_default,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:  # broad to surface API errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
