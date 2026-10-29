"""Genera la audioguía con voces neuronales Piper (código abierto) a partir de audio/texts.json."""
import json, os, subprocess, sys, wave, hashlib
VOICES = {"es": "es_ES-davefx-medium", "en": "en_GB-cori-high", "fr": "fr_FR-siwis-medium",
          "de": "de_DE-thorsten-high", "pt": "pt_PT-tugão-medium"}
texts = json.load(open("audio/texts.json", encoding="utf-8"))
os.makedirs("voices", exist_ok=True)
from piper import PiperVoice
try:
    from piper import SynthesisConfig
except Exception:
    SynthesisConfig = None
manifest_path = "audio/manifest.json"
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
for lang, vname in VOICES.items():
    subprocess.run([sys.executable, "-m", "piper.download_voices", "--download-dir", "voices", vname], check=True)
    voice = PiperVoice.load(os.path.join("voices", vname + ".onnx"))
    os.makedirs(f"audio/{lang}", exist_ok=True)
    for pid, by_lang in texts.items():
        txt = by_lang.get(lang)
        if not txt: continue
        h = hashlib.sha1((vname + txt).encode()).hexdigest()[:12]
        out = f"audio/{lang}/{pid}.mp3"
        if manifest.get(f"{lang}/{pid}") == h and os.path.exists(out): continue
        with wave.open("tmp.wav", "wb") as wf:
            if SynthesisConfig:
                voice.synthesize_wav(txt, wf, syn_config=SynthesisConfig(length_scale=1.06))
            else:
                voice.synthesize_wav(txt, wf)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "tmp.wav", "-af",
                        "apad=pad_dur=0.4,loudnorm=I=-17:TP=-1.5", "-ac", "1", "-ar", "22050",
                        "-c:a", "libmp3lame", "-b:a", "48k", out], check=True)
        manifest[f"{lang}/{pid}"] = h
        print(lang, pid, os.path.getsize(out))
json.dump(manifest, open(manifest_path, "w"), indent=0, sort_keys=True)
os.makedirs("audio/voices", exist_ok=True)
for vname in VOICES.values():
    for f in os.listdir("voices"):
        if f.startswith(vname) and f.endswith(".json"):
            subprocess.run(["cp", os.path.join("voices", f), "audio/voices/"])
