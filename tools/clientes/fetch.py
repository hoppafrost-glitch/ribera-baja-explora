"""Descarga fotos elegidas: tools/clientes/<slug>-photos.txt (id|archivo) -> tools/clientes/img/<slug>/<id>.jpg y -s.jpg"""
import os, sys, time, urllib.request, urllib.parse, glob
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
for lst in glob.glob("tools/clientes/*-photos.txt"):
    slug = os.path.basename(lst)[:-len("-photos.txt")]
    d = f"tools/clientes/img/{slug}"; os.makedirs(d, exist_ok=True)
    for line in open(lst, encoding="utf-8"):
        line = line.strip()
        if not line or "|" not in line: continue
        pid, f = line.split("|", 1)
        for w, suf in ((960, ""), (330, "-s")):
            out = f"{d}/{pid}{suf}.jpg"
            if os.path.exists(out) and os.path.getsize(out) > 2000: continue
            for t in range(3):
                try:
                    u = f if f.startswith("http") else "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(f) + f"?width={w}"
                    data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
                    if f.startswith("http"):
                        import io
                        from PIL import Image
                        im = Image.open(io.BytesIO(data)).convert("RGB"); im.thumbnail((w, w * 2)); bio = io.BytesIO(); im.save(bio, "JPEG", quality=84); data = bio.getvalue()
                    if data[:3] == b"\xff\xd8\xff": open(out, "wb").write(data); break
                except Exception as e: print(pid, e)
                time.sleep(3)
        time.sleep(0.3)
    print(slug, len(os.listdir(d)))
