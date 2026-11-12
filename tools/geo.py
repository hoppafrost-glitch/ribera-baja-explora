import json, time, urllib.request, urllib.parse
UA = {"User-Agent": "RiberaBajaExplora/1.0 (https://hoppafrost-glitch.github.io/ribera-baja-explora/)"}
def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=120))
Q = json.load(open("tools/geo_queries.json", encoding="utf-8"))
out = {"nominatim": {}, "overpass": {}}
for key, qs in Q["nominatim"].items():
    res = []
    for q in qs:
        try:
            r = get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "jsonv2", "limit": 5, "countrycodes": "es"}))
            res += [{"q": q, "name": x.get("display_name"), "lat": x["lat"], "lon": x["lon"], "type": x.get("type"), "cls": x.get("category")} for x in r]
        except Exception as e:
            res.append({"q": q, "error": str(e)})
        time.sleep(1.2)
    out["nominatim"][key] = res
# Overpass: todo lo que tenga nombre en la caja de la comarca y coincida con palabras clave
bbox = "41.26,-0.58,41.53,-0.20"
kw = Q["overpass_regex"]
ql = f'[out:json][timeout:90];(nwr["name"~"{kw}",i]({bbox}););out center tags;'
try:
    r = get("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": ql}).encode())
    for el in r.get("elements", []):
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        t = el.get("tags", {})
        out["overpass"].setdefault(t.get("name", "?"), []).append({"lat": c.get("lat"), "lon": c.get("lon"), "id": f'{el["type"]}/{el["id"]}',
            "tags": {k: v for k, v in t.items() if k in ("historic", "building", "amenity", "tourism", "man_made", "waterway", "religion", "addr:street", "addr:housenumber", "power", "heritage")}})
except Exception as e:
    out["overpass"]["ERROR"] = str(e)

for tq in Q.get("overpass_tags", []):
    ql = f'[out:json][timeout:90];({tq}({bbox}););out center tags;'
    try:
        r = get("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": ql}).encode())
        for el in r.get("elements", []):
            c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
            out.setdefault("tags", {}).setdefault(tq, []).append({"lat": c.get("lat"), "lon": c.get("lon"), "id": f'{el["type"]}/{el["id"]}', "tags": el.get("tags", {})})
    except Exception as e:
        out.setdefault("tags", {})[tq] = str(e)
    time.sleep(2)
json.dump(out, open("tools/geo_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
