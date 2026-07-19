# Ortholingo — Architecture & Decision Log

Last updated: 2026-07-17 (phases 1–2). This file is the durable record of *why*
things are the way they are. If you (human or AI) are about to change a
decision recorded here, read its rationale first.

## 1. System overview

```
┌────────────────── Browser (SvelteKit PWA) ──────────────────┐
│  Lesson player · karaoke cards · SRS review · mic capture   │
│  progress cache (localStorage + device id)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS · JSON (+ multipart audio)
┌──────────────────────────▼──────────────────────────────────┐
│  Caddy / dev server                                         │
│    ├── /assets/audio/*   static phrase + word recordings    │
│    ├── /assets/timings/* word-boundary JSONs                │
│    └── /api → FastAPI                                       │
│          ├── content endpoints                              │
│          ├── progress + FSRS scheduling                     │
│          └── POST /speech/score → ffmpeg → faster-whisper   │
│                └─ normalize → word-level diff → per-word ✓✗ │
│  SQLite                                                     │
└─────────────────────────────────────────────────────────────┘
             ▲
   content/*.yaml ──> pipeline/build_assets.py ──> assets/
   (priest-reviewable)     (edge-tts + QC gate)
```

**Hosting:** prototype runs on the developer desktop (Ryzen 7 5700G / 32GB);
demos are shared via Cloudflare quick tunnel (`cloudflared tunnel --url …`)
because browser mic capture requires a secure context (HTTPS or localhost).
Production later = same Docker Compose on a small VPS.

## 2. Core design decisions

### D1 — Byzantine pronunciation, never Erasmian
Liturgical Koine is pronounced as Modern Greek in Greek Orthodox practice
(η=ι=υ=ει=οι=/i/, β=/v/, αι=/e/…). Consequences: Whisper's modern-Greek
training matches church recitation; all transliterations follow Byzantine
values (Καὶ τῷ πνεύματί σου → "Ke to pnevmatí su").

### D2 — Closed corpus, curated content, no runtime generation
The Liturgy is a fixed text (~hundreds of phrases). All content is YAML in
git with source citations, built to be reviewed by clergy (every entry has
`review: pending` until then). No LLM generates doctrine at runtime.
LLM-assisted *authoring* is allowed; human/priest review is the gate.

### D3 — TTS is build-time; STT is runtime
Audio is pre-generated into `assets/` (static files, offline app). Only STT
runs live (pronunciation scoring), so only STT has a latency budget (≤3s).

### D4 — Speech stack (decided by bake-off, `bakeoff/`, 2026-07-17)
- **TTS:** edge-tts (dev) / official Azure Speech free tier (production).
  **Casting: `el-GR-AthinaNeural` speaks all Greek liturgical text;
  `en-US-AvaMultilingualNeural` is the mascot (PT/EN).** Nestoras (male el)
  reserved for a possible "chanter mode"; Thalita (pt-BR multilingual) is the
  swap if Ava's PT accent grates. Chatterbox Multilingual (MIT, local) stayed
  installed in `bakeoff/` as the fully-local fallback — it won local-model
  Greek but is unstable on very short phrases (~25% clean-take yield).
- **Slow mode:** TWO files per phrase, both natively rate-controlled.
  Client-side playbackRate was rejected: sounds robotic (user judgment).
  History: slow=−40% chosen from a rate ladder (−15/−25/−40); then, after
  playing real lessons, "normal" felt too fast — now **normal=−15%,
  slow=−50%** (Athina's native pace is brisk conversational Greek; −15%
  stays honest to church speed while calmer, −50% is the study speed).
  Rates are part of the pipeline's idempotency hash, so changing them
  regenerates the corpus automatically.
- **STT (phase 4, decided by backend/bench.py):** two-tier scorer. Bench on
  the generated corpus (perfect-speaker proxy): turbo = matched 1.00/sep 0.86
  but 5.6s; small = 1.3s but fails long phrases (min 0.46); medium = worst of
  both (3.7s, min 0.73). Design: `small` int8 answers (~1.3s); any take
  below PASS=0.75 is re-judged by `large-v3-turbo` before the app calls it
  wrong (~7s worst case). Correct speech feels instant; only turbo may fail
  a learner. Models via ORTHOLINGO_WHISPER_FAST/_CAREFUL. Vulkan/whisper.cpp
  remains the GPU escape hatch (AMD gfx1031: no CUDA, ROCm unsupported).
- **Whisper "modernizes" Koine** (τῷ→το, Υἱῷ→Υιό): solved in phase 4 by
  Byzantine phonetic folding in `backend/scoring.py` (η/ι/υ/ει/οι/υι→i,
  αι→e, ω→ο, ου→u before comparison) plus fuzzy per-word matching — homophone
  spellings converge, so grammar-form transcription can't fail a learner.
  `initial_prompt` biasing remains untested/unused (hallucination risk).

### D5 — QC gate for generated audio (two signals, validated)
whisper round-trip similarity ≥ 0.90 **AND** speech rate within 7–20
letters/sec of audio. Rationale: similarity alone shipped a junk-padded take
(model babble that Whisper politely ignored — scored 1.00); the rate bound
catches padding, the similarity bound catches mispronunciation. Retry loop
regenerates failures. Cheap check always on; whisper check opt-in
(`--qc`) since edge output is stable. Refinement (same day): raw letters/sec
bounds only work for phrases — single-letter items ("άλφα") legitimately sit
far below 7 l/s. The pipeline therefore uses a **duration window scaled by
text length** (min 0.2s + letters/30, max 2s + letters/8, ×1.8 for slow),
which catches both babble-padding and truncation at every item size.

### D6 — Word-level sync is captured at generation, not aligned after
edge-tts emits WordBoundary events (exact per-word timestamps) during
synthesis — **but only with `boundary="WordBoundary"`; edge-tts 7.x defaults
to sentence boundaries** (cost us a debug cycle; never again). Timings are
saved per phrase per speed into `assets/timings/{id}.json`. The lesson card
highlights the Greek word and its transliteration counterpart together
(paired spans by index), both during playback and on tap. Tap-a-word plays an
isolated word clip (−20% rate) from a corpus-wide deduplicated pool
(`assets/audio/words/`) — frequent liturgical words are shared across
phrases.

### D7 — Content schema invariants
- `greek` (polytonic) is for display; `tts` (monotonic) is what engines
  receive — polytonic input degrades modern-Greek TTS.
- `words[]` (polytonic tokens) and their `tl` transliterations are aligned
  1:1, and `len(words) == len(tts tokens)` — the pipeline validates this;
  boundary events map to these indices.
- Transliteration is a *training wheel*: UI shows it early and fades it per
  phrase as SRS mastery grows (manual override in settings for accessibility).
- Every entry cites its source (Devocional page / liturgy text) and carries
  `review: pending|approved`.

### D8 — Reverence rules (non-negotiable design constraints)
- The mascot (monastery cat: plain black robe, skoufos, komboskini) never
  wears sacred vestments, sacramental objects, or sacred inscriptions. The
  first draft in a Great Schema analavos was rejected as disrespectful.
- The learning path goes narthex → nave and never "enters" the sanctuary.
- No competitive leaderboards; no punitive mechanics; the mascot never
  guilt-trips. Streak = candle motif (komboskini-as-streak idea shelved
  pending the priest's opinion).
- Branding uses the three-bar Orthodox cross (user's choice, aware it's more
  Slavic than Greek tradition — to be confirmed with the parish priest).
- Source books (PDFs) are copyrighted and are gitignored, never committed.

## 3. Asset pipeline contract

`pipeline/build_assets.py` reads every `content/units/*.yaml` and produces:

```
assets/
├── audio/phrases/{id}_normal.mp3     Athina (or per-entry voice), +0%
├── audio/phrases/{id}_slow.mp3       same text, rate=-40%
├── audio/words/{key}.mp3             isolated word clips, rate=-20%, deduped
├── timings/{id}.json                 {"normal": [[s,e]…], "slow": [[s,e]…]}
└── manifest.json                     everything the frontend needs to render
```

Properties: idempotent (skips up-to-date items by text hash; `--force`
regenerates), validating (schema + word-count alignment fail the build),
QC-gated (D5). Assets are committed to git: they're small, and contributors
shouldn't need network + TTS access to run the app.

## 4. Roadmap

1. ✅ Scaffold (this)
2. ✅ Content pipeline + Units 0–1
3. ✅ Frontend: SvelteKit lesson player, karaoke card, Units 0–1 playable
4. ✅ Backend: two-tier /api/speech/score + SpeakCheck card + bench harness
5. FSRS + Liturgy Map (frequency-weighted "% of Liturgy understood")
6. PWA polish, Sunday-prep, tunnel demos, priest review & blessing,
   parish recordings (ask readers for a slow take too)
