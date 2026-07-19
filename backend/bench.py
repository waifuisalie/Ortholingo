#!/usr/bin/env python3
"""E2E scoring benchmark using the generated corpus as a perfect speaker.

Feeds Athina's own phrase recordings to the scorer:
  - matched pairs (kyrie audio vs kyrie expected) must score high
  - mismatched pairs (kyrie audio vs trisagion expected) must score low
Also reports steady-state latency vs the 3s budget.

Run: backend/.venv/bin/python backend/bench.py
"""
import json
import os
import pathlib
import statistics
import subprocess
import tempfile
import time

from faster_whisper import WhisperModel

from scoring import score_transcript

REPO = pathlib.Path(__file__).resolve().parent.parent
ASSETS = REPO / "assets"
MODEL_NAME = os.environ.get("ORTHOLINGO_WHISPER", "large-v3-turbo")

PHRASES = ["kyrie-eleison", "trisagion", "doxa-patri", "irini-pasi", "proschomen", "ke-nin"]


def expected_text(manifest, pid):
    return " ".join(manifest["items"][pid]["wordkeys"])


def transcribe(model, mp3):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3),
             "-ac", "1", "-ar", "16000", f.name],
            check=True,
        )
        t0 = time.time()
        segments, _ = model.transcribe(f.name, language="el", beam_size=1, vad_filter=True)
        text = " ".join(s.text for s in segments).strip()
        return text, time.time() - t0


def main():
    manifest = json.loads((ASSETS / "manifest.json").read_text())
    print(f"loading whisper {MODEL_NAME} int8…")
    model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")

    lat = []
    print("\n== matched pairs (should be HIGH) ==")
    matched_scores = []
    for pid in PHRASES:
        mp3 = ASSETS / "audio" / "phrases" / f"{pid}_normal.mp3"
        text, dt = transcribe(model, mp3)
        lat.append(dt)
        r = score_transcript(expected_text(manifest, pid), text)
        matched_scores.append(r["score"])
        print(f"  {pid:<15} score={r['score']:.2f}  stt={dt:.1f}s  heard: {text}")

    print("\n== mismatched pairs (should be LOW) ==")
    mismatched_scores = []
    rotated = PHRASES[1:] + PHRASES[:1]
    for pid, wrong in zip(PHRASES, rotated):
        mp3 = ASSETS / "audio" / "phrases" / f"{pid}_normal.mp3"
        text, dt = transcribe(model, mp3)
        lat.append(dt)
        r = score_transcript(expected_text(manifest, wrong), text)
        mismatched_scores.append(r["score"])
        print(f"  {pid:<15} vs {wrong:<15} score={r['score']:.2f}")

    print(f"\nmatched:    min={min(matched_scores):.2f} mean={statistics.mean(matched_scores):.2f}")
    print(f"mismatched: max={max(mismatched_scores):.2f} mean={statistics.mean(mismatched_scores):.2f}")
    print(f"stt latency: mean={statistics.mean(lat):.2f}s  max={max(lat):.2f}s  (budget 3s)")
    sep = min(matched_scores) - max(mismatched_scores)
    print(f"separation (min matched - max mismatched): {sep:.2f} {'OK' if sep > 0.25 else 'WEAK'}")


if __name__ == "__main__":
    main()
