# Running Ortholingo locally

How the dev/test stack is wired, and how to start it from scratch — on your
desktop, or on your phone (which is where the microphone gets a real workout).

## TL;DR

```bash
./dev.sh              # phone testing: backend + built PWA (:4173) + HTTPS tunnel
./dev.sh --desktop    # desktop only: backend + vite dev (:5173), no tunnel
./dev.sh --assets     # re-run the audio pipeline first, then start
```

`dev.sh` starts everything, prints the URLs, and Ctrl+C stops all of it. The
rest of this doc explains what it's doing so you can also run the pieces by
hand (and debug when something misbehaves).

## The four pieces

Two are **long-running services** you leave open; two are **one-shot commands**.

| # | Piece | Command | Port | Type | When |
|---|---|---|---|---|---|
| 1 | **Asset pipeline** | `bakeoff/.venv/bin/python pipeline/build_assets.py` | — | one-shot | Only when `content/*.yaml` changes (regenerates audio) |
| 2 | **Backend** (FastAPI + Whisper) | `backend/.venv/bin/uvicorn main:app --app-dir backend --port 8000` | **8000** | service | Always — it scores the mic |
| 3 | **Frontend** (SvelteKit) | `npm run dev` **or** `npm run build && npm run preview -- --port 4173` | **5173** / **4173** | service | Always — it's the app |
| 4 | **Tunnel** (cloudflared) | `cloudflared tunnel --url http://localhost:4173` | — | service | Only for **phone** testing |

## How they wire together

Your browser only ever talks to **one origin — the frontend**. The frontend
forwards anything under `/api` to the backend (configured in
`frontend/vite.config.js`, in both the `server` and `preview` blocks). The
phone never needs to know port 8000 exists.

```
  📱 Phone browser  (HTTPS — required for the mic)
        │
        ▼
  cloudflared quick tunnel   (random *.trycloudflare.com)
        │
        ▼
  localhost:4173   ← vite preview (the built PWA)
        │
        ├── serves the app + /assets/audio/*   (produced by the pipeline)
        │
        └── proxies /api/*  ──►  localhost:8000  ← FastAPI + faster-whisper
                                      │
                        recording → ffmpeg → whisper → per-word score
```

## Cold start by hand — phone testing

Three terminals, from the repo root, in this order:

```bash
# Terminal 1 — backend (slowest; start it first)
backend/.venv/bin/uvicorn main:app --app-dir backend --port 8000
# Wait for "Application startup complete" (~20s: it loads two Whisper models,
# `small` + `large-v3-turbo`). First-ever run downloads the weights.

# Terminal 2 — frontend (build the PWA, then serve it on 4173)
cd frontend
npm run build
npm run preview -- --port 4173

# Terminal 3 — tunnel (exposes 4173 over HTTPS)
cloudflared tunnel --url http://localhost:4173
# Copy the printed https://…trycloudflare.com URL to your phone.
```

On the phone: open the URL, allow microphone access, go to a lesson's **record**
step.

## Cold start by hand — desktop only

No tunnel, no build. `http://localhost` counts as a *secure context*, so the
mic works over plain http on your own machine.

```bash
# Terminal 1 — backend (same as above)
backend/.venv/bin/uvicorn main:app --app-dir backend --port 8000

# Terminal 2 — frontend with hot reload
cd frontend && npm run dev      # → http://localhost:5173
```

## Rebuilding audio assets (the pipeline)

Run this **only when you've edited `content/*.yaml`** — it's not part of a
normal startup.

```bash
bakeoff/.venv/bin/python pipeline/build_assets.py
```

It reads `content/units/*.yaml`, calls edge-tts, and writes `assets/audio/**`,
`assets/timings/*.json`, and `assets/manifest.json`. It's idempotent —
unchanged phrases are skipped by hash. Needs **network** (edge-tts) and
**ffmpeg**/`ffprobe` on PATH.

After running it you **must rebuild the frontend** so the new audio is copied
in — see gotcha #2.

## Gotchas

These are the things that actually bite. Read them once and save yourself an hour.

1. **The tunnel port must match the frontend port.**
   This is the classic "the mic doesn't work on mobile" bug. If the frontend is
   on 5173 (`npm run dev`) but the tunnel points at 4173, every scoring `POST`
   hits a dead port and surfaces as *"Não consegui usar o microfone…"* — even
   though the mic is fine. `dev.sh` always keeps them matched; by hand, make
   sure `--url http://localhost:<PORT>` equals the port the frontend is serving.

2. **`npm run preview` does NOT rebuild — and only `dev`/`build` sync assets.**
   `preview` just serves whatever is already in `frontend/build/`. The
   asset-copy step (`sync-assets`, which mirrors `assets/` → `frontend/static/assets`)
   runs during `npm run dev` and `npm run build`, never during `preview`. So the
   order after a pipeline run is always **pipeline → build → preview**. Skip the
   build and you'll serve stale audio.

3. **The PWA service worker caches the app.**
   After a new build, the phone keeps serving the old JS until you **reload**
   (pull-to-refresh, or close & reopen if it's installed to the home screen).
   "I changed something but the phone looks the same" is almost always this.

4. **Quick tunnels mint a fresh URL every run.**
   Restarting cloudflared = a new `*.trycloudflare.com` address to re-open on
   the phone. There's no way to keep the previous one with a quick tunnel.
   `vite.config.js` allowlists `.trycloudflare.com`, so any random subdomain is
   accepted without extra config.

5. **The mic needs a secure context.**
   `getUserMedia` only works over HTTPS **or** on `localhost`. That's the whole
   reason the tunnel exists: your phone reaches the app at a non-localhost
   origin, so it needs real HTTPS. A plain `http://192.168.x.x` LAN address will
   load the app but silently block the mic.

6. **ffmpeg must be on PATH.**
   The backend shells out to ffmpeg to convert the phone's `.webm` recording to
   16 kHz mono WAV before Whisper transcribes it. No ffmpeg → every score fails.

## One-time setup (already done on this machine)

For reference, to recreate the environments from scratch:

```bash
# Backend (Python 3.11, needs ffmpeg on PATH)
uv venv backend/.venv --python 3.11
backend/.venv/bin/uv pip install -r backend/requirements.txt   # or: pip install

# Pipeline (shares the bakeoff lab venv; needs edge-tts + PyYAML + ffmpeg)
uv venv bakeoff/.venv --python 3.11
bakeoff/.venv/bin/pip install -r pipeline/requirements.txt

# Frontend
cd frontend && npm install
```

Also required on PATH: **ffmpeg**, **node**/**npm**, and **cloudflared**
(only for phone testing).

## Ports at a glance

| Port | Who | Bound to |
|---|---|---|
| 8000 | FastAPI backend | localhost (reached only via the frontend's `/api` proxy) |
| 5173 | `vite dev` | localhost |
| 4173 | `vite preview` | localhost (what the tunnel points at) |
