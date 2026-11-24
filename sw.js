/* Guía Explora: funciona sin conexión una vez abierta (y mejor tras "Descargar para usar sin conexión"). */
const PFX = "rbx-";
const V = PFX + "v3", EXT = PFX + "ext";
const EXT_MAX = 600;          // tope de teselas del mapa guardadas
const PAGE_WAIT = 3000;       // con mala cobertura, a los 3 s se usa la copia guardada
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    const ks = await caches.keys();
    // Al pasar de v2 a v3 se conservan las fotos y audios ya descargados (con su nombre nuevo, sin versión).
    const old = ks.filter(k => k.startsWith(PFX) && k !== V && k !== EXT);
    const nv = await caches.open(V);
    for (const k of old) {
      const c = await caches.open(k);
      for (const req of await c.keys()) {
        const u = new URL(req.url);
        if (/\/(img|audio)\//.test(u.pathname) && !(await nv.match(u.origin + u.pathname, {ignoreSearch: true}))) {
          const r = await c.match(req); if (r) await nv.put(u.origin + u.pathname, r);
        }
      }
      await caches.delete(k);
    }
    await self.clients.claim();
  })());
});
async function rangeResponse(req, res) {
  const range = req.headers.get("range");
  if (!range || !res) return res;
  const buf = await res.arrayBuffer();
  const m = /bytes=(\d*)-(\d*)/.exec(range) || [];
  const size = buf.byteLength;
  const start = m[1] ? parseInt(m[1], 10) : 0;
  const end = m[2] ? Math.min(parseInt(m[2], 10), size - 1) : size - 1;
  return new Response(buf.slice(start, end + 1), { status: 206, headers: {
    "Content-Type": res.headers.get("Content-Type") || "audio/mpeg",
    "Content-Range": `bytes ${start}-${end}/${size}`, "Content-Length": String(end - start + 1), "Accept-Ranges": "bytes" } });
}
async function trimExt(c) {
  const ks = await c.keys();
  for (let i = 0; i < ks.length - EXT_MAX; i++) await c.delete(ks[i]);
}
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.pathname.endsWith("/__hb")) return;
  if (url.hostname === "api.github.com" || url.hostname.endsWith("goatcounter.com")) return;
  if (url.origin === location.origin) {
    const isPage = req.mode === "navigate" || url.pathname.endsWith(".html") || url.pathname.endsWith("/");
    if (isPage || url.pathname.endsWith("contenido.json") || url.pathname.endsWith("publish.json")) {
      // La página: se pide a la red, pero si en 3 s no llega y hay copia guardada, se usa la copia
      // (la red sigue por detrás y actualiza la copia para la próxima vez).
      const name = url.pathname.split("/").pop() || "index.html";
      const key = isPage && !name.endsWith(".html") ? "index.html" : name;
      const net = fetch(req).then(r => { if (r.ok) { const cp = r.clone(); caches.open(V).then(c => c.put(key, cp)); } return r; });
      e.waitUntil(net.catch(() => {}));
      e.respondWith((async () => {
        const cached = await caches.match(key);
        const fallback = cached || (isPage ? await caches.match("index.html") : new Response("{}", { headers: { "Content-Type": "application/json" } }));
        if (!cached) return net.catch(() => fallback);
        const timer = new Promise(res => setTimeout(() => res(null), PAGE_WAIT));
        const r = await Promise.race([net.catch(() => null), timer]);
        return r || cached;
      })());
      return;
    }
    // Fotos y audios: la copia guardada de esa versión; si cambia la versión (?v=), se baja la nueva y se borra la vieja.
    e.respondWith((async () => {
      const key = url.origin + url.pathname + url.search;
      const c = await caches.open(V);
      let res = await c.match(key);
      if (!res) {
        try {
          const net = await fetch(key);
          if (net.ok) {
            for (const k of await c.keys()) { const ku = new URL(k.url); if (ku.pathname === url.pathname && ku.search !== url.search) await c.delete(k); }
            await c.put(key, net.clone()); res = net;
          } else {
            const old = await c.match(url.origin + url.pathname, {ignoreSearch: true});
            if (old) res = old; else return net;
          }
        } catch (err) {
          const old = await c.match(url.origin + url.pathname, {ignoreSearch: true});
          if (old) res = old; else return new Response("", { status: 504 });
        }
      }
      return rangeResponse(req, res.clone());
    })());
    return;
  }
  // Recursos externos (tipografías, teselas del mapa): lo último que haya, y se refresca por detrás; con tope.
  e.respondWith(caches.open(EXT).then(async c => {
    const hit = await c.match(req);
    const net = fetch(req).then(r => { if (r && (r.ok || r.type === "opaque")) c.put(req, r.clone()).then(() => trimExt(c)); return r; }).catch(() => hit);
    return hit || net;
  }));
});
