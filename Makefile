
.PHONY: help run migrations migrate test server ruff fmt up down

BACKEND_DIR := backend/config
MANAGE := uv run python manage.py

help:
	@echo "Available commands:"
	@echo "  make up          - Start Postgres, Redis and Mailpit"
	@echo "  make down        - Stop Postgres, Redis and Mailpit"
	@echo "  make run         - Start the development server"
	@echo "  make migrations  - Create database migrations"
	@echo "  make migrate     - Apply database migrations"
	@echo "  make test        - Run tests with coverage"
	@echo "  make fmt         - Format the code"

up:
	docker-compose -f infra/docker-compose-dev.yml up -d

down:
	docker-compose -f infra/docker-compose-dev.yml down

run:
	cd $(BACKEND_DIR) && $(MANAGE) runserver

server: run

migrations:
	cd $(BACKEND_DIR) && $(MANAGE) makemigrations

migrate:
	cd $(BACKEND_DIR) && $(MANAGE) migrate

test:
	cd $(BACKEND_DIR) && uv run ruff check . && uv run pytest ../tests

fmt:
	cd $(BACKEND_DIR) && uv run ruff format . && uv run ruff check . --fix