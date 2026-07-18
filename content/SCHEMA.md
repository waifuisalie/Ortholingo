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

Transliteration conventions (Byzantine values, PT-friendly):
η/ι/υ/ει/οι → i · αι → e · β → v · ου → u · ευ → ev/ef · αυ → av/af ·
γ before ε/ι → y (yi) · θ → th · χ → ch · accents kept on the stressed vowel.
