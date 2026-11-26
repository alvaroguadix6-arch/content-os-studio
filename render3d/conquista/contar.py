"""TU PUEBLO CONQUISTA ESPAÑA · cuenta los votos a partir de los comentarios REALES exportados.

    python contar.py comentarios.csv temporada1 2

comentarios.csv: columnas `usuario,comentario` (y opcionalmente `red`: tiktok/instagram/youtube).
Sirve cualquier exportación o una copia a mano. Reglas:
  · 1 voto por cuenta y episodio (cuenta = red + usuario): vale su PRIMER comentario reconocido.
  · El comentario debe nombrar un municipio real; la provincia es obligatoria si el nombre se repite en España
    (p. ej. «Villanueva»). Mayúsculas, tildes y artículos dan igual: «guadix granada», «Guadix, Granada», «Guadix (GR)».
  · Lo que no se reconoce NO suma y va a temporada/revisar/epNN.txt para revisarlo a mano.
Resultado: temporada/votos/epNN.csv  (pueblo,provincia,votos) → listo para `producir.py`.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import datos  # noqa: E402

PROV_ABBR = {"gr": "granada", "al": "almeria", "ja": "jaen", "j": "jaen", "co": "cordoba", "se": "sevilla", "ma": "malaga", "ca": "cadiz",
             "h": "huelva", "m": "madrid", "b": "barcelona", "v": "valencia", "a": "alicante", "mu": "murcia", "z": "zaragoza",
             "to": "toledo", "cr": "ciudad real", "ab": "albacete", "cu": "cuenca", "gu": "guadalajara", "ba": "badajoz", "cc": "caceres"}


def parse(text: str):
    """Intenta sacar (pueblo, provincia) de un comentario libre."""
    t = re.sub(r"[\U0001F000-\U0001FFFF☀-➿#@]", " ", text)  # emojis, hashtags, menciones
    t = re.sub(r"\s+", " ", t).strip(" .!¡?¿")
    t = re.sub(r"(\w)\1{2,}", r"\1", t)                      # letras alargadas: «Jumillaaaa» → «Jumilla»
    t = re.sub(r"\b(capital|ciudad|city|pueblo)\s*$", "", t, flags=re.I).strip(" ,.-")  # «Cádiz capital»
    cands = []
    m = re.match(r"^(.+?)\s*[\(\[]\s*([^\)\]]+)\s*[\)\]]", t)  # «Guadix (Granada)»
    if m:
        cands.append((m.group(1), m.group(2)))
    for sep in (",", " - ", " – ", "/", " de la provincia de ", " provincia de ", " en "):
        if sep in t:
            a, b = t.split(sep, 1)
            cands.append((a, b))
    words = t.split()
    for k in range(len(words) - 1, 0, -1):  # «guadix granada»: última(s) palabra(s) = provincia
        cands.append((" ".join(words[:k]), " ".join(words[k:])))
    cands.append((t, None))
    sin_par = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]?", " ", t).strip()  # «Alcoy (primerooo)» → «Alcoy»
    if sin_par and sin_par != t:
        cands.append((sin_par, None))
    for p, q in cands:
        p = re.sub(r"^(soy de|desde|de|arriba|vamos|viva|aupa|aúpa|dale)\s+", "", p.strip(), flags=re.I)
        if q:
            q = PROV_ABBR.get(datos.norm(q), q)
            if datos.prov_code(q) is None:
                continue
        i, why = datos.find(p, q)
        if i is not None:
            return i, "ok"
    return None, "no reconocido"


def main():
    src, temporada, ep = sys.argv[1], sys.argv[2], int(sys.argv[3])
    munis, provs = datos.load()
    seen, votes, review = set(), Counter(), []
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    for r in rows:
        user = (r.get("red", "") + ":" + (r.get("usuario") or "").strip().lower())
        txt = (r.get("comentario") or "").strip()
        if not txt or user in seen:
            continue
        i, why = parse(txt)
        if i is None:
            review.append(f"{r.get('usuario')}: «{txt}» → {why}")
            continue
        seen.add(user)
        votes[i] += 1
    os.makedirs(os.path.join(temporada, "votos"), exist_ok=True)
    os.makedirs(os.path.join(temporada, "revisar"), exist_ok=True)
    out = os.path.join(temporada, "votos", f"ep{ep:02d}.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pueblo", "provincia", "votos"])
        for i, v in votes.most_common():
            w.writerow([munis[i]["nombre"], provs[munis[i]["prov"]]["nombre"], v])
    open(os.path.join(temporada, "revisar", f"ep{ep:02d}.txt"), "w", encoding="utf-8").write("\n".join(review) + "\n")
    print(f"{len(rows)} comentarios · {sum(votes.values())} votos válidos · {len(votes)} pueblos · {len(review)} para revisar")
    print("→", out)


if __name__ == "__main__":
    main()
