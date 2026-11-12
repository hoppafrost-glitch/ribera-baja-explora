// Prepara la versión pública de una guía para Cloudflare Pages.
// Copia la web a ./public y minifica el JavaScript de las páginas, sin tocar el código fuente del repositorio.
// Uso:  node tools/publicar.js            (la guía está en la raíz del repositorio)
//       SLUG=campo-de-belchite node tools/publicar.js   (una guía dentro de una carpeta)
const fs = require("fs"), path = require("path");
const { minify } = require("terser");

const ROOT = process.cwd();
const SLUG = process.env.SLUG || "";
const SRC = path.join(ROOT, SLUG);
const OUT = path.join(ROOT, "public");
const SKIP = new Set(["tools", ".github", ".git", "app", "node_modules", "public", "voices", "package.json", "package-lock.json", "README.md", "photos.txt", "wrangler.toml"]);
const NOTICE = "/*! Explora Guías · © 2026 Santiago Fernández-Giro. Motor, diseño y código con licencia de uso no transferible. Prohibida su copia o reutilización sin autorización escrita. Los contenidos pertenecen a la entidad titular de la guía. */";

function copy(src, dst) {
  const st = fs.statSync(src);
  if (st.isDirectory()) {
    fs.mkdirSync(dst, { recursive: true });
    for (const f of fs.readdirSync(src)) {
      if (SKIP.has(f) || f.endsWith(".py") || f.endsWith(".bak")) continue;
      copy(path.join(src, f), path.join(dst, f));
    }
  } else fs.copyFileSync(src, dst);
}

async function minHtml(file) {
  let h = fs.readFileSync(file, "utf8");
  const re = /<script>([\s\S]*?)<\/script>/g;
  let out = "", last = 0, m, n = 0;
  while ((m = re.exec(h))) {
    out += h.slice(last, m.index);
    let code = m[1];
    if (code.length > 2000) {
      const r = await minify(code, { compress: { passes: 2 }, mangle: true, format: { comments: false, preamble: n === 0 ? NOTICE : "" } });
      code = r.code.replace(/<\/script/gi, "<\\/script"); n++;
    }
    out += "<script>" + code + "</script>";
    last = re.lastIndex;
  }
  out += h.slice(last);
  if (!/name="robots"/.test(out)) out = out.replace("<head>", '<head>\n<meta name="robots" content="noindex, nofollow">');
  fs.writeFileSync(file, out);
  return [h.length, out.length];
}

(async () => {
  fs.rmSync(OUT, { recursive: true, force: true });
  copy(SRC, OUT);
  for (const f of ["index.html", "placas.html", "simulador.html", "accesibilidad.html", "privacidad.html"]) {
    const p = path.join(OUT, f);
    if (fs.existsSync(p)) { const [a, b] = await minHtml(p); console.log(f, a, "->", b); }
  }
  fs.writeFileSync(path.join(OUT, "robots.txt"), "User-agent: *\nDisallow: /\n");
  fs.writeFileSync(path.join(OUT, "_headers"), "/*\n  X-Robots-Tag: noindex, nofollow\n  X-Frame-Options: SAMEORIGIN\n  Referrer-Policy: strict-origin-when-cross-origin\n");
  console.log("Publicado en", OUT);
})().catch(e => { console.error(e); process.exit(1); });
