"""Prepara datos de clientes nuevos: límites municipales, coordenadas de lugares y fotos de Commons.
Entrada: tools/clientes/in.json  ->  Salida: tools/clientes/out/<slug>-{base,geo,fotos}.json"""
import json, os, re, sys, time, urllib.request, urllib.parse, traceback
from shapely.geometry import LineString, mapping, shape
from shapely.ops import polygonize, unary_union, linemerge
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
os.makedirs("tools/clientes/out", exist_ok=True)
LOG = open("tools/clientes/out/log-" + ("-".join(sys.argv[1:]) or "all") + ".txt", "w")
def log(*a): print(*a, flush=True); print(*a, file=LOG, flush=True)
def get(url, data=None, tries=2):
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=100))
        except Exception as e:
            log("  retry", i, url[:80], e); time.sleep(5)
    raise RuntimeError("fallo " + url[:80])
OVP = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
def overpass(q):
    for u in OVP:
        try: return get(u, urllib.parse.urlencode({"data": q}).encode(), tries=2)
        except Exception as e: log("overpass", u, e)
    raise RuntimeError("overpass")
if not os.path.exists("tools/clientes/in.json"): sys.exit(0)
IN = json.load(open("tools/clientes/in.json", encoding="utf-8"))
only = sys.argv[1:]  # opcional: slugs
for slug, c in IN.items():
    if only and slug not in only: continue
    log("==", slug)
    # 1. límites
    try:
        names = "|".join(re.escape(m) for m in c["munis"])
        q = f'[out:json][timeout:180];area["name"="{c["prov"]}"]["boundary"="administrative"]["admin_level"~"^(4|6)$"]->.p;rel(area.p)["boundary"="administrative"]["admin_level"="8"]["name"~"^({names})( / .*)?$"];out geom;'
        r = overpass(q)
        feats, polys = [], []
        for el in r.get("elements", []):
            lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in el.get("members", []) if m.get("type") == "way" and m.get("role") in ("outer", "") and m.get("geometry")]
            poly = unary_union(list(polygonize(unary_union(lines))))
            if poly.is_empty: log("  sin polígono", el["tags"].get("name")); continue
            poly = poly.simplify(0.0006, preserve_topology=True)
            polys.append(poly)
            feats.append({"type": "Feature", "properties": {"n": el["tags"].get("name"), "c": 1}, "geometry": mapping(poly)})
        found = sorted(f["properties"]["n"].split(" / ")[0] for f in feats)
        log("  municipios", len(feats), "de", len(c["munis"]), "faltan:", sorted(set(c["munis"]) - set(found)))
        if polys:
            out = unary_union(polys).buffer(0.0004).buffer(-0.0004).simplify(0.0008)
            feats.append({"type": "Feature", "properties": {"outline": 1}, "geometry": mapping(out)})
            if c.get("river"):
                minx, miny, maxx, maxy = out.bounds
                bb = f"{miny-0.05},{minx-0.05},{maxy+0.05},{maxx+0.05}"
                rr = overpass(f'[out:json][timeout:120];way["waterway"="river"]["name"="{c["river"]}"]({bb});out geom;')
                ls = [LineString([(p["lon"], p["lat"]) for p in w["geometry"]]) for w in rr.get("elements", []) if w.get("geometry")]
                if ls:
                    mg = linemerge(unary_union(ls))
                    parts = list(mg.geoms) if hasattr(mg, "geoms") else [mg]
                    best = max(parts, key=lambda g: g.length).simplify(0.0005)
                    feats.append({"type": "Feature", "properties": {"river": 1}, "geometry": mapping(best)})
                    log("  río ok", len(best.coords))
        json.dump({"type": "FeatureCollection", "features": feats}, open(f"tools/clientes/out/{slug}-base.json", "w"), ensure_ascii=False)
    except Exception:
        log(traceback.format_exc())
    # 2. coordenadas de los lugares (Nominatim + Overpass por nombre dentro de la caja)
    geo = {}
    vb = c.get("bbox")  # [minlon,minlat,maxlon,maxlat]
    for pid, p in c["pois"].items():
        res = []
        for q in p.get("q", [f'{p["name"]}, {p["mun"]}']):
            try:
                prm = {"q": q, "format": "jsonv2", "limit": 4, "countrycodes": "es"}
                if vb: prm.update(viewbox=",".join(map(str, vb)), bounded=1)
                for x in get("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(prm)):
                    res.append({"q": q, "name": x.get("display_name"), "lat": float(x["lat"]), "lon": float(x["lon"]), "type": x.get("type"), "cls": x.get("category")})
            except Exception as e:
                res.append({"q": q, "error": str(e)})
            time.sleep(1.1)
        geo[pid] = res
    if vb:
        kw = "|".join(re.escape(w) for w in c.get("overpass_kw", []))
        if kw:
            try:
                bb = f"{vb[1]},{vb[0]},{vb[3]},{vb[2]}"
                r = overpass(f'[out:json][timeout:120];(nwr["name"~"{kw}",i]({bb}););out center tags;')
                ov = {}
                for el in r.get("elements", []):
                    cc = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
                    t = el.get("tags", {})
                    ov.setdefault(t.get("name", "?"), []).append({"lat": cc.get("lat"), "lon": cc.get("lon"), "id": f'{el["type"]}/{el["id"]}', "k": {k: v for k, v in t.items() if k in ("historic", "building", "amenity", "tourism", "religion", "natural", "man_made", "leisure")}})
                geo["_overpass"] = ov
            except Exception as e:
                geo["_overpass_error"] = str(e)
    json.dump(geo, open(f"tools/clientes/out/{slug}-geo.json", "w"), ensure_ascii=False, indent=0)
    # 3. fotos de Commons
    def api(params):
        params.update(action="query", format="json")
        return get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))
    cl = lambda s: re.sub(r"<[^>]+>", "", s or "").strip()
    fotos = {}
    for pid, p in c["pois"].items():
        res = []
        for q in p.get("fq", [f'{p["name"]} {p["mun"]}']):
            try:
                if q.startswith("Category:"):
                    j = api({"generator": "categorymembers", "gcmtitle": q, "gcmtype": "file", "gcmlimit": "60", "prop": "imageinfo", "iiprop": "extmetadata|size|mime|url", "iiurlwidth": "240", "iiextmetadatafilter": "Artist|LicenseShortName|ImageDescription"})
                else:
                    j = api({"generator": "search", "gsrnamespace": "6", "gsrlimit": "25", "gsrsearch": q, "prop": "imageinfo", "iiprop": "extmetadata|size|mime|url", "iiurlwidth": "240", "iiextmetadatafilter": "Artist|LicenseShortName|ImageDescription"})
                for pg in (j.get("query", {}).get("pages", {}) or {}).values():
                    ii = (pg.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
                    if ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 900: continue
                    lic = m.get("LicenseShortName", {}).get("value", "")
                    res.append({"file": pg["title"][5:], "author": cl(m.get("Artist", {}).get("value"))[:60], "license": lic, "w": ii["width"], "h": ii["height"], "thumb": ii.get("thumburl"), "desc": cl(m.get("ImageDescription", {}).get("value"))[:160], "q": q})
            except Exception as e:
                res.append({"error": str(e), "q": q})
            time.sleep(0.4)
        seen, uniq = set(), []
        for x in res:
            k = x.get("file") or x.get("error")
            if k in seen: continue
            seen.add(k); uniq.append(x)
        fotos[pid] = uniq[:24]
    json.dump(fotos, open(f"tools/clientes/out/{slug}-fotos.json", "w"), ensure_ascii=False, indent=0)
    log("  hecho", slug)
