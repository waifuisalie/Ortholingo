#!/usr/bin/env python3
"""E2E scoring benchmark using the generated corpus as a perfect speaker.

Feeds Athina's own phrase recordings to the scorer:
  - matched   (kyrie audio  vs kyrie expected)     must score HIGH
  - mismatched(kyrie audio  vs trisagion expected) must score LOW
and reports latency + RTF against the 3s budget.

The phrase set is stratified by recording length, because that is what
separates the models: every model handles «Κύριε, ἐλέησον», and only the
careful one survives the 16-second Sanctus. Results are reported per length
bucket for the same reason — a pooled mean hides exactly the failure the
two-tier scorer exists to catch.

IMPORTANT: the speaker is edge-tts (Athina), not a human. These numbers are a
ceiling and a separation check, never a measure of learner accuracy.

Run:  backend/.venv/bin/python backend/bench.py
      ORTHOLINGO_WHISPER=small backend/.venv/bin/python backend/bench.py --json out.json
"""
import argparse
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
COMPUTE_TYPE = os.environ.get("ORTHOLINGO_COMPUTE", "int8")
CPU_THREADS = int(os.environ.get("ORTHOLINGO_THREADS", "0"))  # 0 = CT2 default

# stratified by audio length; kept liturgically recognisable so the table means
# something to a reader who knows the rite
PHRASES = [
    ("amin", "curta"),                  # 0.8s — shortest in the corpus
    ("kyrie-eleison", "curta"),         # 2.0s — the most-said response of all
    ("en-irini", "curta"),              # 2.1s
    ("pater-1", "média"),               # 3.4s — the Our Father opens
    ("ke-nin", "média"),                # 4.3s
    ("trisagion", "média"),             # 5.2s
    ("evlogimeni-i-vasilia", "longa"),  # 6.2s — the opening blessing
    ("cherubikon", "longa"),            # 9.5s — the Cherubic Hymn
    ("anafora-agios", "muito longa"),   # 16.0s — the Sanctus, the stress test
]
BUCKETS = ["curta", "média", "longa", "muito longa"]


def expected_text(manifest, pid):
    return " ".join(manifest["items"][pid]["wordkeys"])


def audio_seconds(pid):
    return json.loads((ASSETS / "timings" / f"{pid}.json").read_text())["normal"][-1][1]


def transcribe(model, mp3):
    """One decode per clip. beam_size=1 is deterministic, so the same transcript
    serves both the matched and the mismatched comparison — no need to decode
    the identical audio twice."""
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="also write the results to this path")
    args = ap.parse_args()

    manifest = json.loads((ASSETS / "manifest.json").read_text())
    print(f"loading whisper {MODEL_NAME} {COMPUTE_TYPE} threads={CPU_THREADS or 'default'}…")
    t0 = time.time()
    model = WhisperModel(
        MODEL_NAME, device="cpu", compute_type=COMPUTE_TYPE, cpu_threads=CPU_THREADS
    )
    load_s = time.time() - t0
    print(f"  loaded in {load_s:.1f}s\n")

    ids = [p for p, _ in PHRASES]
    rotated = ids[1:] + ids[:1]
    rows = []

    print(f"{'frase':<22}{'áudio':>7}{'stt':>7}{'RTF':>6}{'match':>7}{'mismatch':>9}   ouvido")
    print("─" * 100)
    for (pid, bucket), wrong in zip(PHRASES, rotated):
        mp3 = ASSETS / "audio" / "phrases" / f"{pid}_normal.mp3"
        text, dt = transcribe(model, mp3)
        dur = audio_seconds(pid)
        m = score_transcript(expected_text(manifest, pid), text)["score"]
        x = score_transcript(expected_text(manifest, wrong), text)["score"]
        rows.append(dict(id=pid, bucket=bucket, audio_s=round(dur, 1), stt_s=round(dt, 2),
                         rtf=round(dt / dur, 2), matched=round(m, 2), mismatched=round(x, 2),
                         heard=text))
        print(f"{pid:<22}{dur:6.1f}s{dt:6.1f}s{dt/dur:6.2f}{m:7.2f}{x:9.2f}   {text[:34]}")

    print("\npor faixa de duração")
    print("─" * 100)
    print(f"{'faixa':<14}{'n':>3}{'match min':>11}{'match méd':>11}{'mismatch máx':>14}{'RTF méd':>9}{'pior stt':>10}")
    per_bucket = {}
    for b in BUCKETS:
        r = [x for x in rows if x["bucket"] == b]
        if not r:
            continue
        per_bucket[b] = dict(
            n=len(r),
            matched_min=min(x["matched"] for x in r),
            matched_mean=round(statistics.mean(x["matched"] for x in r), 2),
            mismatched_max=max(x["mismatched"] for x in r),
            rtf_mean=round(statistics.mean(x["rtf"] for x in r), 2),
            stt_max=max(x["stt_s"] for x in r),
        )
        v = per_bucket[b]
        print(f"{b:<14}{v['n']:>3}{v['matched_min']:>11.2f}{v['matched_mean']:>11.2f}"
              f"{v['mismatched_max']:>14.2f}{v['rtf_mean']:>9.2f}{v['stt_max']:>9.1f}s")

    mm = [x["matched"] for x in rows]
    xx = [x["mismatched"] for x in rows]
    lat = [x["stt_s"] for x in rows]
    sep = min(mm) - max(xx)
    print("\nno conjunto todo")
    print("─" * 100)
    print(f"  matched     min={min(mm):.2f}  mean={statistics.mean(mm):.2f}")
    print(f"  mismatched  max={max(xx):.2f}  mean={statistics.mean(xx):.2f}")
    print(f"  separação   {sep:.2f}  {'OK' if sep > 0.25 else 'FRACA'}")
    print(f"  stt         mean={statistics.mean(lat):.2f}s  max={max(lat):.2f}s  (orçamento 3s)")
    print(f"  RTF         mean={statistics.mean(x['rtf'] for x in rows):.2f}")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(dict(
            model=MODEL_NAME, compute=COMPUTE_TYPE, threads=CPU_THREADS or "default",
            load_s=round(load_s, 1), phrases=rows, buckets=per_bucket,
            matched_min=min(mm), matched_mean=round(statistics.mean(mm), 2),
            mismatched_max=max(xx), separation=round(sep, 2),
            stt_mean=round(statistics.mean(lat), 2), stt_max=max(lat),
            rtf_mean=round(statistics.mean(x["rtf"] for x in rows), 2),
        ), ensure_ascii=False, indent=1))
        print(f"\n  → {args.json}")


if __name__ == "__main__":
    main()
