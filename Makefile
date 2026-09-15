.DEFAULT_GOAL := help
BACKEND := backend
COMPOSE := docker compose

.PHONY: help up down clean restart ps logs sh psql redis-cli \
        migrate downgrade revision test lint format check hooks

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

## ---------- docker ----------

up:  ## Start every service in the background
	$(COMPOSE) up -d --build

down:  ## Stop the services, keep the volumes
	$(COMPOSE) down

clean:  ## Stop the services and DELETE the volumes
	$(COMPOSE) down -v

restart:  ## Restart the api service
	$(COMPOSE) restart api

ps:  ## Show the services and their health
	$(COMPOSE) ps

logs:  ## Follow the api logs
	$(COMPOSE) logs -f api

sh:  ## Open a shell inside the api container
	$(COMPOSE) exec api sh

psql:  ## Open psql on the database
	$(COMPOSE) exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB'

redis-cli:  ## Open redis-cli
	$(COMPOSE) exec redis redis-cli

## ---------- database ----------

migrate:  ## Apply every migration
	cd $(BACKEND) && uv run alembic upgrade head

downgrade:  ## Roll back the last migration
	cd $(BACKEND) && uv run alembic downgrade -1

revision:  ## Create a migration (make revision m="add events table")
	cd $(BACKEND) && uv run alembic revision --autogenerate -m "$(m)"

## ---------- backend ----------

test:  ## Run the test suite
	cd $(BACKEND) && uv run pytest

lint:  ## Lint and type check
	cd $(BACKEND) && uv run ruff check
	cd $(BACKEND) && uv run pyrefly check

format:  ## Format the code
	cd $(BACKEND) && uv run ruff format

check: lint  ## Run everything the CI runs
	cd $(BACKEND) && uv run ruff format --check
	cd $(BACKEND) && uv run pytest

hooks:  ## Install the git hooks
	cd $(BACKEND) && uv run pre-commit install

## ---------- test ----------

createdb-test:  ## Create the test database (safe to re-run)
	$(COMPOSE) exec postgres createdb -U $$POSTGRES_USER $${POSTGRES_DB}_test || true
