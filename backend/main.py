"""Ortholingo backend: pronunciation scoring endpoint.

Run:  backend/.venv/bin/uvicorn main:app --app-dir backend --port 8000
Two-tier scorer (decided by backend/bench.py, see ARCHITECTURE D4): whisper
`small` answers in ~1.3s; takes below PASS are re-judged by `large-v3-turbo`
(~5.6s) before the app calls them wrong. Both load at startup (~20s).
"""
import os
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from scoring import score_transcript

FAST_MODEL = os.environ.get("ORTHOLINGO_WHISPER_FAST", "small")
CAREFUL_MODEL = os.environ.get("ORTHOLINGO_WHISPER_CAREFUL", "large-v3-turbo")
PASS = 0.75
models = {}


@asynccontextmanager
async def lifespan(_app):
    from faster_whisper import WhisperModel

    models["fast"] = WhisperModel(FAST_MODEL, device="cpu", compute_type="int8")
    models["careful"] = (
        models["fast"] if CAREFUL_MODEL == FAST_MODEL
        else WhisperModel(CAREFUL_MODEL, device="cpu", compute_type="int8")
    )
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/api/health")
def health():
    return {"ok": True, "fast": FAST_MODEL, "careful": CAREFUL_MODEL}


def transcribe(tier: str, wav: str, lang: str) -> str:
    segments, _info = models[tier].transcribe(
        wav, language=lang, beam_size=1, vad_filter=True
    )
    return " ".join(s.text for s in segments).strip()


@app.post("/api/speech/score")
async def speech_score(
    audio: UploadFile = File(...),
    expected: str = Form(...),
    lang: str = Form("el"),
):
    t0 = time.time()
    raw = await audio.read()
    wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", "pipe:0",
             "-ac", "1", "-ar", "16000", wav],
            input=raw, check=True,
        )
        result = score_transcript(expected, transcribe("fast", wav, lang))
        result["tier"] = "fast"
        if result["score"] < PASS:
            # only turbo may fail a learner (small mishears long phrases)
            result = score_transcript(expected, transcribe("careful", wav, lang))
            result["tier"] = "careful"
    finally:
        os.unlink(wav)
    result["ms"] = int((time.time() - t0) * 1000)
    return result
