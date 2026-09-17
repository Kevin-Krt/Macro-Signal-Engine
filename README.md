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

Then get a free Finnhub API key at [finnhub.io/register](https://finnhub.io/register)
and paste it into `APP_FINNHUB_API_KEY`. The app refuses to start without it.

Finally:

```bash
make up
make migrate
make ingest
curl -s localhost:8000/api/health
```

Expected: `{"status":"ok","checks":{"database":true,"redis":true}}`

## Development

```bash
cd backend && uv sync    # install the dependencies
make hooks               # install the git hooks (not versioned, run once)
make createdb-test       # create the test database (run once)
```

Run the API with hot reload, against the containerised services:

```bash
docker compose up -d postgres redis
cd backend && uv run uvicorn app.main:app --reload
```

## Ingestion

Beat schedules `events.ingest_news` every six hours. `worker-io` consumes the
`ingestion` queue, `worker-cpu` the `compute` queue (used from phase 3 on).

```bash
make ingest        # trigger one now
make workers       # both workers should reply pong
make logs-worker   # follow what they do
```

Ingestion is idempotent: the same article is updated, never duplicated.

## Commands

`make` on its own lists every target.

| Command | What it does |
|---|---|
| `make up` | build and start the six services |
| `make down` | stop them, keep the data |
| `make clean` | stop them and **delete** the volumes |
| `make logs` | follow the API logs |
| `make logs-worker` | follow the worker and beat logs |
| `make psql` | open psql on the database |
| `make revision m="..."` | generate a migration from the models |
| `make migrate` | apply the migrations |
| `make ingest` | trigger an ingestion now |
| `make workers` | check the workers respond and their queues |
| `make test` | run the test suite |
| `make createdb-test` | create the test database (run once) |
| `make check` | everything the CI runs |

## Layout

```
backend/          FastAPI application
  app/core/       config, database, logging, celery
  app/modules/    business modules (health, events)
  app/registry.py every model, imported for Alembic
  alembic/        migrations
  tests/          conftest.py holds the database and fixture helpers
infra/postgres/   database init scripts
.github/          CI workflow
```
