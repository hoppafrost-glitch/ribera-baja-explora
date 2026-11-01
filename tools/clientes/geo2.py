import json, re, time, urllib.request, urllib.parse
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
def nom(q, lat, lon, d=0.15):
    prm = {"q": q, "format": "jsonv2", "limit": 6, "countrycodes": "es", "viewbox": f"{lon-d},{lat+d},{lon+d},{lat-d}", "bounded": 1}
    try: return json.load(urllib.request.urlopen(urllib.request.Request("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(prm), headers=UA), timeout=40))
    except Exception as e: print(e); return []
IN = json.load(open("tools/clientes/geo2_in.json", encoding="utf-8"))
out = {}
for slug, pois in IN.items():
    out[slug] = {}
    for pid, p in pois.items():
        name = re.sub(r"\(.*?\)", "", p["name"]).split("·")[0].strip()
        qs = [name, " ".join(p["words"]) + " " + p["mun"] if p["words"] else None, name.split(" y ")[0]]
        if p["church"]: qs += ["iglesia " + p["mun"], "parroquia " + p["mun"]]
        res = []
        for q in [q for q in qs if q]:
            for x in nom(q, p["lat"], p["lon"]):
                res.append({"q": q, "name": (x.get("display_name") or "").split(",")[0], "lat": float(x["lat"]), "lon": float(x["lon"]), "k": {"amenity": x.get("type") if x.get("category") == "amenity" else "", "cls": x.get("category"), "type": x.get("type")}})
            time.sleep(1.1)
        out[slug][pid] = res
        print(slug, pid, len(res), flush=True)
json.dump(out, open("tools/clientes/out/geo2.json", "w"), ensure_ascii=False, indent=0)
