"""TU PUEBLO CONQUISTA ESPAÑA · datos del mapa (municipios del IGN vía es-atlas, licencia MIT).

- Decodifica el TopoJSON (8.213 recintos: municipios + comunidades/ledanías de pastos compartidos).
- Calcula área (km²) y centroide de cada recinto.
- Índice de nombres para reconocer «pueblo, provincia» escritos a mano (sin tildes, con/sin artículo,
  nombres bilingües, nombres antiguos de provincias).
"""
from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
TOPO = os.path.join(HERE, "datos", "es-atlas-municipios.topojson")

# nombres alternativos de provincias (lo que la gente escribe → código INE)
PROV_ALIAS = {
    "alava": "01", "araba": "01", "albacete": "02", "alicante": "03", "alacant": "03", "almeria": "04", "avila": "05",
    "badajoz": "06", "baleares": "07", "islas baleares": "07", "illes balears": "07", "mallorca": "07", "menorca": "07",
    "ibiza": "07", "eivissa": "07", "formentera": "07", "barcelona": "08", "burgos": "09", "caceres": "10", "cadiz": "11",
    "castellon": "12", "castello": "12", "ciudad real": "13", "cordoba": "14", "a coruna": "15", "la coruna": "15",
    "coruna": "15", "cuenca": "16", "girona": "17", "gerona": "17", "granada": "18", "guadalajara": "19",
    "gipuzkoa": "20", "guipuzcoa": "20", "huelva": "21", "huesca": "22", "jaen": "23", "leon": "24", "lleida": "25",
    "lerida": "25", "la rioja": "26", "rioja": "26", "logrono": "26", "lugo": "27", "madrid": "28", "malaga": "29",
    "murcia": "30", "region de murcia": "30", "navarra": "31", "nafarroa": "31", "ourense": "32", "orense": "32",
    "asturias": "33", "principado de asturias": "33", "oviedo": "33", "palencia": "34", "las palmas": "35",
    "gran canaria": "35", "lanzarote": "35", "fuerteventura": "35", "pontevedra": "36", "salamanca": "37",
    "santa cruz de tenerife": "38", "tenerife": "38", "la palma": "38", "la gomera": "38", "el hierro": "38",
    "cantabria": "39", "santander": "39", "segovia": "40", "sevilla": "41", "soria": "42", "tarragona": "43",
    "teruel": "44", "toledo": "45", "valencia": "46", "valladolid": "47", "bizkaia": "48", "vizcaya": "48",
    "zamora": "49", "zaragoza": "50", "ceuta": "51", "melilla": "52",
}
ARTICLES = ("el ", "la ", "los ", "las ", "l'", "l ", "es ", "sa ", "ses ", "o ", "a ", "os ", "as ", "els ", "les ")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("’", "'").replace("`", "'")
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def variants(name: str):
    """Formas en que alguien puede escribir un municipio."""
    out = set()
    for part in re.split(r"[/]", name):  # «Donostia/San Sebastián», «Alacant/Alicante»
        part = part.strip()
        m = re.match(r"^(.*), (el|la|los|las|l'|es|sa|ses|o|a|os|as|els|les)$", part, re.I)  # «Rozas, Las»
        if m:
            part = f"{m.group(2)} {m.group(1)}"
        n = norm(part)
        out.add(n)
        for a in ARTICLES:
            if n.startswith(a):
                out.add(n[len(a):].strip())
        for p in n.split("-"):
            pass
        if "-" in part:  # «Vitoria-Gasteiz» → «vitoria» y «gasteiz»
            for p in part.split("-"):
                if len(p.strip()) > 3:
                    out.add(norm(p))
    return {v for v in out if v}


def _decode(topo):
    tr = topo["transform"]
    sx, sy = tr["scale"]
    tx, ty = tr["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        pts = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a if not pts else a[1:])
        return pts

    def geom(g):
        if g["type"] == "Polygon":
            return [[ring(r) for r in g["arcs"]]]
        if g["type"] == "MultiPolygon":
            return [[ring(r) for r in p] for p in g["arcs"]]
        return []

    return geom


def ring_area_centroid(r):
    """Área (km²) y centroide (lon, lat) con proyección local equivalente."""
    lat0 = sum(p[1] for p in r) / len(r)
    kx, ky = 111.32 * math.cos(math.radians(lat0)), 110.57
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
        X1, Y1, X2, Y2 = x1 * kx, y1 * ky, x2 * kx, y2 * ky
        c = X1 * Y2 - X2 * Y1
        a += c
        cx += (X1 + X2) * c
        cy += (Y1 + Y2) * c
    if abs(a) < 1e-12:
        return 0.0, r[0]
    return abs(a) / 2, (cx / (3 * a) / kx, cy / (3 * a) / ky)


@lru_cache(maxsize=1)
def load():
    topo = json.load(open(TOPO, encoding="utf-8"))
    geom = _decode(topo)
    provs = {}
    for g in topo["objects"]["provinces"]["geometries"]:
        if g["id"] in [str(i).zfill(2) for i in range(1, 53)]:
            provs[g["id"]] = dict(id=g["id"], nombre=g["properties"]["name"], polys=geom(g))
    munis = []
    for g in topo["objects"]["municipalities"]["geometries"]:
        pid = g["id"][:2]
        name = g["properties"]["name"]
        if pid not in provs and pid != "53":  # Gibraltar (no es España)
            continue
        polys = geom(g)
        area, best, cen = 0.0, -1, None
        for p in polys:
            a, c = ring_area_centroid(p[0])
            area += a
            if a > best:
                best, cen = a, c
        shared = pid == "53" or bool(re.match(r"^(Comunidad de|Ledanía|Facería|Mancomunidad|Parzonería)", name))
        munis.append(dict(id=g["id"], nombre=name, prov=pid, area=area, lon=cen[0], lat=cen[1], polys=polys, votable=not shared))
    return munis, provs


@lru_cache(maxsize=1)
def index():
    munis, provs = load()
    idx = {}
    for i, m in enumerate(munis):
        if not m["votable"]:
            continue
        for v in variants(m["nombre"]):
            idx.setdefault(v, []).append(i)
    return idx


def prov_code(text: str):
    if "/" in text:  # nombres bilingües, como los escribe contar.py: «Alacant/Alicante», «València/Valencia»
        for parte in text.split("/"):
            pc = prov_code(parte)
            if pc:
                return pc
        return None
    n = norm(text)
    if n in PROV_ALIAS:
        return PROV_ALIAS[n]
    for a in ARTICLES:
        if n.startswith(a) and n[len(a):] in PROV_ALIAS:
            return PROV_ALIAS[n[len(a):]]
    munis, provs = load()
    for pid, p in provs.items():
        if n in variants(p["nombre"]):
            return pid
    return None


def find(pueblo: str, provincia: str | None = None):
    """Devuelve (índice del municipio, motivo). índice None si no se reconoce o es ambiguo."""
    munis, _ = load()
    cands = index().get(norm(pueblo), [])
    if not cands and "/" in pueblo:  # «Alcoi/Alcoy»: vale cualquiera de los dos nombres oficiales
        for parte in pueblo.split("/"):
            cands = index().get(norm(parte), [])
            if cands:
                break
    pc = prov_code(provincia) if provincia else None
    if provincia and pc is None:
        return None, f"provincia no reconocida: «{provincia}»"
    if pc:
        cands = [i for i in cands if munis[i]["prov"] == pc]
    if not cands:
        return None, "pueblo no encontrado" + (" en esa provincia" if pc else "")
    if len(cands) > 1:
        return None, "ambiguo: " + ", ".join(f"{munis[i]['nombre']} ({load()[1][munis[i]['prov']]['nombre']})" for i in cands[:6])
    return cands[0], "ok"


if __name__ == "__main__":
    munis, provs = load()
    print(len(munis), "recintos;", sum(m["votable"] for m in munis), "municipios votables;", len(provs), "provincias")
    print("área total", round(sum(m["area"] for m in munis)), "km²")
    for p, q in [("Guadix", "Granada"), ("baza", "granada"), ("Las Rozas de Madrid", "Madrid"), ("san sebastian", "guipuzcoa"),
                 ("Vitoria", "Álava"), ("L'Hospitalet de Llobregat", "Barcelona"), ("Villanueva", None), ("Elche", "Alicante"), ("Xàtiva", "Valencia")]:
        i, why = find(p, q)
        print(f"{p!r:32} {q!r:14} → {munis[i]['nombre'] + ' ' + munis[i]['id'] if i is not None else '—'}  {why}")
