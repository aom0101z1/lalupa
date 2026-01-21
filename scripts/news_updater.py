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
from typing import Optional
import feedparser
import requests
from dateutil import parser as date_parser
import anthropic

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

# Colombian news RSS feeds
RSS_FEEDS = [
    {"name": "El Tiempo - Política", "url": "https://www.eltiempo.com/rss/politica.xml"},
    {"name": "El Tiempo - Justicia", "url": "https://www.eltiempo.com/rss/justicia.xml"},
    {"name": "Semana - Nación", "url": "https://www.semana.com/rss/nacion.xml"},
    {"name": "El Espectador - Política", "url": "https://www.elespectador.com/arc/outboundfeeds/rss/?outputType=xml&_website=el-espectador"},
    {"name": "La Silla Vacía", "url": "https://www.lasillavacia.com/feed/"},
    {"name": "Infobae Colombia", "url": "https://www.infobae.com/feeds/rss/colombia/"},
    {"name": "Blu Radio", "url": "https://www.bluradio.com/rss/nacion.xml"},
    {"name": "Caracol Radio", "url": "https://caracol.com.co/rss/politica.xml"},
]

# Keywords to search for (related to government corruption and scandals)
SEARCH_KEYWORDS = [
    "Petro", "gobierno Petro", "corrupción Colombia", "escándalo político",
    "UNGRD", "nepotismo", "contrato irregular", "conflicto interés",
    "abuso poder", "ministro investigado", "embajador polémica",
    "Fiscalía investiga", "Procuraduría", "Contraloría",
    "sanción internacional", "recursos públicos"
]


def load_existing_data():
    """Load existing cases from data.json"""
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"categorias": [], "casos": []}


def save_data(data):
    """Save updated data to data.json"""
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_case_hash(title: str, url: str) -> str:
    """Generate a unique hash for a case to detect duplicates"""
    content = f"{title.lower()}{url}".encode("utf-8")
    return hashlib.md5(content).hexdigest()[:12]


def fetch_rss_feeds() -> list:
    """Fetch articles from Colombian RSS feeds"""
    articles = []

    for feed_info in RSS_FEEDS:
        try:
            print(f"  Fetching: {feed_info['name']}...")
            feed = feedparser.parse(feed_info["url"])

            for entry in feed.entries[:20]:  # Get latest 20 from each feed
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
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "source": feed_info["name"],
                    "date": pub_date.strftime("%Y-%m-%d") if pub_date else datetime.now().strftime("%Y-%m-%d")
                }

                # Clean HTML from summary
                article["summary"] = re.sub(r'<[^>]+>', '', article["summary"])[:500]

                articles.append(article)

        except Exception as e:
            print(f"  Error fetching {feed_info['name']}: {e}")

    return articles


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
        "ministro Colombia investigación"
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


def analyze_with_claude(client: anthropic.Anthropic, articles: list, existing_hashes: set) -> list:
    """Use Claude to analyze and categorize relevant articles"""

    if not articles:
        return []

    # Filter out already processed articles
    new_articles = []
    for article in articles:
        article_hash = generate_case_hash(article["title"], article["url"])
        if article_hash not in existing_hashes:
            new_articles.append(article)

    if not new_articles:
        print("  No new articles to analyze")
        return []

    print(f"  Analyzing {len(new_articles)} new articles with Claude AI...")

    # Prepare articles for Claude
    articles_text = "\n\n".join([
        f"ARTÍCULO {i+1}:\nTítulo: {a['title']}\nResumen: {a['summary']}\nFuente: {a['source']}\nFecha: {a['date']}\nURL: {a['url']}"
        for i, a in enumerate(new_articles[:30])  # Limit to 30 articles per batch
    ])

    prompt = f"""Eres un analista de noticias políticas colombianas para el sitio "La Lupa", un observatorio ciudadano de transparencia.

Analiza los siguientes artículos y determina cuáles son relevantes para documentar casos de:
- corrupcion: Casos de corrupción, sobornos, malversación
- mentiras: Afirmaciones falsas o engaños por parte de funcionarios
- nepotismo: Nombramientos a familiares o allegados sin mérito
- contratos: Contratos irregulares, sobrecostos, adjudicaciones sospechosas
- conflicto-interes: Decisiones donde hay beneficio personal
- recursos-publicos: Mal uso de dineros públicos
- diplomaticos: Escándalos en embajadas o consulados
- sanciones: Sanciones internacionales a funcionarios
- abuso-poder: Abuso de autoridad, extralimitación de funciones

Para cada artículo RELEVANTE (solo los que documenten hechos concretos, no opiniones), responde en formato JSON:

{{
  "casos_relevantes": [
    {{
      "articulo_numero": 1,
      "titulo_caso": "Título descriptivo del caso",
      "categoria": "categoria_id",
      "descripcion": "Descripción breve y objetiva del caso (máximo 200 palabras)",
      "gravedad": "alta|media|baja",
      "personas_involucradas": ["Nombre 1", "Nombre 2"],
      "entidad": "Nombre de la entidad involucrada",
      "es_nuevo": true,
      "relevancia_score": 8
    }}
  ]
}}

IMPORTANTE:
- Solo incluye artículos que documenten HECHOS CONCRETOS, no opiniones
- relevancia_score de 1-10 (solo incluir si >= 6)
- Evita artículos que sean solo especulación o rumores
- Relacionados con el gobierno actual de Colombia (Petro)
- Si ningún artículo es relevante, devuelve {{"casos_relevantes": []}}

ARTÍCULOS A ANALIZAR:
{articles_text}

Responde SOLO con el JSON, sin explicaciones adicionales."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to parse JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            return result.get("casos_relevantes", [])

    except Exception as e:
        print(f"  Error analyzing with Claude: {e}")

    return []


def create_case_entry(analyzed: dict, article: dict, next_id: int) -> dict:
    """Create a properly formatted case entry"""
    return {
        "id": next_id,
        "titulo": analyzed.get("titulo_caso", article["title"]),
        "categoria": analyzed.get("categoria", "corrupcion"),
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


def main():
    print("=" * 60)
    print("🔍 LA LUPA - Actualizador Automático de Noticias")
    print("=" * 60)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get API keys from environment
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    news_api_key = os.environ.get("NEWS_API_KEY")

    if not anthropic_key:
        print("❌ Error: ANTHROPIC_API_KEY not configured")
        print("   Configure it in GitHub Secrets or environment variables")
        return

    # Initialize Claude client
    client = anthropic.Anthropic(api_key=anthropic_key)

    # Load existing data
    print("📂 Cargando datos existentes...")
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
    print("📰 Buscando noticias...")
    all_articles = []

    # RSS Feeds
    print("  [RSS Feeds]")
    rss_articles = fetch_rss_feeds()
    all_articles.extend(rss_articles)
    print(f"   → {len(rss_articles)} artículos de RSS")

    # NewsAPI
    print("  [NewsAPI]")
    news_api_articles = fetch_news_api(news_api_key)
    all_articles.extend(news_api_articles)
    print(f"   → {len(news_api_articles)} artículos de NewsAPI")

    print(f"\n   Total artículos encontrados: {len(all_articles)}")
    print()

    if not all_articles:
        print("⚠️ No se encontraron artículos nuevos")
        return

    # Analyze with Claude
    print("🤖 Analizando con Claude AI...")
    analyzed_cases = analyze_with_claude(client, all_articles, existing_hashes)

    if not analyzed_cases:
        print("   No se encontraron casos relevantes nuevos")
        print()
        print("✅ Proceso completado - Sin cambios")
        return

    print(f"   Casos relevantes identificados: {len(analyzed_cases)}")
    print()

    # Add new cases
    print("💾 Agregando nuevos casos...")
    next_id = max([c.get("id", 0) for c in existing_cases], default=0) + 1
    new_cases_added = 0

    for analyzed in analyzed_cases:
        # Find the original article
        article_idx = analyzed.get("articulo_numero", 1) - 1
        if 0 <= article_idx < len(all_articles):
            article = all_articles[article_idx]

            # Check if relevance score is high enough
            if analyzed.get("relevancia_score", 0) >= 6:
                new_case = create_case_entry(analyzed, article, next_id)
                existing_cases.insert(0, new_case)  # Add at the beginning
                print(f"   ✓ Agregado: {new_case['titulo'][:60]}...")
                next_id += 1
                new_cases_added += 1

    if new_cases_added > 0:
        # Update and save data
        data["casos"] = existing_cases
        save_data(data)
        print()
        print(f"✅ {new_cases_added} nuevos casos agregados a data.json")
    else:
        print()
        print("✅ No se agregaron casos nuevos (no cumplían criterios)")

    print()
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
