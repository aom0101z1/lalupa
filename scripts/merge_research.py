#!/usr/bin/env python3
"""
La Lupa - Fusiona archivos de investigacion (research_*.json) en data.json con deduplicacion.

Uso:
  python scripts/merge_research.py <carpeta>                 # lee research_archivo.json,
                                                             # research_gobierno.json, research_terremoto.json
  python scripts/merge_research.py <carpeta> --force "Inicio del titulo" [--force "..."]
        # agrega esos titulos aunque el detector de duplicados los marque como similares

Esquema de cada item (array JSON):
  titulo, categoria, fecha (YYYY-MM-DD), descripcion, evidencia,
  fuentes [{nombre, url, fecha}], personas_involucradas [], entidad, gravedad (alta|media|baja)
  terremoto ademas: region (pereira|cali|choco|nacional|otras), signo (positivo|negativo|neutro)
  archivo opcional: tema (etiqueta corta)

Los casos quedan con auto_generated=true (visibles al publico de inmediato; el admin los
desactiva desde el Panel Admin si no le gustan).
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)
import news_updater as nu  # noqa: E402

FILES = [
    ("research_archivo.json", None),
    ("research_gobierno.json", "nuevo-gobierno"),
    ("research_terremoto.json", "terremoto"),
]


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0].startswith("--"):
        print(__doc__)
        sys.exit(2)
    folder = args[0]
    forced = []
    i = 1
    while i < len(args):
        if args[i] == "--force" and i + 1 < len(args):
            forced.append(args[i + 1].lower())
            i += 2
        else:
            i += 1

    data = nu.load_existing_data()
    casos = data["casos"]
    next_id = max(c["id"] for c in casos) + 1
    existing_urls = {f.get("url", "") for c in casos for f in c.get("fuentes", [])}
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cat_archivo = set(nu.CATEGORIES.keys())
    cat_gestion = set(nu.GESTION_CATEGORIES)
    cat_terremoto = set(nu.TERREMOTO_CATEGORIES)

    added, skipped = [], []
    for fname, seccion in FILES:
        path = os.path.join(folder, fname)
        if not os.path.exists(path):
            print(f"[MISSING] {fname}")
            continue
        items = json.load(open(path, encoding="utf-8"))
        print(f"\n=== {fname}: {len(items)} items ===")
        for it in items:
            titulo = (it.get("titulo") or "").strip()
            fuentes = [f for f in it.get("fuentes", []) if str(f.get("url", "")).startswith("http")]
            if not titulo or not fuentes or not it.get("descripcion"):
                skipped.append((fname, titulo, "incompleto"))
                continue
            url = fuentes[0]["url"]
            if url in existing_urls:
                skipped.append((fname, titulo, "url ya existe"))
                continue
            is_forced = any(titulo.lower().startswith(p) for p in forced)
            if not is_forced and nu.is_duplicate_case(titulo, url, it.get("entidad", ""), casos, days_lookback=60):
                skipped.append((fname, titulo, "similar a caso existente (usa --force si es distinto)"))
                continue
            if any(nu.text_similarity(titulo, a["titulo"]) >= 0.65 for a in added):
                skipped.append((fname, titulo, "duplicado en la tanda"))
                continue

            cat = it.get("categoria", "")
            if seccion is None and cat not in cat_archivo:
                cat = "corrupcion"
            if seccion == "nuevo-gobierno" and cat not in cat_gestion:
                cat = "gabinete"
            if seccion == "terremoto" and cat not in cat_terremoto:
                cat = "gestion-nacional"

            fecha = it.get("fecha", "")
            try:
                datetime.strptime(fecha, "%Y-%m-%d")
            except (ValueError, TypeError):
                fecha = fuentes[0].get("fecha") or datetime.now().strftime("%Y-%m-%d")

            entry = {
                "id": next_id,
                "titulo": titulo[:160],
                "categoria": cat,
                "fecha": fecha,
                "descripcion": it["descripcion"].strip(),
                "evidencia": (it.get("evidencia") or f"Reportado por {fuentes[0].get('nombre', 'prensa')}").strip(),
                "fuentes": [{"nombre": f.get("nombre", "Fuente"), "url": f["url"], "fecha": f.get("fecha", fecha)} for f in fuentes[:4]],
                "personas_involucradas": [p for p in it.get("personas_involucradas", []) if isinstance(p, str)][:8],
                "entidad": it.get("entidad", "Por determinar"),
                "estado": "Reportado",
                "gravedad": it.get("gravedad") if it.get("gravedad") in ("alta", "media", "baja") else "media",
                "auto_generated": True,
                "added_date": now,
            }
            if seccion:
                entry["seccion"] = seccion
            if seccion == "terremoto":
                entry["region"] = it.get("region") if it.get("region") in nu.TERREMOTO_REGIONS else "otras"
                entry["signo"] = it.get("signo") if it.get("signo") in ("positivo", "negativo", "neutro") else "neutro"
            if seccion is None and it.get("tema"):
                entry["tema"] = it["tema"]

            added.append(entry)
            existing_urls.add(url)
            next_id += 1
            print(f"  [ADD] {entry['id']} [{seccion or 'archivo'}/{cat}] {fecha} {titulo[:70]}")

    added.sort(key=lambda c: c["fecha"], reverse=True)
    data["casos"] = added + casos
    nu.save_data(data)

    print(f"\nAGREGADOS: {len(added)}   OMITIDOS: {len(skipped)}")
    for s in skipped:
        print(f"  [SKIP] {s[0]} | {s[2]} | {s[1][:70]}")
    print("Por seccion:", Counter(c.get("seccion", "archivo") for c in added))
    print("TOTAL casos ahora:", len(data["casos"]))


if __name__ == "__main__":
    main()
