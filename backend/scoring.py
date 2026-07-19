"""Pronunciation scoring: transcript vs expected text, word by word.

Byzantine-pronunciation-aware in the only way that matters here: everything
is compared after stripping diacritics (polytonic AND monotonic) and
punctuation, and whisper's habit of "modernizing" Koine grammar is absorbed
by fuzzy per-word matching (see docs/ARCHITECTURE.md D4).
"""
import difflib
import unicodedata

# a replaced token still counts as said if it's this similar to the expected one
FUZZY_ACCEPT = 0.72

# Byzantine phonetic folding: homophone spellings converge before comparison,
# so whisper "modernizing" Koine grammar (Υἱῷ -> Υιό) can't fail a learner.
# Digraphs first, then single letters.
FOLD_DIGRAPHS = [("ου", "u"), ("ει", "i"), ("οι", "i"), ("υι", "i"), ("αι", "e")]
FOLD_SINGLE = str.maketrans({"η": "i", "υ": "i", "ι": "i", "ω": "ο"})


def fold(t: str) -> str:
    for pair, rep in FOLD_DIGRAPHS:
        t = t.replace(pair, rep)
    return t.translate(FOLD_SINGLE)


def norm_tokens(text: str) -> list[str]:
    """Split into tokens of bare casefolded letters, phonetically folded."""
    out = []
    for tok in text.split():
        t = unicodedata.normalize("NFD", tok)
        t = "".join(c for c in t if c.isalpha()).casefold()
        if t:
            out.append(fold(t))
    return out


def align(expected: list[str], got: list[str]) -> list[bool]:
    """Mark each expected token as heard/not, tolerant of near-misses."""
    ok = [False] * len(expected)
    sm = difflib.SequenceMatcher(None, expected, got, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                ok[i] = True
        elif tag == "replace":
            for k in range(min(i2 - i1, j2 - j1)):
                sim = difflib.SequenceMatcher(None, expected[i1 + k], got[j1 + k]).ratio()
                if sim >= FUZZY_ACCEPT:
                    ok[i1 + k] = True
    return ok


def score_transcript(expected_text: str, transcript: str) -> dict:
    exp = norm_tokens(expected_text)
    got = norm_tokens(transcript)
    ok = align(exp, got)
    return {
        "words": ok,
        "score": round(sum(ok) / len(exp), 3) if exp else 0.0,
        "transcript": transcript,
    }
