# Manual test guide (phases 1–4)

## Start everything

```bash
# terminal 1 — backend (wait for "Application startup complete", ~20s: two whisper models)
cd ~/Documents/Ortholingo
backend/.venv/bin/uvicorn main:app --app-dir backend --port 8000

# terminal 2 — frontend
cd ~/Documents/Ortholingo/frontend
npm run dev            # → http://localhost:5173

# sanity check
curl http://localhost:8000/api/health   # {"ok":true,"fast":"small","careful":"large-v3-turbo"}
```

## Test tour

### Home path
- [ ] Both units listed (Nártex · alfabeto, Nave · respostas), 4 lessons each
- [ ] "Continuar" card points at the first unfinished lesson
- [ ] XP counter present

### Unit 0 (letters)
- [ ] Karaoke card: tapping the letter (or its name below) plays and highlights it
- [ ] ▶ plays the letter name; "lento" noticeably slower
- [ ] Quizzes: audio auto-plays; wrong answer → correct one shown green, mascot cries
- [ ] Match pairs: wrong pair shakes red; finished board enables Continuar
- [ ] Completion: waving mascot, +20 XP, home node turns gold with ✓
- [ ] Refresh the page: progress survived (localStorage)

### Unit 1 (phrases)
- [ ] Karaoke: highlight follows the audio word by word, in Greek AND
      transliteration together — watch a long phrase (Δόξα Πατρί / Καὶ νῦν)
- [ ] Tap individual words → isolated clip, both lines highlight
- [ ] Gloss chips, context and source shown
- [ ] ke-nin (Καὶ νῦν): ἀεὶ must sound like a word, not a spelling lesson

### Speak check (backend must be running)
- [ ] First use: browser asks mic permission
- [ ] Say the phrase well → green words, score ≥75%, feels fast (~1–2s)
- [ ] Deliberately butcher one word → that word red, others green
      (may take ~7s: the careful model double-checks before failing you)
- [ ] Say something totally different → low score, "Ouvi: …" shows what you said
- [ ] Stay silent → low score, no crash
- [ ] "Tentar de novo" works; "praticar depois" always available
- [ ] Kill the backend, try a speak check → friendly error, skip still works

### On your phone (optional, tests mic over HTTPS)
```bash
cloudflared tunnel --url http://localhost:5173
```
Open the printed https URL on the phone — mic works there because the tunnel
provides a secure context; the vite proxy forwards /api to your desktop.

## What to report
Wording that reads wrong, speeds that feel off (normal is −15%, slow −50%),
scoring that feels unfair (which phrase, what you said, what it heard),
mascot moods that fire at odd moments, anything that crashes.
