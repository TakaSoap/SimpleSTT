# Audio Transcription Web App — Implementation Guide

## Legacy Feature Parity Summary
- Dual provider support: OpenAI (model list) and Azure OpenAI (custom endpoint + deployment + version).
- API key validation via `models.list` sanity call.
- Drag & drop or manual selection of local audio/video files; show metadata, duration, and estimated OpenAI usage cost based on pricing table.
- Configurable language hints, prompt templates, and transcription models.
- Output formats: `text`, `json`, `verbose_json`, `srt`, `vtt` (latter three relevant to Whisper-compatible models).
- Optional streaming transcript updates (available for gpt-4o family only).
- Persisted transcription file saved alongside input and surfaced to user.
- Rich status/progress reporting and error handling.

## Technical Blueprint

### Overall Architecture
- **Frontend**: Vue 3 + TypeScript + Vite + Naive UI. SPA served by backend statics in production, separate dev server during development. Global UI mode (`advanced` / `basic`) is provided via `useAppMode` (see `frontend/src/composables/useAppMode.ts`) so the header toggle and transcription view share state.
- **Backend**: FastAPI + Pydantic Settings + Uvicorn. Provides REST + streaming responses, handles OpenAI/Azure SDK calls, file management, and auth.
- **Shared Contracts**: JSON DTOs defined in `backend/app/models/api.py` and mirrored TypeScript interfaces in `frontend/src/types/api.ts` to prevent drift.
- **Authentication**: HTTP Basic enforced on every API route via FastAPI dependency. Credentials stored in env (`APP_USERNAME`, `APP_PASSWORD`) hashed at startup using `bcrypt` or fallback to salted `secrets.compare_digest` if provided in clear text.
- **File Handling**: Uploaded files are written to a managed temp directory (`app.state.storage_dir/<uuid>`). Metadata cached alongside path. Completed transcripts saved in same folder with computed extension. Background task schedules cleanup after TTL.
- **Streaming**: `POST /api/transcriptions/stream` returns `text/event-stream`; backend streams incremental text chunks, final event includes download id. Frontend consumes via `EventSource` polyfill, updating transcript in real time.

### Backend Structure
```
backend/
  app/
    __init__.py
    main.py
    config.py           # Pydantic settings (auth creds, azure defaults, storage paths)
    dependencies.py     # Shared dependency providers (Basic auth, settings, OpenAI factory)
    routers/
      __init__.py
      auth.py           # /api/auth/login (ping), returns user meta
      files.py          # /api/files/analyze, /api/files/{id} deletion/metadata
      transcriptions.py # streaming + non-streaming transcription endpoints, downloads
    services/
      audio.py          # duration + metadata via mutagen, caching
      cost.py           # price calculation utilities
      storage.py        # File persistence / cleanup
      openai_client.py  # Provider abstraction factory (OpenAI vs Azure)
      transcription.py  # Orchestrates calls, handles streaming aggregator logic
    models/
      api.py            # Pydantic request/response schemas
    utils/
      responses.py      # Stream helpers (SSE)
  tests/
    conftest.py
    test_auth.py
    test_analyze.py
    test_transcriptions.py
```
- **Key Endpoints**
  - `POST /api/auth/login` → validates Basic credentials and returns session info.
  - `GET /api/options` → languages, models, output formats, streamable model IDs.
  - `POST /api/keys/validate` → body contains provider + key details; backend calls OpenAI/Azure `models.list()` (mocked in tests).
  - `POST /api/files/analyze` → multipart upload, returns `{file_id, metadata, cost}`.
  - `DELETE /api/files/{file_id}` → cancel selection, remove temp file (used when user cancels).
  - `POST /api/transcriptions` → JSON body referencing `file_id` and transcription options; returns final transcript + download URL; non-streaming path.
  - `POST /api/transcriptions/stream` → SSE endpoint; yields incremental text updates and final payload (also persists to disk).
  - `GET /api/transcriptions/{transcription_id}/download` → `FileResponse` for saved transcript.
- **Testing Strategy**
  - Use `pytest` + `httpx.AsyncClient` for API tests.
  - Stub OpenAI/Azure clients via FastAPI dependency override to avoid network calls.
  - Generate tiny WAV fixture on the fly for metadata detection, verifying duration & cost calculations.
  - Ensure cleanup tasks remove temp files (assert via filesystem state).

### Frontend Structure
```
frontend/
  src/
    main.ts
    App.vue
    router.ts (simple auth-guarded routes)
    api/
      client.ts         # fetch wrapper attaching Basic auth header
      endpoints.ts      # typed functions per backend route
    components/
      AuthLayout.vue
      ProviderSettings.vue
      FileUploadCard.vue
      LanguageSelect.vue
      PromptTemplates.vue
      ResultPanel.vue
    composables/
      useAuth.ts        # manages credentials in reactive storage/localStorage
      useTranscription.ts
      useAppMode.ts
    types/
      api.ts            # TS interfaces mirroring backend schemas
    views/
      LoginView.vue
      TranscriptionView.vue
  tests/
    unit/
      cost.spec.ts
      promptTemplates.spec.ts
```
- Naive UI components: `n-form`, `n-input`, `n-select`, `n-upload`, `n-progress`, `n-card`, `n-message-provider`, `n-switch` (mode toggle).
- State management via Vue's Composition API + provide/inject (`useAppMode` exposes the advanced/basic switch, shared by `App.vue` and `TranscriptionView.vue`). No external store needed.
- File flow: upon upload, call `/api/files/analyze`, store `fileId` and metadata. In basic mode the view forces Azure provider defaults and text output before calling the transcription endpoint. Result panel handles download link.
- Basic Auth: login form collects username/password, stores base64 token; `api/client.ts` attaches `Authorization` header to each request.
- Streaming consumption: use `EventSource` (with polyfill for POST by first `fetch` to create event stream using `ReadableStream`). Fallback to non-streaming when browsers don't support streaming fetch.

### Testing Plan (Frontend)
- Unit-test cost estimator composable to mirror backend results ensuring UI display parity.
- Component snapshot/DOM tests for login validation and provider toggling using `@vue/test-utils` + `vitest`.
- Mock fetch for API tests.

### Implementation Phases
1. **Bootstrap** backend project skeleton with configs, dependencies, Basic auth, and placeholder endpoints (return TODO). Add pytest infrastructure + fixtures.
2. Implement file storage + audio metadata service + `/api/files/analyze`; include tests.
3. Implement key validation & OpenAI provider abstraction (with test stubs) + `/api/options` endpoint.
4. Build transcription service for non-streaming path; add download handling & tests using mocks.
5. Extend to streaming SSE output; add tests ensuring event format & storage.
6. Create frontend Vite project, configure Naive UI + router + layout scaffolding.
7. Implement login flow & API client with credential persistence; unit tests for auth composable.
8. Build transcription UI (forms, upload, templates), integrate API calls, handle streaming updates.
9. Add frontend tests (Vitest) for critical flows.
10. Final QA: run backend + frontend tests, lint (ESLint/Prettier), update README with run instructions.
11. Manual verification instructions + future enhancements recorded in README.

### Risk & Mitigation Notes
- **OpenAI SDK**: ensure streaming responses are consumed correctly; use official `openai` package's async iterables. Provide fallback to non-streaming with error message.
- **Large files**: use chunked writing avoiding memory spikes; enforce max upload size via settings.
- **Security**: Basic auth credentials hashed; enforce HTTPS recommendation in docs; avoid persisting API keys server-side.
- **Cross-origin**: Configure CORS for local dev (frontend on Vite port). Production uses same origin served by FastAPI static.
