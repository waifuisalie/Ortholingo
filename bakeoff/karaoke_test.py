#!/usr/bin/env python3
"""Karaoke proof-of-concept: word-synced highlighting + click-a-word audio.

For each phrase: generate normal and -40% audio while capturing edge-tts
WordBoundary events (exact per-word timestamps), plus one isolated mp3 per
unique word (-20%). Emits out/karaoke/ assets and out/karaoke.html demo.
"""
import asyncio
import json
import pathlib
import unicodedata

import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent
KDIR = ROOT / "out" / "karaoke"
VOICE = "el-GR-AthinaNeural"

# display: polytonic + word-aligned Byzantine transliteration
PHRASES = [
    {
        "id": "kyrie",
        "tts": "Κύριε, ελέησον.",
        "words": ["Κύριε,", "ἐλέησον."],
        "translit": ["Kírie,", "eléison."],
        "pt": "Senhor, tem piedade.",
    },
    {
        "id": "trisagion",
        "tts": "Άγιος ο Θεός, Άγιος Ισχυρός, Άγιος Αθάνατος, ελέησον ημάς.",
        "words": ["Ἅγιος", "ὁ", "Θεός,", "Ἅγιος", "Ἰσχυρός,", "Ἅγιος", "Ἀθάνατος,", "ἐλέησον", "ἡμᾶς."],
        "translit": ["Ágios", "o", "Theós,", "Ágios", "Ischirós,", "Ágios", "Athánatos,", "eléison", "imás."],
        "pt": "Santo Deus, Santo Forte, Santo Imortal, tem piedade de nós.",
    },
    {
        "id": "pater",
        "tts": "Πάτερ ημών ο εν τοις ουρανοίς, αγιασθήτω το όνομά σου.",
        "words": ["Πάτερ", "ἡμῶν", "ὁ", "ἐν", "τοῖς", "οὐρανοῖς,", "ἁγιασθήτω", "τὸ", "ὄνομά", "σου."],
        "translit": ["Páter", "imón", "o", "en", "tis", "uranís,", "agiasthíto", "to", "ónomá", "su."],
        "pt": "Pai nosso, que estás nos Céus, santificado seja o teu Nome.",
    },
]


def wkey(word: str) -> str:
    """Filename-safe key for a word: strip accents/punctuation, casefold."""
    w = unicodedata.normalize("NFD", word)
    w = "".join(c for c in w if c.isalpha())
    return w.casefold()


async def synth_with_boundaries(text: str, rate: str, path: pathlib.Path):
    """Generate mp3 and return [[start_s, end_s], ...] per spoken word."""
    comm = edge_tts.Communicate(text, VOICE, rate=rate, boundary="WordBoundary")
    audio = b""
    bounds = []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            start = chunk["offset"] / 1e7
            end = start + chunk["duration"] / 1e7
            bounds.append([round(start, 3), round(end, 3), chunk["text"]])
    path.write_bytes(audio)
    return bounds


async def main():
    KDIR.mkdir(parents=True, exist_ok=True)
    data = []
    wordfiles = {}
    for p in PHRASES:
        entry = {"id": p["id"], "words": p["words"], "translit": p["translit"], "pt": p["pt"], "timings": {}}
        for label, rate in (("normal", "+0%"), ("slow", "-40%")):
            bounds = await synth_with_boundaries(p["tts"], rate, KDIR / f"{p['id']}_{label}.mp3")
            if len(bounds) != len(p["words"]):
                print(f"  note: {p['id']} {label}: {len(bounds)} boundaries vs {len(p['words'])} words")
            entry["timings"][label] = [b[:2] for b in bounds]
            print(f"{p['id']:<10} {label:<6} {len(bounds)} word boundaries")
        # isolated word clips (deduped across phrases)
        entry["wordkeys"] = []
        for word, mono in zip(p["words"], p["tts"].replace(".", "").replace(",", "").split()):
            key = wkey(word)
            entry["wordkeys"].append(key)
            if key not in wordfiles:
                await edge_tts.Communicate(mono, VOICE, rate="-20%").save(str(KDIR / f"w_{key}.mp3"))
                wordfiles[key] = True
                print(f"  word clip: {key}")
        data.append(entry)

    payload = json.dumps(data, ensure_ascii=False)
    html = """<!doctype html><meta charset="utf-8"><title>Ortholingo — karaokê litúrgico</title>
<style>
 body{font-family:system-ui;margin:40px auto;max-width:760px;background:#121A2E;color:#F2EAD8;padding:0 16px}
 h1{font-family:Georgia,serif} .hint{color:#97A0BC;font-size:14px;margin-bottom:28px}
 .card{background:#1B2440;border:1px solid #2C3859;border-radius:26px 26px 14px 14px;padding:22px;margin-bottom:22px}
 .gr,.tl{display:flex;flex-wrap:wrap;gap:6px 10px;justify-content:center}
 .gr{font-family:Georgia,serif;font-size:30px;margin-bottom:6px}
 .tl{font-size:15px;font-style:italic;color:#97A0BC;margin-bottom:6px}
 .pt{text-align:center;font-size:14px;color:#F2EAD8;opacity:.85;margin-bottom:16px}
 .w{cursor:pointer;border-radius:8px;padding:2px 6px;transition:background .12s,color .12s}
 .w:hover{background:#242F55}
 .w.hot{background:#C9A24B;color:#241C08}
 .controls{display:flex;gap:10px;justify-content:center}
 button{border:0;border-radius:999px;padding:10px 22px;font-size:14px;font-weight:700;cursor:pointer;
        background:#C9A24B;color:#241C08}
 button.slow{background:none;border:1.5px solid #C9A24B;color:#E7C97D}
</style>
<h1>Karaokê litúrgico — prova de conceito</h1>
<p class="hint">Aperte o play e veja as palavras acenderem (grego e transliteração juntas). Clique em qualquer palavra para ouvi-la sozinha.</p>
<div id="cards"></div>
<script>
const DATA = __DATA__;
const audio = new Audio();
let timings = null, spans = [], raf = null;

function stopHL(){ if(raf) cancelAnimationFrame(raf); spans.forEach(s=>s.forEach(x=>x.classList.remove('hot'))); }

function playPhrase(entry, mode){
  stopHL();
  timings = entry.timings[mode];
  const gr = [...document.querySelectorAll(`#c-${entry.id} .gr .w`)];
  const tl = [...document.querySelectorAll(`#c-${entry.id} .tl .w`)];
  spans = gr.map((g,i)=>[g, tl[i]].filter(Boolean));
  audio.src = `karaoke/${entry.id}_${mode}.mp3`;
  audio.play();
  const tick = ()=>{
    const t = audio.currentTime;
    spans.forEach((pair,i)=>{
      const on = timings[i] && t >= timings[i][0] && t <= timings[i][1] + 0.05;
      pair.forEach(x=>x.classList.toggle('hot', on));
    });
    if(!audio.paused && !audio.ended) raf = requestAnimationFrame(tick);
    else spans.forEach(s=>s.forEach(x=>x.classList.remove('hot')));
  };
  raf = requestAnimationFrame(tick);
}

function playWord(cardId, i, key){
  stopHL(); audio.pause();
  const pair = [
    document.querySelectorAll(`#c-${cardId} .gr .w`)[i],
    document.querySelectorAll(`#c-${cardId} .tl .w`)[i],
  ].filter(Boolean);
  const a = new Audio(`karaoke/w_${key}.mp3`);
  pair.forEach(x=>x.classList.add('hot'));
  a.onended = ()=>pair.forEach(x=>x.classList.remove('hot'));
  a.play();
}

const cards = document.getElementById('cards');
for(const e of DATA){
  const mk = (arr, cls)=>arr.map((w,i)=>
    `<span class="w" onclick="playWord('${e.id}', ${i}, '${e.wordkeys[i]}')">${w}</span>`).join('');
  cards.insertAdjacentHTML('beforeend', `
   <div class="card" id="c-${e.id}">
     <div class="gr">${mk(e.words)}</div>
     <div class="tl">${mk(e.translit)}</div>
     <div class="pt">${e.pt}</div>
     <div class="controls">
       <button onclick='playPhrase(DATA.find(d=>d.id==="${e.id}"),"normal")'>▶ normal</button>
       <button class="slow" onclick='playPhrase(DATA.find(d=>d.id==="${e.id}"),"slow")'>▶ lento (−40%)</button>
     </div>
   </div>`);
}
</script>"""
    (ROOT / "out" / "karaoke.html").write_text(html.replace("__DATA__", payload))
    print(f"\nWrote {ROOT/'out'/'karaoke.html'} ({len(wordfiles)} unique word clips)")


asyncio.get_event_loop().run_until_complete(main())
