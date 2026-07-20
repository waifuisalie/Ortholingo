#!/usr/bin/env python3
"""Spell-read detector: scan word timings for duration outliers.

The TTS voice occasionally SPELL-READS rare accented words aloud (the 'αεί'
incident: a 3-letter word took 1.50s while neighbors took 0.10-0.34s,
because Athina was saying 'me tono' — reading the accent mark). Whisper
round-trips don't reliably catch this (insertions don't lower similarity),
but per-word durations expose it immediately.

Flags any word whose duration exceeds BOTH an absolute floor and a
letters-scaled budget. Run after every corpus build.

Usage: python pipeline/scan_timings.py
"""
import json
import pathlib
import sys
import unicodedata

import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
ABS_FLOOR = 1.2          # ignore anything under this, seconds (the αεί case was 1.50s)
PER_LETTER = 0.18        # generous normal-speed budget per letter
SLOW_FACTOR = 1.9


def letters(tok: str) -> int:
    return sum(c.isalpha() for c in unicodedata.normalize("NFD", tok))


def main():
    manifest = json.loads((REPO / "assets" / "manifest.json").read_text())
    flagged = 0
    for unit_file in sorted((REPO / "content" / "units").glob("*.yaml")):
        doc = yaml.safe_load(unit_file.read_text())
        for item in doc["items"]:
            tpath = REPO / "assets" / "timings" / f"{item['id']}.json"
            if not tpath.exists():
                continue
            timings = json.loads(tpath.read_text())
            tokens = item["tts"].split()
            for label, factor in (("normal", 1.0), ("slow", SLOW_FACTOR)):
                for tok, (s, e) in zip(tokens, timings.get(label, [])):
                    dur = e - s
                    budget = max(ABS_FLOOR, letters(tok) * PER_LETTER) * factor
                    if dur > budget:
                        flagged += 1
                        print(f"SUSPECT {item['id']} [{label}] '{tok}': "
                              f"{dur:.2f}s (budget {budget:.2f}s)")
    if flagged:
        print(f"\n{flagged} suspect word(s) — listen to them, or respell in tts "
              f"(see the αεί fix, commit 8ebe27d)")
        sys.exit(1)
    print("all word durations within budget — no spell-reading detected")


if __name__ == "__main__":
    main()
