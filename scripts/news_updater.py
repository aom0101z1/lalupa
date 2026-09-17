#!/usr/bin/env python3
"""
La Lupa - Automated News Updater
Fetches Colombian news about corruption, nepotism, abuse of power, etc.
Uses Claude AI to categorize and verify relevance.
"""

import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, List, Set
from difflib import SequenceMatcher
import feedparser
import requests
from dateutil import parser as date_parser
import anthropic


# =============================================================================
# DEDUPLICATION FUNCTIONS
# =============================================================================

def normalize_text(text: str) -> str:
    """Normalize text for comparison by removing accents, punctuation, and extra spaces."""
    if not text:
        return ""
    text = text.lower()
    # Remove accents
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
        'ñ': 'n', 'ç': 'c'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove punctuation and extra spaces
    text = re.sub(r'[^\w\s]', '', text)
    text = ' '.join(text.split())
    return text


def text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts (0.0 to 1.0)."""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def extract_key_terms(text: str) -> Set[str]:
    """Extract key terms from text for quick comparison."""
    norm = normalize_text(text)
    words = norm.split()
    # Filter out common words and keep significant terms (3+ chars)
    stopwords = {'el', 'la', 'los', 'las', 'de', 'del', 'en', 'por', 'para', 'con', 'sin', 'que', 'una', 'uno', 'unos', 'unas', 'al', 'es', 'son', 'fue', 'han', 'su', 'sus'}
    return {w for w in words if len(w) >= 3 and w not in stopwords}


def is_duplicate_case(new_title: str, new_url: str, new_entity: str,
                      existing_cases: List[dict], days_lookback: int = 14,
                      similarity_threshold: float = 0.65) -> bool:
    """
    Check if a case is a duplicate of an existing one.

    Checks:
    1. Exact URL match
    2. Title similarity above threshold
    3. Key terms overlap with same entity
    """
    new_title_norm = normalize_text(new_title)
    new_key_terms = extract_key_terms(new_title)
    new_entity_norm = normalize_text(new_entity) if new_entity else ""

    cutoff_date = datetime.now() - timedelta(days=days_lookback)

    for case in existing_cases:
        # Check date range (only compare with recent cases)
        case_date_str = case.get("fecha", "")
        try:
            case_date = datetime.strptime(case_date_str, "%Y-%m-%d")
            if case_date < cutoff_date:
                continue
        except:
            pass

        # Check 1: Exact URL match
        for fuente in case.get("fuentes", []):
            if fuente.get("url", "") == new_url:
                return True

        # Check 2: Title similarity
        existing_title = case.get("titulo", "")
        if text_similarity(new_title, existing_title) >= similarity_threshold:
            return True

        # Check 3: Key terms overlap with same entity
        existing_key_terms = extract_key_terms(existing_title)
        existing_entity_norm = normalize_text(case.get("entidad", ""))

        # If same entity and significant key terms overlap
        # (umbral subido de 3 a 5 términos: con 3, entidades genéricas como "Contraloría"
        # marcaban como duplicados hechos distintos - detectado 17-sep-2026)
        if new_entity_norm and existing_entity_norm:
            if text_similarity(new_entity_norm, existing_entity_norm) >= 0.7:
                term_overlap = len(new_key_terms & existing_key_terms)
                if term_overlap >= 5:
                    return True

    return False


# =============================================================================
# CONFIGURATION
# =============================================================================

# Configuration
CATEGORIES = {
    "mentiras": {
        "keywords": ["mintió", "falso", "mentira", "engaño", "desinformación", "fake", "desmentido"],
        "description": "Afirmaciones falsas comprobadas"
    },
    "corrupcion": {
        "keywords": ["corrupción", "soborno", "malversación", "peculado", "coima", "desfalco", "robo"],
        "description": "Casos de corrupción documentados"
    },
    "nepotismo": {
        "keywords": ["nepotismo", "familiar", "allegado", "cuota política", "nombramiento", "palanca"],
        "description": "Nombramientos a familiares o allegados"
    },
    "contratos": {
        "keywords": ["contrato irregular", "sobrecosto", "licitación", "adjudicación directa", "contrato"],
        "description": "Contratos con irregularidades"
    },
    "conflicto-interes": {
        "keywords": ["conflicto de interés", "beneficio propio", "incompatibilidad", "inhabilidad"],
        "description": "Decisiones con beneficio personal"
    },
    "recursos-publicos": {
        "keywords": ["recursos públicos", "dinero público", "presupuesto", "desvío de fondos", "malgasto"],
        "description": "Uso indebido de dineros públicos"
    },
    "diplomaticos": {
        "keywords": ["embajador", "cónsul", "diplomático", "embajada", "consulado", "cancillería"],
        "description": "Irregularidades en embajadas y consulados"
    },
    "sanciones": {
        "keywords": ["sanción", "OFAC", "lista Clinton", "embargo", "sancionado", "Treasury"],
        "description": "Sanciones de organismos internacionales"
    },
    "abuso-poder": {
        "keywords": ["abuso de poder", "extralimitación", "autoritario", "amenaza", "persecución"],
        "description": "Extralimitación de funciones y amenazas institucionales"
    }
}

# Categorías de la sección "Gestión Nuevo Gobierno" (gobierno De la Espriella, 2026-2030)
GESTION_CATEGORIES = [
    "gestion-emergencia",  # Manejo del terremoto del 10 ago 2026 y otras emergencias
    "seguridad",           # Seguridad y lucha contra grupos armados
    "economia",            # Medidas económicas y fiscales
    "transparencia",       # Transparencia, austeridad, anticorrupción
    "gabinete",            # Conformación del equipo de gobierno
    "empalme",             # Hallazgos del empalme con el gobierno saliente
    "internacional",       # Relaciones exteriores
    "obras",               # Infraestructura, reconstrucción, agenda territorial
    "opinion-publica",     # Encuestas y mediciones de aprobación
]

# Categorías de la sección "Lupa al Terremoto" (terremoto del 10 ago 2026: manejo de dineros y gestión)
TERREMOTO_CATEGORIES = [
    "dineros",           # Recursos asignados, Fondo Milagro, donaciones, créditos, ejecución
    "denuncias",         # Denuncias de corrupción, desvíos, sobrecostos, ayudas que no llegan
    "contratacion",      # Contratos de emergencia y reconstrucción
    "gestion-local",     # Alcaldías y gobernaciones
    "gestion-nacional",  # Presidencia, UNGRD, ministerios, Fondo Milagro
    "avances",           # Resultados verificables: viviendas, subsidios, vías
    "damnificados",      # Albergues, censos, ayudas humanitarias
    "control",           # Contraloría, Procuraduría, Fiscalía, veedurías
]
TERREMOTO_REGIONS = ["pereira", "cali", "choco", "nacional", "otras"]

# Cuántos artículos se envían a Claude por llamada y cuántos como máximo por corrida
BATCH_SIZE = 30
MAX_ARTICLES_PER_RUN = 150

# Dominios con paywall: si la misma noticia existe en otro medio, se prefiere el otro medio
PAYWALLED_DOMAINS = ["eltiempo.com"]

# Colombian news RSS feeds (verificados agosto 2026; varios feeds antiguos ya no existen)
RSS_FEEDS = [
    {"name": "El Tiempo", "url": "https://www.eltiempo.com/rss/politica.xml"},
    {"name": "El Tiempo", "url": "https://www.eltiempo.com/rss/justicia.xml"},
    {"name": "La Silla Vacia", "url": "https://www.lasillavacia.com/feed/"},
    {"name": "El Colombiano", "url": "https://www.elcolombiano.com/rss/Colombia.xml"},
    {"name": "Colombiacheck", "url": "https://colombiacheck.com/rss.xml"},
    {"name": "Infobae", "url": "https://www.infobae.com/arc/outboundfeeds/rss/", "link_filter": "/colombia/"},
    {"name": "France 24", "url": "https://www.france24.com/es/am%C3%A9rica-latina/rss", "keyword_filter": "colombia"},
    {"name": "DW", "url": "https://rss.dw.com/rdf/rss-sp-all", "keyword_filter": "colombia"},
]

# Búsquedas en Google News RSS: agrega medios cuyos feeds directos están rotos
# (Semana, Blu Radio, Caracol Radio, RCN, La FM, W Radio, El Espectador, etc.)
GOOGLE_NEWS_QUERIES = [
    # --- Archivo: corrupción del gobierno Petro y seguimiento judicial ---
    "corrupción Colombia investigación",
    "Petro juicio OR investigación Fiscalía",
    "UNGRD OR pasaportes OR \"Nicolás Petro\" proceso",
    "UNGRD Olmedo López OR Sneyder Pinilla OR \"Carlos Ramón González\"",
    "Ecopetrol Ricardo Roa investigación OR contratos OR Fiscalía",
    "aviones Gripen Colombia contrato OR investigación OR sobrecosto",
    "\"Verónica Alcocer\" viajes OR investigación OR gastos",
    "\"títulos falsos\" OR \"título falso\" funcionario Colombia",
    "\"Juliana Guerrero\" OR \"Laura Sarabia\" OR \"Armando Benedetti\" investigación",
    "\"Paz Total\" beneficios OR gestores de paz OR disidencias investigación",
    "nombramientos gobierno Petro contratos prestación de servicios denuncia",
    "empalme gobierno Colombia hallazgos denuncias",
    "Contraloría OR Procuraduría hallazgo gobierno Petro",
    # --- Nuevo gobierno: resultados y medidas ---
    "gobierno \"De la Espriella\" medidas",
    "capturas OR capturado cabecilla Colombia Policía Ejército",
    "operativo Ejército Colombia disidencias OR ELN OR \"Clan del Golfo\" abatido OR neutralizado",
    "Ministerio de Defensa balance capturas incautaciones",
    "gobierno De la Espriella resultados OR balance OR cifras",
    # --- Lupa al terremoto: dineros y gestión ---
    "terremoto Colombia reconstrucción gobierno",
    "\"Fondo Milagro\" terremoto recursos OR ejecución OR contratos",
    "terremoto Pereira alcaldía OR gobernación Risaralda ayudas OR recursos OR denuncia",
    "terremoto Pereira damnificados subsidios OR albergues OR contratos",
    "terremoto Cali reconstrucción recursos OR denuncia OR contratos",
    "terremoto Chocó Quibdó reconstrucción recursos OR denuncia",
    "terremoto Contraloría OR Procuraduría OR Fiscalía recursos damnificados",
    "terremoto UNGRD contratos OR ayudas OR denuncia corrupción",
]

# Keywords to search for (related to government corruption and scandals)
SEARCH_KEYWORDS = [
    "Petro", "gobierno Petro", "corrupción Colombia", "escándalo político",
    "UNGRD", "nepotismo", "contrato irregular", "conflicto interés",
    "abuso poder", "ministro investigado", "embajador polémica",
    "Fiscalía investiga", "Procuraduría", "Contraloría",
    "sanción internacional", "recursos públicos",
    "De la Espriella", "terremoto", "reconstrucción", "empalme"
]

# Palabras clave para PRIORIZAR artículos (los que las contienen se analizan primero).
# Los feeds RSS generales traen mucha noticia irrelevante; antes solo se analizaban
# los primeros 30 artículos y las noticias relevantes nunca llegaban a Claude.
PRIORITY_KEYWORDS = [
    "corrupci", "petro", "ungrd", "ecopetrol", "roa", "gripen", "alcocer", "sarabia", "benedetti",
    "nicolás petro", "nicolas petro", "pasaporte", "fiscal", "procuradur", "contralor", "imputa",
    "captura", "capturad", "abatid", "neutraliza", "cabecilla", "extradi", "incauta", "eln",
    "disidencia", "clan del golfo", "paz total", "gestor de paz", "título", "titulos falsos",
    "nepotismo", "contrato", "contrataci", "prestación de servicios", "nombramiento",
    "terremoto", "sismo", "damnificad", "reconstrucci", "fondo milagro", "subsidio", "albergue",
    "pereira", "risaralda", "cali", "valle del cauca", "chocó", "choco", "quibdó", "quibdo",
    "de la espriella", "gobierno", "ministerio", "ministra", "ministro", "decreto", "denuncia",
    "sobrecosto", "irregular", "desv", "empalme", "hallazgo", "veedur", "transparencia",
]


def priority_score(article: dict) -> int:
    """Puntaje simple por palabras clave para ordenar los artículos antes de analizarlos."""
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    return sum(1 for kw in PRIORITY_KEYWORDS if kw in text)


def load_existing_data():
    """Load existing cases from data.json"""
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"categorias": [], "casos": []}


def save_data(data):
    """Save updated data to data.json (y actualizar la fecha de última actualización)"""
    stats = data.setdefault("estadisticas", {})
    stats["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
    stats["total_casos"] = len(data.get("casos", []))
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_case_hash(title: str, url: str) -> str:
    """Generate a unique hash for a case to detect duplicates"""
    content = f"{title.lower()}{url}".encode("utf-8")
    return hashlib.md5(content).hexdigest()[:12]


def is_paywalled(url: str) -> bool:
    """Check if a URL belongs to a paywalled outlet"""
    return any(domain in (url or "") for domain in PAYWALLED_DOMAINS)


def fetch_rss_feeds() -> list:
    """Fetch articles from Colombian RSS feeds"""
    articles = []

    for feed_info in RSS_FEEDS:
        try:
            print(f"  Fetching: {feed_info['name']}...")
            feed = feedparser.parse(feed_info["url"])

            for entry in feed.entries[:20]:  # Get latest 20 from each feed
                link = entry.get("link", "")
                title = entry.get("title", "")

                # Feeds generales (Infobae, France24, DW): filtrar solo noticias de Colombia
                if feed_info.get("link_filter") and feed_info["link_filter"] not in link:
                    continue
                if feed_info.get("keyword_filter"):
                    text = (title + " " + entry.get("summary", "")).lower()
                    if feed_info["keyword_filter"] not in text:
                        continue

                # Parse date
                pub_date = None
                if hasattr(entry, 'published'):
                    try:
                        pub_date = date_parser.parse(entry.published)
                    except:
                        pub_date = datetime.now()

                # Only get articles from last 48 hours
                if pub_date and (datetime.now() - pub_date.replace(tzinfo=None)) > timedelta(hours=48):
                    continue

                article = {
                    "title": title,
                    "url": link,
                    "summary": entry.get("summary", entry.get("description", "")),
                    "source": feed_info["name"],
                    "date": pub_date.strftime("%Y-%m-%d") if pub_date else datetime.now().strftime("%Y-%m-%d"),
                    "paywall": is_paywalled(link)
                }

                # Clean HTML from summary
                article["summary"] = re.sub(r'<[^>]+>', '', article["summary"])[:500]

                articles.append(article)

        except Exception as e:
            print(f"  Error fetching {feed_info['name']}: {e}")

    return articles


def fetch_google_news() -> list:
    """Fetch articles from Google News RSS (aggregates outlets whose direct feeds are broken)"""
    from urllib.parse import quote
    articles = []

    for query in GOOGLE_NEWS_QUERIES:
        try:
            url = f"https://news.google.com/rss/search?q={quote(query)}&hl=es-419&gl=CO&ceid=CO:es-419"
            print(f"  Google News: {query}...")
            feed = feedparser.parse(url)

            for entry in feed.entries[:15]:
                # El nombre del medio real viene en la etiqueta <source>
                source_name = "Google News"
                if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                    source_name = entry.source.title

                # El título viene como "Titular - Medio": limpiar el sufijo
                title = entry.get("title", "")
                if title.endswith(f" - {source_name}"):
                    title = title[:-(len(source_name) + 3)]

                pub_date = None
                if hasattr(entry, 'published'):
                    try:
                        pub_date = date_parser.parse(entry.published)
                    except:
                        pub_date = datetime.now()

                # Only get articles from last 48 hours
                if pub_date and (datetime.now() - pub_date.replace(tzinfo=None)) > timedelta(hours=48):
                    continue

                link = entry.get("link", "")
                summary = re.sub(r'<[^>]+>', '', entry.get("summary", ""))[:500]

                articles.append({
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "source": source_name,
                    "date": pub_date.strftime("%Y-%m-%d") if pub_date else datetime.now().strftime("%Y-%m-%d"),
                    "paywall": is_paywalled(link) or is_paywalled(source_name.lower().replace(" ", ""))
                             or source_name.strip().lower() == "el tiempo"
                })

        except Exception as e:
            print(f"  Error fetching Google News for '{query}': {e}")

    return articles


def prefer_free_sources(articles: list) -> list:
    """
    Si la misma noticia aparece en un medio con paywall (ej: El Tiempo) y en otro medio
    sin paywall, conservar solo la versión sin paywall.
    """
    free = [a for a in articles if not a.get("paywall")]
    paywalled = [a for a in articles if a.get("paywall")]

    result = list(free)
    dropped = 0
    for pw_article in paywalled:
        has_free_version = any(
            text_similarity(pw_article["title"], f["title"]) >= 0.55
            for f in free
        )
        if has_free_version:
            dropped += 1
        else:
            result.append(pw_article)

    if dropped:
        print(f"  [Paywall] {dropped} articulo(s) de medios con paywall descartados por existir version libre")
    return result


def fetch_news_api(api_key: str) -> list:
    """Fetch articles from NewsAPI"""
    articles = []

    if not api_key:
        print("  NewsAPI key not configured, skipping...")
        return articles

    base_url = "https://newsapi.org/v2/everything"

    # Search for Colombian political news
    queries = [
        "Petro corrupción",
        "gobierno Colombia escándalo",
        "Colombia nepotismo",
        "ministro Colombia investigación",
        "terremoto Colombia reconstrucción",
        "Colombia captura cabecilla",
    ]

    for query in queries:
        try:
            params = {
                "q": query,
                "language": "es",
                "sortBy": "publishedAt",
                "pageSize": 10,
                "apiKey": api_key
            }

            response = requests.get(base_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                for item in data.get("articles", []):
                    article = {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "summary": item.get("description", ""),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        "date": item.get("publishedAt", "")[:10]
                    }
                    articles.append(article)

        except Exception as e:
            print(f"  Error fetching NewsAPI for '{query}': {e}")

    return articles


def build_prompt(articles_text: str, existing_cases_text: str) -> str:
    """Prompt de análisis: tres secciones (archivo, nuevo-gobierno, terremoto)."""
    return f"""Eres un analista de noticias politicas colombianas para el sitio "La Lupa", un observatorio ciudadano de transparencia.

CONTEXTO: El 7 de agosto de 2026 termino el gobierno de Gustavo Petro (2022-2026) y comenzo el gobierno de Abelardo de la Espriella (2026-2030). El 10 de agosto de 2026 un terremoto de magnitud 7,4 golpeo el occidente del pais (300+ muertos, 15 departamentos). El sitio tiene TRES secciones:

SECCION A - "archivo": Casos de corrupcion e irregularidades del gobierno Petro y su gente, incluyendo el SEGUIMIENTO de procesos judiciales y disciplinarios en curso. Temas prioritarios: UNGRD (Olmedo Lopez, Sneyder Pinilla, sobornos a congresistas), Ecopetrol (Ricardo Roa), nepotismo y contratos a dedo o nombramientos para ganar votos, apoyos o beneficios a guerrillas y grupos armados (Paz Total, gestores de paz), titulos academicos falsos y funcionarios sin titulo, viajes al exterior con despilfarro o corrupcion, compra de aviones Gripen, Veronica Alcocer, Nicolas Petro, pasaportes, Laura Sarabia, Armando Benedetti, hallazgos de Contraloria/Procuraduria/Fiscalia/empalme. Categorias:
- corrupcion: Casos de corrupcion, sobornos, malversacion
- mentiras: Afirmaciones falsas o enganos por parte de funcionarios
- nepotismo: Nombramientos a familiares o allegados sin merito
- contratos: Contratos irregulares, sobrecostos, adjudicaciones sospechosas
- conflicto-interes: Decisiones donde hay beneficio personal
- recursos-publicos: Mal uso de dineros publicos
- diplomaticos: Escandalos en embajadas o consulados
- sanciones: Sanciones internacionales a funcionarios
- abuso-poder: Abuso de autoridad, extralimitacion de funciones

SECCION B - "nuevo-gobierno": Hechos concretos de GESTION y RESULTADOS del gobierno De la Espriella: cifras de capturas, cabecillas abatidos o neutralizados, incautaciones, extradiciones, medidas economicas, decretos, resultados en salud/educacion/obras, encuestas. Tono descriptivo y objetivo, con cifras. Categorias:
- seguridad: Capturas, bajas, operativos, lucha contra grupos armados
- economia: Medidas economicas y fiscales
- transparencia: Medidas de transparencia, austeridad, anticorrupcion
- gabinete: Conformacion del equipo de gobierno y nombramientos
- empalme: Hallazgos y denuncias del empalme sobre el gobierno saliente
- internacional: Relaciones exteriores y cooperacion
- obras: Infraestructura y agenda territorial (NO el terremoto)
- gestion-emergencia: Otras emergencias distintas al terremoto
- opinion-publica: Encuestas y mediciones de aprobacion

SECCION C - "terremoto": Seguimiento al MANEJO DE LOS DINEROS y la gestion de la emergencia del terremoto del 10 de agosto de 2026, por el gobierno nacional (Presidencia, UNGRD, Fondo Milagro, ministerios) y los gobiernos locales (alcaldias y gobernaciones), con enfasis en PEREIRA/RISARALDA, CALI/VALLE y CHOCO. Aqui SI se documentan hechos negativos y positivos por igual: cuanto se asigno, quien administra la plata, como se contrata, que llega a los damnificados, denuncias de corrupcion, sobrecostos, censos inflados, ayudas que no llegan, actuaciones de Contraloria/Procuraduria/Fiscalia/veedurias, y tambien entregas efectivas y avances. Categorias:
- dineros: Recursos asignados, Fondo Milagro, donaciones, creditos, ejecucion presupuestal
- denuncias: Denuncias de corrupcion, desvios, sobrecostos, ayudas que no llegan
- contratacion: Contratos de emergencia y reconstruccion (quien, a quien, por cuanto)
- gestion-local: Manejo por alcaldias y gobernaciones
- gestion-nacional: Manejo por el gobierno nacional
- avances: Resultados verificables (viviendas, subsidios, vias, servicios)
- damnificados: Albergues, censos, ayudas humanitarias, situacion de la poblacion
- control: Actuaciones de Contraloria, Procuraduria, Fiscalia, veedurias
Para esta seccion agrega tambien:
- "region": pereira | cali | choco | nacional | otras
- "signo": positivo (avance/resultado) | negativo (denuncia/irregularidad) | neutro (seguimiento)

CASOS YA DOCUMENTADOS (ultimos 14 dias) - NO DUPLICAR:
{existing_cases_text}

Para cada articulo RELEVANTE (solo los que documenten hechos concretos, no opiniones ni columnas), responde en formato JSON:

{{
  "casos_relevantes": [
    {{
      "articulo_numero": 1,
      "seccion": "archivo" o "nuevo-gobierno" o "terremoto",
      "titulo_caso": "Titulo descriptivo del caso",
      "categoria": "categoria_id (de la seccion correspondiente)",
      "region": "solo para terremoto",
      "signo": "solo para terremoto",
      "descripcion": "Descripcion breve y objetiva del caso con cifras, fechas y nombres (maximo 200 palabras)",
      "gravedad": "alta|media|baja",
      "personas_involucradas": ["Nombre 1", "Nombre 2"],
      "entidad": "Nombre de la entidad involucrada",
      "es_nuevo": true,
      "relevancia_score": 8
    }}
  ]
}}

IMPORTANTE:
- NO INCLUIR articulos que sean sobre el MISMO CASO que los ya documentados arriba
- Si varios articulos hablan del mismo caso, incluir SOLO UNO; si hay version con paywall (El Tiempo) y sin paywall, elegir el articulo del medio SIN paywall
- Solo incluye articulos que documenten HECHOS CONCRETOS, no opiniones, columnas, ni verificaciones de videos virales
- relevancia_score de 1-10 (solo incluir si >= 6). Se generoso con hechos concretos de los temas prioritarios: un avance judicial, una captura con cifras o una denuncia con nombre y entidad SI son relevantes
- Evita articulos que sean solo especulacion o rumores; si es una denuncia sin confirmar, describela como denuncia y di quien la hace
- En "gravedad" para la seccion "nuevo-gobierno" usa la importancia del hecho (alta = decision o resultado de gran impacto nacional)
- La seccion "nuevo-gobierno" es para RESULTADOS y MEDIDAS del gobierno De la Espriella; NO incluir ahi criticas ni casos negativos sobre Abelardo de la Espriella ni Fico de la Espriella. En la seccion "terremoto" si se documentan irregularidades de entidades y funcionarios de cualquier nivel, siempre con fuente
- Si ningun articulo es relevante o todos son duplicados, devuelve {{"casos_relevantes": []}}

ARTICULOS A ANALIZAR:
{articles_text}

Responde SOLO con el JSON, sin explicaciones adicionales."""


# Esquema de salida para structured outputs (JSON garantizado por la API)
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "casos_relevantes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "articulo_numero": {"type": "integer"},
                    "seccion": {"type": "string", "enum": ["archivo", "nuevo-gobierno", "terremoto"]},
                    "titulo_caso": {"type": "string"},
                    "categoria": {"type": "string"},
                    "region": {"type": "string", "description": "Solo para terremoto: pereira|cali|choco|nacional|otras; vacio en otras secciones"},
                    "signo": {"type": "string", "description": "Solo para terremoto: positivo|negativo|neutro; vacio en otras secciones"},
                    "descripcion": {"type": "string"},
                    "gravedad": {"type": "string", "enum": ["alta", "media", "baja"]},
                    "personas_involucradas": {"type": "array", "items": {"type": "string"}},
                    "entidad": {"type": "string"},
                    "relevancia_score": {"type": "integer"},
                },
                "required": ["articulo_numero", "seccion", "titulo_caso", "categoria", "region", "signo",
                             "descripcion", "gravedad", "personas_involucradas", "entidad", "relevancia_score"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["casos_relevantes"],
    "additionalProperties": False,
}


def salvage_cases(text: str) -> list:
    """Si el JSON completo no parsea, extraer los objetos de caso que si esten bien formados."""
    salvaged = []
    for m in re.finditer(r'\{\s*"articulo_numero"[\s\S]*?\n\s*\}', text):
        try:
            obj = json.loads(m.group())
            if isinstance(obj, dict) and "titulo_caso" in obj:
                salvaged.append(obj)
        except json.JSONDecodeError:
            continue
    print(f"    -> {len(salvaged)} caso(s) rescatado(s)")
    return salvaged


def analyze_batch(client: anthropic.Anthropic, batch: list, existing_cases_text: str) -> list:
    """Envía un lote de artículos a Claude y devuelve los casos con su artículo asociado."""
    articles_text = "\n\n".join([
        f"ARTICULO {i+1}:\nTitulo: {a['title']}\nResumen: {a['summary']}\nFuente: {a['source']}\nFecha: {a['date']}\nURL: {a['url']}"
        for i, a in enumerate(batch)
    ])
    prompt = build_prompt(articles_text, existing_cases_text)

    try:
        # output_config.format (structured outputs) garantiza JSON valido: en la corrida del
        # 17-sep-2026 3 de 5 lotes se perdieron por comillas sin escapar en las descripciones
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        )

        # Los modelos actuales pueden devolver bloques de razonamiento antes del texto:
        # tomar solo los bloques de texto
        response_text = "".join(
            block.text for block in response.content
            if getattr(block, "type", "") == "text"
        )

        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            print(f"  [WARN] Claude no devolvio JSON. Respuesta: {response_text[:200]!r}")
            return []

        try:
            result = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            # Ultimo recurso: rescatar los objetos completos uno por uno
            print(f"  [WARN] JSON invalido ({e}); rescatando casos individuales...")
            result = {"casos_relevantes": salvage_cases(json_match.group())}
        casos = result.get("casos_relevantes", [])
        # La numeracion de Claude corresponde a este lote
        for caso in casos:
            idx = caso.get("articulo_numero", 0) - 1
            if 0 <= idx < len(batch):
                caso["_article"] = batch[idx]
        return [c for c in casos if "_article" in c]

    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON invalido en la respuesta de Claude: {e}")
        return []
    except Exception as e:
        print(f"  Error analyzing with Claude: {e}")
        # Fallar en rojo si no hay creditos: antes el workflow quedaba "en verde"
        # y el pipeline moria en silencio durante meses (ver sesion 8-ago-2026)
        err = str(e).lower()
        if "credit balance" in err:
            print()
            print("ERROR FATAL: La API key de Anthropic no tiene creditos.")
            print("   Recargar en https://console.anthropic.com -> Plans & Billing")
            raise SystemExit(1)
        if "not_found_error" in err and "model" in err:
            print()
            print("ERROR FATAL: El modelo de Claude ya no existe en la API.")
            print("   Actualizar el parametro 'model' en scripts/news_updater.py")
            raise SystemExit(1)
        return []


def analyze_with_claude(client: anthropic.Anthropic, articles: list, existing_hashes: set, existing_cases: list) -> list:
    """Use Claude to analyze and categorize relevant articles (en lotes: TODOS los articulos nuevos se analizan)"""

    if not articles:
        return []

    # Filter out already processed articles by URL
    new_articles = []
    existing_urls = set()
    for case in existing_cases:
        for fuente in case.get("fuentes", []):
            existing_urls.add(fuente.get("url", ""))

    seen_urls = set()
    for article in articles:
        article_hash = generate_case_hash(article["title"], article["url"])
        if article_hash in existing_hashes or article["url"] in existing_urls:
            continue
        if article["url"] in seen_urls:
            continue
        seen_urls.add(article["url"])
        new_articles.append(article)

    if not new_articles:
        print("  No new articles to analyze")
        return []

    # Priorizar por palabras clave (orden estable: a igual puntaje se conserva el orden de llegada)
    new_articles.sort(key=priority_score, reverse=True)
    if len(new_articles) > MAX_ARTICLES_PER_RUN:
        print(f"  {len(new_articles)} articulos nuevos; se analizan los {MAX_ARTICLES_PER_RUN} mas relevantes")
        new_articles = new_articles[:MAX_ARTICLES_PER_RUN]

    # Casos recientes para deteccion de duplicados (ultimos 14 dias)
    cutoff = datetime.now() - timedelta(days=14)
    recent_cases = []
    for case in existing_cases[:120]:
        try:
            case_date = datetime.strptime(case.get("fecha", ""), "%Y-%m-%d")
            if case_date >= cutoff:
                recent_cases.append(f"- {case.get('titulo', '')} ({case.get('entidad', '')})")
        except Exception:
            recent_cases.append(f"- {case.get('titulo', '')} ({case.get('entidad', '')})")
    existing_cases_text = "\n".join(recent_cases[:60]) if recent_cases else "Ninguno"

    batches = [new_articles[i:i + BATCH_SIZE] for i in range(0, len(new_articles), BATCH_SIZE)]
    print(f"  Analyzing {len(new_articles)} new articles with Claude AI ({len(batches)} lote(s) de hasta {BATCH_SIZE})...")

    all_cases = []
    for n, batch in enumerate(batches, 1):
        found = analyze_batch(client, batch, existing_cases_text)
        print(f"    Lote {n}/{len(batches)}: {len(batch)} articulos -> {len(found)} caso(s) relevante(s)")
        all_cases.extend(found)
        # Los casos encontrados en este lote cuentan como "ya documentados" para los siguientes
        for c in found:
            existing_cases_text += f"\n- {c.get('titulo_caso', '')} ({c.get('entidad', '')})"

    return all_cases


def create_case_entry(analyzed: dict, article: dict, next_id: int) -> dict:
    """Create a properly formatted case entry"""
    seccion = analyzed.get("seccion", "archivo")
    categoria = analyzed.get("categoria", "corrupcion")

    # Validar coherencia seccion/categoria
    if seccion == "terremoto" and categoria in TERREMOTO_CATEGORIES:
        pass
    elif categoria in GESTION_CATEGORIES:
        seccion = "nuevo-gobierno"
    elif seccion == "terremoto":
        categoria = "gestion-nacional"
    elif seccion == "nuevo-gobierno":
        categoria = "gestion-emergencia" if "terremoto" in analyzed.get("titulo_caso", "").lower() else "gabinete"
    else:
        seccion = "archivo"
        if categoria not in CATEGORIES:
            categoria = "corrupcion"

    entry = {
        "id": next_id,
        "titulo": analyzed.get("titulo_caso", article["title"]),
        "categoria": categoria,
        "fecha": article["date"],
        "descripcion": analyzed.get("descripcion", article["summary"]),
        "evidencia": f"Reportado por {article['source']}",
        "fuentes": [{
            "nombre": article["source"],
            "url": article["url"],
            "fecha": article["date"]
        }],
        "personas_involucradas": analyzed.get("personas_involucradas", []),
        "entidad": analyzed.get("entidad", "Por determinar"),
        "estado": "Reportado",
        "gravedad": analyzed.get("gravedad", "media"),
        "auto_generated": True,
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    if seccion == "nuevo-gobierno":
        entry["seccion"] = "nuevo-gobierno"
    elif seccion == "terremoto":
        entry["seccion"] = "terremoto"
        region = analyzed.get("region", "otras")
        entry["region"] = region if region in TERREMOTO_REGIONS else "otras"
        signo = analyzed.get("signo", "neutro")
        entry["signo"] = signo if signo in ("positivo", "negativo", "neutro") else "neutro"

    return entry


def main():
    print("=" * 60)
    print("LA LUPA - Actualizador Automatico de Noticias")
    print("=" * 60)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get API keys from environment
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    news_api_key = os.environ.get("NEWS_API_KEY")

    if not anthropic_key:
        print("Error: ANTHROPIC_API_KEY not configured")
        print("   Configure it in GitHub Secrets or environment variables")
        return

    # Initialize Claude client
    client = anthropic.Anthropic(api_key=anthropic_key)

    # Load existing data
    print("Cargando datos existentes...")
    data = load_existing_data()
    existing_cases = data.get("casos", [])

    # Generate hashes of existing cases to detect duplicates
    existing_hashes = set()
    for case in existing_cases:
        for source in case.get("fuentes", []):
            case_hash = generate_case_hash(case["titulo"], source.get("url", ""))
            existing_hashes.add(case_hash)

    print(f"   Casos existentes: {len(existing_cases)}")
    print()

    # Fetch articles from various sources
    print("Buscando noticias...")
    all_articles = []

    # Google News primero: son busquedas dirigidas a los temas del sitio
    # (agrega medios sin feed directo: Semana, Blu Radio, Caracol, RCN, La FM, medios de Pereira, etc.)
    print("  [Google News]")
    gn_articles = fetch_google_news()
    all_articles.extend(gn_articles)
    print(f"   -> {len(gn_articles)} articulos de Google News")

    # NewsAPI
    print("  [NewsAPI]")
    news_api_articles = fetch_news_api(news_api_key)
    all_articles.extend(news_api_articles)
    print(f"   -> {len(news_api_articles)} articulos de NewsAPI")

    # RSS Feeds generales
    print("  [RSS Feeds]")
    rss_articles = fetch_rss_feeds()
    all_articles.extend(rss_articles)
    print(f"   -> {len(rss_articles)} articulos de RSS")

    # Preferir medios sin paywall cuando la misma noticia existe en varios
    all_articles = prefer_free_sources(all_articles)

    print(f"\n   Total articulos encontrados: {len(all_articles)}")
    print()

    if not all_articles:
        print("No se encontraron articulos nuevos")
        return

    # Analyze with Claude
    print("Analizando con Claude AI...")
    analyzed_cases = analyze_with_claude(client, all_articles, existing_hashes, existing_cases)

    if not analyzed_cases:
        print("   No se encontraron casos relevantes nuevos")
        print()
        print("Proceso completado - Sin cambios")
        return

    print(f"   Casos relevantes identificados: {len(analyzed_cases)}")
    print()

    # Add new cases with duplicate checking
    print("Agregando nuevos casos...")
    next_id = max([c.get("id", 0) for c in existing_cases], default=0) + 1
    new_cases_added = 0
    skipped_duplicates = 0

    for analyzed in analyzed_cases:
        # El articulo original viene asociado desde analyze_with_claude
        article = analyzed.get("_article")
        if article:

            # Check if relevance score is high enough
            if analyzed.get("relevancia_score", 0) >= 6:
                # Final duplicate check before adding
                new_title = analyzed.get("titulo_caso", article["title"])
                new_entity = analyzed.get("entidad", "")

                if is_duplicate_case(new_title, article["url"], new_entity, existing_cases):
                    print(f"   [SKIP] Duplicado detectado: {new_title[:50]}...")
                    skipped_duplicates += 1
                    continue

                new_case = create_case_entry(analyzed, article, next_id)
                existing_cases.insert(0, new_case)  # Add at the beginning
                print(f"   [ADD] [{new_case.get('seccion', 'archivo')}] {new_case['titulo'][:70]}...")
                next_id += 1
                new_cases_added += 1

    if new_cases_added > 0:
        # Update and save data
        data["casos"] = existing_cases
        save_data(data)
        print()
        print(f"RESULTADO: {new_cases_added} nuevos casos agregados a data.json")
        if skipped_duplicates > 0:
            print(f"           {skipped_duplicates} duplicados omitidos")
    else:
        print()
        print("RESULTADO: No se agregaron casos nuevos (duplicados o no cumplian criterios)")
        if skipped_duplicates > 0:
            print(f"           {skipped_duplicates} duplicados detectados y omitidos")

    print()
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
