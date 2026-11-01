import json, time, urllib.request, urllib.parse
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
def ovp(q):
    for u in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, data=urllib.parse.urlencode({"data": q}).encode(), headers=UA), timeout=120))
        except Exception as e: print(e); time.sleep(5)
    return {}
IN = json.load(open("tools/clientes/geo2_in.json", encoding="utf-8"))
out = {}
for slug, pois in IN.items():
    out[slug] = {}
    for pid, p in pois.items():
        c = f'{p["lat"]},{p["lon"]}'
        parts = []
        if p["church"]: parts.append(f'nwr(around:900,{c})["amenity"="place_of_worship"];')
        if p["words"]:
            rx = "|".join(p["words"])
            parts.append(f'nwr(around:9000,{c})["name"~"{rx}",i];')
        if not parts: parts.append(f'nwr(around:1500,{c})["tourism"~"viewpoint|museum|attraction"];')
        r = ovp(f'[out:json][timeout:90];({"".join(parts)});out center tags;')
        res = []
        for el in r.get("elements", []):
            cc = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
            t = el.get("tags", {})
            res.append({"name": t.get("name", ""), "lat": cc.get("lat"), "lon": cc.get("lon"), "k": {k: v for k, v in t.items() if k in ("amenity", "historic", "tourism", "natural", "building", "religion", "man_made", "leisure", "waterway")}})
        out[slug][pid] = res
        print(slug, pid, len(res), flush=True)
        time.sleep(1.5)
json.dump(out, open("tools/clientes/out/geo2.json", "w"), ensure_ascii=False, indent=0)
