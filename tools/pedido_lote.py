"""Valida render3d/lote/pedido.json (lo escribe «Producción semanal» del repo privado) y da la matriz de lotes.

    python3 tools/pedido_lote.py render3d/lote/pedido.json             → lista JSON de lotes (una línea)
    python3 tools/pedido_lote.py render3d/lote/pedido.json --resumen   → resumen en Markdown

Formato: {"semana": "2026-W52", "pedido": "<fecha ISO>",
          "lotes": [{"temas": "capitales,rios", "paquetes": "paquetes/2026-W52/2026-12-17-x.json"}]}
Reglas: ≤ 4 lotes, ≤ 8 vídeos por lote, nombres seguros, paquetes existentes de esa semana y nada repetido.
"""
from __future__ import annotations

import json
import os
import re
import sys

TEMA = re.compile(r"^[a-z0-9_-]+$")
SEMANA = re.compile(r"^[0-9]{4}-W[0-9]{2}$")
MAX_LOTES, MAX_VIDEOS = 4, 8


def validar(pedido, raiz="."):
    sem = pedido.get("semana", "")
    if not SEMANA.match(sem):
        raise ValueError(f"semana inválida: {sem!r}")
    lotes = pedido.get("lotes")
    if not isinstance(lotes, list) or not 1 <= len(lotes) <= MAX_LOTES:
        raise ValueError(f"hacen falta entre 1 y {MAX_LOTES} lotes")
    vistos, out = set(), []
    paq_re = re.compile(rf"^paquetes/{re.escape(sem)}/[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}-[a-z0-9-]+\.json$")
    for n, lote in enumerate(lotes, 1):
        temas = [t for t in str(lote.get("temas", "")).split(",") if t]
        paqs = [p for p in str(lote.get("paquetes", "")).split(",") if p]
        if not temas and not paqs:
            raise ValueError(f"lote {n} vacío")
        if len(temas) + len(paqs) > MAX_VIDEOS:
            raise ValueError(f"lote {n}: más de {MAX_VIDEOS} vídeos")
        for t in temas:
            if not TEMA.match(t):
                raise ValueError(f"lote {n}: tema inválido {t!r}")
            if not os.path.exists(os.path.join(raiz, "render3d", "simula", "quizzes", t + ".json")):
                raise ValueError(f"lote {n}: no existe el quiz {t}")
        for p in paqs:
            if not paq_re.match(p):
                raise ValueError(f"lote {n}: paquete fuera de paquetes/{sem}/ o con nombre inválido: {p!r}")
            if not os.path.exists(os.path.join(raiz, p)):
                raise ValueError(f"lote {n}: no existe {p}")
        for k in temas + paqs:
            if k in vistos:
                raise ValueError(f"repetido en el pedido: {k}")
            vistos.add(k)
        out.append({"temas": ",".join(temas), "paquetes": ",".join(paqs)})
    return out


def main(argv):
    ruta = argv[1]
    pedido = json.load(open(ruta, encoding="utf-8"))
    lotes = validar(pedido)
    if "--resumen" in argv:
        print(f"## Lote semanal · {pedido['semana']}\n")
        for n, l in enumerate(lotes, 1):
            k = len([x for x in (l["temas"] + "," + l["paquetes"]).split(",") if x])
            print(f"- Lote {n}: {k} vídeos · quiz: {l['temas'] or '—'} · paquetes: {l['paquetes'].count('.json')}")
    else:
        print(json.dumps(lotes, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main(sys.argv)
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"pedido inválido: {e}", file=sys.stderr)
        sys.exit(1)
