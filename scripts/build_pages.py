#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pages.py — Genera las páginas estáticas indexables de La Lupa y el sitemap.

Por qué existe: index.html es una sola página (SPA) y Google/AdSense solo veían 2 URLs.
Este script convierte los datos en páginas HTML reales, con título, descripción,
canonical, Open Graph, JSON-LD y el loader de AdSense:

  caso/<id>-<slug>.html        una por caso (data.json)
  casos/index.html             índice de casos por sección y categoría
  casos/<seccion>-<cat>[-N].html  listado por categoría (paginado)
  lectura/<id>-<slug>.html     una por lectura (lecturas.json)
  lecturas/index.html          índice de lecturas
  lecturas/<seccion>[-N].html  listado por sección (paginado)
  opinion/<slug>.html          una por artículo de opinión PUBLICADO (extraído de index.html)
  opinion/index.html           índice de opinión
  sitemap.xml                  todas las URLs del sitio

Uso (desde la raíz del repo):  python scripts/build_pages.py
Los bots lo ejecutan tras actualizar los datos. Es una construcción limpia: borra y
regenera las carpetas de salida cada vez. No toca index.html ni los JSON.
"""
import datetime as _dt
import html
import json
import os
import re
import shutil
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://lalupa.com.co"
SITE_NAME = "La Lupa"
ADSENSE_ID = "ca-pub-1474229931660831"
GA4_ID = "G-68S1GCTY4J"
OUT_DIRS = ("caso", "casos", "lectura", "lecturas", "opinion")
PAGE_SIZE = 80          # casos por página de listado
LECT_PAGE_SIZE = 60     # lecturas por página de listado
RELATED_N = 6

SECCIONES = {
    "archivo": {
        "nombre": "Investigaciones 2022–2026",
        "corto": "Investigaciones",
        "color": "#1F3A5F",
        "hash": "#archivo",
        "cats": "categorias",
        "sub": "Seguimiento judicial a los casos del período 2022–2026, con fuente verificable.",
    },
    "nuevo-gobierno": {
        "nombre": "Gestión actual 2026–2030",
        "corto": "Gestión actual",
        "color": "#1F3A5F",
        "hash": "#nuevo-gobierno",
        "cats": "categorias_gestion",
        "sub": "Decisiones, programas y resultados del gobierno en curso.",
    },
    "terremoto": {
        "nombre": "Lupa al Terremoto",
        "corto": "Terremoto",
        "color": "#C8561A",
        "hash": "#terremoto",
        "cats": "categorias_terremoto",
        "sub": "Lo positivo y lo negativo de la respuesta al terremoto del 10 de agosto de 2026, con énfasis en Pereira.",
    },
}
SECCIONES_LECTURAS_FALLBACK = {
    "emprendimiento": {"nombre": "Emprendimiento", "color": "#0F7B6C"},
    "ciencia": {"nombre": "Ciencia", "color": "#7A3E9D"},
    "tecnologia": {"nombre": "Tecnología", "color": "#B8620B"},
}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


# ----------------------------------------------------------------- utilidades
def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def slugify(text, maxlen=70):
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    if len(text) > maxlen:
        text = text[:maxlen].rsplit("-", 1)[0]
    return text or "pagina"


def fecha_larga(iso):
    try:
        d = _dt.date.fromisoformat(str(iso)[:10])
        return f"{d.day} de {MESES[d.month - 1]} de {d.year}"
    except Exception:
        return str(iso or "")


def iso_date(s):
    try:
        return _dt.date.fromisoformat(str(s)[:10]).isoformat()
    except Exception:
        return None


def recorte(text, n=170):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def load_json(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------- plantilla
def head_html(title, desc, path, og_type="article", published=None, modified=None,
              jsonld=None, extra_css=False, noindex=False):
    canonical = SITE + path
    parts = [
        '<!DOCTYPE html>', '<html lang="es">', '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'<title>{esc(title)} · {SITE_NAME}</title>',
        f'<meta name="description" content="{esc(desc)}">',
        f'<link rel="canonical" href="{canonical}">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{canonical}">',
        '<meta property="og:locale" content="es_CO">',
        '<meta name="twitter:card" content="summary">',
        f'<meta name="google-adsense-account" content="{ADSENSE_ID}">',
    ]
    if noindex:
        parts.append('<meta name="robots" content="noindex,follow">')
    if published:
        parts.append(f'<meta property="article:published_time" content="{published}">')
    if modified:
        parts.append(f'<meta property="article:modified_time" content="{modified}">')
    parts += [
        f'<link rel="alternate" type="application/rss+xml" title="{SITE_NAME} · Lecturas" href="{SITE}/feed-lecturas.xml">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;0,6..72,800;1,6..72,500&family=Public+Sans:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap">',
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">',
    ]
    if extra_css:
        parts.append('<link rel="stylesheet" href="/styles.css">')
    parts.append('<link rel="stylesheet" href="/pages.css?v=20261105">')
    parts += [
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>',
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','" + GA4_ID + "');</script>",
        f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_ID}" crossorigin="anonymous"></script>',
    ]
    if jsonld:
        parts.append('<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False) + '</script>')
    parts.append('</head>')
    return "\n".join(parts) + "\n"


HEADER = """<body class="lp-static">
<header class="lp-sh">
  <div class="lp-sh-inner">
    <a class="lp-sh-logo" href="/" aria-label="La Lupa, portada">
      <svg viewBox="0 0 52 52" aria-hidden="true"><circle cx="22" cy="22" r="15" fill="#FFD84D" stroke="#131A26" stroke-width="4"/><path d="M33 33 L46 46" stroke="#131A26" stroke-width="6" stroke-linecap="square"/><path d="M15 19 h14 M15 25 h9" stroke="#131A26" stroke-width="3"/></svg>
      <span>La Lupa</span>
    </a>
    <nav class="lp-sh-nav" aria-label="Secciones">
      <a href="/#portada">Portada</a>
      <a href="/#politica">Política</a>
      <a href="/#terremoto">Terremoto</a>
      <a href="/casos/">Casos</a>
      <a href="/lecturas/">Lecturas</a>
      <a href="/opinion/">Opinión</a>
      <a href="/acerca.html">Acerca de</a>
    </nav>
  </div>
</header>
"""

FOOTER = """<footer class="lp-sf">
  <div class="lp-sf-inner">
    <p><strong>La Lupa · Lo que vale la pena leer</strong></p>
    <p>Periódico digital independiente. Toda la información proviene de fuentes periodísticas públicas y verificables. Sin afiliación con partidos políticos.</p>
    <nav class="lp-sf-links" aria-label="Información del sitio">
      <a href="/acerca.html">Acerca de</a>
      <a href="/contacto.html">Contacto</a>
      <a href="/privacidad.html">Privacidad</a>
      <a href="/sugerir.html">Sugerir un caso</a>
      <a href="/feed-lecturas.xml">RSS</a>
    </nav>
    <p class="lp-sf-copy">La Lupa 2024–2026 · Información de dominio público</p>
  </div>
</footer>
</body>
</html>
"""


def page(title, desc, path, body, **kw):
    return head_html(title, desc, path, **kw) + HEADER + body + FOOTER


def crumbs(items):
    out = []
    for label, href in items:
        out.append(f'<a href="{esc(href)}">{esc(label)}</a>' if href else f'<span>{esc(label)}</span>')
    return '<nav class="lp-crumbs" aria-label="Ruta">' + ' <i>›</i> '.join(out) + '</nav>'


# ----------------------------------------------------------------- casos
def seccion_de(caso):
    s = caso.get("seccion") or "archivo"
    return s if s in SECCIONES else "archivo"


def caso_path(caso):
    return f"/caso/{caso['id']}-{slugify(caso.get('titulo', ''))}.html"


def cat_listing_path(sec, cat_id, n=1):
    base = f"/casos/{sec}-{slugify(cat_id)}"
    return base + (".html" if n == 1 else f"-{n}.html")


def lect_listing_path(sec, n=1):
    base = f"/lecturas/{slugify(sec)}"
    return base + (".html" if n == 1 else f"-{n}.html")


def caso_card(c, cats):
    sec = seccion_de(c)
    cat = cats[sec].get(c.get("categoria"), {})
    return (
        '<li class="lp-card">'
        f'<a class="lp-card-t" href="{caso_path(c)}">{esc(c.get("titulo"))}</a>'
        f'<p class="lp-card-m">{esc(cat.get("nombre", c.get("categoria", "")))} · {esc(fecha_larga(c.get("fecha")))} · {esc(c.get("estado", ""))}</p>'
        f'<p class="lp-card-d">{esc(recorte(c.get("descripcion"), 190))}</p>'
        '</li>'
    )


def render_caso(c, cats, related, regiones):
    sec = seccion_de(c)
    info = SECCIONES[sec]
    cat = cats[sec].get(c.get("categoria"), {"nombre": c.get("categoria", "")})
    titulo = c.get("titulo", "")
    desc = recorte(c.get("descripcion"), 158)
    path = caso_path(c)
    pub = iso_date(c.get("fecha")) or iso_date(c.get("added_date"))
    mod = iso_date(c.get("added_date")) or pub

    meta_bits = [f"EXP. #{c['id']}", fecha_larga(c.get("fecha"))]
    if c.get("estado"):
        meta_bits.append("Estado: " + str(c["estado"]))
    if c.get("gravedad"):
        meta_bits.append("Gravedad: " + str(c["gravedad"]))
    if c.get("region"):
        meta_bits.append("Región: " + regiones.get(c["region"], c["region"]))
    if c.get("signo"):
        meta_bits.append("Balance: " + ("positivo" if c["signo"] == "positivo" else "negativo" if c["signo"] == "negativo" else str(c["signo"])))

    ficha = []
    if c.get("entidad"):
        ficha.append(("Entidad", c["entidad"]))
    if c.get("personas_involucradas"):
        ficha.append(("Personas mencionadas", ", ".join(str(p) for p in c["personas_involucradas"])))
    if c.get("evidencia"):
        ficha.append(("Evidencia", c["evidencia"]))
    ficha_html = ""
    if ficha:
        ficha_html = '<dl class="lp-ficha">' + "".join(
            f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in ficha) + "</dl>"

    fuentes = c.get("fuentes") or []
    fuentes_html = ""
    if fuentes:
        lis = []
        for f in fuentes:
            if not isinstance(f, dict):
                continue
            nombre = f.get("nombre") or f.get("url") or "Fuente"
            url = f.get("url") or ""
            fecha = f" · {esc(fecha_larga(f['fecha']))}" if f.get("fecha") else ""
            if url:
                lis.append(f'<li><a href="{esc(url)}" target="_blank" rel="noopener nofollow">{esc(nombre)}</a>{fecha}</li>')
            else:
                lis.append(f"<li>{esc(nombre)}{fecha}</li>")
        if lis:
            fuentes_html = '<section class="lp-fuentes"><h2>Fuentes</h2><ul>' + "".join(lis) + "</ul></section>"

    related_html = ""
    if related:
        related_html = (
            f'<section class="lp-related"><h2>Más casos de {esc(cat.get("nombre", ""))}</h2><ul class="lp-cards">'
            + "".join(caso_card(r, cats) for r in related)
            + "</ul>"
            + f'<p class="lp-more"><a href="{cat_listing_path(sec, c.get("categoria", ""))}">Ver todos los casos de {esc(cat.get("nombre", ""))} →</a></p>'
            + "</section>"
        )

    body = (
        '<main class="lp-page">'
        + crumbs([("La Lupa", "/"), ("Casos", "/casos/"), (info["corto"], "/#" + sec if sec != "archivo" else "/#archivo"),
                  (cat.get("nombre", ""), cat_listing_path(sec, c.get("categoria", "")))])
        + f'<article class="lp-art" style="--c:{info["color"]}">'
        + f'<p class="lp-kicker">{esc(info["nombre"])} · {esc(cat.get("nombre", ""))}</p>'
        + f"<h1>{esc(titulo)}</h1>"
        + '<p class="lp-meta">' + " · ".join(esc(b) for b in meta_bits) + "</p>"
        + '<div class="lp-body"><p>' + esc(c.get("descripcion", "")) + "</p></div>"
        + ficha_html
        + fuentes_html
        + f'<p class="lp-cta"><a class="lp-btn" href="/index.html#caso-{c["id"]}">Ver este caso en La Lupa (comentarios y casos relacionados)</a></p>'
        + f'<p class="lp-note">Cada nota se publica con su fuente. Si encuentras un error o tienes información adicional, <a href="/contacto.html">escríbenos</a> o <a href="/sugerir.html">sugiere un caso</a>.</p>'
        + "</article>"
        + related_html
        + "</main>"
    )

    jsonld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": titulo[:110],
        "description": desc,
        "mainEntityOfPage": SITE + path,
        "articleSection": cat.get("nombre", ""),
        "inLanguage": "es",
        "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE},
    }
    if pub:
        jsonld["datePublished"] = pub
    if mod:
        jsonld["dateModified"] = mod

    return page(titulo, desc, path, body, published=pub, modified=mod, jsonld=jsonld)


def paginate(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)] or [[]]


def pager_html(path_fn, n_pages, current):
    if n_pages <= 1:
        return ""
    links = []
    for n in range(1, n_pages + 1):
        if n == current:
            links.append(f"<strong>{n}</strong>")
        else:
            links.append(f'<a href="{path_fn(n)}">{n}</a>')
    return '<nav class="lp-pager" aria-label="Páginas">' + " ".join(links) + "</nav>"


def build_casos(data):
    casos = [c for c in data.get("casos", []) if c.get("id") is not None and c.get("titulo")]
    cats = {}
    for sec, info in SECCIONES.items():
        cats[sec] = {c["id"]: c for c in data.get(info["cats"], []) if isinstance(c, dict) and c.get("id")}
    regiones = {r["id"]: r.get("nombre", r["id"]) for r in data.get("regiones_terremoto", []) if isinstance(r, dict)}

    # orden determinista: id descendente (los nuevos primero)
    casos.sort(key=lambda c: int(c["id"]), reverse=True)
    por_cat = {}
    for c in casos:
        por_cat.setdefault((seccion_de(c), c.get("categoria")), []).append(c)

    urls = []
    # páginas de caso
    for key, lista in por_cat.items():
        for idx, c in enumerate(lista):
            # relacionados = los siguientes más antiguos de la misma categoría (estable entre corridas)
            related = lista[idx + 1: idx + 1 + RELATED_N]
            if len(related) < RELATED_N:
                related += lista[max(0, idx - (RELATED_N - len(related))): idx]
            write(caso_path(c).lstrip("/"), render_caso(c, cats, related, regiones))
            urls.append((caso_path(c), iso_date(c.get("added_date")) or iso_date(c.get("fecha")), "monthly", "0.6"))

    # listados por categoría
    for (sec, cat_id), lista in por_cat.items():
        info = SECCIONES[sec]
        cat = cats[sec].get(cat_id, {"nombre": cat_id or "Sin categoría", "descripcion": ""})
        pages = paginate(lista, PAGE_SIZE)
        for n, chunk in enumerate(pages, start=1):
            path = cat_listing_path(sec, cat_id or "sin-categoria", n)
            title = f'{cat.get("nombre", "")} · {info["nombre"]}' + (f" (página {n})" if n > 1 else "")
            desc = recorte(f'{cat.get("descripcion", "")} {len(lista)} casos documentados con fuente en {info["nombre"]}.', 158)
            body = (
                '<main class="lp-page">'
                + crumbs([("La Lupa", "/"), ("Casos", "/casos/"), (info["corto"], "/#" + sec), (cat.get("nombre", ""), None)])
                + f'<header class="lp-lhead" style="--c:{info["color"]}"><p class="lp-kicker">{esc(info["nombre"])}</p>'
                + f'<h1>{esc(cat.get("nombre", ""))}</h1><p class="lp-sub">{esc(cat.get("descripcion", ""))} {len(lista)} casos documentados, cada uno con su fuente.</p></header>'
                + '<ul class="lp-cards lp-cards-list">' + "".join(caso_card(c, cats) for c in chunk) + "</ul>"
                + pager_html(lambda k, s=sec, ci=cat_id or "sin-categoria": cat_listing_path(s, ci, k), len(pages), n)
                + "</main>"
            )
            write(path.lstrip("/"), page(title, desc, path, body, og_type="website", noindex=(n > 1)))
            if n == 1:
                urls.append((path, iso_date(lista[0].get("added_date")) if lista else None, "daily", "0.7"))

    # índice de casos
    secs_html = []
    for sec, info in SECCIONES.items():
        items = []
        for cat_id, cat in cats[sec].items():
            n = len(por_cat.get((sec, cat_id), []))
            if n == 0:
                continue
            items.append(f'<li><a href="{cat_listing_path(sec, cat_id)}">{esc(cat.get("nombre", cat_id))}</a> <span>{n}</span></li>')
        secs_html.append(
            f'<section class="lp-secblock" style="--c:{info["color"]}"><h2>{esc(info["nombre"])}</h2><p>{esc(info["sub"])}</p><ul class="lp-catlist">'
            + "".join(items) + "</ul></section>"
        )
    ultimos = casos[:30]
    body = (
        '<main class="lp-page">'
        + crumbs([("La Lupa", "/"), ("Casos", None)])
        + '<header class="lp-lhead"><h1>Todos los casos</h1>'
        + f'<p class="lp-sub">{len(casos)} casos documentados con fuente verificable, organizados por período y categoría.</p></header>'
        + "".join(secs_html)
        + '<section><h2>Lo último</h2><ul class="lp-cards lp-cards-list">' + "".join(caso_card(c, cats) for c in ultimos) + "</ul></section>"
        + "</main>"
    )
    write("casos/index.html", page("Todos los casos", f"{len(casos)} casos documentados con fuente verificable: investigaciones 2022–2026, gestión 2026–2030 y terremoto.", "/casos/", body, og_type="website"))
    urls.append(("/casos/", iso_date(casos[0].get("added_date")) if casos else None, "daily", "0.8"))
    return urls, len(casos)


# ----------------------------------------------------------------- lecturas
def lectura_path(l):
    return f"/lectura/{l['id']}-{slugify(l.get('titulo', ''))}.html"


def lectura_card(l, secs):
    s = secs.get(l.get("seccion"), {})
    extra = f' · {int(l["tiempo_lectura_min"])} min' if l.get("tiempo_lectura_min") else ""
    return (
        '<li class="lp-card">'
        f'<a class="lp-card-t" href="{lectura_path(l)}">{esc(l.get("titulo"))}</a>'
        f'<p class="lp-card-m">{esc(s.get("nombre", l.get("seccion", "")))} · {esc(fecha_larga(l.get("fecha")))}{extra}</p>'
        f'<p class="lp-card-d">{esc(recorte(l.get("resumen"), 190))}</p>'
        '</li>'
    )


def render_lectura(l, secs, related):
    s = secs.get(l.get("seccion"), {"nombre": l.get("seccion", ""), "color": "#131A26"})
    titulo = l.get("titulo", "")
    desc = recorte(l.get("resumen"), 158)
    path = lectura_path(l)
    pub = iso_date(l.get("fecha")) or iso_date(l.get("added_date"))
    fuente = l.get("fuente") or {}
    meta = [fecha_larga(l.get("fecha"))]
    if l.get("tiempo_lectura_min"):
        meta.append(f'Lectura de {int(l["tiempo_lectura_min"])} min')
    if l.get("idioma_original") and l["idioma_original"] != "es":
        meta.append("Resumen en español de un artículo en " + ("inglés" if l["idioma_original"] == "en" else str(l["idioma_original"])))
    tags = l.get("tags") or []
    tags_html = ('<p class="lp-tags">' + " ".join(f"<span>#{esc(t)}</span>" for t in tags) + "</p>") if tags else ""
    porque = f'<section class="lp-porque"><h2>Por qué vale la pena leerlo</h2><p>{esc(l["por_que_leerlo"])}</p></section>' if l.get("por_que_leerlo") else ""
    fuente_html = ""
    if fuente.get("url"):
        fuente_html = (
            f'<p class="lp-cta"><a class="lp-btn" href="{esc(fuente["url"])}" target="_blank" rel="noopener nofollow">'
            f'Leer el artículo original en {esc(fuente.get("nombre") or "la fuente")} ↗</a></p>'
        )
    related_html = ""
    if related:
        related_html = (
            f'<section class="lp-related"><h2>Más lecturas de {esc(s.get("nombre", ""))}</h2><ul class="lp-cards">'
            + "".join(lectura_card(r, secs) for r in related) + "</ul>"
            + f'<p class="lp-more"><a href="{lect_listing_path(l.get("seccion", ""))}">Ver todas las lecturas de {esc(s.get("nombre", ""))} →</a></p></section>'
        )
    body = (
        '<main class="lp-page">'
        + crumbs([("La Lupa", "/"), ("Lecturas", "/lecturas/"), (s.get("nombre", ""), lect_listing_path(l.get("seccion", "")))])
        + f'<article class="lp-art" style="--c:{s.get("color", "#131A26")}">'
        + f'<p class="lp-kicker">Lecturas · {esc(s.get("nombre", ""))}</p>'
        + f"<h1>{esc(titulo)}</h1>"
        + '<p class="lp-meta">' + " · ".join(esc(m) for m in meta) + "</p>"
        + '<div class="lp-body"><p>' + esc(l.get("resumen", "")) + "</p></div>"
        + porque + tags_html + fuente_html
        + f'<p class="lp-note">Las lecturas son resúmenes editoriales en español de artículos publicados por otros medios; el crédito y el contenido completo pertenecen a la fuente enlazada.</p>'
        + "</article>" + related_html + "</main>"
    )
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": titulo[:110],
        "description": desc,
        "mainEntityOfPage": SITE + path,
        "articleSection": s.get("nombre", ""),
        "inLanguage": "es",
        "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE},
    }
    if pub:
        jsonld["datePublished"] = pub
        jsonld["dateModified"] = pub
    return page(titulo, desc, path, body, published=pub, modified=pub, jsonld=jsonld)


def build_lecturas(data):
    lecturas = [l for l in data.get("lecturas", []) if l.get("id") is not None and l.get("titulo")]
    secs = {}
    for s in data.get("secciones", []):
        if isinstance(s, dict) and s.get("id"):
            secs[s["id"]] = s
    for k, v in SECCIONES_LECTURAS_FALLBACK.items():
        secs.setdefault(k, v)
    lecturas.sort(key=lambda l: int(l["id"]), reverse=True)
    por_sec = {}
    for l in lecturas:
        por_sec.setdefault(l.get("seccion") or "otros", []).append(l)

    urls = []
    for sec, lista in por_sec.items():
        for idx, l in enumerate(lista):
            related = lista[idx + 1: idx + 1 + RELATED_N]
            if len(related) < RELATED_N:
                related += lista[max(0, idx - (RELATED_N - len(related))): idx]
            write(lectura_path(l).lstrip("/"), render_lectura(l, secs, related))
            urls.append((lectura_path(l), iso_date(l.get("fecha")) or iso_date(l.get("added_date")), "monthly", "0.5"))

        info = secs.get(sec, {"nombre": sec, "color": "#131A26", "sub": ""})
        pages = paginate(lista, LECT_PAGE_SIZE)
        for n, chunk in enumerate(pages, start=1):
            path = lect_listing_path(sec, n)
            title = f'Lecturas de {info.get("nombre", sec)}' + (f" (página {n})" if n > 1 else "")
            desc = recorte(f'{info.get("sub", "")}. {len(lista)} lecturas seleccionadas y resumidas en español.', 158)
            body = (
                '<main class="lp-page">'
                + crumbs([("La Lupa", "/"), ("Lecturas", "/lecturas/"), (info.get("nombre", sec), None)])
                + f'<header class="lp-lhead" style="--c:{info.get("color", "#131A26")}"><p class="lp-kicker">Lecturas</p><h1>{esc(info.get("nombre", sec))}</h1>'
                + f'<p class="lp-sub">{esc(info.get("sub", ""))} {len(lista)} lecturas seleccionadas por interés y resumidas en español.</p></header>'
                + '<ul class="lp-cards lp-cards-list">' + "".join(lectura_card(l, secs) for l in chunk) + "</ul>"
                + pager_html(lambda k, s=sec: lect_listing_path(s, k), len(pages), n)
                + "</main>"
            )
            write(path.lstrip("/"), page(title, desc, path, body, og_type="website", noindex=(n > 1)))
            if n == 1:
                urls.append((path, iso_date(lista[0].get("fecha")) if lista else None, "daily", "0.7"))

    blocks = []
    for sec, lista in por_sec.items():
        info = secs.get(sec, {"nombre": sec, "color": "#131A26", "sub": ""})
        blocks.append(
            f'<section class="lp-secblock" style="--c:{info.get("color", "#131A26")}"><h2><a href="{lect_listing_path(sec)}">{esc(info.get("nombre", sec))}</a> <span>{len(lista)}</span></h2>'
            f'<p>{esc(info.get("sub", ""))}</p><ul class="lp-cards">' + "".join(lectura_card(l, secs) for l in lista[:6]) + "</ul></section>"
        )
    body = (
        '<main class="lp-page">' + crumbs([("La Lupa", "/"), ("Lecturas", None)])
        + '<header class="lp-lhead"><h1>Lecturas: emprendimiento, ciencia y tecnología</h1>'
        + f'<p class="lp-sub">{len(lecturas)} artículos seleccionados por interés y resumidos en español, cada uno con enlace a su fuente original. También disponibles por <a href="/feed-lecturas.xml">RSS</a>.</p></header>'
        + "".join(blocks) + "</main>"
    )
    write("lecturas/index.html", page("Lecturas", f"{len(lecturas)} lecturas de emprendimiento, ciencia y tecnología, resumidas en español con enlace a la fuente.", "/lecturas/", body, og_type="website"))
    urls.append(("/lecturas/", iso_date(lecturas[0].get("fecha")) if lecturas else None, "daily", "0.8"))
    return urls, len(lecturas)


# ----------------------------------------------------------------- opinión
ARTICLE_RE = re.compile(r'<article class="tema-card[^"]*" id="(tema-[a-z0-9-]+)"([^>]*)>(.*?)</article>', re.S)


def _strip(block):
    block = re.sub(r'<button class="lang-toggle".*?</button>', "", block, flags=re.S)
    block = re.sub(r'<div class="share-header">.*?</div>', "", block, flags=re.S)
    block = re.sub(r'<div class="share-buttons"[^>]*>.*?</div>', "", block, flags=re.S)
    block = re.sub(r'<div class="lang-content en">', '<hr class="lp-lang-sep"><p class="lp-lang-label">English version</p><div class="lang-content en active">', block)
    block = re.sub(r"\son[a-z]+=\"[^\"]*\"", "", block)  # sin handlers inline
    return block


def _text(fragment):
    t = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def build_opinion():
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        src = f.read()
    arts = []
    for m in ARTICLE_RE.finditer(src):
        aid, attrs, inner = m.group(1), m.group(2), m.group(3)
        if 'data-default-status="draft"' in attrs:
            continue
        h3 = re.search(r"<h3>(.*?)</h3>", inner, re.S)
        title = _text(h3.group(1)) if h3 else aid
        preg = re.search(r'<p class="tema-pregunta">(.*?)</p>', inner, re.S)
        desc = recorte(_text(preg.group(1)) if preg else _text(inner), 158)
        slug = aid[len("tema-"):]
        inner2 = _strip(inner)
        inner2 = inner2.replace("<h3>", "<h1>", 1).replace("</h3>", "</h1>", 1) if h3 else inner2
        arts.append({"id": aid, "slug": slug, "title": title, "desc": desc, "inner": inner2})

    urls = []
    for a in arts:
        path = f"/opinion/{a['slug']}.html"
        body = (
            '<main class="lp-page lp-page-opinion">' + crumbs([("La Lupa", "/"), ("Opinión", "/opinion/"), (a["title"], None)])
            + '<section class="temas-section"><div class="temas-grid">'
            + f'<article class="tema-card tema-card-wide lp-op" id="{a["id"]}">' + a["inner"] + "</article>"
            + "</div></section>"
            + f'<p class="lp-cta"><a class="lp-btn" href="/index.html#{a["id"]}">Ver este artículo en La Lupa (comentarios)</a></p>'
            + "</main>"
        )
        jsonld = {
            "@context": "https://schema.org", "@type": "OpinionNewsArticle",
            "headline": a["title"][:110], "description": a["desc"], "mainEntityOfPage": SITE + path,
            "inLanguage": "es", "author": {"@type": "Person", "name": "Alexander O.M."},
            "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE},
        }
        write(path.lstrip("/"), page(a["title"], a["desc"], path, body, jsonld=jsonld, extra_css=True))
        urls.append((path, None, "monthly", "0.7"))

    items = "".join(
        f'<li class="lp-card"><a class="lp-card-t" href="/opinion/{a["slug"]}.html">{esc(a["title"])}</a><p class="lp-card-d">{esc(a["desc"])}</p></li>'
        for a in arts
    )
    body = (
        '<main class="lp-page">' + crumbs([("La Lupa", "/"), ("Opinión", None)])
        + '<header class="lp-lhead" style="--c:#5B4B8A"><h1>Opinión</h1>'
        + f'<p class="lp-sub">{len(arts)} artículos de análisis sobre economía, instituciones y política, en español e inglés. Firmados por su autor; no representan a ninguna organización.</p></header>'
        + '<ul class="lp-cards lp-cards-list">' + items + "</ul></main>"
    )
    write("opinion/index.html", page("Opinión", "Artículos de análisis sobre economía, instituciones y política en Colombia, en español e inglés.", "/opinion/", body, og_type="website"))
    urls.append(("/opinion/", None, "weekly", "0.8"))
    return urls, len(arts)


# ----------------------------------------------------------------- sitemap
def build_sitemap(urls):
    newest = max((u[1] for u in urls if u[1]), default=None)
    static = [
        ("/", newest, "daily", "1.0"),
        ("/sugerir.html", None, "monthly", "0.5"),
        ("/acerca.html", None, "monthly", "0.5"),
        ("/contacto.html", None, "monthly", "0.4"),
        ("/privacidad.html", None, "yearly", "0.3"),
    ]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    seen = set()
    for path, lastmod, freq, prio in static + urls:
        if path in seen:
            continue
        seen.add(path)
        out.append("  <url>")
        out.append(f"    <loc>{esc(SITE + path)}</loc>")
        if lastmod:
            out.append(f"    <lastmod>{lastmod}</lastmod>")
        out.append(f"    <changefreq>{freq}</changefreq>")
        out.append(f"    <priority>{prio}</priority>")
        out.append("  </url>")
    out.append("</urlset>")
    write("sitemap.xml", "\n".join(out) + "\n")
    return len(seen)


# ----------------------------------------------------------------- main
def main():
    for d in OUT_DIRS:
        full = os.path.join(ROOT, d)
        if os.path.isdir(full):
            shutil.rmtree(full)
        os.makedirs(full, exist_ok=True)

    urls = []
    u, n_casos = build_casos(load_json("data.json"))
    urls += u
    u, n_lect = build_lecturas(load_json("lecturas.json"))
    urls += u
    u, n_op = build_opinion()
    urls += u
    n_urls = build_sitemap(urls)
    print(f"build_pages: {n_casos} casos, {n_lect} lecturas, {n_op} artículos de opinión, sitemap con {n_urls} URLs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
