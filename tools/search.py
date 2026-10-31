import json, sys, urllib.request, urllib.parse
UA = {"User-Agent": "RiberaBajaExplora/1.0 (https://hoppafrost-glitch.github.io/ribera-baja-explora/)"}
def api(params):
    params.update(action="query", format="json")
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
qs = json.load(open("tools/queries.json", encoding="utf-8"))
out = {}
for key, q in qs.items():
    res = []
    try:
        if q.startswith("Category:"):
            j = api({"generator": "categorymembers", "gcmtitle": q, "gcmtype": "file|subcat", "gcmlimit": "200",
                     "prop": "imageinfo", "iiprop": "extmetadata|size|mime", "iiextmetadatafilter": "Artist|LicenseShortName|ImageDescription"})
        else:
            j = api({"generator": "search", "gsrnamespace": "6", "gsrlimit": "50", "gsrsearch": q,
                     "prop": "imageinfo", "iiprop": "extmetadata|size|mime", "iiextmetadatafilter": "Artist|LicenseShortName|ImageDescription"})
        for p in (j.get("query", {}).get("pages", {}) or {}).values():
            if p.get("ns") == 14: res.append(["CAT", p["title"]]); continue
            ii = (p.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
            if ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 900: continue
            import re
            cl = lambda s: re.sub(r"<[^>]+>", "", s or "").strip()
            res.append([p["title"][5:], cl(m.get("Artist", {}).get("value"))[:50], m.get("LicenseShortName", {}).get("value", ""),
                        ii["width"], ii["height"], cl(m.get("ImageDescription", {}).get("value"))[:140]])
    except Exception as e:
        res.append(["ERROR", str(e)])
    out[key] = res
json.dump(out, open("tools/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
