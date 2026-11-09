import json, os, re, time, urllib.request, urllib.parse
UA={"User-Agent":"ExploraGuias/1.0 (guia turistica; https://github.com/hoppafrost-glitch)"}
get=lambda u: urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
api=lambda p: json.loads(get("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(dict(p,format="json"))))
cl=lambda s: re.sub(r"<[^>]+>","",s or "").strip()
X=json.load(open("tools/clientes/cats.json"))
out="tools/clientes/cats"; os.makedirs(out,exist_ok=True); meta={}
for cat in X:
    cats=[cat]
    try:
        sub=api({"action":"query","list":"categorymembers","cmtitle":cat,"cmtype":"subcat","cmlimit":"50"})
        cats+= [c["title"] for c in sub["query"]["categorymembers"]]
    except Exception as e: print(cat,e)
    seen=set()
    for c in cats[:25]:
        try:
            j=api({"action":"query","generator":"categorymembers","gcmtitle":c,"gcmtype":"file","gcmlimit":"200","prop":"imageinfo","iiprop":"extmetadata|size|mime","iiurlwidth":"260","iiextmetadatafilter":"Artist|LicenseShortName"})
        except Exception as e: print(c,e); continue
        for pg in (j.get("query",{}).get("pages",{}) or {}).values():
            ii=(pg.get("imageinfo") or [{}])[0]; m=ii.get("extmetadata",{})
            if ii.get("mime")!="image/jpeg" or ii.get("width",0)<800: continue
            f=pg["title"][5:]
            if f in seen: continue
            seen.add(f); key=f"{len(meta)}"
            meta[key]={"file":f,"cat":c,"author":cl(m.get("Artist",{}).get("value"))[:60],"license":m.get("LicenseShortName",{}).get("value",""),"thumb":ii.get("thumburl")}
        time.sleep(0.5)
for k,r in meta.items():
    try: open(f"{out}/{k}.jpg","wb").write(get(r["thumb"])); time.sleep(0.15)
    except Exception as e: print("thumb",e)
json.dump(meta,open(f"{out}/meta.json","w"),ensure_ascii=False,indent=0); print(len(meta))
