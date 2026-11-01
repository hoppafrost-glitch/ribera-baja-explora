"""Descarga el Registro de Turismo de Aragón (datos abiertos) y se queda con la Comarca Ribera Baja del Ebro."""
import csv, io, json, os, time, unicodedata, urllib.request, urllib.parse
MUNIS = ["Alborge","Alforque","Cinco Olivas","Escatrón","Gelsa","La Zaida","Zaida (La)","Pina de Ebro","Quinto","Sástago","Velilla de Ebro"]
def n(s): return unicodedata.normalize("NFD", (s or "").lower()).encode("ascii","ignore").decode()
NM = {n(m) for m in MUNIS} | {"zaida, la", "zaida"}
RES = {"64":"albergue","65":"hotel","66":"apartamento","67":"restaurante","68":"camping","73":"rural"}
UA = {"User-Agent":"ribera-baja-explora/1.0 (guia turistica; github.com/hoppafrost-glitch)"}
os.makedirs("tools/opendata", exist_ok=True)
log = open("tools/opendata/log.txt","w")
out = []
for rid, typ in RES.items():
    url = f"https://opendata.aragon.es/GA_OD_Core/download?resource_id={rid}&formato=csv"
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=400).read()
    except Exception as e:
        print(rid, "ERROR", e, file=log); continue
    txt = None
    for enc in ("utf-8-sig","latin-1"):
        try: txt = raw.decode(enc); break
        except Exception: pass
    first = txt.splitlines()[0] if txt else ""
    delim = ";" if first.count(";") > first.count(",") else ","
    rows = list(csv.DictReader(io.StringIO(txt), delimiter=delim))
    print(rid, typ, "filas", len(rows), "columnas", list(rows[0].keys()) if rows else [], file=log)
    keep = []
    for r in rows:
        blob = " | ".join(str(v) for v in r.values())
        mun = r.get("localidad_establecimiento") or next((r[k] for k in r if k and "municipio" in k.lower()), "") or ""
        com = next((r[k] for k in r if k and "comarca" in k.lower()), "") or ""
        if n(mun) in NM or "ribera baja" in n(com):
            r = {k: v for k, v in r.items() if k and not any(x in k.lower() for x in ("telef","fax","mail","correo","movil","web","titular","nif","cif"))}
            keep.append(r)
    print("  comarca:", len(keep), file=log)
    if keep:
        with open(f"tools/opendata/{typ}.csv","w",newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(keep[0].keys())); w.writeheader(); w.writerows(keep)
    for r in keep:
        out.append({"type":typ, **r})
    time.sleep(1)
# geocodificar
for o in out:
    addr = next((o[k] for k in o if k and "direccion" in k.lower()), "")
    mun = o.get("localidad_establecimiento") or next((o[k] for k in o if k and "municipio" in k.lower()), "")
    q = f"{addr}, {mun}, Zaragoza, España"
    if not mun: continue
    try:
        u = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q":q,"format":"json","limit":1,"countrycodes":"es"})
        j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())
        if j and mun.split()[0].lower() in j[0].get("display_name","").lower(): o["_lat"], o["_lon"], o["_geo"] = float(j[0]["lat"]), float(j[0]["lon"]), j[0].get("display_name","")
    except Exception as e:
        print("geo", q, e, file=log)
    time.sleep(1.2)
json.dump(out, open("tools/opendata/negocios.json","w"), ensure_ascii=False, indent=1)
print("total", len(out), file=log)
