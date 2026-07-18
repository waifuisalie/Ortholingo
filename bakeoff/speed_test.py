#!/usr/bin/env python3
"""Ortholingo speed & stability test for Chatterbox.

Tests:
 1. Slower speech: Chatterbox cfg_weight (pacing) variants vs ffmpeg atempo
    post-stretch vs edge-tts rate=-25%.
 2. Stability: repeated generations of the same phrase to measure babble
    variance, with the two-signal QC gate (whisper similarity + speech rate).

Outputs out/speed/<variant>/<id>.wav|mp3, out/speed/report.md, out/listen_speed.html
"""
import pathlib
import subprocess
import time

import soundfile as sf
import yaml

from bakeoff import ROOT, OUT, normalize

SPEED = OUT / "speed"
PHRASE_IDS = ["kyrie", "trisagion", "pater"]

# QC thresholds
SIM_MIN = 0.90
RATE_BOUNDS = (7.0, 20.0)  # letters per second of audio; outside = suspicious


def letters(text: str) -> int:
    return sum(c.isalpha() for c in text)


def load_phrases():
    all_p = yaml.safe_load((ROOT / "phrases.yaml").read_text())
    return [p for p in all_p if p["id"] in PHRASE_IDS]


def wav_duration(path) -> float:
    info = sf.info(str(path))
    return info.frames / info.samplerate


def main():
    phrases = load_phrases()
    print("loading chatterbox…")
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    cb = ChatterboxMultilingualTTS.from_pretrained(device="cpu")

    print("loading whisper…")
    from faster_whisper import WhisperModel
    import difflib
    whisper = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

    def qc(path, phrase):
        segments, _ = whisper.transcribe(str(path), language=phrase["lang"], beam_size=1)
        text = " ".join(s.text for s in segments).strip()
        sim = difflib.SequenceMatcher(None, normalize(phrase["tts_text"]), normalize(text)).ratio()
        dur = wav_duration(path) if str(path).endswith(".wav") else None
        rate = letters(phrase["tts_text"]) / dur if dur else None
        ok = sim >= SIM_MIN and (rate is None or RATE_BOUNDS[0] <= rate <= RATE_BOUNDS[1])
        return sim, dur, rate, ok, text

    def gen_cb(phrase, outdir, cfg_weight, temperature):
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / f"{phrase['id']}.wav"
        t0 = time.time()
        wav = cb.generate(phrase["tts_text"], language_id=phrase["lang"],
                          cfg_weight=cfg_weight, temperature=temperature)
        dt = time.time() - t0
        sf.write(path, wav.squeeze(0).numpy(), cb.sr)
        return path, dt

    report = ["# Speed & stability test", "",
              "| variant | phrase | audio_s | rate l/s | sim | QC | transcript |",
              "|---|---|---|---|---|---|---|"]
    board = {}  # variant -> {phrase_id: path}

    # ---- Part 1: pacing variants -------------------------------------
    variants = [
        ("cb-default", dict(cfg_weight=0.5, temperature=0.8)),
        ("cb-slow", dict(cfg_weight=0.3, temperature=0.8)),
        ("cb-slow-stable", dict(cfg_weight=0.3, temperature=0.6)),
    ]
    for vname, params in variants:
        print(f"\n== {vname} {params} ==")
        board[vname] = {}
        for p in phrases:
            path, dt = gen_cb(p, SPEED / vname, **params)
            sim, dur, rate, ok, text = qc(path, p)
            board[vname][p["id"]] = path
            flag = "PASS" if ok else "FAIL"
            print(f"  {p['id']:<10} audio={dur:4.1f}s rate={rate:4.1f} sim={sim:.2f} [{flag}] gen={dt:.0f}s")
            report.append(f"| {vname} | {p['id']} | {dur:.1f} | {rate:.1f} | {sim:.2f} | {flag} | {text} |")

    # ---- Part 2: post-stretch of default (atempo 0.75) ---------------
    print("\n== cb-default + atempo 0.75 ==")
    vname = "cb-stretch075"
    board[vname] = {}
    (SPEED / vname).mkdir(parents=True, exist_ok=True)
    for p in phrases:
        src = SPEED / "cb-default" / f"{p['id']}.wav"
        dst = SPEED / vname / f"{p['id']}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                        "-af", "atempo=0.75", str(dst)], check=True)
        sim, dur, rate, ok, text = qc(dst, p)
        board[vname][p["id"]] = dst
        print(f"  {p['id']:<10} audio={dur:4.1f}s rate={rate:4.1f} sim={sim:.2f}")
        report.append(f"| {vname} | {p['id']} | {dur:.1f} | {rate:.1f} | {sim:.2f} | — | {text} |")

    # ---- Part 3: edge slow reference ---------------------------------
    print("\n== edge rate -25% ==")
    import asyncio
    import edge_tts
    vname = "edge-slow25"
    board[vname] = {}
    (SPEED / vname).mkdir(parents=True, exist_ok=True)

    async def edge_gen():
        for p in phrases:
            path = SPEED / vname / f"{p['id']}.mp3"
            await edge_tts.Communicate(p["tts_text"], "el-GR-AthinaNeural", rate="-25%").save(str(path))
            board[vname][p["id"]] = path
            sim, _dur, _rate, _ok, text = qc(path, p)
            print(f"  {p['id']:<10} sim={sim:.2f}")
            report.append(f"| {vname} | {p['id']} | — | — | {sim:.2f} | — | {text} |")
    asyncio.get_event_loop().run_until_complete(edge_gen())

    # ---- Part 4: stability retries on kyrie --------------------------
    print("\n== stability: kyrie x4, default params, QC gate ==")
    p = phrases[0]
    report += ["", "| attempt | audio_s | rate l/s | sim | QC |", "|---|---|---|---|---|"]
    best = None
    for i in range(1, 5):
        path, dt = gen_cb(p, SPEED / f"retry{i}", cfg_weight=0.5, temperature=0.8)
        sim, dur, rate, ok, text = qc(path, p)
        flag = "PASS" if ok else "FAIL"
        print(f"  attempt {i}: audio={dur:4.1f}s rate={rate:4.1f} sim={sim:.2f} [{flag}]")
        report.append(f"| {i} | {dur:.1f} | {rate:.1f} | {sim:.2f} | {flag} |")
        if ok and best is None:
            best = (i, path)
    if best:
        print(f"  QC gate would ship attempt {best[0]}")
        report.append(f"\nQC gate ships attempt {best[0]}.")
        board["retry-best"] = {p["id"]: best[1]}

    # ---- listening board ---------------------------------------------
    cols = list(board)
    by_id = {p["id"]: p for p in phrases}
    rows = []
    for pid in PHRASE_IDS:
        cells = "".join(
            f"<td><audio controls preload='none' src='speed/{path.parent.name}/{path.name}'></audio></td>"
            if (path := board[c].get(pid)) else "<td>—</td>"
            for c in cols
        )
        rows.append(f"<tr><th><div class='gr'>{by_id[pid]['display']}</div></th>{cells}</tr>")
    html = f"""<!doctype html><meta charset="utf-8"><title>Ortholingo — speed & stability</title>
<style>
 body{{font-family:system-ui;margin:40px auto;max-width:1200px;background:#121A2E;color:#F2EAD8}}
 h1{{font-family:Georgia,serif}} table{{border-collapse:collapse;width:100%}}
 th,td{{border:1px solid #2C3859;padding:9px;text-align:left;vertical-align:top}}
 thead th{{color:#C9A24B;text-transform:uppercase;font-size:11px;letter-spacing:.09em}}
 .gr{{font-family:Georgia,serif;font-size:17px}} audio{{width:200px}}
</style>
<h1>Speed & stability — Chatterbox pacing vs post-stretch vs Azure slow</h1>
<table><thead><tr><th>Frase</th>{"".join(f"<th>{c}</th>" for c in cols)}</tr></thead>
<tbody>{"".join(rows)}</tbody></table>"""
    (OUT / "listen_speed.html").write_text(html)
    (SPEED / "report.md").write_text("\n".join(report) + "\n")
    print(f"\nWrote {SPEED/'report.md'} and {OUT/'listen_speed.html'}")


if __name__ == "__main__":
    main()
