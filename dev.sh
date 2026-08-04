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
  for pid in "$backend_pid" "$frontend_pid"; do
    [ -n "$pid" ] && kill -TERM -- "-$pid" 2>/dev/null
  done

  # uvicorn --reload's worker process can take a moment to release its
  # resources after SIGTERM, so give both groups a few seconds to exit
  # gracefully, then force-kill anything left. Without this, a slow child
  # combined with bash's bare `wait` resuming after a trap (a known bash
  # quirk) can leave this script hanging even though shutdown was requested.
  for _ in $(seq 1 20); do
    still_alive=0
    for pid in "$backend_pid" "$frontend_pid"; do
      [ -n "$pid" ] && kill -0 -- "-$pid" 2>/dev/null && still_alive=1
    done
    [ "$still_alive" -eq 0 ] && break
    sleep 0.25
  done
  for pid in "$backend_pid" "$frontend_pid"; do
    [ -n "$pid" ] && kill -KILL -- "-$pid" 2>/dev/null
  done

  exit 0
}
trap cleanup EXIT INT TERM

(cd backend && exec .venv/bin/uvicorn app.main:app --reload --port 8000) &
backend_pid=$!

(cd frontend && exec npm run dev) &
frontend_pid=$!

wait
