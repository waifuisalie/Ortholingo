# Speech scoring — how the models behave on this machine

Measured 2026-08-13 on the machine that currently hosts Ortholingo. Numbers
from `backend/bench.py`; raw JSON per model is reproducible with the command at
the bottom.

## ⚠️ Read this before the tables

**The speaker is not a human.** There are no recordings of real learners yet, so
the benchmark feeds each model *Athina's own synthesised recording* of a phrase
— the same audio the app plays back. That makes these numbers:

- ✅ a **ceiling**: what the scorer does with flawless, accent-free pronunciation
- ✅ a **separation check**: does it tell «Κύριε, ἐλέησον» apart from «Ἅγιος ὁ Θεός»
- ✅ a **latency measurement**: this part is real, and is the main reason the page exists
- ❌ **not** a measure of how a learner scores. Accent, hesitation, room noise and
  phone microphones are all absent

So treat the score columns as "can the scorer recognise a correct phrase at
all", and the time columns as the honest performance number.

## The machine

| | |
|---|---|
| CPU | AMD Ryzen 7 5700G — 8 cores / 16 threads, AVX2, **no AVX-512/VNNI** |
| RAM | 31 GiB, no swap |
| Inference | `faster-whisper` (CTranslate2) on **CPU**, `int8`, CTranslate2's default thread count |
| GPU | not used — Radeon integrated graphics, no CUDA and ROCm unsupported on gfx1031 |

CPU-only is a deliberate constraint, not an oversight: the target is a machine
someone could actually leave running at home.

## Results

Nine phrases, stratified by recording length from 0.8s to 16.0s. `PASS = 0.75`
is the threshold the app uses to call a take correct.

| model | matched min | matched mean | mismatched max | separation | stt mean | stt worst | below PASS |
|---|---|---|---|---|---|---|---|
| `small` | **0.40** | 0.84 | 0.08 | 0.32 | **1.5s** | 2.6s | **2 / 9** |
| `medium` | 0.80 | 0.92 | 0.10 | 0.70 | 4.0s | 5.7s | 0 / 9 |
| `large-v3-turbo` | **0.88** | **0.96** | 0.10 | **0.78** | 5.1s | 5.7s | 0 / 9 |

Model load (once, at server start): `small` 9.7s · `medium` 5.2s · `turbo` 5.7s.

### Latency barely depends on phrase length

This is the least obvious result and the most useful one. Whisper processes
audio in fixed 30-second windows, so a 0.8-second «Ἀμήν» costs almost as much
as the 16-second Sanctus:

| phrase | audio | `small` | `medium` | `large-v3-turbo` |
|---|---|---|---|---|
| amin | 0.8s | 2.6s ¹ | 3.1s | 4.8s |
| kyrie-eleison | 2.0s | 1.1s | 3.1s | 4.8s |
| en-irini | 2.1s | 1.1s | 3.3s | 4.8s |
| pater-1 | 3.4s | 1.2s | 3.5s | 4.9s |
| ke-nin | 4.3s | 1.3s | 3.6s | 4.9s |
| trisagion | 5.2s | 1.4s | 3.9s | 5.1s |
| evlogimeni-i-vasilia | 6.2s | 1.5s | 4.4s | 5.2s |
| cherubikon | 9.5s | 1.9s | 5.5s | 5.5s |
| anafora-agios | 16.0s | 1.9s | 5.7s | 5.7s |

¹ first decode of the run — includes warm-up. `small`'s steady-state worst is 1.9s.

**Twenty times the audio costs turbo 19% more time.** Two consequences:

- *Real-time factor is a misleading metric here.* It mostly measures 1/duration,
  which is why this page reports absolute seconds.
- *`medium` is dominated.* On long phrases it is no faster than turbo (5.5s vs
  5.5s, 5.7s vs 5.7s) and scores worse everywhere. Its only edge is on short
  clips, which is not where accuracy is at risk.

### Where `small` actually fails

`small` is the fast tier, and it fails 2 of 9 — but **not** where you would guess:

| phrase | audio | score | what it heard |
|---|---|---|---|
| `en-irini` | 2.1s | **0.40** | «και η ρήνη του κυρίου δε ηθόμεν» |
| `anafora-agios` | 16.0s | **0.72** | «Άγιος, Άγιος, Άγιος Κύριος Αβαόθητ…» |

Its worst take is a **2-second** phrase, not the 16-second one. «Ἐν εἰρήνῃ»
came back as "και η ρήνη" — the model guessed a commoner word and split it
wrongly. Length is not the predictor; unfamiliar liturgical vocabulary is.

Note the mismatched column in the headline table: **max 0.08 for `small`**. It
never wrongly *accepts* the wrong phrase — every error is a correct take scored
too low. That is precisely why escalation works.

## Why two tiers

The data above is the whole argument:

- `small` answers in ~1.5s and separates phrases cleanly (0.32), but scores
  correct speech below PASS on 2 of 9 phrases
- `turbo` never does that (min 0.88), but costs ~5s on every take
- every one of `small`'s errors is a **false negative**

So Ortholingo runs `small` first and escalates to `turbo` **only when the score
comes back below PASS**. A correct take returns in ~1.5s; only a take that was
about to be marked wrong pays the extra ~5s. Escalation cannot make a passing
take fail — it can only rescue a failing one.

Worst case ≈ 6.6s (both models), and it lands on the learner least likely to be
right. The 3s budget is met for the case that actually matters.

## Method, briefly

For each phrase the harness decodes the app's own `_normal.mp3` once, then
scores that single transcript twice:

- **matched** — against that phrase's own expected words → should be high
- **mismatched** — against the *next* phrase's expected words → should be low

`separation` is `min(matched) − max(mismatched)`; anything above 0.25 means the
scorer is genuinely discriminating rather than passing everything. Scoring runs
through `backend/scoring.py`, which applies Byzantine phonetic folding
(η ι υ ει οι υι → i, αι → e, ω → ο, ου → u) before a fuzzy per-word match, so
Whisper's habit of modernising Koine spelling cannot fail a learner.

The phrase set is stratified by length on purpose. An earlier version of this
harness used six short phrases (none over 5.2s) and could not have found either
of `small`'s failures.

## Reproduce

```bash
ORTHOLINGO_WHISPER=small          backend/.venv/bin/python backend/bench.py --json small.json
ORTHOLINGO_WHISPER=medium         backend/.venv/bin/python backend/bench.py --json medium.json
ORTHOLINGO_WHISPER=large-v3-turbo backend/.venv/bin/python backend/bench.py --json turbo.json
```

`ORTHOLINGO_COMPUTE` (default `int8`) and `ORTHOLINGO_THREADS` (default: let
CTranslate2 choose) are available for sweeping, though on this class of CPU
neither moved the numbers meaningfully.

## Footnote: the machine that didn't make it

The same harness was run on a laptop (Intel i5-7200U, no AVX-512/VNNI, swap
disabled) as a candidate host. `large-v3-turbo` took **~19s per take** — six
times the budget — and `int8`, `int8_float32` and thread tuning all landed
within a second of each other, while `float32` ran the machine out of memory.
That is why the desktop above is the host. The measurement is kept here because
"which CPU can serve this" is the question anyone self-hosting will ask, and a
negative result answers it faster than a positive one.
