"""Genera la audioguía con voces neuronales Piper (código abierto) a partir de audio/texts.json.
Uso: python tools/tts.py <idioma>   (es, en, fr, de, pt)"""
import json, os, subprocess, sys, wave, hashlib, traceback, urllib.request, urllib.parse

VOICES = {"es": ("es_ES", "davefx", "medium"), "en": ("en_GB", "cori", "high"), "fr": ("fr_FR", "siwis", "medium"),
          "de": ("de_DE", "thorsten", "high"), "pt": ("pt_PT", "tugão", "medium")}
LANG = sys.argv[1]
os.makedirs("audio/voices", exist_ok=True)
os.makedirs(f"audio/{LANG}", exist_ok=True)
log = open(f"audio/voices/log-{LANG}.txt", "w", encoding="utf-8")
def say(*a):
    print(*a, flush=True); print(*a, file=log, flush=True)

loc, name, q = VOICES[LANG]
vname = f"{loc}-{name}-{q}"
base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/" + urllib.parse.quote(f"{LANG}/{loc}/{name}/{q}/")
os.makedirs("voices", exist_ok=True)
for suf in (".onnx", ".onnx.json"):
    dst = os.path.join("voices", vname + suf)
    if not os.path.exists(dst):
        urllib.request.urlretrieve(base + urllib.parse.quote(vname + suf), dst)
try:
    urllib.request.urlretrieve(base + "MODEL_CARD", f"audio/voices/MODEL_CARD-{LANG}.txt")
except Exception as e:
    say("model card:", e)

from piper import PiperVoice
try:
    from piper import SynthesisConfig
except Exception:
    SynthesisConfig = None
voice = PiperVoice.load(os.path.join("voices", vname + ".onnx"))
say("voz", vname, "cargada")

def synth(text, path):
    with wave.open(path, "wb") as wf:
        if hasattr(voice, "synthesize_wav"):
            if SynthesisConfig:
                voice.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=1.05))
            else:
                voice.synthesize_wav(text, wf)
        else:  # API antigua (piper-tts < 1.3)
            voice.synthesize(text, wf, length_scale=1.05, sentence_silence=0.35)

texts = json.load(open("audio/texts.json", encoding="utf-8"))
mpath = f"audio/manifest-{LANG}.json"
manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
ok = bad = 0
for pid, by_lang in texts.items():
    txt = by_lang.get(LANG)
    if not txt:
        continue
    h = hashlib.sha1((vname + txt).encode()).hexdigest()[:12]
    out = f"audio/{LANG}/{pid}.mp3"
    if manifest.get(pid) == h and os.path.exists(out):
        continue
    try:
        synth(txt, "tmp.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "tmp.wav", "-af",
                        "apad=pad_dur=0.4,loudnorm=I=-17:TP=-1.5", "-ac", "1", "-ar", "22050",
                        "-c:a", "libmp3lame", "-b:a", "48k", out], check=True)
        manifest[pid] = h; ok += 1
        say(pid, os.path.getsize(out))
        json.dump(manifest, open(mpath, "w"), indent=0, sort_keys=True)
    except Exception:
        bad += 1
        say("ERROR", pid); say(traceback.format_exc())
say(f"hecho: {ok} nuevos, {bad} errores")
