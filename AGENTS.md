# Animal Shelter API — AGENTS.md

## Stack
FastAPI · SQLAlchemy 2 async · asyncpg · PostgreSQL · Alembic · Pydantic v2 · Poetry · starlette-admin · httpx-oauth (Google) · python-jose · bcrypt · Redis (fastapi-cache2) · Stripe · MinIO (S3) · LiveKit (voice) · Anthropic/OpenAI SDKs · Python 3.12

## Layout
```
app/
  core/       config.py · dependencies.py · security.py · cookies.py · exceptions.py · error_codes.py
              oauth.py · logger.py · db.py · minio.py · anthropic/ · openai/ · prompts/
  db/
    enums.py  # Gender, TokenType, Currency, InvoiceStatus, Locale, MessageRole
    models/   base.py · associations.py · user.py · role.py · permission.py · resource.py
              refresh_token.py · oauth_account.py · animal.py · health_log.py · invoice.py
              stripe_event.py · chat_session.py · chat_message.py · translation_base.py
              __init__.py (all FastCRUD instances)
    mixins.py # IDMixin (UUID PK) · TimestampMixin
    session.py
  schemas/    animal · auth · chat · livekit · permission · resource · role · stripe · user
  services/   ai · animal · auth · chat_session · health_log · image · invoice · live_kit
              minio · permission · redis · refresh_token · resource · role · user
              __init__.py (DI factories)
  routers/v1/ animal · anthropic_chat · auth · health_log · image · permission · resource
              role · stripe · users
  livekit_worker/  entrypoint.py · dependencies.py · db.py · tools.py · persistence/  (separate LiveKit agent worker process)
  ws/         server.py (AsyncServer + AsyncRedisManager) · auth.py (get_current_principal) · events.py (@sio.event handlers) · rooms.py
  main.py     # lifespan, CORS, SessionMiddleware, CustomError handler, stripe.api_key
  admin/      setup.py · views.py · auth.py
alembic/
docker/       docker-compose.yml · livekit.yaml
tests/
```

## Auth
JWT access (HS256) + opaque refresh token (HttpOnly cookie, sha256 hash in DB, rotation+reuse-revoke chain) + Google OAuth2.

**JWT claims**: `sub, scopes[], permissions_version, is_superuser, type="access", iat, exp`
**Refresh cookie**: `httponly=True, secure=COOKIE_SECURE (default True), samesite="strict", path="/api/v1/auth", domain=COOKIE_DOMAIN`

**`get_current_principal` flow**: decode JWT → assert `type=="access"` → Redis `permissions_version:{user_id}` (miss → DB, cache 1h; `token.pv < current` → 401) → return `Principal` (no ORM row).

**In-flight invalidation**: role/perm mutations increment `permissions_version` in same commit, then delete Redis key. Stale tokens 401 → client calls `/auth/refresh`.

**Protecting endpoints:**
```python
_ = Depends(require_scopes(f"{resource.name}:{action}"))  # e.g. "animals:read" — action is a free string, not an enum
_ = Depends(require_roles("vet"))
_ = Depends(require_superuser)
```

## RBAC
Users ⇄ Roles ⇄ Permissions (M2M, runtime-editable, all real/active tables — none of this is legacy). `Permission.action` is a free-text string (`String(20)`, unique per `resource_id`), not an enum. Scope = `Resource.name:Permission.action` (e.g. `animals:read`), exposed via `Permission.scope` property. Resource is a first-class DB table. M2M writes use `selectinload`/`lazy="selectin"` in services.

## Stripe / Invoices
`Invoice`: `animal_id, amount_in_cents, status(InvoiceStatus), currency(Currency), user_id` + M2M `health_logs`.
`StripeEvent`: idempotency log, keyed by Stripe event id.

See `INSIGHTS.md` for a known gap in this flow (webhook idempotency is check-then-insert, not atomic) before touching `handle_webhook`.

Webhook route (`POST /webhook`) is **public** — signature verified inside `handle_webhook` via `stripe.Webhook.construct_event`. It's defined last among the stripe router's routes; keep it that way (or otherwise ensure no broader `POST /{invoice_id}`-shaped route can shadow it) if you add new routes to `stripe_router.py`.

## Chat / Voice (LiveKit)
`anthropic_chat_router.py` issues LiveKit room tokens and manages `ChatSession`/`ChatMessage` records (roles: `MessageRole.user/assistant/tool`). The actual voice agent runs as a **separate process** (`app/livekit_worker/`, its own `entrypoint.py`), not inside the FastAPI app — it uses its own `db.py`/`dependencies.py` and calls out to Anthropic/OpenAI (`app/core/anthropic/`, `app/core/openai/`, `app/core/prompts/`) plus `live_kit_service.py`/`ai_service.py` for persistence and tool calls. Treat it as a distinct deployable when reasoning about lifecycle/env/scaling.

## Images
`image_router.py` → `image_service.py` → `minio_service.py` (S3-compatible object storage via `app/core/minio.py`). Used for animal/user avatar uploads.

## WebSocket
Single Socket.IO server (`app/ws/server.py`, `socketio.AsyncServer(async_mode="asgi", client_manager=AsyncRedisManager(...))`) mounted onto the FastAPI app in `app/main.py` as `asgi_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="ws")` — **uvicorn must point at `app.main:asgi_app`, not `app.main:app`** (tests still import the bare `app` directly, unaffected).
Auth happens on the Socket.IO handshake: client sends `auth: { token }`; `connect` in `app/ws/events.py` validates it via `get_current_principal` (`app/ws/auth.py`, same JWT + permissions-version check as `get_current_principal`, just without header coupling) and rejects with `ConnectionRefusedError` on failure.
Per-feature realtime channels are rooms, not separate routes: clients `emit("join_chat_session", { sessionId })` after connecting (ownership checked against the handshake session before `sio.enter_room`), and services push updates with `sio.emit(event, payload, room=chat_session_room(id))` (`app/ws/rooms.py`). `AsyncRedisManager` handles fan-out across worker processes — don't hand-roll Redis pub/sub for this, emit through `sio` instead (see `DocumentService._publish_status`).

## Architecture
Layer order: **Models ← FastCRUD ← Services ← Routers**. Schemas (`app/schemas/`) never import ORM models.
- Routers: parse → call service → return `response_model`. No DB calls, no `*_crud` imports.
- Multi-model writes: `async with session.begin()` in the service.
- `app/core/dependencies.py` and `app/admin/` may call cruds/models directly.

## New model checklist
1. `app/db/models/<name>.py` — `Base, IDMixin, TimestampMixin`. Multi-word: explicit `__tablename__`.
2. FK: `ondelete="CASCADE"` where appropriate.
3. `FastCRUD(<Model>)` in `app/db/models/__init__.py`.
4. Schemas in `app/schemas/` — response: `model_config = ConfigDict(from_attributes=True)`.
5. Service in `app/services/`, DI factory in `app/services/__init__.py`.
6. Router in `app/routers/v1/`, register in `app/routers/v1/__init__.py` + `app/routers/__init__.py`.
7. `ModelView` in `app/admin/views.py`.
8. `alembic revision --autogenerate -m "add <name>"` — review before applying.

## Exceptions
Never `raise HTTPException` from services.
`NotFoundError`→404 · `UnauthorizedError`→401 · `ForbiddenError`→403 · `AlreadyExistsError`→409 · `BadRequestError`→400 · `ValidationError`→422

## HTTP conventions
POST→201 · DELETE→204 · always explicit `response_model=`.

## Invariants — never break
1. **CORS**: never `allow_origins=["*"]` with `allow_credentials=True`.
2. **WWW-Authenticate**: `main.py` handler must forward `error.headers` into `JSONResponse`.
3. **Webhook**: must be unauthenticated; signature verified inside service.
4. **Webhook route ordering**: keep `POST /webhook` from being shadowed by a broader `POST /{invoice_id}`-shaped route in `stripe_router.py`.

## Code style
Ruff + mypy (PostToolUse hook). Line length: 150. Target: py312.
`is_` prefix on all boolean fields. No comments unless WHY is non-obvious.

Note: `make format` calls `poetry run black .`, but `black` is not currently a declared dependency in `pyproject.toml` — it will fail unless black is installed separately. If you hit this, either add `black` to dev deps or drop it from the Makefile target (ruff already handles formatting-adjacent lint fixes).

## Skills & workflow
```
/plan <feature>   → impl-planner: live docs + plan before any code
/arch             → layer-violation check (run before PR)
/review           → full dep + logic review pipeline
/naming           → naming conventions check
/rest-urls        → REST URL best practices
/fastapi-tests    → run + audit pytest suite
library-skills    → discover/install/repair package-bundled agent skills (uvx library-skills)
```

**Feature workflow**: `/plan` → implement → ruff+mypy (auto) → `/arch` → security-auditor (auto on auth/Stripe) → db-migration-reviewer (if migration) → `/fastapi-tests` → `/review`

## Commands
`make install` · `make dev` (reload) / `make run` · `make test` / `test-v` / `test-cov` · `make lint` / `make format` / `make check` (mypy) · `make migrate msg="..."` / `make upgrade` / `make downgrade` · `make stripe-webhook` (local Stripe CLI forwarding) · `make clean` · `make pre-commit` / `pre-commit-update`

## Environment
Venv: `.venv/Scripts/python.exe`. DB: PostgreSQL via `docker/docker-compose.yml` (also defines the LiveKit server via `docker/livekit.yaml`). Secrets in `.env` (never commit) — see `.env.sample` for the full var list.
