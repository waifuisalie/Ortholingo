#!/usr/bin/env bash
#
# dev.sh — one-command dev/test launcher for Ortholingo.
#
# Starts the backend (FastAPI + Whisper), the frontend, and — for phone
# testing — a cloudflared tunnel, then prints the URLs. Ctrl+C stops all of
# them. See docs/RUNNING.md for the full explanation of the moving parts.
#
# Usage:
#   ./dev.sh              phone testing: build + preview (:4173) + tunnel
#   ./dev.sh --desktop    desktop only: vite dev (:5173), no tunnel
#   ./dev.sh --assets     re-run the audio pipeline first (edge-tts), then start
#   ./dev.sh --assets --desktop   (flags combine)
#   ./dev.sh --help
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# --- options -----------------------------------------------------------------
MODE="phone"          # phone (tunnel) | desktop (localhost only)
RUN_ASSETS=0
FRONT_PORT=4173
for arg in "$@"; do
	case "$arg" in
		--desktop) MODE="desktop"; FRONT_PORT=5173 ;;
		--assets)  RUN_ASSETS=1 ;;
		-h|--help)
			sed -n '3,14p' "$0" | sed 's/^# \{0,1\}//'
			exit 0 ;;
		*) echo "unknown option: $arg (try --help)"; exit 1 ;;
	esac
done

LOGS="$ROOT/.dev-logs"
mkdir -p "$LOGS"

# --- cleanup: kill everything we started on exit / Ctrl+C --------------------
PIDS=()
cleanup() {
	echo
	echo "Stopping…"
	for pid in "${PIDS[@]:-}"; do kill "$pid" 2>/dev/null || true; done
	wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# --- prerequisites -----------------------------------------------------------
MISS=0
req() { command -v "$1" >/dev/null 2>&1 || { echo "  ✗ missing '$1' on PATH"; MISS=1; }; }
req ffmpeg; req node; req npm
[ "$MODE" = phone ] && req cloudflared
[ -x backend/.venv/bin/uvicorn ] || { echo "  ✗ backend/.venv not set up — see docs/RUNNING.md"; MISS=1; }
[ -d frontend/node_modules ]     || { echo "  ✗ frontend deps missing — run: cd frontend && npm install"; MISS=1; }
if [ "$RUN_ASSETS" = 1 ]; then
	[ -x bakeoff/.venv/bin/python ] || { echo "  ✗ bakeoff/.venv (pipeline env) missing — see docs/RUNNING.md"; MISS=1; }
fi
[ "$MISS" = 1 ] && { echo "Fix the above and re-run."; exit 1; }

# --- 0. optional: rebuild audio assets ---------------------------------------
if [ "$RUN_ASSETS" = 1 ]; then
	echo "▶ rebuilding audio assets (edge-tts — needs network)…"
	bakeoff/.venv/bin/python pipeline/build_assets.py
fi

# --- 1. backend (reuse if already healthy) -----------------------------------
if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
	echo "✓ backend already up on :8000 (reusing)"
else
	echo "▶ backend :8000 — loading Whisper models (~20s)…"
	backend/.venv/bin/uvicorn main:app --app-dir backend --port 8000 \
		> "$LOGS/backend.log" 2>&1 &
	PIDS+=($!)
	up=0
	for _ in $(seq 1 90); do
		curl -sf http://localhost:8000/api/health >/dev/null 2>&1 && { up=1; break; }
		kill -0 "${PIDS[-1]}" 2>/dev/null || { echo "  backend crashed — see $LOGS/backend.log"; exit 1; }
		sleep 1
	done
	[ "$up" = 1 ] || { echo "  backend didn't come up in 90s — see $LOGS/backend.log"; exit 1; }
	echo "  backend ready."
fi

# --- 2. frontend -------------------------------------------------------------
# Serve vite directly (not via `npm run`) so the tracked PID is the real
# server and Ctrl+C actually kills it (npm would leave an orphan).
if [ "$MODE" = phone ]; then
	echo "▶ building frontend (syncs assets/ into build)…"
	( cd frontend && npm run build ) > "$LOGS/build.log" 2>&1 \
		|| { echo "  build failed — see $LOGS/build.log"; exit 1; }
	echo "▶ frontend :$FRONT_PORT (preview — production PWA)…"
	( cd frontend && exec node_modules/.bin/vite preview --port "$FRONT_PORT" ) \
		> "$LOGS/frontend.log" 2>&1 &
	PIDS+=($!)
else
	echo "▶ syncing assets…"
	( cd frontend && npm run sync-assets ) > "$LOGS/build.log" 2>&1
	echo "▶ frontend :$FRONT_PORT (dev — hot reload)…"
	( cd frontend && exec node_modules/.bin/vite dev --port "$FRONT_PORT" ) \
		> "$LOGS/frontend.log" 2>&1 &
	PIDS+=($!)
fi

for _ in $(seq 1 30); do
	curl -sf "http://localhost:$FRONT_PORT/" >/dev/null 2>&1 && break
	sleep 1
done

# --- 3. tunnel (phone mode only) ---------------------------------------------
URL=""
if [ "$MODE" = phone ]; then
	echo "▶ cloudflared tunnel → :$FRONT_PORT …"
	cloudflared tunnel --url "http://localhost:$FRONT_PORT" > "$LOGS/cloudflared.log" 2>&1 &
	PIDS+=($!)
	for _ in $(seq 1 30); do
		URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOGS/cloudflared.log" | head -1 || true)
		[ -n "$URL" ] && break
		sleep 1
	done
fi

# --- summary -----------------------------------------------------------------
echo
echo "  ☦  Ortholingo is up."
echo "     backend   → http://localhost:8000/api/health"
echo "     frontend  → http://localhost:$FRONT_PORT"
if [ "$MODE" = phone ]; then
	echo "     phone     → ${URL:-<not found — check .dev-logs/cloudflared.log>}"
else
	echo "     (desktop mode — open the frontend URL; mic works over http on localhost)"
fi
echo
echo "  Logs: .dev-logs/{backend,frontend,cloudflared}.log   ·   Ctrl+C stops everything."
echo

# Block until Ctrl+C; the trap tears everything down.
wait
