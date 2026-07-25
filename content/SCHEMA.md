# Content schema

One YAML file per unit in `content/units/`. Every field exists to serve either
the learner, the pipeline, or the reviewing priest.

```yaml
unit:
  id: unit1-respostas          # kebab-case, stable forever (asset keys derive from item ids)
  title: "As respostas do povo"
  section: nave                # nartex | nave  (never beyond — see ARCHITECTURE D8)
  order: 2
  intro_pt: "One-paragraph introduction shown before the first lesson."

items:
  - id: kyrie-eleison          # globally unique across ALL units
    kind: phrase               # phrase | letter
    greek: "Κύριε, ἐλέησον."   # polytonic — DISPLAY ONLY
    tts: "Κύριε, ελέησον."     # monotonic — what TTS engines receive
    words:                     # 1:1 aligned tokens; len == len(tts tokens)
      - { el: "Κύριε,",   tl: "Kírie," }
      - { el: "ἐλέησον.", tl: "eléison." }
    pt: "Senhor, tem piedade."           # translation (Devocional wording when available)
    segments:                             # OPTIONAL — only for long phrases; see below
      - { words: "0",   pt: "Senhor" }
      - { words: "1",   pt: "tem piedade" }
    gloss:                                # word-by-word meaning for tap-to-reveal
      - { el: "Κύριε",   pt: "Senhor (vocativo)" }
      - { el: "ἐλέησον", pt: "tem piedade (imperativo)" }
    context_pt: >-                        # liturgical/theological context card
      A resposta mais frequente do povo…
    source: "Devocional, p. 8"            # citation; "Divina Liturgia" if not in the books
    tags: [liturgia, litania, resposta-do-povo]
    voice: athina              # athina (default, Greek) | ava (mascot, PT/EN lines)
    review: pending            # pending | approved  (set by clergy review, never by us)
```

Rules enforced by the pipeline:
1. `len(words) == len(tts.split())` — word boundaries map by index.
2. Every `words[i]` has both `el` and `tl` (paired highlighting depends on it).
3. `tts` must not contain polytonic combining marks (breathings/iota subscript).
4. Item ids are unique repo-wide (asset filenames derive from them).
5. `segments` (when present) tile `words[]` exactly: contiguous, non-overlapping,
   in order, covering index 0 through the last with no gaps.

## Segments (optional) — breaking a long phrase into learnable parts

Long phrases (the opening blessing, the litany conclusions, the Creed) are too
big to meet and to *speak* all at once. `segments` cuts a phrase into sense-parts
the learner hears, sees the meaning of, and speaks one at a time — then assembles
the whole. Short phrases omit `segments` entirely and behave as before.

```yaml
segments:
  - { words: "0-2",   pt: "Bendito seja o reino" }
  - { words: "3-11",  pt: "do Pai e do Filho e do Espírito Santo" }
  - { words: "12-20", pt: "agora e sempre e pelos séculos dos séculos" }
```

- `words`: an inclusive index range into `words[]` — `"a-b"`, or a single `"a"`.
- `pt`: the part's meaning. **This is authored translation text**, so it inherits
  the item's `review: pending` — it is NOT auto-derived and must be blessed like
  any content. It is *not* required to be a slice of the item's `pt`: Portuguese
  word order and articles rarely line up 1:1 with Greek (e.g. «ἡμᾶς» → "-nos"
  smeared across several verbs), so segment `pt` is written to mean the part
  faithfully. The full `pt` stays the card's canonical translation line; segment
  `pt` is the highlight layer surfaced as each part plays.
- Audio is a **slice of the existing recording** (resolved from per-word timings by
  the pipeline into `[start,end]` per speed) — no new audio is generated.

Transliteration conventions (Byzantine values, PT-friendly):
η/ι/υ/ει/οι → i · αι → e · β → v · ου → u · ευ → ev/ef · αυ → av/af ·
γ before ε/ι → y (yi) · θ → th · χ → ch · accents kept on the stressed vowel.
