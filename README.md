# Audio Transcription Web Application

Modern web experience for the legacy Tkinter transcription tool, rebuilt with Vue 3 + Naive UI on the frontend and FastAPI on the backend. Provides OpenAI & Azure OpenAI transcription workflows, file analysis, cost estimation, real-time streaming, and secure access via HTTP Basic authentication.

## Features
- Responsive Vue interface with Naive UI components and drag-and-drop uploads.
- Internationalised interface with English, 简体中文, and 繁體中文 support.
- Automatic dark/light theme following system settings with manual override.
- Provider-aware configuration (OpenAI / Azure OpenAI) with live API key validation.
- Global *Advanced / Basic* mode toggle. Advanced exposes every provider and formatting control. Basic collapses settings, uses the server's Azure defaults, and lets users simply upload & transcribe.
- Optional server-managed API keys defined via `.env`; when the UI leaves fields blank, the backend securely applies the default key.
- Detailed file analysis (size, duration) and cost estimation using configurable rate tables.
- Language selection, prompt presets, model and output format controls.
- Streaming and non-streaming transcription modes with downloadable transcript artifacts.
- Simple HTTP Basic auth with configurable credentials.
- Comprehensive automated tests for backend (pytest + httpx) and frontend (Vitest + Vue Test Utils).

## Architecture Overview
- **Frontend**: Vite-powered Vue 3 SPA (TypeScript). Uses Naive UI for layout, `fetch` API for backend integration, and Composition API composables for state.
- **Backend**: FastAPI application organized by routers/services. Uses Pydantic settings, OpenAI Python SDK, Azure OpenAI SDK, and Mutagen for audio metadata.
- **Communication**: REST JSON endpoints plus Server-Sent Events for streaming transcripts. Shared DTOs documented in `backend/app/models/api.py` and mirrored in `frontend/src/types`.
- **Storage**: Uploaded files saved in a temporary storage directory with automatic cleanup via background tasks; transcripts written to disk and exposed via download endpoint.
- **Security**: HTTP Basic authentication enforced globally. Credentials configured via environment variables.

Refer to [AGENT.md](AGENT.md) for the full engineering plan and internal design notes.

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- `uv` or `pip` for Python dependency management
- `npm`/`pnpm`/`yarn` (examples use `npm`)

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # generated via uv/poetry export
cp .env.example .env              # fill APP_USERNAME, APP_PASSWORD, etc.
uvicorn app.main:app --reload
```
The API will default to `http://localhost:8000`. Interactive docs live at `/docs` (requires Basic auth).

### Frontend Setup
```bash
cd frontend
pnpm install
pnpm dev
```

You can customise the default locale and theme via `VITE_DEFAULT_LOCALE` and `VITE_DEFAULT_THEME` in `frontend/.env`.
The dev server runs on `http://localhost:5173`. Configure the backend base URL via `frontend/.env` (see `.env.example`). During development enable CORS in backend settings.

The header switch toggles between **Advanced** (full settings) and **Basic** (Azure defaults only) modes. Basic mode assumes valid Azure defaults are configured in the backend `.env`.

### Testing
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
pnpm test --run
```

## Deployment Notes
- Serve the built frontend via FastAPI's static files middleware for same-origin auth simplicity (`npm run build` → copy `dist` into backend `static/`).
- Use HTTPS in production; Basic auth transmits credentials per request.
- Configure environment variables for credentials, storage paths, and provider defaults. Rotate Basic auth passwords regularly.
  - Backend defaults such as provider, Azure endpoint, and currency conversion ratios are configurable via `.env`.

## Roadmap & Enhancements
1. Persist user preferences (prompt, language) per account.
2. Add OAuth or SSO provider in place of Basic auth for production use.
3. Provide job history with search and re-download.
4. Integrate chunked uploads for very large media files.
5. Support other LLM providers when available via plugin architecture.
