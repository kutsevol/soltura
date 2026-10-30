.PHONY: help install up down ps logs db-shell run migrate migrate-down migrate-create migrate-history test lint format type-check

help:
	@echo "Available commands:"
	@echo "  make install         - Install dependencies and pre-commit hooks"
	@echo ""
	@echo "  make up              - Start local Postgres"
	@echo "  make down            - Stop local Postgres"
	@echo "  make ps              - Show container status"
	@echo "  make logs            - Follow container logs"
	@echo "  make db-shell        - Open a psql shell"
	@echo ""
	@echo "  make run             - Run the app with auto-reload on http://localhost:8000"
	@echo ""
	@echo "  make migrate         - Apply migrations (alembic upgrade head)"
	@echo "  make migrate-down    - Roll back one migration"
	@echo "  make migrate-create  - Create an empty migration to write by hand (MSG='description')"
	@echo "  make migrate-history - Show migration history"
	@echo ""
	@echo "  make test            - Run tests (needs Docker for the Postgres test container)"
	@echo "  make lint            - Run ruff linter and format check"
	@echo "  make format          - Fix lint issues and format code"
	@echo "  make type-check      - Run mypy"

install:
	uv sync
	uv run pre-commit install

up:
	docker compose up -d --wait

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

db-shell:
	docker compose exec postgres psql -U postgres -d soltura

run:
	uv run uvicorn soltura.app:app --reload

migrate:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade -1

migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide MSG='description'"; \
		exit 1; \
	fi
	uv run alembic revision -m "$(MSG)"

migrate-history:
	uv run alembic history --verbose

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

type-check:
	uv run mypy soltura/
