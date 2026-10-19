#!/usr/bin/env python3
"""
La Lupa - Fusiona archivos de investigacion de promesas (promesas_*.json de agentes) en promesas.json.

Uso:
  python scripts/merge_promesas.py <carpeta_o_archivos...> [--check-urls]

- Asigna ids enteros consecutivos (continua desde el max existente).
- Valida gobierno/estado/tema contra promesas.json.
- Dedup por texto de promesa (similitud >= 0.85) dentro del mismo gobierno.
- --check-urls: hace GET a cada URL y descarta la promesa si la fuente de la promesa
  responde >= 400 o no responde; las fuentes de resultado rotas se eliminan (si todas se
  caen y el estado no es "sin-avance", la promesa se descarta). Nunca se publica una URL inventada.
"""
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from news_updater import text_similarity  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMESAS = os.path.join(ROOT, "promesas.json")


def url_ok(url: str, cache: dict) -> bool:
    if url in cache:
        return cache[url]
    import requests, urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ok = False
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (compatible; LaLupaBot/1.0)"}, allow_redirects=True, stream=True)
        ok = r.status_code < 400
        if not ok:
            print(f"     [URL {r.status_code}] {url}")
    except requests.exceptions.SSLError:
        # Sitios oficiales (.gov.co) con certificados mal configurados: reintentar sin verificar
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (compatible; LaLupaBot/1.0)"}, allow_redirects=True, stream=True, verify=False)
            ok = r.status_code < 400
            print(f"     [URL SSL {'ok' if ok else r.status_code}] {url}")
        except Exception as e:
            print(f"     [URL ERROR] {url} ({type(e).__name__})")
    except Exception as e:
        print(f"     [URL ERROR] {url} ({type(e).__name__})")
    cache[url] = ok
    return ok


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check-urls" in sys.argv
    files = []
    for a in args:
        files += glob.glob(os.path.join(a, "promesas_*.json")) if os.path.isdir(a) else [a]
    if not files:
        print("Uso: merge_promesas.py <carpeta|archivos> [--check-urls]")
        sys.exit(2)

    with open(PROMESAS, encoding="utf-8") as f:
        data = json.load(f)
    gobiernos = {g["id"]: set(g["estados"]) for g in data["gobiernos"]}
    temas = set(data["temas"])
    existing = data["promesas"]
    next_id = max([p["id"] for p in existing], default=0) + 1
    cache, added, dropped = {}, 0, 0

    for path in files:
        print(f"\n== {os.path.basename(path)}")
        with open(path, encoding="utf-8") as f:
            src = json.load(f)
        gob = src.get("gobierno")
        for p in src.get("promesas", []):
            titulo = (p.get("promesa") or "").strip()
            g = p.get("gobierno") or gob
            why = None
            if g not in gobiernos:
                why = f"gobierno invalido {g!r}"
            elif p.get("estado") not in gobiernos[g]:
                why = f"estado invalido {p.get('estado')!r} para {g}"
            elif not titulo or not p.get("resultado"):
                why = "sin promesa o sin resultado"
            elif not str((p.get("fuente_promesa") or {}).get("url", "")).startswith("http"):
                why = "fuente_promesa sin URL"
            elif any(x["gobierno"] == g and text_similarity(titulo, x["promesa"]) >= 0.85 for x in existing):
                why = "duplicada"
            if not why and check:
                if not url_ok(p["fuente_promesa"]["url"], cache):
                    why = "fuente_promesa no responde"
                else:
                    fr = [f for f in (p.get("fuentes_resultado") or []) if str(f.get("url", "")).startswith("http") and url_ok(f["url"], cache)]
                    if not fr and p.get("estado") != "sin-avance":
                        why = "ninguna fuente de resultado responde"
                    p["fuentes_resultado"] = fr
            if why:
                print(f"   [DROP] {titulo[:70]} -> {why}")
                dropped += 1
                continue
            entry = {
                "id": next_id,
                "gobierno": g,
                "tema": p.get("tema") if p.get("tema") in temas else "otros",
                "promesa": titulo,
                "fuente_promesa": p["fuente_promesa"],
                "estado": p["estado"],
                "resultado": p["resultado"].strip(),
                "fuentes_resultado": p.get("fuentes_resultado") or [],
                "fecha_actualizacion": p.get("fecha_actualizacion") or "",
            }
            existing.append(entry)
            next_id += 1
            added += 1
            print(f"   [ADD] [{g}] [{entry['estado']}] {titulo[:70]}")

    data["promesas"] = existing
    from datetime import datetime
    data.setdefault("estadisticas", {})["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
    with open(PROMESAS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\nRESULTADO: {added} promesas agregadas, {dropped} descartadas. Total: {len(existing)}")


if __name__ == "__main__":
    main()
