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
      - { el: "Κύριε,",   tl: "Kírie,",   pt: "Senhor" }      # pt: per-word gloss,
      - { el: "ἐλέησον.", tl: "eléison.", pt: "tem piedade" } #   Greek word-order
    pt: "Senhor, tem piedade."           # flowing translation; shown when NOT segmented
    segments:                             # OPTIONAL — long phrases only; see below
      - { words: "0" }                    # a part is just a range of word indices
      - { words: "1" }
    gloss:                                # legacy tap-to-reveal tags; superseded by
      - { el: "Κύριε",   pt: "Senhor (vocativo)" }        # per-word pt on segmented
      - { el: "ἐλέησον", pt: "tem piedade (imperativo)" } # phrases (drop when segmented)
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
6. When `segments` are present, every `words[i]` carries `pt` — the per-word gloss
   the parts are rendered from.

## Segments (optional) — breaking a long phrase into learnable parts

Long phrases (the opening blessing, the litany conclusions, the Creed) are too
big to meet and to *speak* all at once. `segments` cuts a phrase into sense-parts
the learner hears, sees the meaning of, and speaks one at a time — then assembles
the whole. Short phrases omit `segments` entirely and behave as before.

```yaml
segments:              # each part is just a range of word indices…
  - { words: "0-2" }
  - { words: "3-11" }
  - { words: "12-20" }
```

The translation of a segmented phrase is carried **per word** on `words[i].pt`
(Greek word-order), so each Portuguese word can be tapped to hear and highlight
its Greek word across all three lines. A chip renders as the tappable per-word
`pt`s of its range; the flowing `pt` line is dropped as redundant.

- `words`: an inclusive index range into `words[]` — `"a-b"`, or a single `"a"`.
- `words[i].pt` is **authored translation text**: it inherits the item's
  `review: pending` and must be blessed like any content. Function words with no
  Greek token (a copula "seja", some articles) simply aren't shown.
- Audio: the pipeline cuts each part into its own clip
  `assets/audio/segments/{id}_{i}_{speed}.mp3` (a sample-accurate slice of the
  phrase recording — mobile browsers can't seek a shared element).

Transliteration conventions (Byzantine values, PT-friendly):
η/ι/υ/ει/οι → i · αι → e · β → v · ου → u · ευ → ev/ef · αυ → av/af ·
γ before ε/ι → y (yi) · θ → th · χ → ch · accents kept on the stressed vowel.
