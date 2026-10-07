# Animal Shelter API

FastAPI service for an animal shelter: RBAC auth (JWT + refresh + Google OAuth2),
animals & health logs, Stripe invoicing, an admin panel, and an AI chat assistant
(text + voice over LiveKit, image generation, PDF documents via `book-rag`).

**Stack:** FastAPI · SQLAlchemy 2 (async) · asyncpg · PostgreSQL · Alembic ·
Pydantic v2 · Redis · Socket.IO · MinIO · LiveKit Agents · Stripe · Poetry · Python 3.12

> Running the whole system (API + worker + book-rag + frontend)? See the [root README](../README.md).

This repo contains **two processes**:

| Process | Entry point | Purpose |
|---|---|---|
| API | `app.main:asgi_app` | REST API + Socket.IO (`/ws`) |
| LiveKit worker | `app.livekit_worker.entrypoint` | Voice/text agent: STT → Claude → TTS, persists messages |

---

## Prerequisites

- **Python 3.12+**
- **Poetry 2.0+** — dependency & virtualenv manager ([install guide](https://python-poetry.org/docs/#installation))
- **Docker + Docker Compose** — for PostgreSQL, Redis, MinIO, LiveKit (+ pgAdmin, RedisInsight)

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

# 4. Start infrastructure (Postgres, Redis, MinIO, LiveKit)
docker compose -f docker/docker-compose.yml up -d postgres redis minio minio-init livekit

# 5. Apply database migrations
make upgrade          # == poetry run alembic upgrade head

# 6. Run the API (auto-reload)
make dev              # == poetry run uvicorn app.main:asgi_app --reload --host 0.0.0.0 --port 8000

# 7. In a second terminal: run the LiveKit worker (needed for chat)
poetry run python -m app.livekit_worker.entrypoint dev
```

The API is now on **http://localhost:8000** — docs at **http://localhost:8000/docs**.

> Uvicorn must serve `app.main:asgi_app` (Socket.IO wrapped around FastAPI), not `app.main:app`,
> otherwise `/ws` returns 404 and realtime document statuses never arrive.

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
| Redis | `REDIS_HOST` `REDIS_PORT` `REDIS_USER` `REDIS_PASSWORD` | cache, permissions version, Socket.IO fan-out |
| Auth | `ACCESS_TOKEN_SECRET` `JWT_ALGORITHM` `ACCESS_TOKEN_TIME_MINUTES` `REFRESH_TOKEN_TIME_DAYS` `COOKIE_SECURE` `COOKIE_DOMAIN` | `COOKIE_SECURE` defaults to `true`; set `false` only if your browser drops the refresh cookie over plain HTTP |
| Admin | `ADMIN_SECRET` `SUPERUSER_EMAIL` `SUPERUSER_PASSWORD` | starlette-admin + bootstrap superuser |
| Frontend | `CORS_ORIGINS` `FRONTEND_URL` | e.g. `http://localhost:5173` |
| Google OAuth2 | `GOOGLE_CLIENT_ID` `GOOGLE_CLIENT_SECRET` `GOOGLE_REDIRECT_URI` | |
| Stripe | `STRIPE_SECRET_KEY` `STRIPE_WEBHOOK_SECRET` | webhook secret comes from `make stripe-webhook` locally |
| Anthropic | `ANTHROPIC_API_KEY` `ANTHROPIC_MODEL` `ANTHROPIC_MAX_TOKEN` `ANTHROPIC_TITLE_MAX_TOKEN` `ANTHROPIC_SUMMERY_MAX_TOKEN` `SUMMARY_EVERY_N` `RECENT_WINDOW` | chat model, title/summary generation, history window |
| MinIO | `MINIO_ROOT_USER` `MINIO_ROOT_PASSWORD` `MINIO_ACCESS_KEY` `MINIO_SECRET_KEY` `MINIO_BUCKET_NAME` `MINIO_HOST` `MINIO_REGION` `MINIO_SECURE` | bucket is created on first use; `MINIO_HOST=localhost:9000` |
| Speech | `DEEPGRAM_API_KEY` `ELEVENLABS_API_KEY` `ELEVENLABS_VOICE_ID` `ELEVENLABS_MODEL` | worker only (STT / TTS) |
| OpenAI | `OPENAI_API_KEY` `OPENAI_IMAGE_MODEL` | image generation |
| LiveKit | `LIVEKIT_URL` `LIVEKIT_API_KEY` `LIVEKIT_API_SECRET` `LIVEKIT_AGENT_NAME` | same values for API and worker; `LIVEKIT_URL=ws://localhost:7880`, secret ≥ 32 chars |
| Web search | `EXA_API_KEY` | worker tool |
| book-rag | `BOOK_RAG_BASE_URL` `INTERNAL_SERVICE_TOKEN` `BOOK_RAG_MAX_UPLOAD_SIZE_BYTES` `BOOK_RAG_MAX_DOCUMENTS_PER_SESSION` `BOOK_RAG_REQUEST_TIMEOUT_SECONDS` | token must equal book-rag's `INTERNAL_SERVICE_TOKEN` |

> When running the API on the host and the database in Docker, set `DB_HOST=localhost`
> and `REDIS_HOST=localhost` (the container ports are published to your machine).

---

## Infrastructure (Docker)

`docker/docker-compose.yml` services:

| Service | Port | URL |
|---|---|---|
| `postgres` | 5432 | — |
| `redis` | 6379 | — |
| `minio` | 9000 (API) / 9001 (console) | http://localhost:9001 |
| `livekit` | 7880 (signal) / 7881 (TCP) / 52000-52050 (UDP) | ws://localhost:7880 |
| `pgadmin` | 5050 | http://localhost:5050 |
| `redisinsight` | 5540 | http://localhost:5540 |
| `animal_fast_api` | 80 | containerised API — **skip it for local dev** |

For local development, name the services so the containerised API isn't built and started next to `make dev`:

```bash
docker compose -f docker/docker-compose.yml up -d postgres redis minio minio-init livekit   # start (+ pgadmin redisinsight if needed)
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

## LiveKit worker

The voice/text agent is a **separate process** with its own DB engine (`app/livekit_worker/`).
It reads the same `.env` as the API. The API creates the LiveKit token and dispatches the agent by
`LIVEKIT_AGENT_NAME`; the worker joins the room, answers with Claude, and saves messages to PostgreSQL.

```bash
poetry run python -m app.livekit_worker.entrypoint dev     # development: hot reload, verbose logs
poetry run python -m app.livekit_worker.entrypoint start   # production mode
```

Requires: the `livekit` container running, matching `LIVEKIT_*` values in API and worker,
and the speech/LLM keys (`DEEPGRAM_*`, `ELEVENLABS_*`, `ANTHROPIC_*`, `EXA_API_KEY`).
Without the worker, sessions open but no reply ever arrives.

Document search in chat additionally needs the [`book-rag`](../book-rag/README.md#http-service-used-by-the-animal-backend) HTTP service.

---

## Common workflow

```bash
make install                                                                    # once, after cloning
docker compose -f docker/docker-compose.yml up -d postgres redis minio minio-init livekit  # start infra
make upgrade                                                                    # migrate DB
make dev                                                                        # terminal 1: API with reload
poetry run python -m app.livekit_worker.entrypoint dev                          # terminal 2: worker
make check && make test                                                         # before committing
```
