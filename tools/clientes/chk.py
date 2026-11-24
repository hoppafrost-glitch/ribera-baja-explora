"""Metadatos de Commons de todas las fotos de las guías: coordenadas, categorías y descripción."""
import json, time, urllib.request, urllib.parse, re
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
L = json.load(open("tools/clientes/chk_in.json", encoding="utf-8"))
titles = sorted({"File:" + x["file"] for x in L if not x["aerial"]})
out = {}
cl = lambda s: re.sub(r"<[^>]+>", "", s or "").strip()
for i in range(0, len(titles), 40):
    b = titles[i:i+40]
    q = {"action": "query", "format": "json", "titles": "|".join(b), "prop": "imageinfo|categories|coordinates",
         "iiprop": "extmetadata|url", "iiurlwidth": "480", "cllimit": "max", "clshow": "!hidden", "colimit": "max", "coprop": "type|name"}
    for t in range(3):
        try:
            j = json.load(urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q), headers=UA), timeout=60)); break
        except Exception as e: print(e); time.sleep(5)
    norm = {n["to"]: n["from"] for n in j.get("query", {}).get("normalized", [])}
    for pg in j.get("query", {}).get("pages", {}).values():
        t = norm.get(pg["title"], pg["title"])
        ii = (pg.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
        out[t[5:]] = {"title": pg["title"], "missing": "missing" in pg,
            "gps": [m.get("GPSLatitude", {}).get("value"), m.get("GPSLongitude", {}).get("value")],
            "coords": [[c.get("lat"), c.get("lon"), c.get("type")] for c in pg.get("coordinates", [])],
            "cats": [c["title"][9:] for c in pg.get("categories", [])],
            "desc": cl(m.get("ImageDescription", {}).get("value"))[:300], "obj": cl(m.get("ObjectName", {}).get("value"))[:120],
            "thumb": ii.get("thumburl")}
    time.sleep(1)
json.dump(out, open("tools/clientes/chk_out.json", "w"), ensure_ascii=False, indent=0)
print(len(out), "de", len(titles))
