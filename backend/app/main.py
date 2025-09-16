from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .dependencies import lifespan
from .routers import auth, files, keys, options, transcriptions


settings = get_settings()
app = FastAPI(
    title="Audio Transcription API",
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(options.router)
app.include_router(keys.router)
app.include_router(files.router)
app.include_router(transcriptions.router)


@app.get("/health", tags=["health"])
async def health(settings_dep: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "environment": settings_dep.environment}


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_app() -> FastAPI:
    return app
