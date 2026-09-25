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

Then get two free API keys and paste them into `.env`. The app refuses to
start without them.

| Key | Where | Variable |
|---|---|---|
| Finnhub | [finnhub.io/register](https://finnhub.io/register) | `APP_FINNHUB_API_KEY` |
| FRED | [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) | `APP_FRED_API_KEY` |

Finally:

```bash
make up
make migrate
make ingest-news
make ingest-calendar
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

Before committing:

```bash
make fix     # ruff check --fix, then ruff format
make check   # everything the CI runs
```

## Ingestion

Two sources feed the timeline, each with its own Celery task:

| Task | Source | Schedule | What it brings |
|---|---|---|---|
| `events.ingest_news` | Finnhub | every 6 hours | ~100 market news articles |
| `events.ingest_calendar` | FRED | 07:00 and 20:00 UTC | 29 US economic indicators, past and upcoming |

`worker-io` consumes the `ingestion` queue, `worker-cpu` the `compute` queue
(used from phase 3 on). Beat schedules both.

```bash
make ingest-news       # trigger one now
make ingest-calendar
make workers           # both workers should reply pong
make logs-worker       # follow what they do
```

Ingestion is idempotent: the same event is updated, never duplicated.

Calendar figures are **frozen once published**: FRED revises its series
afterwards — July payrolls went from −23k to +21k — and the timeline must show
what the market saw that day. Upcoming events stay open until their value
arrives.

The indicators are listed in `fred_indicators.py`. After editing that list:

```bash
export FRED_API="your key"
cd backend && uv run python scripts/check_fred.py
```

It checks every series against the live API: right release, fresh data,
seasonally adjusted, and a value for the chosen unit.

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
| `make ingest-news` | trigger a news ingestion now |
| `make ingest-calendar` | trigger a calendar ingestion now |
| `make workers` | check the workers respond and their queues |
| `make createdb-test` | create the test database (run once) |
| `make test` | run the test suite |
| `make fix` | apply every automatic fix |
| `make check` | everything the CI runs |

## Layout

```
backend/
  app/core/            config, database, logging, celery, shared types
  app/modules/events/  models, repository, tasks
    ingestion/         the connector protocol and one file per source
  app/registry.py      every model, imported for Alembic
  alembic/             migrations
  scripts/             one-off checks, not part of the test suite
  tests/               conftest.py holds the database and fixture helpers
    fixtures/          recorded API responses
infra/postgres/        database init scripts
.github/               CI workflow
```
