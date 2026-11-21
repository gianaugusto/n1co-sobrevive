.PHONY: help install up down migrate api web test test-backend test-frontend lint format

help: ## Show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

install: ## Install backend and frontend dependencies
	cd backend && pip install -e ".[dev]"
	cd frontend && npm ci

up: ## Start PostgreSQL and Kafka (with topics)
	docker compose up -d --wait postgres kafka
	docker compose run --rm kafka-init

down: ## Stop the local stack
	docker compose down

migrate: ## Apply database migrations
	cd backend && alembic upgrade head

api: ## Run the API with reload
	cd backend && uvicorn forgetme.main:build_app --factory --reload

web: ## Run the frontend dev server
	cd frontend && npm run dev

test: test-backend test-frontend ## Run every test suite

test-backend: ## Backend unit + integration tests (SQLite unless DATABASE_URL is set)
	cd backend && pytest

test-frontend: ## Frontend tests
	cd frontend && npm test

lint: ## Lint and type-check everything
	cd backend && ruff check . && ruff format --check . && mypy src
	cd frontend && npm run typecheck

format: ## Auto-format the backend
	cd backend && ruff check --fix . && ruff format .
