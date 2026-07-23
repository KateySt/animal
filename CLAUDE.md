# Animal Shelter API — CLAUDE.md

## Stack
FastAPI + SQLAlchemy 2 async + asyncpg + PostgreSQL + Alembic + Pydantic v2 + Poetry + starlette-admin + fastapi-users + httpx-oauth + python-jose + bcrypt + Redis (fastapi-cache2). Python 3.11.

## Project layout
```
app/
  core/
    config.py              # AppConfig, DBConfig, AuthConfig, RedisConfig (pydantic-settings)
    dependencies.py        # require_permission(resource, policy), require_superuser
    exceptions.py          # CustomError hierarchy (NotFound, Unauthorized, AlreadyExists, …)
    security.py            # hash_password, verify_password (bcrypt helpers)
    fastapi_users_setup.py # fastapi_users instance, current_active_user
    google_oauth.py        # google_oauth_client (httpx-oauth GoogleOAuth2)
    logger.py
  db/
    enums.py          # Gender, Policy, Role (StrEnum)
    models/
      base.py         # DeclarativeBase + auto __tablename__
      animal.py       # Animal model
      health_log.py   # HealthLog model
      user.py         # User model (extends SQLAlchemyBaseUserTableUUID, adds role, oauth_accounts)
      oauth_account.py# OAuthAccount (SQLAlchemyBaseOAuthAccountTableUUID)
      permission.py   # Permission model (role, resource, action)
      __init__.py     # FastCRUD instances: animal_crud, health_log_crud, permission_crud
    mixins.py         # IDMixin (UUID PK), TimestampMixin
    session.py        # engine, AsyncSessionLocal, get_db_session
  admin/
    setup.py          # setup_admin(app) — mounts starlette-admin at /admin
    auth.py           # AdminAuthProvider (session-cookie login)
    views.py          # AnimalAdmin, HealthLogAdmin, UserAdmin (ModelView)
  schemas/
    animal.py         # AnimalCreate, AnimalResponse, HealthLog*
    user.py           # UserRead, UserCreate, UserUpdate (fastapi-users schemas + role)
    policy.py         # PermissionCreate, PermissionResponse
  services/
    animal_service.py
    health_log_service.py
    permission_service.py  # list_permissions, add_permission, remove_permission
    redis_service.py       # RedisService (asyncio redis pool, set/get/delete_cache); redis_service singleton
    user_manager.py        # UserManager, get_user_manager, get_user_db, auth_backend (JWT)
    __init__.py            # DI factories: get_animal_service, get_health_log_service,
                           #               get_permission_service, get_redis_service
  routers/
    animal_router.py
    health_log_router.py
    policy_router.py  # GET/POST /permissions, DELETE /permissions/{id} — superuser only
  main.py             # lifespan (FastAPICache init + redis close), all routers + fastapi-users routers
alembic/              # migrations
tests/
```

## Auth — fastapi-users (replaced hand-rolled JWT)
The project now uses **fastapi-users** for all user auth. The old `auth_router.py` is gone.

Registered routers (all under `/api`):
| Prefix | Router |
|---|---|
| `/auth/jwt` | `get_auth_router` — `POST /login`, `POST /logout` |
| `/auth` | `get_register_router` — `POST /register` |
| `/auth` | `get_reset_password_router` |
| `/auth` | `get_verify_router` |
| `/auth/google` | `get_oauth_router` (Google OAuth2, associate_by_email=True) |
| `/users` | `get_users_router` — CRUD on `/users/me`, `/users/{id}` |

Key objects:
- `auth_backend` — JWT via `BearerTransport` + `JWTStrategy` (secret: `AuthConfig.ACCESS_TOKEN_SECRET`, lifetime: `ACCESS_TOKEN_TIME_MINUTES * 60`)
- `current_active_user` — `fastapi_users.current_user(active=True)` — use this in dependencies
- `UserManager` — `UUIDIDMixin + BaseUserManager`; hooks: `on_after_register`, `on_after_forgot_password`, `on_after_request_verify`
- `get_user_db` — yields `SQLAlchemyUserDatabase(session, User, OAuthAccount)`

**User model** extends `SQLAlchemyBaseUserTableUUID` (gives `id, email, hashed_password, is_active, is_superuser, is_verified`) and adds:
- `role: Role` (default `Role.user`)
- `oauth_accounts: list[OAuthAccount]` (lazy="joined")

**No** `user_crud` FastCRUD instance — user DB access goes through fastapi-users `SQLAlchemyUserDatabase`.

## RBAC — Permission model
`Permission(role, resource, action)` stores per-role allowances.

- `Role`: `user | admin | staff`
- `Policy` (action): `read | create | update | delete`
- `require_permission(resource, policy)` — dependency factory; superusers bypass the check.
- `require_superuser` — dependency; raises `ForbiddenError` if `user.is_superuser` is False.
- Permission CRUD endpoints at `/permissions` are superuser-only.

### Protecting an endpoint
```python
# role-based (checks Permission table)
user = Depends(require_permission("animals", Policy.create))

# superuser only
_ = Depends(require_superuser)
```

## Redis + caching
- `RedisService` (singleton `redis_service`) wraps `redis.asyncio` with a connection pool.
- `fastapi-cache2` is initialised in `lifespan` with `RedisBackend(redis_service.redis)`, prefix `"fastapi-cache"`.
- Cache is closed in lifespan teardown: `await redis_service.close()`.
- Required env vars: `REDIS_HOST`, `REDIS_PORT`, `REDIS_USER`, `REDIS_PASSWORD`.

## Known bugs — never reintroduce

### 1. CORS is `allow_origins=["*"]` — tighten before production
Set `CORS_ORIGINS` env var and load it via `AppConfig`; never hardcode wildcard in prod.

## Patterns to follow

### Adding a new model
1. Create `app/db/models/<name>.py` — inherit `Base, IDMixin, TimestampMixin`.
2. Add FK with `ondelete="CASCADE"` where appropriate.
3. Auto-tablename comes from `Base.__tablename__`; no need to set it manually.
4. Register `FastCRUD(<Model>)` instance in `app/db/models/__init__.py`.
5. Create Pydantic schemas in `app/schemas/`; always set `model_config = ConfigDict(from_attributes=True)` on response models.
6. Add service in `app/services/`, DI factory in `app/services/__init__.py`.
7. Add router in `app/routers/`, register in `main.py`.
8. Register a `ModelView` subclass in `app/admin/views.py` and add it to `setup_admin()`.
9. Generate migration: `alembic revision --autogenerate -m "add <name>"`.

### Adding a new endpoint
- Router only does: parse input → call service → return response model. No DB logic in routers.
- Always set `response_model=` explicitly — never return raw ORM objects.
- Use `status.HTTP_201_CREATED` for POST, `status.HTTP_204_NO_CONTENT` for DELETE.
- Protect with `Depends(require_permission(...))` or `Depends(require_superuser)` — never `Depends(current_active_user)` directly in routers unless the endpoint truly needs no RBAC.

### Exceptions
Use `app.core.exceptions` — never raise bare `HTTPException` from services:
- `NotFoundError` → 404
- `UnauthorizedError` → 401
- `ForbiddenError` → 403
- `AlreadyExistsError` → 409
- `BadRequestError` → 400
- `ValidationError` → 422

### Migrations
- Always review autogenerated migration before applying — check for missing `server_default`, wrong types.
- Never edit the DB schema directly; always use Alembic.

## Code style
- Ruff + mypy run automatically on every file save (PostToolUse hook).
- Line length: 150. Target: py311.
- Boolean fields/properties: `is_` prefix (e.g. `is_query_logging_enabled`).
- No comments unless the WHY is non-obvious.

## Architecture
Run `/arch` to check Clean Architecture layer violations before any PR:
- Dependency rule: Models ← FastCRUD instances ← Services ← Routers; Schemas are used by all layers but must never import ORM.
- Schemas must not import or construct ORM instances.
- Multi-model writes in one service method must be wrapped in `async with session.begin()`.
- Routers must not import from `app.db.models` or call `*_crud` directly — go through a service.
- `app/core/dependencies.py` is allowed to call `permission_crud` directly (it is infrastructure glue, not a router).
- Admin views (`app/admin/`) may import models directly for `starlette-admin` registration; this is the only layer allowed to do so outside of `app/db/models/__init__.py`.

## Review pipeline
Run `/review` to trigger the full pipeline:
`code-reviewer` → `dep-checker` + `logic-reviewer` (parallel) → `arbitrator` (if conflict).
Arbitrator priority: Security > Correctness > minimal blast radius > defer non-blocking.

## Environment
- Venv: `.venv/Scripts/python.exe` (Windows).
- Run locally: `uvicorn app.main:app --reload`.
- DB: PostgreSQL via Docker (`docker/docker-compose.yml`).
- Secrets in `.env` (never commit); see `.env.sample`.
- Required env vars: `DB_*`, `ACCESS_TOKEN_SECRET`, `RESET_PASSWORD_TOKEN_SECRET`, `VERIFICATION_TOKEN_SECRET`, `ADMIN_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `REDIS_*`.
