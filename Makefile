.PHONY: install run dev test lint format migrate upgrade downgrade shell

install:
	poetry install

run:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest

test-v:
	poetry run pytest -v

test-cov:
	poetry run pytest --cov=app --cov-report=html

lint:
	poetry run ruff check .

format:
	poetry run black .
	poetry run ruff check . --fix

check: lint
	poetry run mypy app

migrate:
	poetry run alembic revision --autogenerate -m "$(msg)"

upgrade:
	poetry run alembic upgrade head

downgrade:
	poetry run alembic downgrade -1

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/

pre-commit:
	poetry run pre-commit run --all-files

pre-commit-update:
	poetry run pre-commit autoupdate
