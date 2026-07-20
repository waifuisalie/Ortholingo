# Ortholingo ☦

**Aprenda o grego da Divina Liturgia.** A Duolingo-style app for learning liturgical (Koine) Greek — focused, fast, and faithful to how Greek is actually pronounced and prayed in the Orthodox Church.

Built by a catechumen, for catechumens and converts: instead of "general Greek from zero" (years), Ortholingo teaches exactly the Greek you hear and say at the Divine Liturgy — the people's responses, the Trisagion, the Creed, the Our Father — with meaning, liturgical context, and pronunciation practice.

> Ουκ ένι Ιουδαίος ουδέ Έλλην… πάντες γαρ υμείς εις εστέ εν Χριστώ Ιησού. (Gl 3:28)

## Why this exists

- **Byzantine pronunciation, always.** Liturgical Greek is pronounced the Modern Greek way in church — never the classroom "Erasmian" way. Every audio asset and every pronunciation check in this project follows the pronunciation you'll actually hear on Sunday.
- **A closed corpus, hand-curated.** The Liturgy is a fixed text. Every phrase is curated in versioned YAML with source citations — no runtime AI generation of doctrine. Content is written to be reviewable (and, God willing, blessed) by clergy.
- **Learn to *participate*, not just translate.** The goal metric is "how much of this Sunday's Liturgy did you understand?"

## Features (building toward)

- 🔤 Unit path from the **narthex** (alphabet, Byzantine reading rules) into the **nave** (responses, prayers, Creed)
- 🎵 **Liturgical karaoke**: word-by-word highlighting synced to audio, in Greek script and transliteration together; tap any word to hear it alone
- 🎙 **Pronunciation feedback**: speak a phrase, get per-word scoring (Whisper-based, Byzantine-pronunciation-aware)
- 🐢 **Slow mode**: natively slow-generated audio (−40%), not robotic time-stretching
- 🗺 **Liturgy Map**: the order of the Divine Liturgy with every phrase you've learned lit up — "você já entende 38% da Liturgia"
- 📅 **Sunday prep**: a 5-minute review of the responses, right before you need them
- 🧠 Spaced repetition (FSRS) with transliteration "training wheels" that fade as mastery grows
- 🐈 A monastery-cat mascot who reacts, waits patiently, and never guilt-trips

## The road ahead

Greek first — but the architecture is language-agnostic by design. The same
curated-corpus schema, asset pipeline, and pronunciation scoring extend
naturally to the other liturgical languages of the one Orthodox Church:
Church Slavonic, Romanian, Arabic, Georgian… One app, every tradition,
starting from the nave of a Greek parish in Brazil.

## Repository layout

```
content/    the curriculum — YAML phrase files with Greek, transliteration,
            Portuguese, glosses, context and source citations (priest-reviewable)
pipeline/   asset builder: text → audio (edge-tts, QC-gated) + word timings
assets/     generated audio corpus + timing JSONs (committed, app-ready)
frontend/   SvelteKit PWA (phase 3)
backend/    FastAPI pronunciation scoring (phase 4)
bakeoff/    the speech-stack laboratory: TTS/STT benchmarks that decided the stack
docs/       architecture and decision log
pictures/   mascot art
```

## Tech stack (decided by benchmark, not vibes — see `bakeoff/`)

| Concern | Choice |
|---|---|
| TTS (build-time) | Microsoft neural voices via edge-tts — `el-GR-AthinaNeural` for Greek, `en-US-AvaMultilingualNeural` for the mascot; official Azure Speech free tier for production |
| Word sync | edge-tts WordBoundary events captured at generation into timing JSONs |
| STT (runtime) | faster-whisper `large-v3-turbo` int8, word-level diff scoring |
| Frontend | SvelteKit PWA |
| Backend | FastAPI + SQLite |
| SRS | FSRS |

## Content sources

Portuguese translations follow the *Devocional — O Livro de Orações do Cristão Ortodoxo* (Edições ECCLESIA, 2024) and context draws on *O Catecismo Ortodoxo de São Nectário de Egina* (ECCLESIA, 2023). The books themselves are **not** distributed in this repository. All curriculum content carries `review: pending` until reviewed by clergy.

---

*Ortholingo is a personal study project by an Orthodox catechumen. It is not an official publication of any parish or jurisdiction.*
