# Animal Shelter API — CLAUDE.md

## Stack
FastAPI · SQLAlchemy 2 async · asyncpg · PostgreSQL · Alembic · Pydantic v2 · Poetry · starlette-admin · httpx-oauth (Google) · python-jose · bcrypt · Redis (fastapi-cache2) · Stripe · Python 3.11

## Layout
```
app/
  core/       config.py · dependencies.py · security.py · cookies.py · exceptions.py · oauth.py · logger.py
  db/
    enums.py  # Gender, Policy, InvoiceStatus, Currency  (Role = legacy/unused)
    models/   base.py · associations.py · invoice.py · stripe_event.py · __init__.py (all FastCRUD instances)
    mixins.py # IDMixin (UUID PK) · TimestampMixin
    session.py
  services/   auth · role · permission · resource · invoice · refresh_token · user · health_log · animal · redis · __init__.py (DI factories)
  routers/v1/ auth · users · role · permission · resource · animal · health_log · stripe
  main.py     # lifespan, CORS, SessionMiddleware, CustomError handler, stripe.api_key
  admin/      setup.py · views.py · auth.py
alembic/
tests/
```

## Auth
JWT access (HS256) + opaque refresh token (HttpOnly cookie, sha256 hash in DB, rotation+reuse-revoke chain) + Google OAuth2.

**JWT claims**: `sub, scopes[], permissions_version, is_superuser, type="access", iat, exp`
**Refresh cookie**: `httponly=True, secure=True, samesite="strict", path="/api/auth"`

**`get_current_principal` flow**: decode JWT → assert `type=="access"` → Redis `permissions_version:{user_id}` (miss → DB, cache 1h; `token.pv < current` → 401) → return `Principal` (no ORM row).

**In-flight invalidation**: role/perm mutations increment `permissions_version` in same commit, then delete Redis key. Stale tokens 401 → client calls `/auth/refresh`.

**Protecting endpoints:**
```python
_ = Depends(require_scopes(f"{Animal.subject()}:{Policy.create}"))
_ = Depends(require_roles("vet"))
_ = Depends(require_superuser)
```

## RBAC
Users ⇄ Roles ⇄ Permissions (M2M, runtime-editable). Scope = `Resource.name:Policy` (e.g. `animals:read`). Resource is a first-class DB table. M2M writes use `selectinload` in services.

## Stripe / Invoices
`Invoice`: `animal_id, amount_in_cents, status(InvoiceStatus), currency(Currency), user_id` + M2M `health_logs`.
`StripeEvent`: idempotency log. Webhook route is **public** — signature verified inside `handle_webhook`.

## Architecture
Layer order: **Models ← FastCRUD ← Services ← Routers**. Schemas never import ORM.
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
4. **Webhook route order**: `POST /webhook` before any `POST /{invoice_id}` in stripe_router.
5. **Refresh rotation**: lock row with `with_for_update()` before checking `is_revoked`.
6. **Webhook idempotency**: atomic INSERT ON CONFLICT — not check-then-insert.

## Code style
Ruff + mypy (PostToolUse hook). Line length: 150. Target: py311.
`is_` prefix on all boolean fields. No comments unless WHY is non-obvious.

## Skills & workflow
```
/plan <feature>   → impl-planner: live docs + plan before any code
/arch             → layer-violation check (run before PR)
/review           → full dep + logic review pipeline
/naming           → naming conventions check
/rest-urls        → REST URL best practices
/fastapi-tests    → run + audit pytest suite
```

**Feature workflow**: `/plan` → implement → ruff+mypy (auto) → `/arch` → security-auditor (auto on auth/Stripe) → db-migration-reviewer (if migration) → `/fastapi-tests` → `/review`

## Environment
Venv: `.venv/Scripts/python.exe`. Run: `uvicorn app.main:app --reload`.
DB: PostgreSQL via `docker/docker-compose.yml`. Secrets in `.env` (never commit).
