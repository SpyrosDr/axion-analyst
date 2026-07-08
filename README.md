# Axion Analyst Investigation Workbench

Axion Analyst Investigation Workbench is an AI-assisted fraud investigation tool that helps investigators structure, assess, and document fraud-related cases.

It is not a fraud detection engine, AML transaction monitoring system, or alert-generation platform. It focuses on the investigation phase after a suspicious case, alert, concern, or internal issue has already been identified. The AI supports the investigator — human review remains central to all conclusions.

## Features

* **Case management** — create cases with context, description, and evidence items; add evidence as an investigation develops.
* **AI-assisted analysis** — one click runs entity extraction, timeline construction, risk assessment, and draft report generation. All four outputs come from a single AI analysis, so they are internally consistent.
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

# Optional: seed three fake demo cases (owned by the first admin):
python -m app.sample_data

uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000` — interactive docs at `/docs`. The SQLite database file (`aletheia.db`) is created automatically on first run.

There are no schema migrations: if you pull a change that alters the database models, delete `backend/aletheia.db` and re-run the `create_admin` bootstrap (a stale database will fail with "no such column" errors).

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
* `SECRET_KEY` — signs login tokens. The dev default is insecure; **always override it outside local development**.
* `ACCESS_TOKEN_EXPIRE_HOURS` — login token lifetime (default 24).

## Users, access, and sharing

* Accounts are created by admins only (no public signup). The first admin is bootstrapped via `python -m app.create_admin`.
* A case is visible only to its owner and to collaborators the owner has added. Collaborators can view and edit (add evidence, run analysis) but cannot manage collaborators or delete the case.
* Requests for cases you cannot access return 404, deliberately not revealing whether the case exists.

**Known limitation**: logging out clears the token from the browser but does not invalidate it server-side — an issued token remains valid until it expires (24h by default). There is no token revocation list in this version. Rotating `SECRET_KEY` invalidates all outstanding tokens at once if ever needed.

## Testing

```bash
pytest
```

Run from the repository root. Tests use an isolated temporary database and never touch your development data.

## Security and data handling

This repository should contain only source code and fake sample evidence. It should never contain:

* real API keys,
* real customer data,
* real investigation files,
* real financial records,
* confidential evidence,
* production credentials.

Local secrets belong in `backend/.env`, which must not be committed. Public configuration examples live in `backend/.env.example`.

**Pseudonymization**: before any case text is sent to a real AI provider (`anthropic`/`openai`), `backend/app/ai/pseudonymizer.py` detects person names, email addresses, and account numbers (regex-based, the same heuristics the `mock` entity extractor uses) and replaces each with a consistent fake stand-in for that call — e.g. "Jack Doom" becomes "John Doe" everywhere it appears in the context, description, and evidence, so the AI can still correlate the same entity across the text. The real values are restored in the structured result before it's stored or displayed, so they're never persisted in fake form. This reduces exposure of confidential names/emails/accounts to the third-party provider but is not a hard guarantee: the detection is heuristic and can occasionally miss unusual name formats or over-match capitalized phrases that aren't names (over-matching only means extra, harmless masking, not under-masking). The `mock` provider never calls a third party, so this step is skipped entirely when `AI_PROVIDER=mock`.
