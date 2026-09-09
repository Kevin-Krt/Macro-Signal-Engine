<div align="center">

# 🗺️ ROADMAP — Macro Signal Engine

**Commit-by-commit delivery plan, with the validation test for every step.**

`132 commits` · `8 phases` · `6 to 7 weeks part-time`

</div>

---

## 📖 How to read this document

Every phase is a **shippable increment**: it ends with something that runs and can be shown. That is what prevents the project from being abandoned after three weeks.

Each commit has three columns:

| Column | What it is |
|---|---|
| **Message** | The exact commit message to write |
| **Task** | What you build |
| **✅ Validation test** | How you verify it works **before** committing |

> 🎯 **Golden rule: never commit without running the validation column.** A commit that breaks the project forces you to go back, and a clean history is exactly what a recruiter looks at.

---

## 📝 Commit message convention

The standard used is **Conventional Commits**. Most teams adopt it, it allows changelog generation, and it shows immediately in a `git log`.

### Format

```
type(scope): imperative description, lowercase, no trailing period
```

- **72 characters maximum** on the first line
- **Imperative present**: `add`, `fix`, `remove` — not `added` nor `adds a function that...`
- **One commit = one intent.** If you write "and" in the message, it is probably two commits.

### Types

| Type | When to use it | Example |
|---|---|---|
| `feat` | New user-visible feature | `feat(auth): add refresh token rotation` |
| `fix` | Bug fix | `fix(rag): correct the rrf fusion order` |
| `docs` | Documentation only | `docs: add the architecture diagram` |
| `style` | Formatting, no logic change | `style: apply ruff format` |
| `refactor` | Rewrite without behaviour change | `refactor(events): extract parsing into a service` |
| `perf` | Performance improvement | `perf(rag): add an embedding cache` |
| `test` | Add or fix tests | `test(auth): cover replay detection` |
| `build` | Dependencies, Docker, build system | `build(backend): add the multi-stage dockerfile` |
| `ci` | Continuous integration pipeline | `ci: add the pyrefly job` |
| `chore` | Config, tooling, misc | `chore: add pre-commit` |
| `revert` | Revert a commit | `revert: revert feat(rag) 3f2a1b` |

### Scopes for this project

`core` · `auth` · `users` · `events` · `rag` · `conversations` · `evaluation` · `health` · `front` · `infra` · `ci` · `docs`

The scope is optional but recommended: it makes `git log` readable at a glance.

### Examples

```bash
✅ feat(auth): add google id_token verification
✅ fix(events): fix deduplication on accented titles
✅ test(rag): cover chunking with overlap
✅ build(infra): split the ingestion and processing queues
✅ docs(adr): justify the pgvector choice

❌ update                          # no information
❌ fix bug                         # which bug?
❌ WIP                             # never commit a WIP on main
❌ Added authentication.           # not imperative, trailing period
❌ feat: add auth and fix the timeline and update the readme
```

### Commit body (optional but valuable)

For a non-trivial commit, add a body after a blank line. That is where you explain the **why**, never the *how* — the code already says how.

```
feat(auth): add refresh token replay detection

A revoked token presented again means either theft or a client bug.
In both cases the right answer is to invalidate the whole token
family rather than simply rejecting the request.

Ref: docs/adr/0002-own-tokens-vs-google.md
```

---

## 🌿 Git hygiene

Even solo, work like a team. This is exactly what a recruiter checks when opening your repository.

| Rule | Why |
|---|---|
| One **branch per phase**: `phase/01-ingestion` | Enables one PR per phase, therefore a readable history |
| One **Pull Request per phase**, self-reviewed | Forces review and leaves a trace of your reasoning |
| **Squash only if necessary** — keep your commits atomic | They are what tells the story of your work |
| `main` **always green** | CI must never be red on `main` |
| Never `--force` on `main` | |
| **Commits spread over time** | 132 commits over 6 weeks is credible. 132 commits in 2 days is not |

> 💡 A clean `git log --oneline` of 132 commits spread over six weeks is worth more, to a lead developer, than one extra feature.

---

## 📅 Overview

| Phase | Subject | Commits | Duration | Deliverable |
|:---:|---|:---:|:---:|---|
| **0** | Foundations | 14 | 2–3 d | `make up` works, CI green |
| **1** | Ingestion & timeline | 18 | 1 wk | Real event timeline online |
| **2** | Authentication | 22 | 1 wk | Google sign-in + persistent session |
| **3** | LLM classification | 14 | 4–5 d | Events classified automatically |
| **4** | RAG & chat | 20 | 1.5 wk | Question about gold → sourced answer |
| **5** | 2FA & profile | 14 | 3–4 d | End-to-end TOTP flow |
| **6** | Evaluation | 14 | 4–5 d | Real hit-rate published |
| **7** | Polish & production | 16 | 1 wk | The link you put on your CV |
| | **Total** | **132** | **6–7 wk** | |

> ⚠️ **If the schedule tightens:** phases 0 to 4 already make a perfectly defensible interview project. Phases 5 to 7 take it from good to remarkable. Never sacrifice phase 0 to save time — it is what makes all the others possible.

---

# 🏁 DAY 1 — Setup

Before writing a single line of application code, close these six points. Budget half a day.

### 1. Accounts and keys

- [ ] **Google Cloud Console** → create a project, configure the consent screen under **Google Auth Platform**, create **Web application** credentials, add `http://localhost:8000/api/auth/google/callback` as an authorised redirect URI. Collect `client_id` and `client_secret`. ⚠️ Also add yourself under **Audience → test users**, otherwise your own sign-in is refused.
- [ ] **LLM provider** → create an API key and **immediately set a monthly spending limit**. This is the classic trap: a misconfigured retry loop can burn a budget overnight.
- [ ] **News API** → free account at Finnhub or Marketaux, collect the key.
- [ ] **GitHub** → create the repository private for now, make it public in phase 7.

### 2. Local environment

- [ ] Docker and Docker Compose installed, `docker run hello-world` works
- [ ] Node 24 LTS (`node -v`) — Node 20 is removed from GitHub runners on 16 Sept 2026
- [ ] `uv` installed **outside any venv** (`curl -LsSf https://astral.sh/uv/install.sh | sh`), Python 3.14 via `uv python install 3.14`
- [ ] An editor configured with the **Ruff** and **Pyrefly** extensions — one type checker, the same one as in CI

### 2 bis. The trap that costs an hour at commit 4

Your code will live in `backend/app/`. Three tools — `python`, `pytest`, `pyrefly` — each have **their own idea** of the import root, and will give you three different errors for a single cause.

The fix: declare the package in `pyproject.toml` and install it, rather than patching a path per tool.

```toml
[build-system]                          # ⚠️ WITHOUT this section, the next one is SILENTLY ignored
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

Verification, before going further:

```bash
uv run python -c "import app; print(app.__file__)"
```

And one rule: **the terminal is the source of truth, not the editor's squiggles.** If Pylance and Pyrefly disagree, Pyrefly wins — it is the one running in CI. Disable Pylance analysis, or install the Pyrefly extension.

### 3. Secrets

```bash
openssl rand -hex 32              # → JWT_SECRET
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # → FERNET_KEY
```

⚠️ These two keys must be **different**. If the JWT secret leaks, the TOTP secret must not fall with it.

### 4. The tracking board

Create a GitHub Project on the repository with three columns: `Todo`, `In Progress`, `Done`. Import the 8 phases as issues. This gives you a publicly visible project-management history — a rare and noticed detail.

### 4 bis. The three non-negotiable constraints on tests

Set now, they will save you from redoing everything in phase 7:

| Constraint | Why |
|---|---|
| **No real network calls** | On the GitHub runner there is no `.env`, no key, and outbound calls are slow. A test that depends on them passes locally and fails in CI |
| **Suite under 10 seconds** | That is what makes it runnable on every commit rather than once a day |
| **Fixtures in `function` scope** | A fixture returning a **mutable** object in `module` scope contaminates later tests, and execution order becomes significant — the worst kind of bug to diagnose |

For external clients: a fake conforming to the `Protocol` when the dependency is injected, `respx` when you test the HTTP client itself. The rule: **replace as little as possible.** The more you replace, the less you test.

⚠️ **The limit to know:** a fake only tests what you wrote into it. It verifies that *your code reacts correctly to a given response*, not that the API actually returns that response. Hence recorded responses from commit 18 onward, and a nightly contract test that really calls the API to check its shape.

### 5. Cadence

Decide your slot now and hold it. **Two hours a day held for six weeks** is worth infinitely more than ten hours one Sunday then nothing for a fortnight — and the GitHub contribution graph shows it.

### 6. The habit to build

Before every commit, in order:

```bash
make lint && make test && git add -p && git commit
```

`git add -p` shows you your diff **hunk by hunk** and waits for `y` (stage it), `n` (leave it), `s` (split further). It forces you to re-read your own work, and it lets you extract two clean commits from one messy session. It is the best habit you can build right now.

---

# 🧱 PHASE 0 — Foundations

**14 commits · 2 to 3 days · branch `phase/00-foundations`**

> 🎯 **Goal:** a skeleton that boots, a database that answers, a green CI. Nothing functional, but everything else depends on it.

| # | Message | Task | ✅ Validation test |
|:---:|---|---|---|
| 1 | `chore: initialise the repository` | `git init`, `.gitignore` (Python, Node, `.env`), MIT `LICENSE`, skeleton README | `git status` lists no sensitive file ; `git check-ignore -v .env` shows the rule that excludes it |
| 2 | `build(infra): add postgres and redis to compose` | `docker-compose.yml` with both services and their volumes | `docker compose up db redis` then `pg_isready -h localhost` → accepting ; `redis-cli ping` → `PONG` |
| 3 | `build(infra): enable the pgvector extension` | `pgvector/pgvector:pg16` image, init script `CREATE EXTENSION vector` | `make psql` then `SELECT extname FROM pg_extension WHERE extname='vector';` → 1 row |
| 4 | `build(backend): initialise the python project` | `pyproject.toml`: `[project]`, `[dependency-groups] dev`, `[build-system]` hatchling, ruff / pyrefly `preset="strict"` / pytest `asyncio_mode="auto"` config | `uv sync` with no error ; `uv run ruff check` and `uv run pyrefly check` pass ; `uv.lock` is committed |
| 5 | `feat(core): add pydantic settings configuration` | `core/config.py`, reads `.env`, typed values | Unit test: a missing required variable raises `ValidationError` **at startup**, not at first use |
| 6 | `feat(core): add the async sqlalchemy session` | `core/database.py`: engine, `async_session`, `Base` | Script: open a session, `SELECT 1`, close → no unclosed-connection warning |
| 7 | `feat(health): add the health endpoint` | `modules/health/router.py`, actually checks db **and** redis | `curl localhost:8000/api/health` → 200. Then `docker compose stop redis` → **503**, not 200 |
| 8 | `build(backend): add the multi-stage dockerfile` | Build stage + runtime stage, non-root user | `docker build` OK ; `docker run --rm img whoami` ≠ `root` ; `docker images` → size < 300 MB |
| 9 | `build(infra): add the api service with healthcheck` | `api` service, `healthcheck`, `depends_on: condition: service_healthy` | `make down && make up`: the API does **not** start before the database is ready. Check the logs |
| 10 | `feat(core): configure structured json logging` | `core/logging.py`, `request_id` middleware, JSON format | One request produces a JSON line containing `request_id`, `method`, `path`, `status`, `duration_ms` |
| 11 | `build(backend): initialise alembic` | `alembic/`, `env.py` importing `app.registry`, first empty revision | `make migrate` OK ; `alembic downgrade base` then `upgrade head` with no error |
| 12 | `ci: add the continuous integration workflow` | `.github/workflows/ci.yml`: `actions/checkout@v5`, `astral-sh/setup-uv@v5`, then `uv sync --frozen`, `ruff check`, `ruff format --check`, `pyrefly check`, `pytest` with postgres + redis services | Push → green badge. Break the lint on purpose → red badge, then fix. Verify that a `pyproject.toml` / `uv.lock` mismatch makes `--frozen` **fail** |
| 13 | `chore: add pre-commit` | `ruff-check --fix`, `ruff-format`, `gitleaks`, `end-of-file-fixer`, `trailing-whitespace`, `check-added-large-files` | `git commit` of a file containing a fake `sk-ant-…` key → **blocked**. ⚠️ `detect-private-key` alone would see nothing: it only recognises `-----BEGIN … PRIVATE KEY-----` headers, not API keys |
| 14 | `docs: add the makefile and the getting started guide` | Complete `Makefile`, README section | **Most important test of the phase:** clone the repository into `/tmp`, follow the README to the letter, get a `/health` returning 200 |

<details>
<summary>🧪 <b>Phase 0 exit test</b></summary>

```bash
cd /tmp && rm -rf test-clone
git clone <your-repo> test-clone && cd test-clone
cp .env.example .env      # fill it in
make up && make migrate
curl -s localhost:8000/api/health | jq
docker compose stop redis && curl -s -o /dev/null -w "%{http_code}" localhost:8000/api/health   # → 503
docker compose start redis
```

**Pass criterion:** a stranger can run your project following only the README.

</details>

<details>
<summary>⚠️ Traps in this phase</summary>

- **Forgetting `depends_on: condition: service_healthy`.** The API starts before Postgres and crashes on first launch. This is the most widespread flaw in student projects.
- **`.env` accidentally committed at commit 1.** Once in history, you have to rewrite history. Check `git status` before the first `git add`.
- **A healthcheck that always returns 200.** A `/health` that tests nothing is useless. It must really ping the database and Redis.

</details>

---

# 📥 PHASE 1 — Ingestion & timeline

**18 commits · 1 week · branch `phase/01-ingestion`**

> 🎯 **Goal:** real data in the database, displayed in a UI. No authentication yet — that comes next, so as not to mix two hard subjects.

| # | Message | Task | ✅ Validation test |
|:---:|---|---|---|
| 15 | `feat(events): add the event model` | `modules/events/models.py` + migration | `make revision` then `make migrate` ; `\d events` in psql shows the columns |
| 16 | `feat(events): add the source uniqueness constraint` | `UNIQUE (source, external_id)` | Test: insert the same pair twice → `IntegrityError` |
| 17 | `feat(events): define the connector protocol` | `ingestion/base.py`, a **`Protocol`** `SourceConnector` — structural typing, no inheritance required | `pyrefly check` passes ; a fake connector satisfies the interface **without inheriting from it** and is tested |
| 18 | `feat(events): implement the macro calendar connector` | HTTP call, parsing into `Event` | Test with a recorded response (`respx`) → N events parsed, dates in UTC |
| 19 | `test(events): cover calendar parsing` | Nominal case, truncated response, missing field | `pytest` green ; a malformed response raises a typed exception, not a raw `KeyError` |
| 20 | `feat(events): add the idempotent upsert` | `ON CONFLICT (source, external_id) DO UPDATE` | **Key test:** run ingestion twice in a row → `SELECT count(*)` identical |
| 21 | `build(infra): add celery with two workers and beat` | `core/celery_app.py`, `worker-io`, `worker-cpu`, `beat` services, queue routing | `celery -A app.core.celery_app inspect ping` → both workers answer |
| 22 | `feat(events): add the scheduled fetch_calendar task` | Task on the `ingestion` queue, Beat schedule every 6 h | `make ingest` fills the table ; worker logs show the task |
| 23 | `feat(events): add retry with backoff` | `autoretry_for`, `retry_backoff=True`, `max_retries=3` | Mock a source returning 500 → 3 spaced attempts then a clean failure, without corrupting the database |
| 24 | `feat(events): implement the news connector and dedup` | News connector + `dedup.py` on a normalised title hash | Two articles with titles identical up to case → one row |
| 25 | `feat(core): add reusable pagination` | `core/pagination.py`, `Page[T]` schema | Test: `limit=10&offset=20` returns the right items and a correct `total` |
| 26 | `feat(events): expose the event list` | `GET /api/events` + `asset_class`, `from`, `to`, `direction` filters | `curl "…/api/events?from=2026-09-01"` → 200, filtered items, pagination present |
| 27 | `feat(events): expose detail and upcoming events` | `GET /api/events/{id}` and `/upcoming` | Unknown `id` → **404** with a structured error body, not a 500 |
| 28 | `test(events): add api integration tests` | Tests with an ephemeral database and fixtures | `make test-back` green ; `events` module coverage > 70 % |
| 29 | `build(frontend): initialise react vite typescript tailwind` | Scaffolding, ESLint, Prettier, `features/` structure | `npm run dev` shows a page ; `npm run build` with no TypeScript error |
| 30 | `feat(front): add the api client and tanstack query` | `api/client.ts`, Query provider, shared types | The page shows **real** events from the API, not hardcoded data |
| 31 | `feat(front): add the timeline page with filters` | `features/events/TimelinePage.tsx`, cards, date and asset filters | Changing a filter changes the list ; the URL reflects the filters (search params) |
| 32 | `feat(front): add loading and error states` | Skeletons, error message, empty state | **Stop the API** (`docker compose stop api`) → clear message, never a blank screen or a crash |

<details>
<summary>🧪 <b>Phase 1 exit test</b></summary>

1. `make up` → wait 10 minutes → `SELECT count(*) FROM events;` is **> 0** with no manual action
2. Run `make ingest` three times → the count does not grow artificially
3. Open the front → the timeline shows real, filterable events
4. Stop the API → the UI shows a clean error

**Pass criterion:** you can show the screen to someone and they understand what the application does.

</details>

<details>
<summary>⚠️ Traps in this phase</summary>

- **Time zones.** Store **everything** in UTC (`TIMESTAMPTZ`), convert only for display. A CPI release at 14:30 ET, badly converted, shifts your whole evaluation later.
- **Testing against the real API.** Your tests become slow, non-deterministic, and burn your quota. Record responses from the very first connector.
- **Wanting to do authentication at the same time.** Resist. One phase, one subject.

</details>
---

# 🔐 PHASE 2 — Authentication

**22 commits · 1 week · branch `phase/02-auth`**

> 🎯 **Goal:** the phase worth the most in interviews. Take your time on commits 43 to 45 — that is where the difference with other candidates is made.

| # | Message | Task | ✅ Validation test |
|:---:|---|---|---|
| 33 | `feat(users): add the user model` | `modules/users/models.py` + migration, `google_sub` UNIQUE | `\d users` shows the unique index on `google_sub` |
| 34 | `feat(auth): add the token models` | `RefreshToken` (with `family_id`, `replaced_by_id`), `RecoveryCode` | Migration applied ; foreign keys and indexes present |
| 35 | `feat(auth): add jwt utilities` | `security.py`: `create_access_token`, `decode_token` | Test: a created token decodes ; the `sub`, `exp`, `jti`, `amr` claims are present |
| 36 | `test(auth): cover expiry and invalid signature` | JWT edge cases | Expired token → dedicated exception ; tampered signature → dedicated exception. **Never** an `except: pass` |
| 37 | `feat(auth): add refresh token generation` | 32 bytes via `secrets.token_urlsafe`, **hashed before storage** | Test: the plaintext token appears **nowhere** in the database. Verify with a `SELECT` |
| 38 | `feat(auth): start the google oauth flow` | `GET /auth/google`, signed `state` + PKCE (`code_verifier` / `code_challenge`) | Call → 302 to Google with `state`, `code_challenge`, `nonce` in the URL |
| 39 | `feat(auth): implement the callback and verify the id_token` | Code exchange, JWKS signature verification, `aud`, `iss`, `exp`, `nonce` | Test with mocked JWKS: an incorrect `aud` is **rejected**. An unknown `state` is rejected |
| 40 | `test(auth): cover id_token verification` | Invalid signature, wrong `iss`, expired token, missing `nonce` | All 4 cases raise an exception. None slips through |
| 41 | `feat(auth): upsert the user on sign-in` | Create or update on `google_sub`, `last_login_at` | Two sign-ins from the same Google account → **one** user in the database |
| 42 | `feat(auth): set the refresh cookie` | `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/api/auth` | In DevTools: the cookie is present and **unreachable** from `document.cookie` |
| 43 | `feat(auth): implement refresh token rotation` | `POST /auth/refresh`: revoke the old one, issue a new one in the same family | Test: call refresh → new token ; the old one is marked `revoked_at` in the database |
| 44 | `feat(auth): add replay detection` | A revoked token presented → invalidate the **whole family** | **The signature test of this project.** See the block below |
| 45 | `test(auth): cover rotation replay and revocation` | Full three-act scenario | Detailed in the collapsible block below |
| 46 | `feat(auth): implement logout` | `POST /auth/logout`, revoke the family, clear the cookie | After logout, refresh fails with 401 and the cookie is gone |
| 47 | `feat(core): add the get_current_user dependency` | `get_current_user` in `core/dependencies.py` | Protected route with no token → 401 ; with a valid token → 200 ; with an expired token → 401 |
| 48 | `feat(core): add rate limiting on auth routes` | Redis limiter, `5/minute` on `/auth/*` | 6 rapid calls → the 6th returns **429** with a `Retry-After` header |
| 49 | `feat(users): expose the current profile` | `GET` and `PATCH /users/me` | `GET` returns the right data ; `PATCH` of a non-allowed field is **rejected**, not silently ignored |
| 50 | `feat(front): add the auth context and login page` | `AuthProvider`, access token **in memory only**, Google button | Full sign-in works ; `localStorage` is **empty** — check in DevTools |
| 51 | `feat(front): add the refresh interceptor` | On 401: a single refresh call, a queue for concurrent requests, replay | Wait 16 minutes, click → the session continues with no visible re-login |
| 52 | `test(front): cover the interceptor under concurrency` | 3 simultaneous 401 requests | **Exactly one** call to `/auth/refresh` is issued, and all 3 requests are replayed |
| 53 | `feat(front): add the auth guard and layout` | Redirect to login when unauthenticated, `AppShell`, sidebar | Protected URL in a private window → redirect to `/login` |
| 54 | `docs(adr): justify the own-tokens decision` | `docs/adr/0002-own-tokens-vs-google.md` | The document explains context, decision, alternatives and consequences |

<details>
<summary>🧪 <b>The commit 45 test — write it carefully</b></summary>

```python
async def test_refresh_token_replay_invalidates_family(client, user):
    # Act 1 — sign in, we get R1
    r1 = await login_as(client, user)

    # Act 2 — normal rotation: R1 → R2
    r2 = await client.post("/api/auth/refresh", cookies={"refresh": r1})
    assert r2.status_code == 200
    new_token = extract_refresh_cookie(r2)

    # Act 3 — replay R1, already revoked → 401
    replay = await client.post("/api/auth/refresh", cookies={"refresh": r1})
    assert replay.status_code == 401

    # Consequence — R2 must ALSO be invalidated (the whole family falls)
    after = await client.post("/api/auth/refresh", cookies={"refresh": new_token})
    assert after.status_code == 401
```

The last assertion is what makes the difference. One candidate in twenty implements it. Be ready to explain it in an interview: a revoked token that reappears means either theft or a client bug — in both cases the right answer is to invalidate everything, not merely to reject the request.

</details>

<details>
<summary>🧪 <b>Phase 2 exit test</b></summary>

1. Full Google sign-in from the front end
2. Wait 16 minutes, navigate → **no** re-login requested
3. DevTools → `localStorage` empty, refresh cookie is `HttpOnly`
4. Copy the refresh cookie, rotate it, replay the old one → 401 **and** the new one becomes invalid
5. 6 rapid calls to `/auth/refresh` → 429
6. `make test-back`: `auth` module coverage **> 90 %**

</details>

<details>
<summary>⚠️ Traps in this phase</summary>

- **Storing the access token in `localStorage`.** Every tutorial does it and it is vulnerable to XSS. In memory only.
- **Forgetting to verify the `nonce`.** Without it, the flow is vulnerable to `id_token` replay.
- **A looping interceptor.** If `/auth/refresh` returns 401, the interceptor must **not** call `/auth/refresh` again. Exclude that route explicitly.
- **Concurrent requests.** Three simultaneous 401s must trigger only one refresh. Without a queue, you burn your rotation and sign the user out.

</details>

---

# 🏷️ PHASE 3 — LLM classification

**14 commits · 4 to 5 days · branch `phase/03-classification`**

> 🎯 **Goal:** turn raw text into structured, usable data — reliably and testably, without ever calling the API in tests.

| # | Message | Task | ✅ Validation test |
|:---:|---|---|---|
| 55 | `feat(core): define the llm client protocol` | `core/llm/base.py`, an `LLMClient` **`Protocol`** with `complete` and `embed` | `pyrefly check` passes ; a fake client satisfies it **without inheritance**. Changing a protocol signature must fail the check **at the call site** |
| 56 | `feat(core): implement the openai client` | `openai_client.py`, `factory.py` driven by `LLM_PROVIDER` | Changing `LLM_PROVIDER` in `.env` changes the client without touching calling code |
| 57 | `feat(core): add the provider factory` | pytest fixture returning predefined responses | **Absolute rule:** no test may consume quota. Verify with `pytest --collect-only`, then by cutting the network |
| 58 | `feat(events): add the classification model` | Model + migration, with `model` and `prompt_version` | `\d classifications` ; check constraint on `direction` and on the `surprise_score` bounds |
| 59 | `feat(events): define the strict output schema` | Pydantic schema with enums and bounds | A JSON with `direction: "up"` (out-of-enum value) is **rejected** |
| 60 | `feat(events): write the versioned classification prompt` | `core/llm/prompts/classification_v1.py`, low temperature, forced JSON | The prompt explicitly instructs to return `neutral` with low confidence rather than inventing a direction |
| 61 | `feat(events): implement the classifier` | LLM call, parsing, schema validation | Test with 5 mocked responses → 5 valid classifications in the database |
| 62 | `feat(events): add the single correction retry` | One correction attempt, then `failed` status with the raw output kept | Mock returning broken JSON → one retry, then `status='failed'` and non-empty `raw` |
| 63 | `test(events): cover invalid llm output` | Valid, malformed, off-schema, empty response, timeout | All 5 cases have defined, tested behaviour. None crashes the worker |
| 64 | `feat(events): add the process_pending task` | `processing` queue, Beat every 5 minutes, anti-duplicate lock | Two parallel workers do **not** process the same event twice |
| 65 | `feat(core): add rate limiting on llm calls` | Redis limiter on the provider, respecting its quota | A burst of calls is throttled instead of returning 429 from the provider |
| 66 | `feat(events): expose classification in the api` | Join in `GET /events` and `/events/{id}` | The response contains a `classification` object or `null`, never a missing key |
| 67 | `feat(front): display classification on event cards` | Direction badge, surprise score, confidence | A low-confidence classification is visually distinguishable |
| 68 | `test(events): cover the classification pipeline` | End-to-end with a mocked client | `make test-back` green ; no network call — verify with the network off |

<details>
<summary>🧪 <b>Phase 3 exit test</b></summary>

1. `make ingest` then wait for a `process_pending` cycle → `SELECT count(*) FROM classifications` > 0
2. Every classification respects the schema: `direction` in the enum, `surprise_score` within bounds
3. A deliberately broken response leads to `status='failed'` with `raw` kept, never to a crashed worker
4. `pytest` runs with the network **off** and stays green

**Pass criterion:** you can explain why the retry is limited to a single attempt, and what happens after it.

</details>

<details>
<summary>⚠️ Traps in this phase</summary>

- **Calling the real API in tests.** Slow, non-deterministic, and it burns quota. Fixture from the very first commit.
- **An unbounded retry loop.** This is the trap that empties a budget overnight. One attempt, then `failed`.
- **Not versioning the prompt.** Without `prompt_version` in the table, you cannot compare two prompt versions later — and phase 6 loses half its value.
- **Discarding the raw output on failure.** It is exactly what you need to understand *why* the model failed.

</details>

---

# 🔍 PHASE 4 — RAG & chat

**20 commits · 1.5 weeks · branch `phase/04-rag`**

> 🎯 **Goal:** the most visible phase of the project. By the end, the question about gold returns a real sourced answer. This is the screen you will show in interviews.

| # | Message | Task | ✅ Validation test |
|:---:|---|---|---|
| 69 | `feat(rag): add the document model` | `modules/rag/models.py`, `embedding vector(1536)` column, `content_hash` | The model imports ; `pyrefly check` passes on `Mapped[list[float]]` + `Vector(1536)` |
| 70 | `feat(rag): add the hnsw and gin indexes` | Migration with a cosine HNSW index + a GIN index on `tsvector` | `\di` in psql shows both ; `EXPLAIN` of a vector query uses the HNSW index, not a seq scan |
| 71 | `feat(rag): implement chunking with overlap` | 400–600 tokens, 15 % overlap, **title + date prefix** | Test: a 2000-token text produces 4 chunks ; each starts with the event title and date |
| 72 | `test(rag): cover chunking` | Short text, long text, empty text, overlap | A text shorter than the target produces **one** chunk, not zero |
| 73 | `feat(rag): implement embeddings with redis cache` | Batches of 100, partial-failure handling, cache keyed on `content_hash` | 250 chunks → 3 calls. A failed batch does not lose the other two |
| 74 | `feat(rag): add the embed_pending task` | `processing` queue, handles classified but unindexed events | After one cycle, `SELECT count(*) FROM documents` > 0 |
| 75 | `feat(rag): implement vector search` | Cosine similarity, top 20 | A query on "inflation" surfaces relevant documents at the top |
| 76 | `feat(rag): implement lexical search` | `tsvector`, English and French configurations | **Decisive test:** a query for `FOMC` surfaces documents containing the exact acronym — which vector search alone misses |
| 77 | `feat(rag): implement reciprocal rank fusion` | `score = Σ 1/(60 + rank)` over both lists | A document present in both lists ranks above one present in only one |
| 78 | `test(rag): cover rrf ranking` | Known result set, expected order written by hand | The computed order matches the expected order exactly |
| 79 | `feat(rag): apply sql filters before retrieval` | Time window and asset classes **before** the search | `EXPLAIN` shows the filter applied before the index scan, not after |
| 80 | `feat(conversations): add the conversation models` | `Conversation`, `Message` + migration, `citations` as JSONB | Migration OK ; cascade deletion of messages tested |
| 81 | `feat(rag): write the generation prompt` | Delimited context, mandatory citations, refusal when information is absent | **Anti-hallucination test:** ask a question with no relevant document → the answer says it does not have the information, it does not invent |
| 82 | `feat(rag): implement streaming generation` | SSE, token-by-token relay | `curl -N` shows tokens as they arrive |
| 83 | `feat(rag): extract and resolve citations` | Parse cited ids, resolve to `event` objects, store in `messages.citations` | Every cited id resolves to a real event ; an unknown id is dropped, never displayed broken |
| 84 | `feat(conversations): expose the sse message endpoint` | `POST /conversations/{id}/messages` streaming | A client closing the connection mid-stream releases the resource ; user A **cannot** read user B's conversation → 404, not 403 |
| 85 | `feat(conversations): add question rewriting` | Short LLM call turning "and on silver?" into a standalone question | **Essential test:** ask a question, then "and on silver?" → retrieved documents really are about silver |
| 86 | `feat(conversations): add conversational memory` | Last 6 messages injected, summary beyond that | A 20-message conversation still answers coherently, and the summary is stored |
| 87 | `feat(front): add the chat view with streaming` | Conversation list, thread, live streaming | Text appears progressively, not in one block after 20 seconds |
| 88 | `feat(front): display clickable sources` | Citation cards under the answer | Clicking a citation opens the source event |

<details>
<summary>🧪 <b>Phase 4 exit test — the moment of truth</b></summary>

Ask exactly this question in the UI:

> "On the gold market, what do you make of the latest announcements about its price?"

**Pass criteria, all mandatory:**

- [ ] The answer streams in, not in one block after 20 seconds
- [ ] It cites **at least 2 sources**, all clickable
- [ ] The cited sources really concern gold or precious metals
- [ ] No source is older than 30 days if the question is about "the latest"
- [ ] Then ask "and on silver?" → the answer really is about the metal
- [ ] Ask something off-topic ("what's the weather in Nice?") → the model **refuses** rather than inventing

If a single criterion fails, fix it before moving on. This is the screen you will show in interviews.

</details>

<details>
<summary>⚠️ Traps in this phase</summary>

- **Forgetting the title + date prefix on chunks.** An isolated chunk saying "the rise was 0.3 %" without a date is unusable, and the model will mix up different months.
- **Filtering after the vector search.** You retrieve 20 documents, filter out 18, and are left with 2: quality collapses. Filter in SQL first.
- **Not rewriting follow-up questions.** The most common mistake in naive RAG implementations. "And on silver?" embedded as-is retrieves nothing.
- **Streaming without disconnect handling.** A client closing the tab mid-stream must release the connection, otherwise connections pile up.
- **Building the HNSW index before inserting data.** On pgvector this works but is less efficient ; at this volume it is not blocking — just be ready to explain it.

</details>
---

# 🔒 PHASE 5 — 2FA & profile

**14 commits · 3 to 4 days · branch `phase/05-2fa`**

> 🎯 **Goal:** complete the authentication with an optional second factor, properly implemented. Short but dense in security details.

| # | Message | Task | ✅ Validation test |
|:---:|---|---|---|
| 89 | `feat(core): add encryption at rest` | `core/crypto.py`, Fernet with `FERNET_KEY` | Round-trip encrypt/decrypt test ; the key is **distinct** from `JWT_SECRET` — verify in `.env` |
| 90 | `feat(auth): add the totp columns` | `totp_secret` (encrypted, nullable), `totp_enabled` + migration | An inserted secret is unreadable in the database: `SELECT totp_secret FROM users` does not return the plaintext |
| 91 | `feat(auth): implement totp setup` | `POST /auth/2fa/setup`, `pyotp` secret, `otpauth://` URI as a QR code | The QR scans in Google Authenticator or Aegis and produces codes |
| 92 | `feat(auth): implement activation verification` | `POST /auth/2fa/verify`, activates **only** after a valid code | **Key test:** call `setup` then sign out without verifying → 2FA is **not** active, the account stays reachable |
| 93 | `test(auth): verify an unverified secret stays inactive` | Explicit case | `totp_enabled` stays `false` until `verify` succeeds |
| 94 | `feat(auth): generate recovery codes` | 10 codes, shown **once**, stored hashed | A code used once is refused the second time ; plaintext codes exist nowhere in the database |
| 95 | `feat(auth): add the pending_2fa token and challenge` | 5-minute token, `amr:["pwd"]`, opens only `/auth/2fa/challenge` | **Security test:** use the `pending_2fa` token on `/users/me` → **401**. It must open no other route |
| 96 | `test(auth): cover the full 2fa journey` | setup → verify → logout → login → challenge → access | The scenario passes end to end, with real tokens generated by `pyotp` |
| 97 | `feat(auth): add totp replay protection and rate limit` | Consumed code refused, 5 attempts per minute | Replaying the same code in the same window → refused. 6 wrong codes → 429 |
| 98 | `feat(auth): implement 2fa deactivation` | `DELETE /auth/2fa`, **requires a valid TOTP code** | Deactivation without a code → 400. With a valid code → `totp_enabled` back to `false` |
| 99 | `feat(users): expose session management` | `GET /users/me/sessions`, `DELETE /users/me/sessions/{id}` | The list shows browser and date ; revoking a session signs out **that** browser only |
| 100 | `feat(users): implement account deletion` | Soft or hard deletion, cascade on personal data | After deletion, no personal data remains ; conversations are deleted |
| 101 | `feat(front): add the 2fa setup page` | QR code, verification field, recovery codes shown once | The recovery codes cannot be displayed again after closing the modal |
| 102 | `feat(front): add the 2fa challenge screen` | Code field, "use a recovery code" link | A wrong code shows a clear message without revealing whether the account exists |

<details>
<summary>🧪 <b>Phase 5 exit test</b></summary>

1. Enable 2FA from the profile, scan the QR with a real app
2. Sign out, sign in again → the challenge screen appears
3. Enter a valid code → access granted
4. Sign out, sign in, use a **recovery code** → access granted, and that code stops working
5. Intercept the `pending_2fa` token and use it on `/api/users/me` → **401**
6. Disable 2FA without providing a code → refused

</details>

<details>
<summary>⚠️ Traps in this phase</summary>

- **Activating 2FA at `setup`.** If the user closes the tab before scanning, the account is locked forever. The two-step `setup` then `verify` exists exactly for this.
- **A `pending_2fa` token that is too permissive.** If it opens routes other than the challenge, 2FA is pointless. Test it explicitly.
- **Plaintext recovery codes.** They must be hashed like passwords.
- **Too wide a TOTP window.** ±1 interval is enough (30 seconds either side). Beyond that you widen the attack surface for nothing.

</details>

---

# 📊 PHASE 6 — Evaluation

**14 commits · 4 to 5 days · branch `phase/06-evaluation`**

> 🎯 **Goal:** measure the system's performance honestly. This is the section that turns a demo into engineering work.

| # | Message | Task | ✅ Validation test |
|:---:|---|---|---|
| 103 | `feat(evaluation): add the price observation model` | Model + migration: `t0_price`, `t1_price`, `horizon_minutes`, `pct_change` | Migration OK ; uniqueness constraint on `(event_id, symbol, horizon_minutes)` |
| 104 | `feat(evaluation): implement the market data connector` | Interface + Stooq or yfinance implementation | Test with a recorded response: a series is parsed, dates are in UTC |
| 105 | `test(evaluation): cover price parsing` | Empty series, bank holiday, unknown symbol | A day with no quote does not crash the task, it produces a missing observation |
| 106 | `feat(evaluation): add the fetch_prices task` | `ingestion` queue, hourly, only events without an observation | Run the task twice → no duplicate (uniqueness constraint) |
| 107 | `feat(evaluation): implement the hit-rate computation` | Predicted direction vs sign of `pct_change`, explicit neutrality threshold | Test on a controlled set of 10 observations whose result is computed by hand |
| 108 | `test(evaluation): verify the hit-rate computation` | Nominal and neutral cases | Does a +0.02 % move classified `bullish` count as a hit? The threshold must be **explicit and documented** |
| 109 | `feat(evaluation): add the confidence interval` | Wilson interval, and expose the **n** | On 5 observations the interval is very wide — and that is correct. It must be displayed |
| 110 | `feat(evaluation): expose the summary` | `GET /api/evaluation/summary`, global + per asset + per confidence level | The response always carries the `n` next to each rate |
| 111 | `feat(front): add the evaluation page` | Global rate, interval, observation count clearly visible | A rate computed on fewer than 30 observations is shown with an explicit warning |
| 112 | `feat(front): add the breakdown by asset class` | Chart per asset class and per declared confidence level | You can see whether the model is better on currencies than on indices |
| 113 | `feat(evaluation): compare two llm providers on the same corpus` | Reclassify the **same** events with a second provider (`LLM_PROVIDER` changes, nothing else), store both sets via `classifications.model` | Both `model` values coexist ; no event is classified twice by the same model |
| 114 | `docs: publish the cost / hit-rate comparison` | Table: hit-rate, cost per 1,000 events, p50/p95 latency, invalid-JSON rate on first attempt | The table carries the **n** for every row. A 2-point gap on 40 observations is explicitly presented as **not significant** |
| 115 | `docs: document the methodology and its biases` | README section + `docs/architecture.md` | The reader understands what the number measures **and** what it does not |
| 116 | `docs(adr): justify the 60-minute window` | `docs/adr/0006-evaluation-window.md` | The choice is owned, and the alternatives (15 min, 1 day) are discussed |

<details>
<summary>🧪 <b>Phase 6 exit test</b></summary>

1. The page shows a hit-rate, its confidence interval and the number of observations
2. **The number is the real number.** If it is 51 %, you display 51 %
3. The breakdown by asset is consistent: the parts add up to the total
4. The documentation explains the limitations

> 🎯 **The real criterion:** can you explain out loud, in two minutes, what your number measures, why it is what it is, and what you would do to improve it? If yes, this phase succeeded — regardless of the value of the number.

</details>

<details>
<summary>⚠️ Traps in this phase</summary>

- **Cheating without meaning to.** Excluding "hard" events, counting only high-confidence ones, choosing the horizon after the fact: these are classic methodological biases. Fix the method **before** looking at the results.
- **Comparing two providers without freezing everything else.** Corpus, prompt, prompt version, evaluation window and neutrality threshold must be **strictly identical** across both runs. One variable changes: the model. Otherwise the comparison measures nothing.
- **Rotating providers in production.** Tempting for quotas, but it destroys the evaluation: classifications from three models are no longer comparable. One active provider, selected by environment variable — the comparison is an **experiment**, not an architecture.
- **Forgetting the observation count.** A rate without its `n` carries no information.
- **An implicit neutrality threshold.** Decide and document: below what move do you consider that nothing happened?
- **Being discouraged by a poor number.** A system at 52 % explained honestly is an excellent interview subject. A system at 90 % left unexplained is a red flag.

</details>

---

# 🚢 PHASE 7 — Polish & production

**16 commits · 1 week · branch `phase/07-production`**

> 🎯 **Goal:** turn a project that works locally into a link you put on your CV.

| # | Message | Task | ✅ Validation test |
|:---:|---|---|---|
| 117 | `test: add end-to-end integration tests` | `tests/integration/`: sign-in → ingestion → classification → question | `make test-back` green against a real PostgreSQL |
| 118 | `test(e2e): add playwright on the main journey` | Sign in → ask a question → check the citations | `make e2e` passes locally and in CI |
| 119 | `perf(conversations): paginate message history` | Lazy loading, 20 messages per page | A 200-message conversation opens in under a second |
| 120 | `fix(front): fix mobile layout` | Breakpoints, collapsible sidebar, touch targets | Tested on a real phone, not only in DevTools |
| 121 | `feat(core): add global error handling` | Exception handlers, 404 and 500 pages, uniform error body | Trigger a 500 → clean message on the front, full trace in the logs, **no** trace exposed to the user |
| 122 | `feat(front): add loading states everywhere` | Skeletons on every page, polished empty states | No page shows a blank screen while loading |
| 123 | `build(frontend): add the multi-stage dockerfile` | Vite build then static nginx serving | Final image < 50 MB ; the site serves correctly |
| 124 | `build(infra): split dev and prod compose files` | `docker-compose.override.yml` (volumes, hot reload) and `.prod.yml` (images, restart) | In prod, **no** code volume mounted ; in dev, hot reload works |
| 125 | `build(infra): add caddy and automatic tls` | Reverse proxy, automatic Let's Encrypt certificate | `https://` works with a valid certificate ; `http://` redirects |
| 126 | `ci: add the deployment workflow` | On `main`: build, push images, deploy | A push to `main` updates production with no manual step |
| 127 | `chore(infra): add healthchecks and restart policy` | `restart: unless-stopped`, healthchecks on every service | Kill the API container → it restarts on its own in under 30 seconds |
| 128 | `docs(adr): write the architecture decision records` | The 6 ADRs as context / decision / alternatives / consequences | Each ADR fits on one page and reads in two minutes |
| 129 | `docs: add screenshots` | 4 screenshots in `docs/screenshots/`, embedded in the README | The README shows the product without needing to run it |
| 130 | `docs: finalise the readme with the production url` | Demo link, badges up to date, demo section filled | A stranger understands the project in 30 seconds of reading |
| 131 | `chore: add the pr template and contributing guide` | `.github/pull_request_template.md`, `CONTRIBUTING.md` | Opening a test PR shows the template |
| 132 | `chore(release): publish version 1.0.0` | Annotated tag, GitHub release with notes, repository made public | The tag exists ; the release lists the features ; the repository is publicly visible |

<details>
<summary>🧪 <b>Phase 7 exit test — the CV checklist</b></summary>

Before putting the link in an application, all of these must be true:

- [ ] The production URL answers over HTTPS with a valid certificate
- [ ] A visitor can sign in with Google and ask a question in under a minute
- [ ] The README shows screenshots and the demo link at the top
- [ ] `git log --oneline | wc -l` ≥ 125, spread over several weeks
- [ ] CI is green on `main`
- [ ] No secret in history: `git log -p | grep -iE "api[_-]?key|secret|password"` returns nothing real
- [ ] The site is usable on a phone
- [ ] The 6 ADRs are written
- [ ] The evaluation page shows a real number
- [ ] You can explain any file in the repository out loud

</details>

---

# 📌 Appendices

## Commit distribution by type

| Type | Count | Share |
|---|:---:|:---:|
| `feat` | 79 | 60 % |
| `test` | 16 | 12 % |
| `build` | 12 | 9 % |
| `docs` | 11 | 8 % |
| `chore` | 7 | 5 % |
| `ci` | 3 | 2 % |
| `fix` / `perf` / `refactor` | 4 | 3 % |

> 💡 A `test` share around 12 % and a `docs` share around 8 % is exactly what is expected of a serious project. A repository at 100 % `feat` signals someone who writes neither tests nor documentation.

## Fallback order if time runs short

| Priority | Phases | What you get |
|:---:|---|---|
| 🟢 Essential | 0 → 4 | A complete, defensible project with RAG and authentication |
| 🟡 Strongly advised | 7 | Deployment — without it, nobody sees the project |
| 🟠 Differentiating | 6 | The honest evaluation, your best interview subject |
| 🔵 Bonus | 5 | 2FA, appreciated but not critical |

If you must cut: do **0 → 4, then 7**, and add 6 then 5 afterwards. A deployed project without 2FA is worth infinitely more than a complete one that only runs on your machine.

## The interview questions this project prepares

Prepare a two-minute answer for each. They will come up.

1. Why pgvector rather than a dedicated vector database?
2. Explain your hybrid search. Why not vector search alone?
3. How do you handle token refresh? What happens if a refresh token is stolen?
4. How do you stop your model from hallucinating?
5. Your hit-rate is X %. What is it worth, and how would you improve it?
6. Why two Celery workers and not one?
7. How do you test code that calls an LLM?
8. What does not work in your project?

> 🎯 Question 8 is the one that separates candidates. Prepare it seriously: it is the "Known limitations" section of your README, said out loud.

## Progress tracker

```
Phase 0  ░░░░░░░░░░░░░░  0/14    Foundations
Phase 1  ░░░░░░░░░░░░░░  0/18    Ingestion & timeline
Phase 2  ░░░░░░░░░░░░░░  0/22    Authentication
Phase 3  ░░░░░░░░░░░░░░  0/14    LLM classification
Phase 4  ░░░░░░░░░░░░░░  0/20    RAG & chat
Phase 5  ░░░░░░░░░░░░░░  0/14    2FA & profile
Phase 6  ░░░░░░░░░░░░░░  0/14    Evaluation
Phase 7  ░░░░░░░░░░░░░░  0/16    Production
                         ─────
                         0/132
```

Update this block at the end of every phase. Watching it fill up is the best fuel over six weeks.

---

<div align="center">

**One commit a day beats thirty on a Sunday.**

[⬅ Back to the README](README.md)

</div>
