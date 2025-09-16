import secrets
from typing import Annotated, AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import Settings, get_settings

security = HTTPBasic()


def get_basic_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> HTTPBasicCredentials:
    settings = get_settings()

    username_valid = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.app_username.encode("utf-8"),
    )
    password_valid = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.app_password.encode("utf-8"),
    )

    if not (username_valid and password_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


CredentialsDep = Annotated[HTTPBasicCredentials, Depends(get_basic_credentials)]


def get_settings_dep() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    yield
