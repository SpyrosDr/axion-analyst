# Axion Analyst — Investigation Case-file Accelerator

Axion Analyst helps financial-crime, compliance, and investigation teams turn a small, mixed case file into an evidence-linked chronology, reviewable risk signals, and a draft investigation report. It reduces the administrative first pass while keeping judgement, decisions, and accountability with the investigator.

It is not a fraud detection engine, AML transaction monitoring system, or alert-generation platform. It focuses on the investigation phase after a suspicious case, alert, concern, or internal issue has already been identified. The AI supports the investigator — human review remains central to all conclusions.

New to the app? See the [How-To Guide](docs/how-to-guide.md) for task-focused instructions on sign-in, cases, evidence, entity search, analysis results, collaborators, and user management.

## Features

* **Case management** — create cases with context, description, and evidence items; add evidence as an investigation develops. Evidence items support file attachments (screenshots, PDFs, statements) alongside text.
* **AI-assisted analysis** — one click runs entity extraction, timeline construction, risk-signal assessment, and draft report generation. All four outputs come from a single AI analysis, so they are internally consistent.
* **Evidence-led output** — timeline events and mock-extracted entities retain their source evidence reference; the interface makes draft status explicit so outputs are investigated, not treated as autonomous conclusions.
* **Multi-user with per-case sharing** — admin-created accounts, JWT login, cases are private to their owner by default, and owners can add colleagues as collaborators with full view/edit access.
* **Quick Assess** — a stateless one-shot assessment form for a fast first read on a case, with nothing persisted.
* **Pluggable AI providers** — `mock` (built-in keyword/regex heuristics, no API key needed), `anthropic` (Claude), or `openai`, selected via one environment variable.
* **Pseudonymization before AI calls** — when using a real provider (`anthropic`/`openai`), person names, email addresses, and account numbers are swapped for consistent fake stand-ins before the case text leaves the system, then mapped back to the real values in the response. See [Security and data handling](#security-and-data-handling).

## Architecture

* **Backend**: FastAPI + SQLAlchemy + SQLite (`backend/`). Routes → services → models layering; AI provider abstraction in `backend/app/ai/`.
* **Frontend**: React + Vite (`frontend/`), no router or state library — a deliberately small single-page app. The dev server proxies `/api/*` to the backend.

## Getting started

Do the one-time setup below for the backend and frontend first. After that, `./dev.sh` from the repo root starts both dev servers together and stops both on Ctrl-C — no need to run them in separate terminals by hand.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create the first admin account (required before anything else works):
python -m app.create_admin <username> <password>

# Optional: seed four fictional demo cases (owned by the first admin), including
# the flagship vendor-payment / conflict-of-interest case:
python -m app.sample_data

uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000` — interactive docs at `/docs`. The SQLite database file (`aletheia.db`) is created automatically on first run.

### Database migrations

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/) (`backend/alembic/`). `init_db()` runs automatically on every app startup (and before `create_admin`/`sample_data`) and migrates the database to the latest schema — including a database created by an older version of this app before Alembic existed, which gets detected and stamped rather than replayed. There's no need to delete `aletheia.db` when you pull a change that alters the models.

If you change a SQLAlchemy model, generate the migration for it:

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
```

Review the generated file in `backend/alembic/versions/` before committing — autogenerate is a good first draft, not a guarantee (it can miss renames, check constraints, and some SQLite-specific changes).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and sign in with the admin account you created.

## Configuration

Copy `backend/.env.example` to `backend/.env` and adjust as needed. Key variables:

* `AI_PROVIDER` — `mock` (default, no key needed) | `anthropic` | `openai`.
* `ANTHROPIC_API_KEY` — required for `anthropic`; model defaults to `claude-haiku-4-5`.
* `OPENAI_API_KEY` and `OPENAI_MODEL` — both required for `openai` (pick a current model that supports Structured Outputs).
* `SEARCH_PROVIDER` — backend for the entity web-search tool: `mock` (default, no key needed) | `anthropic` | `openai` | `tavily`. `anthropic`/`openai` reuse the API keys/models above via each provider's hosted web-search tool; `tavily` needs `TAVILY_API_KEY`.
* `SEARCH_CACHE_TTL_SECONDS` — how long an identical entity search (same query + entity type + provider) is served from a previous result instead of re-hitting the search provider (default 3600s / 1 hour). Set to `0` to disable caching.
* `SECRET_KEY` — signs login tokens. The dev default is insecure; **always override it outside local development**. If `ENVIRONMENT=production` and `SECRET_KEY` is still the default, the app refuses to start rather than boot insecurely.
* `ENVIRONMENT` — `development` (default) | `production`. Only gates the `SECRET_KEY` check above.
* `ACCESS_TOKEN_EXPIRE_HOURS` — login token lifetime (default 24).
* `LOGIN_RATE_LIMIT_*` — login brute-force throttling (see below).
* `CORS_ALLOWED_ORIGINS` — comma-separated origins allowed to call the API cross-origin. Defaults to the Vite dev server; set to your real frontend origin(s) in production.
* `EVIDENCE_UPLOAD_DIR` — where evidence attachment files are stored on disk (default `backend/data/evidence_attachments`). Point this at a separate volume/mount in production.
* `EVIDENCE_MAX_ATTACHMENT_SIZE_BYTES` — per-file upload size limit (default 20MB).
* `EVIDENCE_ALLOWED_ATTACHMENT_EXTENSIONS` — comma-separated, no dots (default `png,jpg,jpeg,gif,webp,pdf,txt,csv,eml,docx,xlsx`). Deliberately excludes anything a browser might execute or render inline (`html`, `svg`, `js`, ...) — an attachment is meant to be evidence, not interpreted content.

## Users, access, and sharing

* Accounts are created by admins only (no public signup). The first admin is bootstrapped via `python -m app.create_admin`.
* A case is visible only to its owner and to collaborators the owner has added. Collaborators can view and edit (add evidence, run analysis) but cannot manage collaborators or delete the case.
* Requests for cases you cannot access return 404, deliberately not revealing whether the case exists.
* Failed logins are throttled in-process: an account locks out after `LOGIN_RATE_LIMIT_ATTEMPTS` failures (default 5) within `LOGIN_RATE_LIMIT_WINDOW_SECONDS` (default 300s), and a client IP locks out after a larger `LOGIN_RATE_LIMIT_IP_ATTEMPTS` (default 20) — catching a spray across many usernames without punishing a whole shared IP for one mistyped password. A locked-out attempt gets `429` with a `Retry-After` header. This state lives in the process's memory (no Redis), so it resets on restart and isn't shared across multiple worker processes.

**Known limitation**: logging out clears the token from the browser but does not invalidate it server-side — an issued token remains valid until it expires (24h by default). There is no token revocation list in this version. Rotating `SECRET_KEY` invalidates all outstanding tokens at once if ever needed.

## Testing

```bash
pytest
```

Run from the repository root. Tests use an isolated temporary database and never touch your development data.

```bash
cd frontend
npm test          # run once
npm run test:watch  # re-run on change
```

Component tests use [Vitest](https://vitest.dev/) + Testing Library, with `../api` mocked so no backend is needed. Coverage today is limited to permission-sensitive UI — `ManageUsers` and `Collaborators` — where a rendering bug (e.g. a role control appearing for a user who shouldn't get one) is an access-control bug, not just a cosmetic one.

## Security and data handling

This repository should contain only source code and fake sample evidence. It should never contain:

* real API keys,
* real customer data,
* real investigation files,
* real financial records,
* confidential evidence,
* production credentials.

The flagship case at `backend/data/sample_cases/vendor_payment_conflict_case.json` is entirely synthetic. It contains a vendor onboarding file, corporate-registration extract, emails, transaction extracts, an interview note, and a bank-account comparison so the demo can be run end-to-end without customer material.

Local secrets belong in `backend/.env`, which must not be committed. Public configuration examples live in `backend/.env.example`.

**Pseudonymization**: before any case text is sent to a real AI provider (`anthropic`/`openai`), `backend/app/ai/pseudonymizer.py` detects person names, email addresses, and account numbers (regex-based, the same heuristics the `mock` entity extractor uses) and replaces each with a consistent fake stand-in for that call — e.g. "Jack Doom" becomes "John Doe" everywhere it appears in the context, description, and evidence, so the AI can still correlate the same entity across the text. The real values are restored in the structured result before it's stored or displayed, so they're never persisted in fake form. This reduces exposure of confidential names/emails/accounts to the third-party provider but is not a hard guarantee: the detection is heuristic and can occasionally miss unusual name formats or over-match capitalized phrases that aren't names (over-matching only means extra, harmless masking, not under-masking). The `mock` provider never calls a third party, so this step is skipped entirely when `AI_PROVIDER=mock`.

## License

Copyright (C) 2026 Spyridon Drakopoulos

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.

Because this is the AGPL, running a modified version of Axion Analyst as a
network service obliges you to offer its users the corresponding source of your
modified version.
