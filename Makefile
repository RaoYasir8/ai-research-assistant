.PHONY: up down logs test lint build clean

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f backend worker frontend

test:
	docker build --target test -t ai-research-assistant-backend-test ./backend
	docker run --rm ai-research-assistant-backend-test

lint:
	docker build --target test -t ai-research-assistant-backend-test ./backend
	docker run --rm ai-research-assistant-backend-test ruff check app tests

build:
	docker compose build

clean:
	docker compose down --remove-orphans
