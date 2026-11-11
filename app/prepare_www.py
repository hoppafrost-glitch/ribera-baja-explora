# Copia la guía publicada dentro de la app y la adapta para funcionar instalada.
import os, shutil, sys
SRC = sys.argv[1]; DST = "www"; LIVE = "https://hoppafrost-glitch.github.io/ribera-baja-explora/"
shutil.rmtree(DST, ignore_errors=True); os.makedirs(DST)
for f in ["index.html","accesibilidad.html","privacidad.html","manifest.webmanifest","icon-192.png","icon-512.png","apple-touch-icon.png"]:
    shutil.copy(os.path.join(SRC,f), DST)
for d in ["img","audio"]:
    shutil.copytree(os.path.join(SRC,d), os.path.join(DST,d))
p = os.path.join(DST,"index.html"); s = open(p,encoding="utf8").read()
rep = [('fetch("contenido.json"', 'fetch("'+LIVE+'contenido.json"'),   # avisos y cambios del panel, en directo
       ('location.href.split("#")[0]', '"'+LIVE+'"'),                   # enlaces compartidos -> web pública
       ('navigator.serviceWorker.register("sw.js")', 'Promise.resolve()'),
       ('const OFF_OK=()=>', 'const OFF_OK=()=>false&&')]                 # sin botón de descarga: ya está todo dentro  # la app ya lleva todo dentro
for a,b in rep:
    n = s.count(a); assert n, a; s = s.replace(a,b)
open(p,"w",encoding="utf8").write(s); print("www listo")
