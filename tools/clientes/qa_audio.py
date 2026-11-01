"""Control de calidad de la audioguía: transcribe una muestra con Whisper y compara con el texto."""
import json, glob, os, random, re, unicodedata
from faster_whisper import WhisperModel
def n(s): return re.findall(r"[a-z0-9]+", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode())
model = WhisperModel("base", device="cpu", compute_type="int8")
out = {}
for tf in sorted(glob.glob("tools/clientes/texts/*.json")):
    slug = os.path.basename(tf)[:-5]; T = json.load(open(tf))
    out[slug] = {}
    for lang in ["es", "en", "fr", "de", "pt"]:
        files = sorted(glob.glob(f"tools/clientes/audio/{slug}/{lang}/*.mp3"))
        random.seed(7); sample = random.sample(files, min(4, len(files)))
        rows = []
        for f in sample:
            pid = os.path.basename(f)[:-4]
            segs, info = model.transcribe(f, language=None, beam_size=1, vad_filter=False, without_timestamps=True, clip_timestamps=[0, 40])
            txt = " ".join(s.text for s in segs)
            ref = n(T[pid][lang])[:90]; hyp = n(txt)
            hit = sum(1 for w in set(hyp) if w in set(ref)) / max(1, len(set(hyp)))
            rows.append({"id": pid, "lang_detectado": info.language, "prob": round(info.language_probability, 2), "acierto": round(hit, 2), "oido": txt[:160]})
        out[slug][lang] = rows
        print(slug, lang, [(r["lang_detectado"], r["acierto"]) for r in rows], flush=True)
json.dump(out, open("tools/clientes/out/qa-audio.json", "w"), ensure_ascii=False, indent=1)
