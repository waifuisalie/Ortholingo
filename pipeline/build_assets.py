#!/usr/bin/env python3
"""Ortholingo asset pipeline: content/*.yaml -> assets/ (audio + timings + manifest).

For every item in every unit:
  assets/audio/phrases/{id}_normal.mp3   voice at natural rate
  assets/audio/phrases/{id}_slow.mp3     voice at rate=-40% (native slow generation)
  assets/audio/words/{key}.mp3           isolated word clips at -20%, deduped corpus-wide
  assets/timings/{id}.json               per-word [start,end] for normal and slow
  assets/manifest.json                   everything the frontend needs

Validation (fails the build):
  - words[] and tts token counts match, every word has el+tl
  - tts has no polytonic combining marks
  - item ids unique repo-wide

QC (see docs/ARCHITECTURE.md D5):
  - always: duration window scaled by text length (catches babble-padding and
    truncation on any item size, including single letters), with retries
  - --qc: whisper round-trip similarity >= 0.90 (needs faster-whisper installed)

Idempotent: items are skipped when their manifest hash (tts+voice) is
unchanged and files exist. --force regenerates everything.

Usage:
  python build_assets.py [--qc] [--force] [--units unit0-alfabeto,...]
"""
import argparse
import asyncio
import hashlib
import json
import pathlib
import subprocess
import sys
import unicodedata

import edge_tts
import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
CONTENT = REPO / "content" / "units"
ASSETS = REPO / "assets"
PHRASES_DIR = ASSETS / "audio" / "phrases"
WORDS_DIR = ASSETS / "audio" / "words"
TIMINGS_DIR = ASSETS / "timings"
MANIFEST = ASSETS / "manifest.json"

VOICES = {"athina": "el-GR-AthinaNeural", "ava": "en-US-AvaMultilingualNeural"}
SLOW_RATE = "-40%"
WORD_RATE = "-20%"
MAX_RETRIES = 3

# Polytonic-only combining marks that must not appear in tts text
POLYTONIC_MARKS = {"̓", "̔", "͂", "̀", "ͅ"}


def die(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def norm_key(word: str) -> str:
    w = unicodedata.normalize("NFD", word)
    return "".join(c for c in w if c.isalpha()).casefold()


def letters(text: str) -> int:
    return sum(c.isalpha() for c in text)


def item_hash(item: dict) -> str:
    return hashlib.sha256(f"{item['tts']}|{item['voice']}".encode()).hexdigest()[:16]


def mp3_duration(path: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def load_units(only=None):
    units = []
    seen_ids = {}
    for path in sorted(CONTENT.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text())
        unit, items = doc["unit"], doc["items"]
        if only and unit["id"] not in only:
            continue
        for item in items:
            item.setdefault("voice", "athina")
            item.setdefault("kind", "phrase")
            # --- validation ---
            if item["id"] in seen_ids:
                die(f"duplicate id {item['id']} ({path.name} and {seen_ids[item['id']]})")
            seen_ids[item["id"]] = path.name
            nfd = unicodedata.normalize("NFD", item["tts"])
            if any(m in nfd for m in POLYTONIC_MARKS):
                die(f"{item['id']}: tts text contains polytonic marks — use monotonic")
            ntts, nwords = len(item["tts"].split()), len(item["words"])
            if ntts != nwords:
                die(f"{item['id']}: {ntts} tts tokens vs {nwords} words[] entries")
            for w in item["words"]:
                if not w.get("el") or not w.get("tl"):
                    die(f"{item['id']}: words[] entry missing el or tl: {w}")
            if item["voice"] not in VOICES:
                die(f"{item['id']}: unknown voice {item['voice']}")
        units.append((unit, items))
    if not units:
        die("no units found")
    return units


async def synth(text: str, voice: str, rate: str, path: pathlib.Path, want_bounds: bool):
    """Generate one mp3; return word timings [[start,end],...] when requested."""
    comm = edge_tts.Communicate(text, voice, rate=rate,
                                boundary="WordBoundary" if want_bounds else "SentenceBoundary")
    audio, bounds = b"", []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary" and want_bounds:
            start = chunk["offset"] / 1e7
            bounds.append([round(start, 3), round(start + chunk["duration"] / 1e7, 3)])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return bounds


async def gen_phrase_speed(item: dict, label: str, rate: str, qc_fn):
    """Generate one speed of one phrase with QC + retries. Returns timings."""
    voice = VOICES[item["voice"]]
    path = PHRASES_DIR / f"{item['id']}_{label}.mp3"
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        bounds = await synth(item["tts"], voice, rate, path, want_bounds=True)
        dur = mp3_duration(path)
        nletters = letters(item["tts"])
        # duration window: generous per-length bounds; slow rate stretches ~1.8x
        dur_max = (2.0 + nletters / 8) * (1.8 if label == "slow" else 1.0)
        dur_min = 0.2 + nletters / 30
        ok = dur_min <= dur <= dur_max and len(bounds) == len(item["words"])
        if ok and qc_fn:
            ok = qc_fn(path, item)
        if ok:
            return bounds
        last = f"dur={dur:.1f}s (window {dur_min:.1f}-{dur_max:.1f}), {len(bounds)}/{len(item['words'])} bounds"
        print(f"    retry {attempt} for {item['id']}_{label} ({last})")
    die(f"{item['id']}_{label}: QC failed after {MAX_RETRIES} attempts ({last})")


def make_qc_fn():
    """Whisper round-trip gate (optional, heavy)."""
    from faster_whisper import WhisperModel
    import difflib
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

    def normalize(text):
        t = unicodedata.normalize("NFD", text)
        t = "".join(c for c in t if unicodedata.category(c) not in ("Mn", "Po", "Pd", "Pi", "Pf"))
        return " ".join(t.casefold().split())

    def qc(path, item):
        lang = "el" if item["voice"] == "athina" else None
        segs, _ = model.transcribe(str(path), language=lang, beam_size=1)
        text = " ".join(s.text for s in segs).strip()
        sim = difflib.SequenceMatcher(None, normalize(item["tts"]), normalize(text)).ratio()
        if sim < 0.90:
            print(f"    whisper QC {item['id']}: sim={sim:.2f} heard: {text}")
        return sim >= 0.90
    return qc


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qc", action="store_true", help="enable whisper round-trip QC")
    ap.add_argument("--force", action="store_true", help="regenerate everything")
    ap.add_argument("--units", help="comma-separated unit ids to build")
    args = ap.parse_args()

    only = set(args.units.split(",")) if args.units else None
    units = load_units(only)
    qc_fn = make_qc_fn() if args.qc else None

    old = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"items": {}}
    manifest = {"voices": VOICES, "slow_rate": SLOW_RATE, "units": [], "items": {}, "words": {}}
    wordfiles = {}
    n_gen = n_skip = 0

    for unit, items in units:
        manifest["units"].append({**unit, "items": [i["id"] for i in items]})
        print(f"\n== {unit['id']} ({len(items)} items) ==")
        for item in items:
            h = item_hash(item)
            entry = {
                "unit": unit["id"], "kind": item["kind"], "greek": item["greek"],
                "words": item["words"], "pt": item["pt"], "gloss": item.get("gloss", []),
                "context_pt": item.get("context_pt", ""), "source": item.get("source", ""),
                "tags": item.get("tags", []), "voice": item["voice"],
                "review": item.get("review", "pending"), "hash": h,
                "wordkeys": [norm_key(w) for w in item["tts"].split()],
            }
            timings_path = TIMINGS_DIR / f"{item['id']}.json"
            fresh = (not args.force
                     and old["items"].get(item["id"], {}).get("hash") == h
                     and (PHRASES_DIR / f"{item['id']}_normal.mp3").exists()
                     and (PHRASES_DIR / f"{item['id']}_slow.mp3").exists()
                     and timings_path.exists())
            if fresh:
                n_skip += 1
            else:
                t_normal = await gen_phrase_speed(item, "normal", "+0%", qc_fn)
                t_slow = await gen_phrase_speed(item, "slow", SLOW_RATE, qc_fn)
                timings_path.parent.mkdir(parents=True, exist_ok=True)
                timings_path.write_text(json.dumps({"normal": t_normal, "slow": t_slow}))
                n_gen += 1
                print(f"  {item['id']}")
            # word clips (deduped by normalized key)
            for token, key in zip(item["tts"].split(), entry["wordkeys"]):
                if key in wordfiles or not key:
                    continue
                wpath = WORDS_DIR / f"{key}.mp3"
                if args.force or not wpath.exists():
                    await synth(token.strip(".,·;!?"), VOICES[item["voice"]],
                                WORD_RATE, wpath, want_bounds=False)
                wordfiles[key] = True
            manifest["items"][item["id"]] = entry

    manifest["words"] = {k: f"audio/words/{k}.mp3" for k in sorted(wordfiles)}
    ASSETS.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(f"\ngenerated {n_gen} items, skipped {n_skip} up-to-date, "
          f"{len(wordfiles)} word clips\nmanifest: {MANIFEST}")


if __name__ == "__main__":
    asyncio.run(main())
