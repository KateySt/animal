Local run: `make dev` serves `app.main:asgi_app`. Run the LiveKit worker in a separate terminal: `poetry run python -m app.livekit_worker.entrypoint dev`. Start infra with `docker compose -f docker/docker-compose.yml up -d postgres redis minio minio-init livekit`; a bare `up` also builds the containerised API on :80. Full-stack guide: `../README.md`.

