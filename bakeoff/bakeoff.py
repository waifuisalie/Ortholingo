#!/usr/bin/env python3
"""Ortholingo TTS bake-off.

Generates the test phrases (phrases.yaml) through each candidate TTS engine,
times them, then round-trips the audio through faster-whisper to sanity-check
intelligibility. Produces out/<engine>/<id>.wav|mp3, out/report.md and
out/listen.html for side-by-side listening.

Engines:
  chatterbox  Chatterbox Multilingual (Resemble, MIT) - local, el/pt/en
  mms         Meta MMS-TTS (VITS) - local, per-language models, lightweight
  edge        Microsoft Edge neural voices - CLOUD, quality reference baseline

Usage:
  python bakeoff.py                      # all engines + STT round-trip
  python bakeoff.py --engines mms,edge   # subset
  python bakeoff.py --no-stt             # skip whisper round-trip
"""
import argparse
import difflib
import pathlib
import time
import traceback
import unicodedata

import yaml

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "out"


def load_phrases():
    return yaml.safe_load((ROOT / "phrases.yaml").read_text())


def normalize(text: str) -> str:
    """Fold case, strip diacritics (polytonic AND monotonic) and punctuation."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) not in ("Mn", "Po", "Pd", "Pi", "Pf"))
    return " ".join(text.casefold().split())


# ---------------------------------------------------------------- engines

def gen_chatterbox(phrases, outdir):
    import soundfile as sf
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    rows = []
    for p in phrases:
        t0 = time.time()
        wav = model.generate(p["tts_text"], language_id=p["lang"])
        dt = time.time() - t0
        wav = wav.squeeze(0).numpy()
        path = outdir / f"{p['id']}.wav"
        sf.write(path, wav, model.sr)
        rows.append((p["id"], path, len(wav) / model.sr, dt))
    return rows


def gen_mms(phrases, outdir):
    import soundfile as sf
    import torch
    from transformers import AutoTokenizer, VitsModel

    repo = {"el": "facebook/mms-tts-ell", "pt": "facebook/mms-tts-por", "en": "facebook/mms-tts-eng"}
    cache = {}
    rows = []
    for p in phrases:
        if p["lang"] not in cache:
            cache[p["lang"]] = (
                VitsModel.from_pretrained(repo[p["lang"]]),
                AutoTokenizer.from_pretrained(repo[p["lang"]]),
            )
        model, tok = cache[p["lang"]]
        t0 = time.time()
        inputs = tok(p["tts_text"], return_tensors="pt")
        with torch.no_grad():
            wav = model(**inputs).waveform.squeeze(0).numpy()
        dt = time.time() - t0
        sr = model.config.sampling_rate
        path = outdir / f"{p['id']}.wav"
        sf.write(path, wav, sr)
        rows.append((p["id"], path, len(wav) / sr, dt))
    return rows


def gen_edge(phrases, outdir):
    import asyncio

    import edge_tts

    voices = {"el": "el-GR-AthinaNeural", "pt": "pt-BR-FranciscaNeural", "en": "en-US-JennyNeural"}

    async def synth(p):
        path = outdir / f"{p['id']}.mp3"
        t0 = time.time()
        await edge_tts.Communicate(p["tts_text"], voices[p["lang"]]).save(str(path))
        return p["id"], path, None, time.time() - t0

    async def run():
        return [await synth(p) for p in phrases]

    return asyncio.get_event_loop().run_until_complete(run())


ENGINES = {"chatterbox": gen_chatterbox, "mms": gen_mms, "edge": gen_edge}


# ---------------------------------------------------------------- STT round-trip

def stt_roundtrip(results, phrases, report):
    from faster_whisper import WhisperModel

    print("\n== STT round-trip (faster-whisper large-v3-turbo, int8 CPU) ==")
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    by_id = {p["id"]: p for p in phrases}
    for engine, rows in results.items():
        for pid, path, _dur, _dt in rows:
            p = by_id[pid]
            t0 = time.time()
            segments, _info = model.transcribe(str(path), language=p["lang"], beam_size=5)
            text = " ".join(s.text for s in segments).strip()
            dt = time.time() - t0
            sim = difflib.SequenceMatcher(None, normalize(p["tts_text"]), normalize(text)).ratio()
            line = f"  {engine:<10} {pid:<12} sim={sim:.2f}  stt={dt:4.1f}s  heard: {text}"
            print(line)
            report.append(f"| {engine} | {pid} | {sim:.2f} | {dt:.1f}s | {text} |")


# ---------------------------------------------------------------- report

def write_listen_html(results, phrases):
    by_id = {p["id"]: p for p in phrases}
    engines = list(results)
    rows_html = []
    for p in phrases:
        cells = "".join(
            f"<td><audio controls preload='none' src='{eng}/{path.name}'></audio></td>"
            if (path := next((r[1] for r in results[eng] if r[0] == p["id"]), None))
            else "<td>—</td>"
            for eng in engines
        )
        rows_html.append(
            f"<tr><th><div class='gr'>{p['display']}</div><div class='pt'>{p['pt']}</div></th>{cells}</tr>"
        )
    html = f"""<!doctype html><meta charset="utf-8"><title>Ortholingo TTS bake-off</title>
<style>
 body{{font-family:system-ui;margin:40px auto;max-width:1100px;background:#121A2E;color:#F2EAD8}}
 h1{{font-family:Georgia,serif}} table{{border-collapse:collapse;width:100%}}
 th,td{{border:1px solid #2C3859;padding:10px;text-align:left;vertical-align:top}}
 thead th{{color:#C9A24B;text-transform:uppercase;font-size:12px;letter-spacing:.1em}}
 .gr{{font-family:Georgia,serif;font-size:18px}} .pt{{color:#97A0BC;font-size:12px}}
 audio{{width:230px}}
</style>
<h1>Ortholingo — TTS bake-off</h1>
<p>Ouça e compare. O mascote deve soar como <b>um</b> personagem em todas as línguas.</p>
<table><thead><tr><th>Frase</th>{"".join(f"<th>{e}</th>" for e in engines)}</tr></thead>
<tbody>{"".join(rows_html)}</tbody></table>"""
    (OUT / "listen.html").write_text(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engines", default="chatterbox,mms,edge")
    ap.add_argument("--no-stt", action="store_true")
    args = ap.parse_args()

    phrases = load_phrases()
    report = [
        "# TTS bake-off report", "",
        "| engine | phrase | audio_s | gen_s | RTF |", "|---|---|---|---|---|",
    ]
    results = {}
    for name in args.engines.split(","):
        name = name.strip()
        outdir = OUT / name
        outdir.mkdir(parents=True, exist_ok=True)
        print(f"\n== {name} ==")
        try:
            t0 = time.time()
            rows = ENGINES[name](phrases, outdir)
            print(f"  done in {time.time()-t0:.0f}s (incl. model load)")
            results[name] = rows
            for pid, _path, dur, dt in rows:
                rtf = f"{dt/dur:.2f}" if dur else "—"
                d = f"{dur:.1f}" if dur else "—"
                print(f"  {pid:<12} audio={d:>5}s gen={dt:5.1f}s rtf={rtf}")
                report.append(f"| {name} | {pid} | {d} | {dt:.1f} | {rtf} |")
        except Exception:
            print(f"  FAILED: {name}")
            traceback.print_exc()

    if results:
        write_listen_html(results, phrases)
        if not args.no_stt:
            report += ["", "| engine | phrase | similarity | stt_s | transcript |", "|---|---|---|---|---|"]
            stt_roundtrip(results, phrases, report)
        (OUT / "report.md").write_text("\n".join(report) + "\n")
        print(f"\nWrote {OUT/'report.md'} and {OUT/'listen.html'}")


if __name__ == "__main__":
    main()
