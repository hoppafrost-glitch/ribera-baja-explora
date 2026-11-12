import json, os, urllib.request, urllib.parse
B = json.load(open("tools/pnoa/in.json"))
os.makedirs("tools/pnoa/out", exist_ok=True)
for k, (la1, lo1, la2, lo2) in B.items():
    q = {"service": "WMS", "version": "1.3.0", "request": "GetMap", "layers": "OI.OrthoimageCoverage", "styles": "",
         "crs": "EPSG:4326", "bbox": f"{la1},{lo1},{la2},{lo2}", "width": "1600", "height": "1000", "format": "image/jpeg"}
    u = "https://www.ign.es/wms-inspire/pnoa-ma?" + urllib.parse.urlencode(q)
    try:
        data = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "RiberaBajaExplora/1.0"}), timeout=120).read()
        open(f"tools/pnoa/out/{k}.jpg", "wb").write(data); print(k, len(data))
    except Exception as e:
        print(k, "ERROR", e)
