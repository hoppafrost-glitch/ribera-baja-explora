"""Búsquedas Overpass alrededor de un punto: tools/clientes/geo3_in.json -> out/geo3.json"""
import json, time, urllib.request, urllib.parse
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
IN = json.load(open("tools/clientes/geo3_in.json", encoding="utf-8"))
OV = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
out = {}
for k, (lat, lon, r, filt) in IN.items():
    q = f'[out:json][timeout:60];nwr{filt}(around:{r},{lat},{lon});out center tags 40;'
    res = None
    for t in range(6):
        u = OV[t % len(OV)]
        try:
            res = json.load(urllib.request.urlopen(urllib.request.Request(u, data=urllib.parse.urlencode({"data": q}).encode(), headers=UA), timeout=90)); break
        except Exception as e: print(k, u, e); time.sleep(8)
    out[k] = [{"lat": (el.get("center") or el).get("lat"), "lon": (el.get("center") or el).get("lon"), "tags": {a: b for a, b in el.get("tags", {}).items() if a in ("name", "amenity", "historic", "building", "man_made", "natural", "tourism", "religion", "landuse", "water")}} for el in (res or {}).get("elements", [])]
    print(k, len(out[k]), flush=True); time.sleep(2)
json.dump(out, open("tools/clientes/out/geo3.json", "w"), ensure_ascii=False, indent=0)
