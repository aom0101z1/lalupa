#!/usr/bin/env python3
"""
La Lupa - Actualizador de LECTURAS (Emprendimiento, Ciencia, Tecnologia).

Segundo bot, separado de news_updater.py (que maneja los CASOS de data.json).
Lee feeds en ingles y espanol, Claude escoge solo lo que vale la pena leer y lo
resume en espanol, y el resultado se guarda en lecturas.json (las mas nuevas primero).

Reglas (ver harness/domains/lecturas-nuevas-secciones.md):
- Se analizan TODOS los articulos nuevos por lotes (nunca "los primeros N").
- Structured outputs (output_config + OUTPUT_SCHEMA): JSON garantizado.
- Sin creditos o modelo retirado -> SystemExit(1) (workflow en rojo).
- Umbral de interes alto: pocas lecturas por corrida, pero buenas.
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta

import anthropic
import feedparser
import requests
from dateutil import parser as date_parser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from news_updater import BLOCKED_DOMAINS, BLOCKED_SOURCES, text_similarity  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LECTURAS_FILE = os.path.join(ROOT, "lecturas.json")

MODEL = "claude-sonnet-5"
SECCIONES = ["emprendimiento", "ciencia", "tecnologia"]
MIN_INTERES = 7            # solo entra lo que Claude puntue >= 7/10
MAX_POR_CORRIDA = 12       # pocas lecturas, buenas
MAX_POR_SECCION = 5
BATCH_SIZE = 40
MAX_ARTICLES_PER_RUN = 200
HOURS_WINDOW = 48
DEDUP_DAYS = 14
PER_FEED = 25

# Feeds verificados el 2026-10-18 (harness/domains/lecturas-nuevas-secciones.md).
# "hint" orienta a Claude sobre la seccion probable; la decision final es suya.
FEEDS = [
    # --- Ciencia ---
    {"name": "Phys.org", "url": "https://phys.org/rss-feed/", "lang": "en", "hint": "ciencia"},
    {"name": "ScienceDaily", "url": "https://www.sciencedaily.com/rss/top/science.xml", "lang": "en", "hint": "ciencia"},
    {"name": "Quanta Magazine", "url": "https://api.quantamagazine.org/feed/", "lang": "en", "hint": "ciencia"},
    {"name": "NASA", "url": "https://www.nasa.gov/feed/", "lang": "en", "hint": "ciencia"},
    # --- Tecnologia ---
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "lang": "en", "hint": "tecnologia"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "lang": "en", "hint": "tecnologia"},
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage?points=150", "lang": "en", "hint": "tecnologia"},
    {"name": "Xataka", "url": "https://www.xataka.com/feedburner.xml", "lang": "es", "hint": "tecnologia"},
    {"name": "Hipertextual", "url": "https://hipertextual.com/feed", "lang": "es", "hint": "tecnologia"},
    # --- Emprendimiento y negocios ---
    {"name": "La Republica", "url": "https://www.larepublica.co/rss", "lang": "es", "hint": "emprendimiento"},
    {"name": "Valora Analitik", "url": "https://www.valoraanalitik.com/feed/", "lang": "es", "hint": "emprendimiento"},
    {"name": "Bloomberg Linea", "url": "https://www.bloomberglinea.com/arc/outboundfeeds/rss/?outputType=xml", "lang": "es", "hint": "emprendimiento"},
    {"name": "Contxto", "url": "https://contxto.com/es/feed/", "lang": "es", "hint": "emprendimiento"},
]

# Busquedas en Google News para lo que los feeds no cubren (startups y ciencia en Colombia)
GOOGLE_NEWS_QUERIES = [
    "startup colombiana ronda inversión OR levantó millones",
    "emprendimiento Colombia empresa innovación caso de éxito",
    "universidad colombiana investigación descubrimiento OR patente",
    "startup latinoamérica ronda serie A OR serie B",
]

# Descripcion de las secciones (misma copia en lecturas.json -> secciones)
SECCIONES_DESC = {
    "emprendimiento": "Negocios, startups, rondas de inversion, mercados, historias de empresas, como funciona una industria, dinero y finanzas practicas",
    "ciencia": "Descubrimientos, estudios con datos, salud y medicina, espacio, biologia, fisica, clima medido con evidencia",
    "tecnologia": "Inteligencia artificial, software y herramientas nuevas, ingenieria, energia, hardware, seguridad informatica, lo que cambia como trabajamos",
}


# ---------------------------------------------------------------- utilidades
def url_hash(url: str) -> str:
    return hashlib.md5((url or "").strip().lower().encode("utf-8")).hexdigest()


def clean(text: str, n: int = 400) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:n]


def parse_date(entry):
    for key in ("published", "updated"):
        if entry.get(key):
            try:
                return date_parser.parse(entry[key]).replace(tzinfo=None)
            except Exception:
                pass
    return None


def is_blocked(article: dict) -> bool:
    name = (article.get("source") or "").strip().lower()
    url = (article.get("url") or "").lower()
    return name in BLOCKED_SOURCES or any(d in url for d in BLOCKED_DOMAINS)


# ---------------------------------------------------------------- datos
def load_lecturas() -> dict:
    with open(LECTURAS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_lecturas(data: dict):
    data.setdefault("estadisticas", {})["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
    with open(LECTURAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ---------------------------------------------------------------- fetch
def fetch_feeds() -> list:
    articles = []
    cutoff = datetime.now() - timedelta(hours=HOURS_WINDOW)
    for feed_info in FEEDS:
        try:
            print(f"  Fetching: {feed_info['name']}...")
            r = requests.get(feed_info["url"], timeout=20, headers={"User-Agent": "Mozilla/5.0 (compatible; LaLupaBot/1.0)"})
            feed = feedparser.parse(r.content)
            n = 0
            for entry in feed.entries[:PER_FEED]:
                pub = parse_date(entry)
                if pub is None or pub < cutoff:
                    continue
                link = entry.get("link", "")
                if not link:
                    continue
                articles.append({
                    "title": clean(entry.get("title", ""), 200),
                    "url": link,
                    "summary": clean(entry.get("summary", entry.get("description", ""))),
                    "source": feed_info["name"],
                    "lang": feed_info["lang"],
                    "hint": feed_info["hint"],
                    "date": pub.strftime("%Y-%m-%d"),
                })
                n += 1
            print(f"     {n} articulos recientes")
        except Exception as e:
            print(f"  Error fetching {feed_info['name']}: {e}")
    return articles


def fetch_google_news() -> list:
    from urllib.parse import quote
    articles = []
    cutoff = datetime.now() - timedelta(hours=HOURS_WINDOW)
    for query in GOOGLE_NEWS_QUERIES:
        try:
            url = f"https://news.google.com/rss/search?q={quote(query)}&hl=es-419&gl=CO&ceid=CO:es-419"
            print(f"  Google News: {query}...")
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                source_name = "Google News"
                if hasattr(entry, "source") and hasattr(entry.source, "title"):
                    source_name = entry.source.title
                title = entry.get("title", "")
                if title.endswith(f" - {source_name}"):
                    title = title[:-(len(source_name) + 3)]
                pub = parse_date(entry)
                if pub is None or pub < cutoff:
                    continue
                articles.append({
                    "title": clean(title, 200),
                    "url": entry.get("link", ""),
                    "summary": clean(entry.get("summary", "")),
                    "source": source_name,
                    "lang": "es",
                    "hint": "emprendimiento",
                    "date": pub.strftime("%Y-%m-%d"),
                })
        except Exception as e:
            print(f"  Error fetching Google News for '{query}': {e}")
    return articles


# ---------------------------------------------------------------- Claude
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "lecturas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "articulo_numero": {"type": "integer"},
                    "seccion": {"type": "string", "enum": SECCIONES},
                    "titulo": {"type": "string"},
                    "resumen": {"type": "string"},
                    "por_que_leerlo": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "tiempo_lectura_min": {"type": "integer"},
                    "interes_score": {"type": "integer"},
                    "idioma_original": {"type": "string", "enum": ["es", "en"]},
                },
                "required": ["articulo_numero", "seccion", "titulo", "resumen", "por_que_leerlo",
                             "tags", "tiempo_lectura_min", "interes_score", "idioma_original"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["lecturas"],
    "additionalProperties": False,
}


def build_prompt(articles_text: str, recientes_text: str) -> str:
    return f"""Eres el editor de "La Lupa", un periodico digital colombiano cuyo lema es "Lo que vale la pena leer".
Tu trabajo: de una lista de articulos, escoger SOLO los que de verdad valen la pena y resumirlos en espanol.

EL LECTOR: colombiano, emprendedor, curioso y pragmatico. Quiere entender como funcionan las cosas, enterarse de lo nuevo que importa y encontrar ideas que pueda usar. Prefiere hechos, cifras y evidencia. Desconfia del hype, del clickbait y de las polemicas de redes. NO le interesan: deportes, farandula, politica partidista (eso va en otra seccion), horoscopos, notas de bolsa del dia, promociones ni cambios de precio menores.

SECCIONES:
- emprendimiento: {SECCIONES_DESC['emprendimiento']}
- ciencia: {SECCIONES_DESC['ciencia']}
- tecnologia: {SECCIONES_DESC['tecnologia']}

COMO PUNTUAR "interes_score" (1-10):
- Novedad: es algo que no se sabia o acaba de pasar.
- Sorpresa: cambia lo que uno creia o explica algo que no se entendia.
- Utilidad: el lector puede usarlo (una herramienta, un dato para decidir, una leccion de negocio).
- Evidencia: hay cifras, un estudio, una fuente concreta, no solo opinion.
- Suma puntos si es de Colombia o America Latina, o si le sirve a alguien que emprende.
- Resta puntos: opiniones y columnas, listas ("las 10 mejores"), rumores, anuncios corporativos sin sustancia, notas de producto menores, politica, duplicados de un tema ya cubierto.
Solo devuelve articulos con interes_score >= {MIN_INTERES}. Es normal que de un lote salgan 0, 1 o 2. Si varios tratan el mismo tema, deja solo el mejor.

LECTURAS YA PUBLICADAS (ultimos {DEDUP_DAYS} dias) - NO REPETIR EL TEMA:
{recientes_text}

PARA CADA LECTURA ESCOGIDA:
- "titulo": en espanol, informativo y concreto, sin clickbait, maximo 90 caracteres. Si el original esta en ingles, traduce y reescribe.
- "resumen": 2 o 3 frases en espanol con los hechos y cifras clave. Nada de "en este articulo se habla de".
- "por_que_leerlo": UNA frase que diga que gana el lector al leerlo.
- "tags": 2 a 4 palabras clave en espanol, minusculas.
- "tiempo_lectura_min": estimado de 2 a 12 minutos segun el tipo de articulo.
- "idioma_original": "es" o "en".
- Nunca inventes datos que no esten en el titulo o el resumen del articulo.

ARTICULOS A EVALUAR:
{articles_text}

Responde SOLO con el JSON."""


def analyze_batch(client: anthropic.Anthropic, batch: list, recientes_text: str) -> list:
    articles_text = "\n\n".join([
        f"ARTICULO {i+1}:\nTitulo: {a['title']}\nResumen: {a['summary']}\nFuente: {a['source']} (idioma {a['lang']}, seccion probable {a['hint']})\nFecha: {a['date']}\nURL: {a['url']}"
        for i, a in enumerate(batch)
    ])
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            messages=[{"role": "user", "content": build_prompt(articles_text, recientes_text)}],
            output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        )
        text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            print(f"  [WARN] Claude no devolvio JSON: {text[:200]!r}")
            return []
        result = json.loads(m.group())
        out = []
        for lec in result.get("lecturas", []):
            idx = lec.get("articulo_numero", 0) - 1
            if 0 <= idx < len(batch):
                lec["_article"] = batch[idx]
                out.append(lec)
        return out
    except Exception as e:
        print(f"  Error analyzing with Claude: {e}")
        err = str(e).lower()
        if "credit balance" in err:
            print("\nERROR FATAL: La API key de Anthropic no tiene creditos (console.anthropic.com -> Plans & Billing)")
            raise SystemExit(1)
        if "not_found_error" in err and "model" in err:
            print("\nERROR FATAL: El modelo de Claude ya no existe en la API. Actualizar MODEL en scripts/lecturas_updater.py")
            raise SystemExit(1)
        return []


# ---------------------------------------------------------------- main
def main():
    print("=" * 60)
    print("LA LUPA - Actualizador de Lecturas (emprendimiento, ciencia, tecnologia)")
    print("=" * 60)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not configured")
        return
    client = anthropic.Anthropic(api_key=api_key)

    data = load_lecturas()
    existing = data.get("lecturas", [])
    existing_hashes = {url_hash(l.get("fuente", {}).get("url", "")) for l in existing}
    cutoff = (datetime.now() - timedelta(days=DEDUP_DAYS)).strftime("%Y-%m-%d")
    recientes = [l for l in existing if (l.get("fecha") or "") >= cutoff]
    recientes_text = "\n".join(f"- [{l['seccion']}] {l['titulo']}" for l in recientes[:120]) or "(ninguna)"
    print(f"   Lecturas existentes: {len(existing)} (recientes: {len(recientes)})\n")

    print("Buscando articulos...")
    articles = fetch_feeds() + fetch_google_news()
    before = len(articles)
    articles = [a for a in articles if not is_blocked(a)]
    if before != len(articles):
        print(f"   -> {before - len(articles)} de medios bloqueados descartados")

    # Dedup por URL (contra lo publicado y dentro de la corrida)
    seen, nuevos = set(existing_hashes), []
    for a in articles:
        h = url_hash(a["url"])
        if h in seen:
            continue
        seen.add(h)
        nuevos.append(a)
    print(f"\n   Total articulos: {before} | nuevos: {len(nuevos)}")
    if not nuevos:
        print("No hay articulos nuevos")
        return

    nuevos = nuevos[:MAX_ARTICLES_PER_RUN]
    batches = [nuevos[i:i + BATCH_SIZE] for i in range(0, len(nuevos), BATCH_SIZE)]
    print(f"\nAnalizando con Claude: {len(nuevos)} articulos en {len(batches)} lotes de {BATCH_SIZE}...")
    candidatas = []
    for i, batch in enumerate(batches, 1):
        print(f"  Lote {i}/{len(batches)} ({len(batch)} articulos)")
        res = analyze_batch(client, batch, recientes_text)
        print(f"     -> {len(res)} lecturas propuestas")
        candidatas.extend(res)

    # Filtro de calidad, dedup por titulo y topes por seccion/corrida
    candidatas = [c for c in candidatas if c.get("interes_score", 0) >= MIN_INTERES and c.get("seccion") in SECCIONES]
    candidatas.sort(key=lambda c: c.get("interes_score", 0), reverse=True)
    aceptadas, por_seccion = [], {s: 0 for s in SECCIONES}
    for c in candidatas:
        if len(aceptadas) >= MAX_POR_CORRIDA:
            break
        if por_seccion[c["seccion"]] >= MAX_POR_SECCION:
            continue
        dup = any(text_similarity(c["titulo"], x["titulo"]) >= 0.6 for x in aceptadas) or \
              any(text_similarity(c["titulo"], x.get("titulo", "")) >= 0.6 for x in recientes)
        if dup:
            print(f"   [SKIP] Tema repetido: {c['titulo'][:60]}")
            continue
        aceptadas.append(c)
        por_seccion[c["seccion"]] += 1

    if not aceptadas:
        print("\nRESULTADO: ninguna lectura supero el umbral")
        return

    next_id = max([l.get("id", 0) for l in existing], default=0) + 1
    entries = []
    for c in aceptadas:
        a = c["_article"]
        entries.append({
            "id": next_id,
            "titulo": c["titulo"].strip(),
            "resumen": c["resumen"].strip(),
            "por_que_leerlo": c["por_que_leerlo"].strip(),
            "seccion": c["seccion"],
            "tags": [t.strip().lower() for t in c.get("tags", [])][:4],
            "fuente": {"nombre": a["source"], "url": a["url"]},
            "idioma_original": c.get("idioma_original", a["lang"]),
            "tiempo_lectura_min": max(1, min(30, int(c.get("tiempo_lectura_min", 4)))),
            "interes_score": int(c["interes_score"]),
            "fecha": a["date"],
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "auto_generated": True,
        })
        print(f"   [ADD] [{c['seccion']}] ({c['interes_score']}/10) [{a['source']}] {c['titulo'][:60]}")
        next_id += 1

    data["lecturas"] = entries + existing  # las mas nuevas primero
    save_lecturas(data)
    print(f"\nRESULTADO: {len(entries)} lecturas agregadas a lecturas.json")
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
