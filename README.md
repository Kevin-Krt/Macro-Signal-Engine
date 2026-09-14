[![CI](https://github.com/Kevin-Krt/Macro-Signal-Engine/actions/workflows/ci.yml/badge.svg)](https://github.com/Kevin-Krt/Macro-Signal-Engine/actions/workflows/ci.yml)

# Macro Signal Engine

Macroeconomic event tracking with a RAG-powered conversational assistant.

🚧 Work in progress — see [ROADMAP.md](ROADMAP.md).

## Requirements

- Docker and Docker Compose
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Python 3.14 (uv installs it for you)
- GNU Make

## Getting started

```bash
git clone git@github.com:Kevin-Krt/Macro-Signal-Engine.git
cd Macro-Signal-Engine
cp .env.example .env
```

Generate the two secrets and paste them into `.env`:

```bash
openssl rand -hex 32                                    # APP_JWT_SECRET
python3 -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"   # APP_FERNET_KEY
```

Then:

```bash
make up
make migrate
curl -s localhost:8000/api/health
```

Expected: `{"status":"ok","checks":{"database":true,"redis":true}}`

## Development

```bash
cd backend && uv sync    # install the dependencies
make hooks               # install the git hooks (not versioned, run once)
```

Run the API with hot reload, against the containerised services:

```bash
docker compose up -d postgres redis
cd backend && uv run uvicorn app.main:app --reload
```

## Commands

`make` on its own lists every target.

| Command | What it does |
|---|---|
| `make up` | build and start the three services |
| `make down` | stop them, keep the data |
| `make clean` | stop them and **delete** the volumes |
| `make logs` | follow the API logs |
| `make psql` | open psql on the database |
| `make migrate` | apply the migrations |
| `make test` | run the test suite |
| `make check` | everything the CI runs |

## Layout

```
backend/          FastAPI application
  app/core/       config, database, logging
  app/modules/    business modules
  alembic/        migrations
  tests/
infra/postgres/   database init scripts
.github/          CI workflow
```
