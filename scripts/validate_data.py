#!/usr/bin/env python3
"""
La Lupa - Validador del harness.

Verifica que el sitio no se pueda romper por un dato o un archivo mal formado:
  1. data.json: JSON valido, IDs unicos, campos obligatorios, categorias/secciones/regiones validas
  2. index.html: contenedores que script.js necesita (ids)
  3. script.js: sintaxis (node --check) si node esta disponible
  4. scripts/news_updater.py: compila

Uso:
  python scripts/validate_data.py            # todo
  python scripts/validate_data.py --data-only

Sale con codigo 1 si hay errores (los warnings no bloquean).
Lo usan: el hook PostToolUse de Claude Code, el guard de git push y el workflow de GitHub.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ONLY = "--data-only" in sys.argv

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


# ---------------------------------------------------------------- data.json
def validate_data():
    path = os.path.join(ROOT, "data.json")
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        if raw.startswith("﻿"):
            err("data.json tiene BOM UTF-8 (rompe fetch en algunos navegadores)")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        err(f"data.json NO es JSON valido: {e}")
        return
    except FileNotFoundError:
        err("data.json no existe")
        return

    for key in ("categorias", "categorias_gestion", "categorias_terremoto", "regiones_terremoto", "casos", "estadisticas"):
        if key not in data:
            err(f"data.json: falta la clave '{key}'")
    if errors:
        return

    cat_archivo = {c["id"] for c in data["categorias"]}
    cat_gestion = {c["id"] for c in data["categorias_gestion"]}
    cat_terremoto = {c["id"] for c in data["categorias_terremoto"]}
    regiones = {r["id"] for r in data["regiones_terremoto"]}
    for grupo, cats in (("categorias", data["categorias"]), ("categorias_gestion", data["categorias_gestion"]),
                        ("categorias_terremoto", data["categorias_terremoto"])):
        for c in cats:
            for k in ("id", "nombre", "icono", "color"):
                if not c.get(k):
                    err(f"{grupo}: categoria {c.get('id')} sin '{k}'")

    casos = data["casos"]
    if not isinstance(casos, list) or not casos:
        err("data.json: 'casos' vacio o no es lista")
        return

    ids, urls = {}, {}
    secciones_ok = {None, "nuevo-gobierno", "terremoto"}
    for i, c in enumerate(casos):
        tag = f"caso[{i}] id={c.get('id')}"
        cid = c.get("id")
        if not isinstance(cid, int):
            err(f"{tag}: id no es entero")
        elif cid in ids:
            err(f"{tag}: id DUPLICADO (tambien en caso[{ids[cid]}])")
        else:
            ids[cid] = i

        for k in ("titulo", "descripcion", "categoria", "fecha"):
            if not c.get(k):
                err(f"{tag}: falta '{k}'")

        fecha = c.get("fecha", "")
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except (ValueError, TypeError):
            err(f"{tag}: fecha invalida '{fecha}' (debe ser YYYY-MM-DD)")

        sec = c.get("seccion")
        if sec not in secciones_ok:
            err(f"{tag}: seccion desconocida '{sec}'")
        cat = c.get("categoria")
        if sec is None and cat not in cat_archivo:
            err(f"{tag}: categoria '{cat}' no existe en 'categorias' (archivo)")
        elif sec == "nuevo-gobierno" and cat not in cat_gestion:
            err(f"{tag}: categoria '{cat}' no existe en 'categorias_gestion'")
        elif sec == "terremoto":
            if cat not in cat_terremoto:
                err(f"{tag}: categoria '{cat}' no existe en 'categorias_terremoto'")
            if c.get("region") not in regiones:
                err(f"{tag}: region '{c.get('region')}' no existe en 'regiones_terremoto'")
            if c.get("signo") not in ("positivo", "negativo", "neutro"):
                err(f"{tag}: signo '{c.get('signo')}' invalido")

        fuentes = c.get("fuentes")
        if not isinstance(fuentes, list) or not fuentes:
            err(f"{tag}: sin fuentes")
        else:
            for f in fuentes:
                url = f.get("url", "")
                if not url.startswith("http"):
                    err(f"{tag}: fuente sin URL valida ({url!r})")
                elif url in urls and urls[url] != cid:
                    warn(f"{tag}: URL repetida con caso id={urls[url]}: {url[:80]}")
                else:
                    urls.setdefault(url, cid)

        if c.get("gravedad") not in ("alta", "media", "baja", None):
            warn(f"{tag}: gravedad rara '{c.get('gravedad')}'")

    # Orden: los casos mas nuevos van primero (el bot inserta al inicio)
    if len(casos) > 1 and isinstance(casos[0].get("id"), int) and isinstance(casos[1].get("id"), int):
        if casos[0]["id"] < casos[1]["id"]:
            warn("casos[0] tiene id menor que casos[1]: el orden esperado es el mas nuevo primero")

    print(f"  data.json: {len(casos)} casos, ids unicos={len(ids) == len(casos)}, "
          f"archivo={sum(1 for c in casos if not c.get('seccion'))}, "
          f"nuevo-gobierno={sum(1 for c in casos if c.get('seccion') == 'nuevo-gobierno')}, "
          f"terremoto={sum(1 for c in casos if c.get('seccion') == 'terremoto')}")


# ---------------------------------------------------------------- index.html
REQUIRED_IDS = [
    "stats-grid", "casos-grid", "casos-count", "no-results",
    "gestion-compare", "gestion-filters", "gestion-grid", "gestion-count",
    "terremoto-resumen", "terremoto-regiones", "terremoto-filters", "terremoto-grid", "terremoto-count",
    "temas-interes", "admin-content",
    "politica", "politica-tabs", "archivo", "nuevo-gobierno", "violencia",
    "portada-lecturas", "emprendimiento", "ciencia", "tecnologia",
    "lecturas-emprendimiento", "lecturas-ciencia", "lecturas-tecnologia",
    "promesas", "promesas-content", "tab-promesas",
]


def validate_html():
    path = os.path.join(ROOT, "index.html")
    try:
        html = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        err("index.html no existe")
        return
    for el_id in REQUIRED_IDS:
        if f'id="{el_id}"' not in html:
            err(f"index.html: falta el elemento id=\"{el_id}\" que script.js necesita")
    m = re.search(r'script\.js\?v=(\d+)', html)
    if not m:
        warn("index.html: script.js no tiene cache-bust ?v=YYYYMMDD")
    print(f"  index.html: {len(REQUIRED_IDS)} contenedores requeridos, cache-bust v={m.group(1) if m else '-'}")


# ---------------------------------------------------------------- script.js / python
def validate_js():
    node = shutil.which("node")
    if not node:
        warn("node no disponible: no se verifico la sintaxis de script.js")
        return
    r = subprocess.run([node, "--check", os.path.join(ROOT, "script.js")], capture_output=True, text=True)
    if r.returncode != 0:
        err("script.js NO compila:\n" + (r.stderr or r.stdout)[-1500:])
    else:
        print("  script.js: sintaxis OK")


def validate_py():
    import py_compile
    for name in ("news_updater.py", "lecturas_updater.py"):
        path = os.path.join(ROOT, "scripts", name)
        try:
            py_compile.compile(path, doraise=True)
            print(f"  {name}: compila OK")
        except py_compile.PyCompileError as e:
            err(f"{name} NO compila: {e}")


# ---------------------------------------------------------------- promesas.json
PROMESA_REQUIRED = ("id", "gobierno", "tema", "promesa", "estado", "resultado", "fuente_promesa")


def validate_promesas():
    path = os.path.join(ROOT, "promesas.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        err(f"promesas.json NO es JSON valido: {e}")
        return
    except FileNotFoundError:
        err("promesas.json no existe")
        return
    for key in ("gobiernos", "estados", "temas", "promesas"):
        if key not in data:
            err(f"promesas.json: falta la clave '{key}'")
            return
    gobiernos = {g["id"]: set(g.get("estados", [])) for g in data["gobiernos"]}
    estados = {e["id"] for e in data["estados"]}
    temas = set(data["temas"])
    ids = {}
    for i, p in enumerate(data["promesas"]):
        tag = f"promesa[{i}] id={p.get('id')}"
        for k in PROMESA_REQUIRED:
            if k not in p or p[k] in ("", None):
                err(f"{tag}: falta '{k}'")
        pid = p.get("id")
        if not isinstance(pid, int):
            err(f"{tag}: id debe ser entero")
        elif pid in ids:
            err(f"{tag}: id DUPLICADO")
        else:
            ids[pid] = i
        if p.get("gobierno") not in gobiernos:
            err(f"{tag}: gobierno invalido '{p.get('gobierno')}'")
        elif p.get("estado") not in gobiernos[p["gobierno"]]:
            err(f"{tag}: estado '{p.get('estado')}' no es valido para el gobierno {p['gobierno']}")
        if p.get("estado") not in estados:
            err(f"{tag}: estado invalido '{p.get('estado')}'")
        if p.get("tema") not in temas:
            err(f"{tag}: tema invalido '{p.get('tema')}'")
        fp = p.get("fuente_promesa") or {}
        if not isinstance(fp, dict) or not str(fp.get("url", "")).startswith("http"):
            err(f"{tag}: fuente_promesa sin URL valida")
        for j, f in enumerate(p.get("fuentes_resultado") or []):
            if not str(f.get("url", "")).startswith("http"):
                err(f"{tag}: fuentes_resultado[{j}] sin URL valida")
        if p.get("estado") != "sin-avance" and not (p.get("fuentes_resultado") or []):
            warn(f"{tag}: estado '{p.get('estado')}' sin fuentes_resultado")
    print(f"  promesas.json: {len(data['promesas'])} promesas, ids unicos={len(ids) == len(data['promesas'])}")


# ---------------------------------------------------------------- lecturas.json
LECTURA_SECCIONES = {"emprendimiento", "ciencia", "tecnologia"}
LECTURA_REQUIRED = ("id", "titulo", "resumen", "seccion", "fuente", "fecha", "interes_score")


def validate_lecturas():
    path = os.path.join(ROOT, "lecturas.json")
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        if raw.startswith("\ufeff"):
            err("lecturas.json tiene BOM UTF-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        err(f"lecturas.json NO es JSON valido: {e}")
        return
    except FileNotFoundError:
        err("lecturas.json no existe")
        return
    for key in ("secciones", "lecturas", "estadisticas"):
        if key not in data:
            err(f"lecturas.json: falta la clave '{key}'")
            return
    secciones = {s.get("id") for s in data["secciones"]}
    if secciones != LECTURA_SECCIONES:
        err(f"lecturas.json: secciones {sorted(secciones)} != {sorted(LECTURA_SECCIONES)}")
    ids, urls = {}, {}
    for i, l in enumerate(data["lecturas"]):
        tag = f"lectura[{i}] id={l.get('id')}"
        for k in LECTURA_REQUIRED:
            if k not in l or l[k] in ("", None):
                err(f"{tag}: falta '{k}'")
        lid = l.get("id")
        if not isinstance(lid, int):
            err(f"{tag}: id debe ser entero")
        elif lid in ids:
            err(f"{tag}: id DUPLICADO (tambien en lectura[{ids[lid]}])")
        else:
            ids[lid] = i
        if l.get("seccion") not in LECTURA_SECCIONES:
            err(f"{tag}: seccion invalida '{l.get('seccion')}'")
        f = l.get("fuente") or {}
        if not isinstance(f, dict) or not str(f.get("url", "")).startswith("http"):
            err(f"{tag}: fuente sin URL valida")
        else:
            u = f["url"]
            if u in urls:
                warn(f"{tag}: URL repetida con lectura id={urls[u]}")
            urls[u] = lid
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(l.get("fecha", ""))):
            err(f"{tag}: fecha debe ser YYYY-MM-DD")
        sc = l.get("interes_score")
        if not isinstance(sc, int) or not 1 <= sc <= 10:
            err(f"{tag}: interes_score debe ser entero 1-10")
    print(f"  lecturas.json: {len(data['lecturas'])} lecturas, ids unicos={len(ids) == len(data['lecturas'])}")


if __name__ == "__main__":
    print("La Lupa - validador")
    validate_data()
    validate_lecturas()
    validate_promesas()
    if not DATA_ONLY:
        validate_html()
        validate_js()
        validate_py()
    for w in warnings:
        print(f"  [WARN] {w}")
    if errors:
        print(f"\nERRORES ({len(errors)}):")
        for e in errors:
            print(f"  [ERROR] {e}")
        sys.exit(1)
    print(f"\nOK - sin errores ({len(warnings)} warning(s))")
