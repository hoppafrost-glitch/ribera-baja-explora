import urllib.request, concurrent.futures as cf, json, ssl
L=[l.strip() for l in open("tools/clientes/links.txt") if l.strip()]
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36","Accept-Language":"es-ES,es"}
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def chk(u):
    for m in ("HEAD","GET"):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers=UA,method=m),timeout=25,context=ctx); return u,r.status,r.geturl()
        except urllib.error.HTTPError as e:
            if m=="GET" or e.code not in (403,405,400,404,501): last=(u,e.code,"")
            if m=="GET": return u,e.code,""
        except Exception as e:
            if m=="GET": return u,"ERR "+type(e).__name__+" "+str(e)[:80],""
    return last
with cf.ThreadPoolExecutor(16) as ex: R=list(ex.map(chk,L))
json.dump(R,open("tools/clientes/links_out.json","w"),ensure_ascii=False,indent=0)
print(sum(1 for r in R if r[1]==200),"ok de",len(R))
