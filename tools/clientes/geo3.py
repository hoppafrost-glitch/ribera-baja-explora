"""Coordenadas: Nominatim + Overpass alrededor de un punto. tools/clientes/geo3_in.json -> out/geo3.json"""
import json, time, socket, urllib.request, urllib.parse
socket.setdefaulttimeout(45)
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica)"}
IN = json.load(open("tools/clientes/geo3_in.json", encoding="utf-8"))
OV = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
def get(u, data=None):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, data=data, headers=UA)))
out = {}
for k, v in IN.items():
    lat, lon, r, filt = v[:4]; names = v[4] if len(v) > 4 else []
    res = {"nominatim": {}, "overpass": []}
    for n in names:
        try:
            res["nominatim"][n] = [{"lat": x["lat"], "lon": x["lon"], "name": x.get("display_name"), "type": x.get("type")} for x in get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": n, "format": "json", "limit": 5, "countrycodes": "es"}))]
        except Exception as e: print(k, n, e)
        time.sleep(1.5)
    q = f'[out:json][timeout:40];nwr{filt}(around:{r},{lat},{lon});out center tags 40;'
    for u in OV:
        try:
            els = get(u, urllib.parse.urlencode({"data": q}).encode()).get("elements", [])
            res["overpass"] = [{"lat": (el.get("center") or el).get("lat"), "lon": (el.get("center") or el).get("lon"), "tags": {a: b for a, b in el.get("tags", {}).items() if a in ("name", "amenity", "historic", "building", "man_made", "natural", "tourism", "religion", "landuse", "water")}} for el in els]
            break
        except Exception as e: print(k, u, e)
    out[k] = res; print(k, len(res["overpass"]), {n: len(x) for n, x in res["nominatim"].items()}, flush=True)
json.dump(out, open("tools/clientes/out/geo3.json", "w"), ensure_ascii=False, indent=0)
