# Animal Shelter API

FastAPI service for an animal shelter: RBAC auth (JWT + refresh + Google OAuth2),
animals & health logs, Stripe invoicing, an admin panel, and an AI chat assistant
(text + voice over LiveKit, image generation, PDF documents via `book-rag`).

**Stack:** FastAPI · SQLAlchemy 2 (async) · asyncpg · PostgreSQL · Alembic ·
Pydantic v2 · Redis · Vercel Blob · LiveKit (tokens) · Stripe · Poetry · Python 3.12

> Running the whole system (API + agent + book-rag + frontend)? See the [root README](../README.md).

This project is the API only (`app.main:app`, REST). Document statuses are polled by the frontend over REST. The LiveKit voice/text
agent is a separate project, [`../animal-agent/`](../animal-agent/README.md); it calls this API over HTTP
(see [Agent internal API](#agent-internal-api)).

---

## Prerequisites

- **Python 3.12+**
- **Poetry 2.0+** — dependency & virtualenv manager ([install guide](https://python-poetry.org/docs/#installation))
- **Docker + Docker Compose** — for PostgreSQL, Redis (+ pgAdmin, RedisInsight)
- **LiveKit Cloud project** — https://cloud.livekit.io, gives `LIVEKIT_URL` / key / secret

Verify Poetry:

```bash
poetry --version
```

---

## Quick start

```bash
# 1. Clone
git clone <repo-url>
cd animal

# 2. Create your environment file (see "Environment" below)
cp .env.sample .env
#   Windows PowerShell:  Copy-Item .env.sample .env

# 3. Install dependencies (creates the virtualenv)
make install          # == poetry install

# 4. Start infrastructure (Postgres, Redis)
docker compose -f docker/docker-compose.yml up -d postgres redis

# 5. Apply database migrations
make upgrade          # == poetry run alembic upgrade head

# 6. Run the API (auto-reload)
make dev              # == poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. For chat, run the agent from ../animal-agent (see its README)
```

The API is now on **http://localhost:8000** — docs at **http://localhost:8000/docs**.


---

## Working with Poetry

Poetry owns the virtualenv, so **do not** `pip install` or activate a venv manually.
Every command runs through Poetry:

```bash
poetry install                 # install all deps (main + dev groups)
poetry install --only main     # runtime deps only (e.g. production image)
poetry add <package>           # add a runtime dependency
poetry add --group dev <pkg>   # add a dev dependency
poetry run <command>           # run a command inside the venv
poetry env info --path         # show the virtualenv path
```

To open a shell inside the environment:

```bash
poetry env activate            # prints the activate command to run
# or run one-off commands with `poetry run ...`
```

> The `Makefile` wraps the common `poetry run ...` commands — prefer `make <target>`.

---

## Environment

Configuration is loaded from `.env` (see `app/core/config.py`). Copy the sample and
fill in the values — **never commit `.env`**.

```bash
cp .env.sample .env
```

Variables by group (`.env.sample` is the source of truth):

| Group | Variables | Notes |
|---|---|---|
| PostgreSQL | `DB_NAME` `DB_USER` `DB_PASSWORD` `DB_HOST` `DB_PORT` `DB_ECHO` | also used by the compose `postgres` service |
| Redis | `REDIS_HOST` `REDIS_PORT` `REDIS_USER` `REDIS_PASSWORD` | cache, permissions version |
| Auth | `ACCESS_TOKEN_SECRET` `JWT_ALGORITHM` `ACCESS_TOKEN_TIME_MINUTES` `REFRESH_TOKEN_TIME_DAYS` `COOKIE_SECURE` `COOKIE_DOMAIN` | `COOKIE_SECURE` defaults to `true`; set `false` only if your browser drops the refresh cookie over plain HTTP |
| Admin | `ADMIN_SECRET` `SUPERUSER_EMAIL` `SUPERUSER_PASSWORD` | starlette-admin + bootstrap superuser |
| Frontend | `CORS_ORIGINS` `FRONTEND_URL` | e.g. `http://localhost:5173` |
| Google OAuth2 | `GOOGLE_CLIENT_ID` `GOOGLE_CLIENT_SECRET` `GOOGLE_REDIRECT_URI` | |
| Stripe | `STRIPE_SECRET_KEY` `STRIPE_WEBHOOK_SECRET` | webhook secret comes from `make stripe-webhook` locally |
| Anthropic | `ANTHROPIC_API_KEY` `ANTHROPIC_MODEL` `ANTHROPIC_MAX_TOKEN` `ANTHROPIC_TITLE_MAX_TOKEN` `ANTHROPIC_SUMMERY_MAX_TOKEN` `SUMMARY_EVERY_N` `RECENT_WINDOW` | chat model, title/summary generation, history window |
| Vercel Blob | `BLOB_READ_WRITE_TOKEN` `BLOB_DOCUMENTS_READ_WRITE_TOKEN` | read-write tokens of the public store (avatars, chat images) and the private store (chat PDFs); used locally too |
| Agent API | `AGENT_SERVICE_TOKEN` | agent → API auth, at least 32 chars; must equal the agent's (see [Agent internal API](#agent-internal-api)) |
| OpenAI | `OPENAI_API_KEY` `OPENAI_IMAGE_MODEL` | image generation |
| LiveKit | `LIVEKIT_URL` `LIVEKIT_API_KEY` `LIVEKIT_API_SECRET` `LIVEKIT_AGENT_NAME` | LiveKit Cloud: `LIVEKIT_URL=wss://<project>.livekit.cloud`; agent name must match the agent's (`animal-chat-agent-dev` locally) |
| book-rag | `BOOK_RAG_BASE_URL` `INTERNAL_SERVICE_TOKEN` `BOOK_RAG_MAX_UPLOAD_SIZE_BYTES` `BOOK_RAG_MAX_DOCUMENTS_PER_SESSION` `BOOK_RAG_REQUEST_TIMEOUT_SECONDS` | token must equal book-rag's `INTERNAL_SERVICE_TOKEN`; with book-rag on Vercel set `BOOK_RAG_REQUEST_TIMEOUT_SECONDS=60` (cold container start) |

> When running the API on the host and the database in Docker, set `DB_HOST=localhost`
> and `REDIS_HOST=localhost` (the container ports are published to your machine).

---

## Infrastructure (Docker)

`docker/docker-compose.yml` services:

| Service | Port | URL |
|---|---|---|
| `postgres` | 5432 | — |
| `redis` | 6379 | — |
| `pgadmin` | 5050 | http://localhost:5050 |
| `redisinsight` | 5540 | http://localhost:5540 |
| `animal_fast_api` | 80 | containerised API — **skip it for local dev** |

For local development, name the services so the containerised API isn't built and started next to `make dev`:

```bash
docker compose -f docker/docker-compose.yml up -d postgres redis   # start (+ pgadmin redisinsight if needed)
docker compose -f docker/docker-compose.yml ps         # status
docker compose -f docker/docker-compose.yml logs -f    # logs
docker compose -f docker/docker-compose.yml down       # stop
docker compose -f docker/docker-compose.yml down -v    # stop + wipe volumes
```

---

## Database migrations (Alembic)

```bash
make upgrade                       # apply all migrations (alembic upgrade head)
make downgrade                     # roll back one revision
make migrate msg="add invoice"     # autogenerate a new revision
```

> Always review an autogenerated migration before applying it.

---

## Running the API

```bash
make dev     # development, auto-reload   → http://localhost:8000
make run     # production-style, no reload
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Testing & quality

```bash
make test                          # run the full suite
make test-v                        # verbose
make test-cov                      # coverage → htmlcov/index.html

poetry run pytest tests/unit/          # unit tests only
poetry run pytest tests/integration/   # integration tests only
poetry run pytest -m unit              # by marker (unit | integration)

make lint       # ruff check .
make check      # ruff + mypy
make format     # black + ruff --fix
```

---

## Agent internal API

The voice/text agent lives in [`../animal-agent/`](../animal-agent/README.md) and runs in LiveKit Cloud.
It has no database access. This API creates the LiveKit token, dispatches the agent by `LIVEKIT_AGENT_NAME`
and serves the agent's internal endpoints.

Agent → API: base `/api/v1/internal/agent/sessions/{session_id}`, header `X-Agent-Token: <AGENT_SERVICE_TOKEN>`
(identical in `animal/.env` and `animal-agent/.env`, at least 32 chars; 401 otherwise). Endpoints: `GET /context`,
`POST /messages`, `GET /documents/statuses`, `POST /documents/search`, `GET /invoices`. The API does the DB work,
book-rag search and title/summary generation. Code: `app/routers/v1/agent_internal_router.py` +
`app/schemas/agent.py` (the agent side is `animal-agent/src/api_client.py` + `src/api_models.py` - change both together).

For local chat set `LIVEKIT_AGENT_NAME=animal-chat-agent-dev` in `animal/.env` and in `animal-agent/.env`, otherwise
jobs are split between the cloud and the local agent. The API must be reachable from the internet for a cloud agent
(deployed URL; for testing: `cloudflared tunnel --url http://localhost:8000`).

Document search in chat additionally needs the [`book-rag`](../book-rag/README.md#http-service-used-by-the-animal-backend) HTTP service (called by the API).

On Windows run the API with `PYTHONUTF8=1` if logs crash with `UnicodeEncodeError` on a cp1251 console.

---

## Common workflow

```bash
make install                                                                    # once, after cloning
docker compose -f docker/docker-compose.yml up -d postgres redis          # start infra
make upgrade                                                                    # migrate DB
make dev                                                                        # terminal 1: API with reload
(cd ../animal-agent && uv run python -m src.entrypoint dev)                     # terminal 2: agent
make check && make test                                                         # before committing
```
