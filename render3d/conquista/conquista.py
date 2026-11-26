"""TU PUEBLO CONQUISTA ESPAÑA · motor de la competición.

Entrada: temporadaN/votos/epNN.csv  (pueblo,provincia,votos) = votos REALES contados en los comentarios del
episodio anterior. ep01.csv va vacío (la serie empieza a cero). Nada se inventa: lo que no se reconoce
se apunta en temporadaN/revisar/epNN.txt y no suma.

Reglas de conquista (deterministas, iguales para todos):
  · Cada voto vale `km2_por_voto` km² de territorio (por defecto 150 km²).
  · Un pueblo con V votos alcanza un radio r = √(V·km2_por_voto / π) alrededor de su municipio.
  · Cada municipio de España pertenece al pueblo que lo alcanza «más holgadamente» (menor distancia/radio):
    si dos pueblos se disputan una zona, la frontera se desplaza hacia el que tiene menos votos.
  · El municipio propio siempre es tuyo mientras tengas al menos 1 voto... salvo que otro pueblo te lo quite
    (si su alcance relativo es mayor). Así hay invasiones de verdad.
  · Dominar una provincia = controlar más del 50 % de su superficie (corona en el mapa).
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import datos  # noqa: E402

PALETA = [(255, 196, 0), (255, 64, 129), (0, 229, 255), (118, 255, 3), (255, 109, 0), (213, 0, 249), (29, 233, 182),
          (255, 23, 68), (41, 121, 255), (255, 234, 0), (0, 230, 118), (245, 0, 87), (101, 31, 255), (255, 145, 0),
          (24, 255, 255), (198, 255, 0), (234, 128, 252), (255, 82, 82), (64, 196, 255), (178, 255, 89)]


def cfg(temporada):
    c = dict(nombre="TU PUEBLO CONQUISTA ESPAÑA", km2_por_voto=150.0, marca="NIVEL OCULTO")
    p = os.path.join(temporada, "config.json")
    if os.path.exists(p):
        c.update(json.load(open(p, encoding="utf-8")))
    return c


def votos_pendientes(temporada, ep):
    """True si los votos de este episodio no se pudieron contar a tiempo (marcador epNN.pendiente).
    No se inventa nada: el episodio sale con el mapa tal como estaba y esos votos se suman en el siguiente."""
    return os.path.exists(os.path.join(temporada, "votos", f"ep{ep:02d}.pendiente")) and \
        not os.path.exists(os.path.join(temporada, "votos", f"ep{ep:02d}.csv"))


def read_votes(temporada, ep):
    """Lee epNN.csv, reconoce cada pueblo y devuelve {índice_municipio: votos} + lista para revisar."""
    path = os.path.join(temporada, "votos", f"ep{ep:02d}.csv")
    votes, review = defaultdict(int), []
    if not os.path.exists(path):
        return votes, review
    for row in csv.DictReader(open(path, encoding="utf-8-sig")):
        p, q = (row.get("pueblo") or "").strip(), (row.get("provincia") or "").strip()
        try:
            v = int(float(row.get("votos") or 0))
        except ValueError:
            review.append(f"{p}, {q}: votos no numéricos «{row.get('votos')}»")
            continue
        if not p or v <= 0:
            continue
        i, why = datos.find(p, q)
        if i is None:
            review.append(f"{p}, {q} ({v} votos): {why}")
            continue
        votes[i] += v
    return votes, review


_geo = None


def geo():
    """Centroides en km (proyección local) y áreas, en arrays."""
    global _geo
    if _geo is None:
        munis, provs = datos.load()
        lon = np.array([m["lon"] for m in munis])
        lat = np.array([m["lat"] for m in munis])
        x = lon * 111.32 * np.cos(np.radians(40.0))
        y = lat * 110.57
        area = np.array([m["area"] for m in munis])
        prov = np.array([m["prov"] for m in munis])
        _geo = dict(x=x, y=y, area=area, prov=prov, munis=munis, provs=provs)
    return _geo


def territory(totals: dict, km2: float, order: list):
    """owner[m] = índice del pueblo (en `order`) dueño del municipio m, o -1."""
    g = geo()
    n = len(g["x"])
    owner = -np.ones(n, int)
    best = np.full(n, np.inf)
    for k, t in enumerate(order):
        v = totals.get(t, 0)
        if v <= 0:
            continue
        r = math.sqrt(v * km2 / math.pi)
        d = np.hypot(g["x"] - g["x"][t], g["y"] - g["y"][t])
        rel = d / r
        rel[t] = min(rel[t], 0.0)  # su propio municipio: máxima prioridad para él
        take = (rel <= 1.0) & (rel < best)
        owner[take] = k
        best[take] = rel[take]
    return owner


_adj = None


def adjacency():
    """Vecinos de cada municipio (comparten un arco en el TopoJSON)."""
    global _adj
    if _adj is None:
        topo = json.load(open(datos.TOPO, encoding="utf-8"))
        munis, _ = datos.load()
        pos = {m["id"]: i for i, m in enumerate(munis)}
        arc_owner = defaultdict(set)

        def walk(a, i):
            if isinstance(a, int):
                arc_owner[a if a >= 0 else ~a].add(i)
            else:
                for b in a:
                    walk(b, i)
        for g in topo["objects"]["municipalities"]["geometries"]:
            if g["id"] in pos:
                walk(g["arcs"], pos[g["id"]])
        _adj = defaultdict(set)
        for s in arc_owner.values():
            for a in s:
                _adj[a] |= s - {a}
    return _adj


def estado(temporada, ep):
    """Estado completo de la competición en el episodio `ep` (y el del anterior para comparar)."""
    c = cfg(temporada)
    km2 = c["km2_por_voto"]
    g = geo()
    munis, provs = g["munis"], g["provs"]
    totals, first_seen, history, review = defaultdict(int), {}, [], {}
    for e in range(1, ep + 1):
        v, rv = read_votes(temporada, e)
        review[e] = rv
        prev_totals = dict(totals)
        for t, n in v.items():
            totals[t] += n
            first_seen.setdefault(t, e)
        history.append((dict(prev_totals), dict(totals)))
    prev, cur = history[-1] if history else ({}, {})
    # orden estable: primero quien llegó antes; colores fijos para toda la temporada
    order = sorted(cur, key=lambda t: (first_seen[t], munis[t]["id"]))
    color = {t: PALETA[k % len(PALETA)] for k, t in enumerate(order)}
    own_prev = territory(prev, km2, order)
    own_cur = territory(cur, km2, order)

    def rank(tot):
        """Ranking con empates compartidos (1, 2, 2, 2…): mismo nº de votos = mismo puesto."""
        vals = sorted((v for v in tot.values() if v > 0), reverse=True)
        return {t: 1 + sum(1 for x in vals if x > tot[t]) for t in tot if tot[t] > 0}
    r_prev, r_cur = rank(prev), rank(cur)
    pueblos = []
    for k, t in enumerate(order):
        mine = own_cur == k
        area = float(g["area"][mine].sum())
        dom = []
        for pid, p in provs.items():
            pa = g["area"][g["prov"] == pid].sum()
            if pa > 0 and g["area"][mine & (g["prov"] == pid)].sum() > 0.5 * pa:
                dom.append(p["nombre"])
        pueblos.append(dict(idx=int(t), id=munis[t]["id"], nombre=munis[t]["nombre"], provincia=provs[munis[t]["prov"]]["nombre"],
                            votos=int(cur.get(t, 0)), votos_antes=int(prev.get(t, 0)), nuevo=t not in prev,
                            puesto=r_cur.get(t), puesto_antes=r_prev.get(t), color=color[t], km2=round(area),
                            municipios=int(mine.sum()), domina=dom, lon=munis[t]["lon"], lat=munis[t]["lat"]))
    # invasiones: municipios que cambian de un pueblo a otro
    inv = defaultdict(int)
    for m in np.where((own_prev >= 0) & (own_cur >= 0) & (own_prev != own_cur))[0]:
        inv[(int(order[own_cur[m]]), int(order[own_prev[m]]))] += 1
    # rivalidades: territorios que se tocan (o misma provincia), ordenados por igualdad de votos
    adj = adjacency()
    touching = set()
    for m in np.where(own_cur >= 0)[0]:
        for nb in adj.get(int(m), ()):
            if own_cur[nb] >= 0 and own_cur[nb] != own_cur[m]:
                a, b = sorted((int(order[own_cur[m]]), int(order[own_cur[nb]])))
                touching.add((a, b))
    byid = {p["idx"]: p for p in pueblos}
    pairs = set(touching)
    for a in byid:
        for b in byid:
            if a < b and byid[a]["provincia"] == byid[b]["provincia"]:
                pairs.add((a, b))
    riv = sorted(pairs, key=lambda ab: (ab not in touching,  # primero los que comparten frontera
                                        abs(byid[ab[0]]["votos"] - byid[ab[1]]["votos"]) / max(1, byid[ab[0]]["votos"] + byid[ab[1]]["votos"]),
                                        -(byid[ab[0]]["votos"] + byid[ab[1]]["votos"])))
    total_area = float(g["area"].sum())
    return dict(
        temporada=os.path.basename(os.path.abspath(temporada)), episodio=ep, config=c,
        pueblos=sorted(pueblos, key=lambda p: (p["puesto"] or 1e9, datos.norm(p["nombre"]))),  # empates: orden alfabético
        votos_total=int(sum(cur.values())), votos_nuevos=int(sum(cur.values()) - sum(prev.values())),
        conquistado=round(100 * float(g["area"][own_cur >= 0].sum()) / total_area, 2),
        conquistado_antes=round(100 * float(g["area"][own_prev >= 0].sum()) / total_area, 2),
        invasiones=[dict(atacante=a, defensor=d, municipios=n) for (a, d), n in sorted(inv.items(), key=lambda kv: -kv[1])],
        rivalidades=[dict(a=a, b=b, frontera=(a, b) in touching) for a, b in riv[:5]],
        revisar=review.get(ep, []),
        votos_pendientes=votos_pendientes(temporada, ep),
        _owner_prev=own_prev, _owner_cur=own_cur, _order=order,
    )


def resumen(st):
    out = [f"EPISODIO {st['episodio']} · {st['votos_total']} votos ({st['votos_nuevos']} nuevos) · {len(st['pueblos'])} pueblos · "
           f"{st['conquistado']}% de España conquistado"]
    for p in st["pueblos"][:10]:
        mv = "NUEVO" if p["nuevo"] else (f"{p['puesto_antes'] - p['puesto']:+d}" if p["puesto_antes"] else "")
        out.append(f"  {p['puesto']:>2}. {p['nombre']} ({p['provincia']}) {p['votos']} votos · {p['km2']} km² · {p['municipios']} municipios {mv}"
                   + (f" · domina {', '.join(p['domina'])}" if p["domina"] else ""))
    for r in st["revisar"]:
        out.append("  ⚠ revisar: " + r)
    return "\n".join(out)


if __name__ == "__main__":
    t, ep = sys.argv[1], int(sys.argv[2])
    print(resumen(estado(t, ep)))
