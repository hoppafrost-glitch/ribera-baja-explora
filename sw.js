/* Ribera Baja Explora: funciona sin conexión una vez abierta (y mejor tras "Descargar para usar sin conexión"). */
const V = "rbx-v1";
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V && k !== "rbx-ext").map(k => caches.delete(k)))).then(() => self.clients.claim()));
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
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.pathname.endsWith("/__hb")) return;
  if (url.origin === location.origin) {
    // La página: primero red (para recibir actualizaciones), si no hay conexión, la copia guardada.
    if (req.mode === "navigate" || url.pathname.endsWith(".html") || url.pathname.endsWith("/")) {
      e.respondWith(fetch(req).then(r => { const cp = r.clone(); caches.open(V).then(c => c.put("index.html", cp)); return r; })
        .catch(() => caches.match("index.html")));
      return;
    }
    // Fotos y audios: primero la copia guardada.
    e.respondWith((async () => {
      const key = url.origin + url.pathname;
      const c = await caches.open(V);
      let res = await c.match(key);
      if (!res) {
        try {
          const net = await fetch(key);
          if (net.ok) { await c.put(key, net.clone()); res = net; } else return net;
        } catch (err) { return new Response("", { status: 504 }); }
      }
      return rangeResponse(req, res.clone());
    })());
    return;
  }
  // Recursos externos (tipografías, teselas del mapa): lo último que haya, y se refresca por detrás.
  e.respondWith(caches.open("rbx-ext").then(async c => {
    const hit = await c.match(req);
    const net = fetch(req).then(r => { if (r && (r.ok || r.type === "opaque")) c.put(req, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
