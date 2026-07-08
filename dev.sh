#!/usr/bin/env bash
# Starts backend + frontend dev servers together and stops both on Ctrl-C.
# Assumes one-time setup is already done (see README.md): backend/.venv with
# requirements installed, an admin account created, and frontend/node_modules
# installed via `npm install`.
set -euo pipefail
set -m # give each background job its own process group so cleanup can kill
       # it and any children it spawns (uvicorn --reload forks a reloader
       # subprocess that a plain `kill` on the job's own pid would miss)
cd "$(dirname "$0")"

if [ ! -d backend/.venv ]; then
  echo "backend/.venv not found -- run the backend setup steps in README.md first." >&2
  exit 1
fi
if [ ! -d frontend/node_modules ]; then
  echo "frontend/node_modules not found -- run 'npm install' in frontend/ first." >&2
  exit 1
fi

backend_pid=""
frontend_pid=""

cleanup() {
  trap - EXIT INT TERM
  [ -n "$backend_pid" ] && kill -TERM -- "-$backend_pid" 2>/dev/null
  [ -n "$frontend_pid" ] && kill -TERM -- "-$frontend_pid" 2>/dev/null
}
trap cleanup EXIT INT TERM

(cd backend && exec .venv/bin/uvicorn app.main:app --reload --port 8000) &
backend_pid=$!

(cd frontend && exec npm run dev) &
frontend_pid=$!

wait
