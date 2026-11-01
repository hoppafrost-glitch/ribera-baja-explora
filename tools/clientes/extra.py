import json, os, re, time, urllib.request, urllib.parse
UA = {"User-Agent": "ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
X = json.load(open("tools/clientes/extra.json", encoding="utf-8"))
cl = lambda s: re.sub(r"<[^>]+>", "", s or "").strip()
for slug, pois in X.items():
    d = f"tools/clientes/extra/{slug}"; os.makedirs(d, exist_ok=True); meta = {}
    for pid, qs in pois.items():
        res = []
        for q in qs:
            prm = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "extmetadata|size|mime|url", "iiurlwidth": "330", "iiextmetadatafilter": "Artist|LicenseShortName"}
            if q.startswith("Category:"): prm.update(generator="categorymembers", gcmtitle=q, gcmtype="file", gcmlimit="30")
            else: prm.update(generator="search", gsrnamespace="6", gsrlimit="12", gsrsearch=q)
            try:
                j = json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(prm)))
                for pg in (j.get("query", {}).get("pages", {}) or {}).values():
                    ii = (pg.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
                    if ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 900: continue
                    if any(r["file"] == pg["title"][5:] for r in res): continue
                    res.append({"file": pg["title"][5:], "author": cl(m.get("Artist", {}).get("value"))[:60], "license": m.get("LicenseShortName", {}).get("value", ""), "thumb": ii.get("thumburl"), "q": q})
            except Exception as e: print(pid, q, e)
            time.sleep(0.4)
        res = res[:10]
        for i, r in enumerate(res):
            try:
                open(f"{d}/{pid}__{i}.jpg", "wb").write(get(r["thumb"])); time.sleep(0.3)
            except Exception as e: print("thumb", e)
        meta[pid] = res
    json.dump(meta, open(f"{d}/meta.json", "w"), ensure_ascii=False, indent=0)
    print(slug, "ok")
