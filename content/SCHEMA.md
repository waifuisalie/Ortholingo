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

## Per-word `pt` — every phrase, not just the long ones

**Every `kind: phrase` item carries `pt` on every word.** This is what makes any
Portuguese word tappable: tap it, hear and highlight its Greek. One rule holds
everywhere, so the learner never has to guess which cards respond to a tap.
Letters (`kind: letter`) have no per-word `pt` and keep the flowing line.

Author the per-word gloss by **decomposing the item's existing `pt`** into Greek
word order — do not retranslate. The flowing `pt` is the blessed rendering (it
comes from the Devocional and the GOA text); the per-word row is a crib laid
under the Greek. Where the Greek has a token the translation has no word for
(particles like `τε`, some articles), give it its plain function-word sense;
where several verbs share one object, gloss that object once rather than
smearing it across them (`«ἡμᾶς»` → "nos", once, in antilavou).

The row often reads oddly — "por · da · paz", "e · da · de todos · união".
That is inherent to a word-order crib over Greek hyperbaton, not a defect.
Fluency lives in the item's flowing `pt`; the row's job is the mapping.

## Segments (optional) — breaking a long phrase into learnable parts

Long phrases (the opening blessing, the litany conclusions, the Creed) are too
big to meet and to *speak* all at once. `segments` cuts a phrase into sense-parts
the learner hears, sees the meaning of, and speaks one at a time — then assembles
the whole. Short phrases omit `segments` entirely and behave as before.

**When to segment:** the phrase's normal-speed recording runs **≥ 6.0s**, or it
is **≥ 14 words**. Below both, it is one breath — leave it whole. Word count
alone is a poor test (`credo-6` is 8 words in one breath; `credo-12` is 9 words
in three sentences), which is why duration leads and the word clause only
catches phrases that are a visual wall despite being quick.

Two further constraints, both about the learner's time and voice:

- **Prefer boundaries on punctuation.** A part is cut from the recording at its
  first and last word, so a boundary mid-clause can clip an onset. Commas,
  colons and full stops cut clean.
- **Budget the parts per lesson, not per phrase.** Each part is a microphone
  take (`buildLesson` emits karaoke + speak per part, plus the assembled whole),
  and lessons hold 3 items. Aim for **≤ 9 speaks in a lesson**; when a chunk runs
  over, cut segments on the phrases *in that chunk* rather than spreading evenly.

A segmented phrase also carries a short `title` (e.g. `title: "a bênção de
abertura"`), shown as «parte 1 de 3 · {title}» while the learner works the parts
and «a frase completa · {title}» on the assembled whole.

```yaml
segments:              # each part is just a range of word indices…
  - { words: "0-2" }
  - { words: "3-11" }
  - { words: "12-20" }
```

On a segmented phrase the assembled view renders one chip per part, built from
that range's per-word `pt`; the flowing `pt` line is dropped there as redundant.

- `words`: an inclusive index range into `words[]` — `"a-b"`, or a single `"a"`.
- `words[i].pt` is **authored translation text**: it inherits the item's
  `review: pending` and must be blessed like any content. Function words with no
  Greek token (a copula "seja", some articles) simply aren't shown.
- `gloss` (the dashed chips with grammatical notes) is **kept on unsegmented
  phrases** — "Κύριε · Senhor (vocativo — chamando)" teaches something per-word
  `pt` cannot — and **dropped when a phrase gains `segments`**, where it is both
  subsumed and too much for an already long card.
- Audio: the pipeline cuts each part into its own clip
  `assets/audio/segments/{id}_{i}_{speed}.mp3` (a sample-accurate slice of the
  phrase recording — mobile browsers can't seek a shared element).

Transliteration conventions (Byzantine values, PT-friendly):
η/ι/υ/ει/οι → i · αι → e · β → v · ου → u · ευ → ev/ef · αυ → av/af ·
γ before ε/ι → y (yi) · θ → th · χ → ch · accents kept on the stressed vowel.
