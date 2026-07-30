# Animal Shelter API — CLAUDE.md

## Stack
FastAPI · SQLAlchemy 2 async · asyncpg · PostgreSQL · Alembic · Pydantic v2 · Poetry · starlette-admin · httpx-oauth (Google) · python-jose · bcrypt · Redis (fastapi-cache2) · Stripe. Python 3.11. Auth is **hand-rolled**.

## Layout
```
app/
  core/
    config.py        # AppConfig, DBConfig, AuthConfig, RedisConfig, StripeConfig (pydantic-settings, lru_cache getters)
    dependencies.py  # oauth2_scheme, Principal, get_current_principal, require_scopes, require_roles, require_superuser, get_current_user
    security.py      # hash/verify_password, create/decode_access_token, generate/hash_refresh_token
    cookies.py       # helpers for setting/clearing the refresh-token HttpOnly cookie
    exceptions.py    # CustomError hierarchy
    oauth.py         # Google OAuth2 setup
    logger.py
  db/
    enums.py         # Gender, Policy, InvoiceStatus, Currency. Role enum is legacy/unused.
    models/
      base.py        # DeclarativeBase + auto __tablename__ + subject()
      associations.py# user_roles, role_permissions M2M tables
      invoice.py     # Invoice + invoice_health_logs association table
      stripe_event.py# StripeEvent (idempotency log for webhook events)
      __init__.py    # all FastCRUD instances: animal_crud, health_log_crud, invoice_crud,
                     #   role_crud, permission_crud, resource_crud, refresh_token_crud,
                     #   stripe_event_crud, user_crud, oauth_account_crud
    mixins.py        # IDMixin (UUID PK), TimestampMixin
    session.py       # get_db_session
  services/
    auth_service.py        # register, authenticate, login, refresh (rotation+reuse), logout, google_callback
    role_service.py        # CRUD + assign users to roles, bump_permissions_version
    permission_service.py  # CRUD permissions
    resource_service.py    # CRUD resources
    invoice_service.py     # create, get_by_id, confirm_payment, handle_webhook
    refresh_token_service.py
    user_service.py
    health_log_service.py
    animal_service.py
    redis_service.py       # RedisService singleton (asyncio pool)
    __init__.py            # DI factory functions for all services
  routers/v1/
    auth_router.py       # /auth register|login|refresh|logout|google/*
    users_router.py      # /users/me, PUT /users/{id}/roles (superuser)
    role_router.py       # /roles CRUD + PUT /roles/{id}/permissions (superuser)
    permission_router.py # /permissions CRUD (superuser)
    resource_router.py   # /resources CRUD (superuser)
    animal_router.py
    health_log_router.py
    stripe_router.py     # /invoices — create(vet), get, confirm_payment, webhook
  main.py   # lifespan (FastAPICache + Redis), CORS, SessionMiddleware, CustomError handler, stripe.api_key init
  admin/
    setup.py / views.py / auth.py
alembic/
tests/
```

## Auth
OAuth2PasswordBearer + JWT access + DB-tracked refresh token (HttpOnly cookie) + Google OAuth2.

**Tokens** (`app/core/security.py`):
- **Access JWT** HS256: claims `sub, scopes[], permissions_version, is_superuser, type="access", iat, exp`. TTL: `ACCESS_TOKEN_TIME_MINUTES`.
- **Refresh**: opaque `secrets.token_urlsafe`; sha256 hash stored in `refresh_tokens` table, raw in HttpOnly Secure SameSite=strict cookie at path `/api/auth`. Rotation on every refresh; reuse of a revoked token revokes the whole user's chain. TTL: `REFRESH_TOKEN_TIME_DAYS`.

**User model**: `id, email, hashed_password, is_active, is_superuser, is_verified, permissions_version` + `roles` (M2M), `oauth_accounts`, `refresh_tokens`, `invoices`. M2M writes and scope resolution use `selectinload` in services (not FastCRUD).

## RBAC
Users ⇄ Roles ⇄ Permissions (M2M, runtime-editable). Scope = `Resource.name:Policy` (e.g. `animals:read`). Resource is a first-class DB table.

**`get_current_principal`** flow: decode JWT → assert `type=="access"` → Redis `permissions_version:{user_id}` check (miss → load from DB, cache 1h; `token.pv < current` → 401). Returns `Principal` (no ORM row).

**In-flight invalidation**: role/permission/user-role mutations increment `permissions_version` in the same commit, then delete `permissions_version:{id}` from Redis after commit. Stale tokens 401 → client calls `/auth/refresh`.

**Protecting endpoints:**
```python
_ = Depends(require_scopes(f"{Animal.subject()}:{Policy.create}"))  # scope-based
_ = Depends(require_roles("vet"))                                    # role-based
_ = Depends(require_superuser)                                       # superuser only
```
Superusers bypass scope/role checks but still hit the `pv` check.

## Stripe / Invoices
- `StripeConfig`: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` — loaded via `get_stripe_config()`.
- `stripe.api_key` set at module level in `main.py`.
- `Invoice` model: `animal_id, amount_in_cents, status (InvoiceStatus), currency (Currency), user_id` + M2M `health_logs` via `invoice_health_logs` table.
- `StripeEvent` model: idempotency log for processed webhook events.
- `InvoiceService`: `create`, `get_by_id`, `confirm_payment(invoice_id, confirmation_token_id, user)`, `handle_webhook(body, sig_header)`.
- Webhook route is public (no auth), Stripe signature verified inside `handle_webhook`.

## Architecture rules
Layer order: Models ← FastCRUD ← Services ← Routers. Schemas never import ORM.
- Routers: parse input → call service → return `response_model`. No DB calls, no `*_crud` imports.
- Multi-model writes in a service must use `async with session.begin()`.
- `app/core/dependencies.py` may call cruds directly (infrastructure glue).
- `app/admin/` may import models directly — only layer allowed to besides `app/db/models/__init__.py`.

## Patterns

**New model checklist:**
1. `app/db/models/<name>.py` — inherit `Base, IDMixin, TimestampMixin`. Multi-word names set `__tablename__` explicitly.
2. FK with `ondelete="CASCADE"` where appropriate.
3. Register `FastCRUD(<Model>)` in `app/db/models/__init__.py`.
4. Pydantic schemas in `app/schemas/` — response models need `model_config = ConfigDict(from_attributes=True)`.
5. Service in `app/services/`, DI factory in `app/services/__init__.py`.
6. Router in `app/routers/v1/`, imported in `app/routers/v1/__init__.py`, registered in `app/routers/__init__.py`.
7. `ModelView` in `app/admin/views.py`, added to `setup_admin()`.
8. `alembic revision --autogenerate -m "add <name>"` — review before applying.

**Exceptions** (never raise bare `HTTPException` from services):
`NotFoundError`→404 · `UnauthorizedError`→401 · `ForbiddenError`→403 · `AlreadyExistsError`→409 · `BadRequestError`→400 · `ValidationError`→422

**HTTP conventions:** `201` for POST, `204` for DELETE, explicit `response_model=` always.

## Known invariants — never break
1. **CORS**: never `allow_origins=["*"]` with `allow_credentials=True`. Use `get_auth_config().CORS_ORIGINS`.
2. **`WWW-Authenticate` headers**: `main.py` exception handler must forward `error.headers` into the `JSONResponse`.
3. **Webhook route**: must remain unauthenticated; signature verification happens inside the service.

## Code style
- Ruff + mypy on every save (PostToolUse hook). Line length: 150. Target: py311.
- `is_` prefix on all boolean fields/properties.
- No comments unless the WHY is non-obvious.

## Skills
- `/arch` — Clean Architecture layer-violation check (run before PR).
- `/review` — full pipeline: `code-reviewer` → `dep-checker` + `logic-reviewer` → `arbitrator`. Priority: Security > Correctness > blast radius > non-blocking.
- `/naming` — naming conventions check.
- `/rest-urls` — REST URL best-practices check.
- `/plan <feature>` — **use before any non-trivial feature**. Spawns `impl-planner` → fetches live library docs via `lib-versions` → produces a step-by-step implementation plan (files, signatures, migration command, test plan) for approval before code is written.

## Agents (spawned automatically by skills or explicitly via Agent tool)

| Agent | Model | When used |
|-------|-------|-----------|
| `impl-planner` | sonnet | Orchestrates `/plan`: reads project, calls `lib-versions`, outputs structured plan |
| `lib-versions` | haiku (background) | Fetches CURRENT version + API patterns from PyPI/docs before any implementation. Prevents use of deprecated APIs from training data. |
| `security-auditor` | sonnet | Checks 10 project invariants + OWASP API Top 10. Returns PASS/WARN/BLOCK. Run before merge on auth/router/Stripe changes. |
| `db-migration-reviewer` | sonnet | Reviews Alembic migration files for destructive ops, missing server_defaults, enum gotchas, index gaps, and zero-downtime risks. Run after `alembic revision --autogenerate`, before `upgrade head`. |
| `code-reviewer` | sonnet | Orchestrates `/review` pipeline |
| `dep-checker` | haiku (background) | CVE + version check, called by `code-reviewer` |
| `logic-reviewer` | sonnet | Deep logic/DB/security review, called by `code-reviewer` |
| `arbitrator` | sonnet | Resolves conflicts between `dep-checker` and `logic-reviewer` |
| `fastapi-test-reviewer` | sonnet | Deep test audit, called by `/fastapi-tests` |

## Recommended workflow for new features

```
1. /plan <feature>          ← get plan + live docs, approve before touching code
2. implement (Claude writes code)
3. ruff + mypy auto-run via PostToolUse hook
4. /arch                    ← verify no layer violations
5. security-auditor         ← verify invariants (auto on auth/Stripe changes)
6. db-migration-reviewer    ← if migration was generated
7. /fastapi-tests           ← run + audit tests
8. /review                  ← full dep + logic review before PR
```

## Environment
- Venv: `.venv/Scripts/python.exe` (Windows). Run: `uvicorn app.main:app --reload`.
- DB: PostgreSQL via Docker (`docker/docker-compose.yml`). Secrets in `.env` (never commit).
- Required env vars: `DB_*`, `ACCESS_TOKEN_SECRET`, `ACCESS_TOKEN_TIME_MINUTES`, `REFRESH_TOKEN_TIME_DAYS`, `JWT_ALGORITHM`, `ADMIN_SECRET`, `SUPERUSER_EMAIL`, `SUPERUSER_PASSWORD`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_USER`, `REDIS_PASSWORD`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `CORS_ORIGINS`.
