"""NIVEL OCULTO · Física «satisfying» en arena circular (formatos virales).

Modos (campo "modo" del archivo de reglas):
  batalla   bolas de colores que se conquistan al chocar; engranaje con brazo giratorio; gana un color
  crece     una bola que crece con cada rebote hasta llenar el círculo
  anillos   anillos concéntricos que giran con un hueco; cada anillo que atraviesa la bola, explota
  multiplica  +1 bola cada N rebotes contra la pared, hasta llenar el círculo
  ppt       piedra, papel o tijera: tres equipos que se convierten al chocar hasta que queda uno

Física 2D propia (NumPy/SciPy): gravedad, choques elásticos (impulso + corrección de solapes), pared circular,
brazos giratorios (cápsulas con velocidad de superficie) y anillos con hueco. Varios subpasos por fotograma.
Sonido sintetizado con cada choque (sim.synth_audio).  Uso:  python arena.py reglas/x.json --out x.mp4 [--stats]
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import SR, W, H, SS, font, synth_audio  # noqa: E402

TEAMS = [(235, 50, 60), (40, 110, 240), (80, 220, 70), (250, 200, 30), (190, 60, 230), (30, 210, 210)]
TEAM_NAMES = ["ROJO", "AZUL", "VERDE", "AMARILLO", "MORADO", "TURQUESA"]
PPT = ["PIEDRA", "PAPEL", "TIJERA"]


class Rules:
    defaults = dict(modo="batalla", titulo="", etiqueta="", duracion=60.0, fps=60, subpasos=4, semilla=1, centro=[540.0, 1060.0],
                    radio_arena=440.0, gravedad=0.0, rebote=1.0, radio=12.0, velocidad=500.0, velocidad_max=1600.0,
                    max_bolas=600, equipos=4, iniciales=6, brazo=True, giro_brazo=1.3, rebotes_por_bola=10, crecer=3.0,
                    anillos=8, hueco=48.0, marca="NIVEL OCULTO", ventaja_mayoria=1.0, reproducir=0.35, contagio=0.2)

    def __init__(self, path=None, **over):
        d = dict(self.defaults)
        if path:
            d.update(json.load(open(path, encoding="utf-8")))
        d.update({k: v for k, v in over.items() if v is not None})
        self.__dict__.update(d)


class Arena:
    def __init__(self, R: Rules):
        self.R = R
        self.rng = np.random.default_rng(R.semilla)
        n = R.max_bolas + 50
        self.pos = np.zeros((n, 2))
        self.vel = np.zeros((n, 2))
        self.rad = np.full(n, float(R.radio))
        self.team = np.zeros(n, int)
        self.alive = np.zeros(n, bool)
        self.cool = np.zeros(n)
        self.nb = np.zeros(n, int)
        self.t = 0.0
        self.events = []
        self.bounces = 0
        self.arm_angle = 0.0
        self.c = np.array(R.centro, float)
        self.winner = None
        self.win_t = None
        self.particles = []  # (x, y, vx, vy, vida, color)
        self.rings = []
        self.escaped = False
        m = R.modo
        if m == "batalla":
            for k in range(R.equipos):
                for _ in range(R.iniciales):
                    self.add(self.random_point(), k)
        elif m == "ppt":
            for k in range(3):
                ang0 = k * 2 * math.pi / 3
                for _ in range(R.iniciales):
                    p = self.c + np.array([math.cos(ang0), math.sin(ang0)]) * R.radio_arena * 0.55 + self.rng.normal(0, 60, 2)
                    self.add(p, k)
        elif m in ("crece", "anillos"):
            self.add(self.c + np.array([0.0, -40.0 if m == "crece" else 0.0]), 0)
            if m == "anillos":
                for i in range(R.anillos):
                    rr = 90 + i * (R.radio_arena - 90) / max(1, R.anillos - 1)
                    self.rings.append(dict(r=rr, ang=self.rng.uniform(0, 2 * math.pi), w=(0.9 + 0.12 * i) * (1 if i % 2 else -1),
                                           hue=(i / R.anillos), alive=True))
        else:  # multiplica
            for k in range(R.iniciales):
                self.add(self.random_point(), k % len(TEAMS))

    def random_point(self):
        a = self.rng.uniform(0, 2 * math.pi)
        r = self.R.radio_arena * math.sqrt(self.rng.uniform(0.15, 0.8))
        return self.c + np.array([math.cos(a), math.sin(a)]) * r

    def add(self, p, team, v=None):
        free = np.where(~self.alive)[0]
        if len(free) == 0:
            return None
        i = free[0]
        a = self.rng.uniform(0, 2 * math.pi)
        self.pos[i] = p
        self.vel[i] = v if v is not None else np.array([math.cos(a), math.sin(a)]) * self.R.velocidad
        self.team[i] = team
        self.alive[i] = True
        self.cool[i] = 0.3
        self.nb[i] = 0
        return i

    @property
    def count(self):
        return int(self.alive.sum())

    def team_counts(self, k):
        return [int((self.alive & (self.team == i)).sum()) for i in range(k)]

    # ───── brazo giratorio (como el engranaje del vídeo de referencia) ─────
    def arm_pts(self):
        """Brazo curvo en forma de gancho que gira alrededor del centro."""
        pts = []
        a0 = self.arm_angle
        for j in range(15):
            u = j / 14
            ang = a0 + math.pi * 1.15 * u
            rr = 150 * (0.35 + 0.65 * math.sin(math.pi * u * 0.5 + 0.3))
            pts.append(self.c + np.array([math.cos(ang), math.sin(ang)]) * rr)
        return pts

    def collide_arm(self, idx):
        R = self.R
        w = R.giro_brazo
        pts = self.arm_pts()
        thick = 14.0
        for a, b in zip(pts[:-1], pts[1:]):
            ab = b - a
            L2 = ab @ ab
            p = self.pos[idx]
            tt = np.clip(((p - a) @ ab) / L2, 0, 1)
            q = a + tt[:, None] * ab
            d = p - q
            dist = np.hypot(d[:, 0], d[:, 1])
            hit = dist < self.rad[idx] + thick
            if not hit.any():
                continue
            ii = idx[hit]
            n = d[hit] / np.maximum(dist[hit], 1e-6)[:, None]
            self.pos[ii] = q[hit] + n * (self.rad[ii] + thick)[:, None]
            rq = q[hit] - self.c
            vw = np.stack([-rq[:, 1], rq[:, 0]], 1) * w  # velocidad de la superficie del brazo
            rel = self.vel[ii] - vw
            vn = np.sum(rel * n, 1)
            ap = vn < 0
            self.vel[ii[ap]] -= ((1 + R.rebote) * vn[ap])[:, None] * n[ap]
            for j in ii[ap][:2]:
                self.events.append((self.t, "obstaculo", 0.7, int(self.team[j])))
        # el engranaje del centro
        d = self.pos[idx] - self.c
        dist = np.hypot(d[:, 0], d[:, 1])
        hit = dist < self.rad[idx] + 34
        if hit.any():
            ii = idx[hit]
            n = d[hit] / np.maximum(dist[hit], 1e-6)[:, None]
            self.pos[ii] = self.c + n * (self.rad[ii] + 34)[:, None]
            vn = np.sum(self.vel[ii] * n, 1)
            ap = vn < 0
            self.vel[ii[ap]] -= ((1 + R.rebote) * vn[ap])[:, None] * n[ap]

    # ───── paso ─────
    def step(self, dt):
        R = self.R
        idx = np.where(self.alive)[0]
        self.cool[idx] -= dt
        self.vel[idx, 1] += R.gravedad * dt
        if R.modo in ("batalla", "ppt"):  # velocidad casi constante: siempre en movimiento
            sp = np.hypot(self.vel[idx, 0], self.vel[idx, 1])
            self.vel[idx] *= (1 + 0.02 * (R.velocidad / np.maximum(sp, 1) - 1))[:, None]
        sp = np.hypot(self.vel[idx, 0], self.vel[idx, 1])
        self.vel[idx] *= np.minimum(1, R.velocidad_max / np.maximum(sp, 1e-6))[:, None]
        self.pos[idx] += self.vel[idx] * dt
        self.arm_angle += R.giro_brazo * dt
        for ring in self.rings:
            ring["ang"] += ring["w"] * dt
        iters = 1 if len(idx) < 150 else 3
        allp = []
        for _ in range(iters):
            allp.append(self.collide_pairs(idx))
            if R.brazo and R.modo == "batalla":
                self.collide_arm(idx)
            self.collide_wall(idx)
        if self.rings:
            self.collide_rings(idx)
        pairs = np.unique(np.concatenate(allp), axis=0) if any(len(p) for p in allp) else np.zeros((0, 2), int)
        self.rules(idx, pairs)
        # partículas
        np_ = []
        for (x, y, vx, vy, life, col) in self.particles:
            life -= dt
            if life > 0:
                np_.append((x + vx * dt, y + vy * dt, vx * 0.99, vy * 0.99 + 400 * dt, life, col))
        self.particles = np_
        self.t += dt

    def collide_wall(self, idx):
        R = self.R
        if self.R.modo == "anillos":
            return
        d = self.pos[idx] - self.c
        dist = np.hypot(d[:, 0], d[:, 1])
        lim = R.radio_arena - self.rad[idx]
        hit = dist > lim
        if not hit.any():
            return
        ii = idx[hit]
        n = d[hit] / np.maximum(dist[hit], 1e-6)[:, None]
        self.pos[ii] = self.c + n * lim[hit][:, None]
        vn = np.sum(self.vel[ii] * n, 1)
        ap = vn > 0
        self.vel[ii[ap]] -= ((1 + R.rebote) * vn[ap])[:, None] * n[ap]
        for j in ii[ap]:
            self.on_wall(j, float(min(1, vn[ap][list(ii[ap]).index(j)] / 1200)) if False else 0.8)

    def collide_pairs(self, idx):
        if len(idx) < 2:
            return np.zeros((0, 2), int)
        R = self.R
        p = self.pos[idx]
        if len(idx) <= 200:
            d = p[:, None, :] - p[None, :, :]
            dist = np.hypot(d[..., 0], d[..., 1])
            rs = self.rad[idx][:, None] + self.rad[idx][None, :]
            ii, jj = np.where(np.triu(dist < rs, 1))
        else:
            from scipy.spatial import cKDTree
            pr = cKDTree(p).query_pairs(2 * float(self.rad[idx].max()), output_type="ndarray")
            if len(pr) == 0:
                return np.zeros((0, 2), int)
            ii, jj = pr[:, 0], pr[:, 1]
            dv = p[ii] - p[jj]
            ok = np.hypot(dv[:, 0], dv[:, 1]) < self.rad[idx][ii] + self.rad[idx][jj]
            ii, jj = ii[ok], jj[ok]
        if len(ii) == 0:
            return np.zeros((0, 2), int)
        a, b = idx[ii], idx[jj]
        dv = self.pos[a] - self.pos[b]
        dist = np.maximum(np.hypot(dv[:, 0], dv[:, 1]), 1e-6)
        n = dv / dist[:, None]
        pen = self.rad[a] + self.rad[b] - dist
        corr = n * (pen / 2)[:, None]
        np.add.at(self.pos, a, corr)
        np.add.at(self.pos, b, -corr)
        rv = np.sum((self.vel[a] - self.vel[b]) * n, 1)
        ap = rv < 0
        imp = (-(1 + R.rebote) * rv / 2)[ap][:, None] * n[ap]
        np.add.at(self.vel, a[ap], imp)
        np.add.at(self.vel, b[ap], -imp)
        return np.stack([a[ap], b[ap]], 1)

    def collide_rings(self, idx):
        R = self.R
        for ring in self.rings:
            if not ring["alive"]:
                continue
            d = self.pos[idx] - self.c
            dist = np.hypot(d[:, 0], d[:, 1])
            ang = np.arctan2(d[:, 1], d[:, 0])
            rel = (ang - ring["ang"] + math.pi) % (2 * math.pi) - math.pi
            half = math.radians(R.hueco) / 2
            in_gap = np.abs(rel) < half - self.rad[idx] / ring["r"]
            near = (dist + self.rad[idx] > ring["r"] - 6) & (dist < ring["r"])
            hit = near & ~in_gap
            if hit.any():
                ii = idx[hit]
                n = d[hit] / np.maximum(dist[hit], 1e-6)[:, None]
                self.pos[ii] = self.c + n * (ring["r"] - 6 - self.rad[ii])[:, None]
                vn = np.sum(self.vel[ii] * n, 1)
                ap = vn > 0
                self.vel[ii[ap]] -= ((1 + R.rebote) * vn[ap])[:, None] * n[ap]
                for _ in ii[ap][:1]:
                    self.bounces += 1
                    self.events.append((self.t, "pared", 0.8, int(ring["hue"] * 10) + 5))
            if (dist > ring["r"] + 4).any():  # la bola ha cruzado el hueco: el anillo explota
                ring["alive"] = False
                self.events.append((self.t, "escape", 1.0, int(ring["hue"] * 10) + 5))
                col = rgbh(ring["hue"])
                for k in range(80):
                    a = self.rng.uniform(0, 2 * math.pi)
                    x, y = self.c + np.array([math.cos(a), math.sin(a)]) * ring["r"]
                    s = self.rng.uniform(80, 400)
                    self.particles.append((x, y, math.cos(a) * s, math.sin(a) * s, self.rng.uniform(0.5, 1.2), col))
        if all(not r["alive"] for r in self.rings) and not self.escaped:
            self.escaped = True
            self.win_t = self.t

    # ───── reglas de cada modo ─────
    def on_wall(self, j, inten):
        R = self.R
        self.bounces += 1
        m = R.modo
        if m == "crece":
            self.rad[j] = min(R.radio_arena * 0.985, self.rad[j] + R.crecer)
            self.events.append((self.t, "pared", 1.0, self.bounces))
            if self.rad[j] >= R.radio_arena * 0.98 and self.win_t is None:
                self.win_t = self.t
                self.events.append((self.t, "escape", 1.0, 10))
        elif m == "multiplica":
            self.events.append((self.t, "pared", inten, int(self.team[j]) + (self.bounces % 3) * 5))
            self.nb[j] += 1
            if self.nb[j] % R.rebotes_por_bola == 0 and self.count < R.max_bolas:
                v = self.vel[j] @ np.array([[0.8, -0.6], [0.6, 0.8]])
                k = self.add(self.pos[j] - (self.pos[j] - self.c) * 0.05, int(self.rng.integers(0, len(TEAMS))), v)
                if k is not None:
                    self.events.append((self.t, "spawn", 0.6, 0))
                if self.count >= R.max_bolas and self.win_t is None:
                    self.win_t = self.t
                    self.events.append((self.t, "escape", 1.0, 10))
        else:
            if self.rng.random() < 0.15:
                self.events.append((self.t, "pared", 0.4, int(self.team[j])))

    def rules(self, idx, pairs):
        R = self.R
        m = R.modo
        if m not in ("batalla", "ppt") or self.winner is not None:
            return
        for a, b in pairs:
            ta, tb = self.team[a], self.team[b]
            if ta == tb:
                if m == "batalla" and self.count < R.max_bolas and self.cool[a] <= 0 and self.cool[b] <= 0 and self.rng.random() < R.reproducir:
                    k = self.add((self.pos[a] + self.pos[b]) / 2 + self.rng.normal(0, 4, 2), ta)
                    self.cool[a] = self.cool[b] = 1.2
                    if k is not None:
                        self.events.append((self.t, "spawn", 0.4, int(ta)))
                continue
            if self.rng.random() > R.contagio or self.cool[a] > 0 or self.cool[b] > 0:
                continue
            if m == "ppt":  # piedra(0) > tijera(2) > papel(1) > piedra(0)
                win = ta if (ta - tb) % 3 == 2 else tb
            else:  # el equipo más grande tiene ventaja (efecto bola de nieve, así siempre hay un ganador)
                ca, cb = (self.alive & (self.team == ta)).sum(), (self.alive & (self.team == tb)).sum()
                pa = ca ** R.ventaja_mayoria / (ca ** R.ventaja_mayoria + cb ** R.ventaja_mayoria)
                win = ta if self.rng.random() < pa else tb
            lose = b if win == ta else a
            self.team[lose] = win
            self.cool[lose] = 0.5
            self.events.append((self.t, "choque", 0.8, int(win)))
        k = R.equipos if m == "batalla" else 3
        cnt = self.team_counts(k)
        alive_teams = [i for i, c in enumerate(cnt) if c > 0]
        if len(alive_teams) == 1 and self.count > 1:
            self.winner = alive_teams[0]
            self.win_t = self.t
            self.events.append((self.t, "escape", 1.0, 0))


def rgbh(h, s=0.8, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


# ───── dibujo ─────
class Painter:
    def __init__(self, A: Arena):
        self.A = A
        self.cache = {}

    def ball(self, col, r):
        key = (col, int(r))
        if key not in self.cache:
            rr = max(2, int(r * SS))
            n = rr * 2 + 2
            yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
            dx, dy = (xx - n / 2) / rr, (yy - n / 2) / rr
            d2 = dx * dx + dy * dy
            inside = d2 <= 1
            z = np.sqrt(np.clip(1 - d2, 0, 1))
            light = np.clip(0.35 + 0.75 * (z * 0.7 - dx * 0.35 - dy * 0.45), 0.25, 1.15)
            spec = np.clip((1 - ((dx + 0.35) ** 2 + (dy + 0.4) ** 2) / 0.09), 0, 1) ** 2
            rgb = np.array(col, np.float32)[None, None, :] * light[..., None] + 255 * spec[..., None] * 0.8
            a = np.zeros((n, n, 4), np.uint8)
            a[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
            edge = np.clip((1 - np.sqrt(d2)) * rr, 0, 1)
            a[..., 3] = (inside * edge * 255).astype(np.uint8)
            self.cache[key] = Image.fromarray(a)
            if len(self.cache) > 4000:
                self.cache.clear()
        return self.cache[key]

    def ppt_icon(self, d, k, x, y, r):
        s = SS
        if k == 0:  # piedra
            pts = [(x + math.cos(a) * r * (0.85 + 0.15 * math.sin(a * 3)), y + math.sin(a) * r * (0.8 + 0.15 * math.cos(a * 2))) for a in np.linspace(0, 2 * math.pi, 9)]
            d.polygon([(px * s, py * s) for px, py in pts], fill=(150, 150, 160), outline=(90, 90, 100))
        elif k == 1:  # papel
            d.rectangle([(x - r * 0.75) * s, (y - r) * s, (x + r * 0.75) * s, (y + r) * s], fill=(245, 245, 250), outline=(160, 160, 170))
            for j in range(3):
                yy = y - r * 0.5 + j * r * 0.45
                d.line([((x - r * 0.45) * s, yy * s), ((x + r * 0.45) * s, yy * s)], fill=(120, 150, 210), width=max(1, int(s)))
        else:  # tijera
            for sx in (-1, 1):
                d.ellipse([(x + sx * r * 0.45 - r * 0.35) * s, (y + r * 0.25) * s, (x + sx * r * 0.45 + r * 0.35) * s, (y + r * 0.95) * s],
                          outline=(235, 60, 70), width=int(3 * s))
                d.line([((x + sx * r * 0.35) * s, (y + r * 0.3) * s), ((x - sx * r * 0.4) * s, (y - r) * s)], fill=(200, 205, 215), width=int(4 * s))

    def frame(self, pulse):
        A, R = self.A, self.A.R
        big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 255))
        d = ImageDraw.Draw(big)
        cx, cy = A.c
        RA = R.radio_arena
        if R.modo != "anillos":
            d.ellipse([(cx - RA - 4) * SS, (cy - RA - 4) * SS, (cx + RA + 4) * SS, (cy + RA + 4) * SS], outline=(255, 255, 255), width=5 * SS)
        for ring in A.rings:  # anillos con hueco
            if not ring["alive"]:
                continue
            r = ring["r"]
            g0 = math.degrees(ring["ang"]) + R.hueco / 2
            d.arc([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], g0, g0 + 360 - R.hueco, fill=rgbh(ring["hue"]), width=10 * SS)
        if R.brazo and R.modo == "batalla":  # brazo y engranaje
            pts = A.arm_pts()
            d.line([(p[0] * SS, p[1] * SS) for p in pts], fill=(150, 150, 160), width=28 * SS, joint="curve")
            d.line([(p[0] * SS, p[1] * SS) for p in pts], fill=(185, 185, 195), width=14 * SS, joint="curve")
            teeth = []
            for k in range(24):
                a = A.arm_angle * 1.6 + k * math.pi / 12
                rr = 34 if k % 2 == 0 else 26
                teeth.append(((cx + math.cos(a) * rr) * SS, (cy + math.sin(a) * rr) * SS))
            d.polygon(teeth, fill=(215, 215, 225))
            d.ellipse([(cx - 10) * SS, (cy - 10) * SS, (cx + 10) * SS, (cy + 10) * SS], fill=(120, 120, 130))
        idx = np.where(A.alive)[0]
        for i in idx:
            x, y = A.pos[i]
            r = A.rad[i]
            if R.modo == "ppt":
                self.ppt_icon(d, A.team[i], x, y, r * 1.25)
                continue
            col = TEAMS[A.team[i] % len(TEAMS)] if R.modo != "crece" else rgbh(0.95 - 0.8 * r / RA)
            spr = self.ball(col, r)
            big.alpha_composite(spr, (int(x * SS - spr.width / 2), int(y * SS - spr.height / 2)))
        for (x, y, vx, vy, life, col) in A.particles:
            rr = 4 * life + 1
            d.ellipse([(x - rr) * SS, (y - rr) * SS, (x + rr) * SS, (y + rr) * SS], fill=col)
        img = big.convert("RGB").reduce(SS)
        dd = ImageDraw.Draw(img)
        self.hud(dd, pulse)
        if R.marca:
            dd.text((540, 1800), " ".join(R.marca), font=font("ExtraBold", 30), fill=(120, 120, 130), anchor="mm")
        return img

    def hud(self, dd, pulse):
        A, R = self.A, self.A.R
        dd.text((540, 215), R.titulo, font=font("ExtraBold", 62), fill=(255, 255, 255), anchor="mm")
        m = R.modo
        if m in ("batalla", "ppt"):
            k = R.equipos if m == "batalla" else 3
            cnt = A.team_counts(k)
            tot = max(1, sum(cnt))
            x = 90
            for i, c in enumerate(cnt):  # barra de reparto
                w_ = 900 * c / tot
                dd.rectangle([x, 300, x + w_, 340], fill=TEAMS[i] if m == "batalla" else [(150, 150, 160), (235, 235, 240), (235, 60, 70)][i])
                x += w_
            for i, c in enumerate(cnt):
                name = TEAM_NAMES[i] if m == "batalla" else PPT[i]
                xx = 540 + (i - (k - 1) / 2) * (900 / k)
                dd.text((xx, 395), f"{c}", font=font("ExtraBold", 54), fill=TEAMS[i] if m == "batalla" else (235, 235, 240), anchor="mm")
                dd.text((xx, 445), name, font=font("Bold", 26), fill=(170, 170, 180), anchor="mm")
            if A.winner is not None:
                name = TEAM_NAMES[A.winner] if m == "batalla" else PPT[A.winner]
                dd.text((540, 1640), f"¡GANA {'EL ' if m == 'batalla' else 'LA ' if A.winner in (0, 2) else 'EL '}{name}!", font=font("ExtraBold", 80),
                        fill=TEAMS[A.winner] if m == "batalla" else (255, 214, 70), anchor="mm")
        else:
            val = {"crece": A.bounces, "anillos": sum(1 for r in A.rings if r["alive"]), "multiplica": A.count}[m]
            s = 1 + 0.18 * pulse
            dd.text((540, 380), f"{val}", font=font("ExtraBold", int(140 * s)), fill=(255, 214, 70), anchor="mm")
            dd.text((540, 480), R.etiqueta, font=font("Bold", 38), fill=(200, 200, 210), anchor="mm")
            if A.win_t is not None:
                txt = {"crece": "¡LLENO!", "anillos": "¡LIBRE!", "multiplica": "¡LLENO!"}[m]
                dd.text((540, 1640), txt, font=font("ExtraBold", 96), fill=(255, 214, 70), anchor="mm")


def run(path, out=None, stats=False, seconds=None):
    R = Rules(path)
    if seconds:
        R.duracion = seconds
    A = Arena(R)
    frames = int(R.duracion * R.fps)
    dt = 1 / (R.fps * R.subpasos)
    P = Painter(A) if out else None
    proc = None
    if out:
        tmp = os.path.splitext(out)[0] + "_video.mp4"
        proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(R.fps),
                                 "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "6M", "-bufsize", "12M",
                                 "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    last, pulse, log, t0 = None, 0.0, [], time.time()
    for f in range(frames):
        for _ in range(R.subpasos):
            A.step(dt)
        key = (A.count, A.bounces if R.modo == "crece" else 0, sum(r["alive"] for r in A.rings))
        if key != last:
            pulse, last = 1.0, key
        pulse *= 0.85
        if f % R.fps == 0:
            info = A.team_counts(R.equipos if R.modo == "batalla" else 3) if R.modo in ("batalla", "ppt") else A.count
            log.append((f // R.fps, info, A.bounces, sum(r["alive"] for r in A.rings), A.win_t))
            if stats or f % (R.fps * 10) == 0:
                print(f"[arena:{R.modo}] t={f / R.fps:4.0f}s  {info}  rebotes={A.bounces}  anillos={sum(r['alive'] for r in A.rings)}  "
                      f"fin={A.win_t}  ({time.time() - t0:.0f}s)", flush=True)
        if proc:
            proc.stdin.write(P.frame(pulse).tobytes())
    if proc:
        proc.stdin.close()
        proc.wait()
        wav = os.path.splitext(out)[0] + "_audio.wav"
        synth_audio(A.events, R.duracion, wav)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-movflags", "+faststart", "-shortest", out], check=True)
        os.remove(tmp)
        os.remove(wav)
        print("✅ Vídeo listo:", out, flush=True)
    return log, A


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("reglas")
    ap.add_argument("--out")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--segundos", type=float)
    a = ap.parse_args()
    run(a.reglas, a.out, a.stats, a.segundos)
