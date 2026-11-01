"""Búsqueda amplia de fotos libres por lugar: Commons (texto, categoría y cercanía) + Openverse (Flickr y otros, solo CC BY, CC BY-SA, CC0, dominio público).
Entrada tools/clientes/in2.json {slug:{pid:{name,mun,lat,lon,fq:[...]}, "_towns": {...}}}  ->  out/<slug>-fotos2.json + miniaturas en cand/<slug>/"""
import json, os, re, sys, time, urllib.request, urllib.parse
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
def get(u, raw=False):
    for i in range(2):
        try:
            d = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
            return d if raw else json.loads(d)
        except Exception as e:
            time.sleep(3)
    return None
cl = lambda s: re.sub(r"<[^>]+>", "", s or "").strip()
IN = json.load(open("tools/clientes/in2.json", encoding="utf-8"))
only = sys.argv[1:]
def commons(params):
    params.update(action="query", format="json", prop="imageinfo", iiprop="extmetadata|size|mime|url", iiurlwidth="330", iiextmetadatafilter="Artist|LicenseShortName|ImageDescription")
    j = get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)) or {}
    out = []
    for pg in (j.get("query", {}).get("pages", {}) or {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
        if ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 800: continue
        lic = m.get("LicenseShortName", {}).get("value", "")
        if re.search(r"\bNC\b|\bND\b|non-?commercial", lic, re.I): continue
        out.append({"src": "commons", "file": pg["title"][5:], "author": cl(m.get("Artist", {}).get("value"))[:60], "license": lic,
                    "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(pg["title"].replace(" ", "_")), "thumb": ii.get("thumburl"),
                    "w": ii["width"], "h": ii["height"], "desc": cl(m.get("ImageDescription", {}).get("value"))[:140]})
    return out
for slug, pois in IN.items():
    if only and slug not in only: continue
    d = f"tools/clientes/cand/{slug}"; os.makedirs(d, exist_ok=True)
    res_all = {}
    for pid, p in pois.items():
        res = []
        for q in p.get("fq", []):
            if q.startswith("Category:"): res += commons({"generator": "categorymembers", "gcmtitle": q, "gcmtype": "file", "gcmlimit": "40"})
            else: res += commons({"generator": "search", "gsrnamespace": "6", "gsrlimit": "15", "gsrsearch": q})
            time.sleep(0.3)
        if p.get("lat"):
            res += [dict(x, near=True) for x in commons({"generator": "geosearch", "ggscoord": f'{p["lat"]}|{p["lon"]}', "ggsradius": str(p.get("radius", 350)), "ggsnamespace": "6", "ggslimit": "30"})]
            time.sleep(0.3)
        q = f'{p["name"]} {p["mun"]}'
        j = get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "license": "by,by-sa,cc0,pdm", "page_size": 12})) or {}
        for x in j.get("results", []):
            if not x.get("url") or (x.get("width") or 1000) < 800: continue
            res.append({"src": "openverse", "file": x["url"], "author": (x.get("creator") or "")[:60], "license": ("CC " + (x.get("license") or "").upper() + " " + (x.get("license_version") or "")).strip().replace("CC CC0", "CC0").replace("CC PDM", "Dominio público"),
                        "page": x.get("foreign_landing_url") or x["url"], "thumb": x.get("thumbnail") or x["url"], "w": x.get("width"), "h": x.get("height"), "desc": (x.get("title") or "")[:140], "provider": x.get("provider")})
        time.sleep(0.6)
        seen, uniq = set(), []
        for x in res:
            if x["file"] in seen: continue
            seen.add(x["file"]); uniq.append(x)
        uniq = uniq[:16]
        for i, x in enumerate(uniq):
            b = get(x["thumb"], raw=True)
            if b and b[:3] == b"\xff\xd8\xff":
                fn = f"{d}/{pid}__{i}.jpg"; open(fn, "wb").write(b); x["cand"] = os.path.basename(fn)
            time.sleep(0.15)
        res_all[pid] = uniq
        print(slug, pid, len(uniq), flush=True)
    json.dump(res_all, open(f"tools/clientes/out/{slug}-fotos2.json", "w"), ensure_ascii=False, indent=0)
