"""NIVEL OCULTO · «El espantapájaros» — cortometraje emotivo sin voz (≈71 s, 1080×1920), música de piano propia.

Estructura (la de los cortos virales de sacrificio): gancho con la imagen más dura → planteamiento (otoño: un petirrojo
herido cae a sus pies) → entrega progresiva (sombrero, bufanda, abrigo, su propia paja) → la noche más fría →
pérdida (primavera: se queda vacío y el pájaro se va) → giro (vuelve con su bandada y lo reconstruyen con flores) →
mensaje y pregunta para comentarios. Historia original; textos mínimos para verlo sin sonido.

    python3 espantapajaros.py salida.mp4            → vídeo completo
    python3 espantapajaros.py frames dir t1 t2 ...  → fotogramas de prueba
"""
from __future__ import annotations

import json
import math
import os
import random
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, S = 1080, 1920, 2
FPS, DUR = 30, 71.0
SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
ANTON = os.path.join(HERE, "..", "assets", "fonts", "Anton-Regular.ttf")
_F = {}

HORIZON, GROUND_Y = 1250, 1400
BIRD_G = 1322             # donde cae el pájaro (dentro de la zona segura con el zoom)
ZOOM = 1.2
PIV = (540, 930)            # cuello
BAR_Y = 950
NEST = (800, 925)           # sombrero-nido sobre el brazo derecho
INK = (40, 30, 30)
STRAW, STRAW_D = (238, 200, 92), (196, 152, 60)
SACK = (222, 192, 138)
SHIRT, COAT, HATC = (112, 138, 88), (156, 62, 50), (226, 186, 96)


def font(size, sc=S):
    size = int(size * sc)
    if sc != S:
        if ("n", size) not in _F:
            _F[("n", size)] = ImageFont.truetype(ANTON, size)
        return _F[("n", size)]
    if size not in _F:
        _F[size] = ImageFont.truetype(ANTON, size)
    return _F[size]


def cl(x):
    return max(0.0, min(1.0, x))


def k(t, a, b):
    x = cl((t - a) / (b - a))
    return x * x * (3 - 2 * x)


def lerp(a, b, x):
    return a + (b - a) * x


def mixc(c1, c2, x):
    return tuple(int(lerp(a, b, x)) for a, b in zip(c1, c2))


def rot(px, py, cx, cy, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    dx, dy = px - cx, py - cy
    return cx + dx * ca - dy * sa, cy + dx * sa + dy * ca


# ───── dibujo con escala S ─────
class Pen:
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img)

    def E(self, x, y, rx, ry, fill, ol=None, w=0):
        if rx <= 0 or ry <= 0:
            return
        self.d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S], fill=fill, outline=ol, width=int(w * S))

    def P(self, pts, fill, ol=None, w=0):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
        if ol and w:
            self.d.line([(x * S, y * S) for x, y in pts + [pts[0]]], fill=ol, width=int(w * S), joint="curve")

    def L(self, pts, col, w):
        self.d.line([(x * S, y * S) for x, y in pts], fill=col, width=max(1, int(w * S)), joint="curve")

    def R(self, x0, y0, x1, y1, fill, r=0, ol=None, w=0):
        self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=int(r * S), fill=fill, outline=ol, width=int(w * S))

    def text(self, x, y, s, size, col=(255, 255, 255), stroke=7, alpha=1.0):
        if alpha <= 0.01:
            return
        lay = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((x * S, y * S), s, font=font(size), fill=col + (255,), anchor="mm", stroke_width=int(stroke * S),
                                 stroke_fill=(25, 20, 30, 255))
        if alpha < 1:
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
        self.img.alpha_composite(lay)


# ───── fondos por estación (precalculados) ─────
SEASONS = {
    "otono": dict(sky=((248, 158, 86), (255, 222, 160)), hill=(186, 112, 66), hill2=(214, 140, 74), ground=(214, 162, 74), det=(180, 126, 50)),
    "invierno": dict(sky=((120, 140, 182), (202, 212, 230)), hill=(196, 206, 228), hill2=(220, 228, 242), ground=(236, 241, 248), det=(205, 214, 232)),
    "noche": dict(sky=((16, 20, 44), (54, 62, 104)), hill=(70, 80, 120), hill2=(96, 106, 146), ground=(170, 180, 212), det=(140, 150, 186)),
    "primavera": dict(sky=((110, 186, 250), (222, 242, 255)), hill=(92, 162, 84), hill2=(120, 190, 96), ground=(122, 192, 92), det=(96, 160, 72)),
}
_BG = {}


def background(name):
    if name in _BG:
        return _BG[name]
    c = SEASONS[name]
    img = Image.new("RGBA", (W * S, H * S))
    p = Pen(img)
    top, bot = c["sky"]
    for y in range(0, HORIZON + 10, 4):
        p.R(0, y, W, y + 4, mixc(top, bot, y / HORIZON))
    r = random.Random(4)
    if name == "noche":
        for _ in range(120):
            x, y = r.uniform(0, W), r.uniform(0, 1000)
            p.E(x, y, 2, 2, (230, 236, 255))
        p.E(820, 330, 70, 70, (246, 244, 226))
        p.E(845, 315, 62, 62, top)
    if name in ("otono", "primavera"):
        p.E(250 if name == "otono" else 840, 360, 90, 90, (255, 236, 170) if name == "otono" else (255, 250, 210))
    pts = [(x, HORIZON - 120 - 60 * math.sin(x / 170 + 1) - 30 * math.sin(x / 70)) for x in range(-20, W + 40, 20)]
    p.P(pts + [(W + 40, HORIZON + 20), (-20, HORIZON + 20)], c["hill"])
    pts = [(x, HORIZON - 40 - 40 * math.sin(x / 120 + 3)) for x in range(-20, W + 40, 20)]
    p.P(pts + [(W + 40, HORIZON + 20), (-20, HORIZON + 20)], c["hill2"])
    p.R(0, HORIZON, W, H, c["ground"])
    for i in range(260):
        x, y = r.uniform(0, W), r.uniform(HORIZON + 10, H)
        sz = 4 + (y - HORIZON) / 40
        if name == "otono":
            p.L([(x, y), (x + r.uniform(-6, 6), y - sz * 3)], c["det"], 3)
        elif name == "primavera":
            p.L([(x, y), (x + r.uniform(-4, 4), y - sz * 2)], c["det"], 3)
            if i % 4 == 0:
                p.E(x, y - sz * 2, sz * 0.6, sz * 0.6, r.choice([(255, 240, 120), (255, 255, 255), (250, 150, 190)]))
        else:
            p.E(x, y, sz, sz * 0.3, c["det"])
    _BG[name] = img
    return img


def season_mix(t):
    """(fondo A, fondo B, mezcla)"""
    if t < 3.5:
        return "noche", "noche", 0
    if t < 14:
        return "otono", "otono", 0
    if t < 35:
        return "otono", "invierno", k(t, 14, 15.6)
    if t < 43:
        return "invierno", "noche", k(t, 35, 36.6)
    return "noche", "primavera", k(t, 43, 44.2)


# ───── estado de la historia ─────
def state(t):
    te = 40.8 if t < 3.5 else t
    s = {}
    s["hat_nest"] = k(te, 9.0, 10.6) * (1 - k(te, 58.6, 60.0))
    s["scarf_nest"] = k(te, 17.6, 19.0) * (1 - k(te, 59.2, 60.6))
    s["coat"] = k(te, 23.0, 25.0)
    s["fill"] = 1 - 0.45 * k(te, 29.0, 32.6) + 0.45 * k(te, 55.6, 59.0)
    tilt = 0.17 * k(te, 7.4, 8.4) * (1 - k(te, 12.6, 13.6)) + 0.38 * k(te, 37.0, 38.6) - 0.38 * k(te, 59.0, 60.6)
    s["tilt"] = tilt
    s["droop"] = 26 * k(te, 44.0, 46.0) * (1 - k(te, 59.0, 60.6))
    s["closed"] = 39.2 < te < 60.2
    s["look"] = (10, 12) if 7.4 < te < 12.6 else (8, 4) if 36 < te < 43 else (0, 0)
    sm = 0.35
    sm = lerp(sm, 0.95, k(te, 12.8, 13.6))
    sm = lerp(sm, 0.15, k(te, 15.0, 16.0))
    sm = lerp(sm, 0.55, k(te, 19.2, 20.0) * (1 - k(te, 21.5, 22.5)))
    sm = lerp(sm, -0.05, k(te, 35.0, 37.0))
    sm = lerp(sm, -0.45, k(te, 44.0, 46.0))
    sm = lerp(sm, 1.0, k(te, 60.4, 61.2))
    s["smile"] = sm
    s["shiver"] = (0.5 * k(te, 25.0, 26.0) + 0.6 * k(te, 35.0, 37.0)) * (1 - k(te, 42.8, 43.2))
    s["snow"] = k(te, 37.0, 42.0) * (1 - k(te, 43.0, 43.3))
    s["flowers"] = int(16 * k(te, 55.6, 60.0))
    s["hurt"] = te < 45.4
    return s


# ───── personajes ─────
def flower(p, x, y, r, col):
    for i in range(5):
        a = i * 2 * math.pi / 5
        p.E(x + math.cos(a) * r, y + math.sin(a) * r, r * 0.75, r * 0.75, col)
    p.E(x, y, r * 0.6, r * 0.6, (255, 214, 70))


FLOWER_SPOTS = [(-60, 1010), (40, 1060), (-30, 1140), (70, 1180), (-90, 1210), (10, 1240), (-140, 955), (150, 955), (-230, 945),
                (240, 940), (-320, 955), (95, 990), (-15, 960), (60, 1120), (-100, 1090), (120, 1240)]
FLOWER_COLS = [(250, 120, 160), (255, 255, 255), (180, 140, 240), (255, 160, 80), (250, 90, 110)]


def straw_tuft(p, x, y, ang, n=7, ln=34, seed=0):
    r = random.Random(seed)
    for i in range(n):
        a = ang + r.uniform(-0.55, 0.55)
        l = ln * r.uniform(0.6, 1.1)
        p.L([(x, y), (x + math.cos(a) * l, y + math.sin(a) * l)], STRAW if i % 2 else STRAW_D, 5)


def hat(p, x, y, sc=1.0, flowers=0):
    p.E(x, y, 165 * sc, 32 * sc, HATC, INK, 5)
    p.P([(x - 85 * sc, y - 4 * sc), (x - 70 * sc, y - 92 * sc), (x + 70 * sc, y - 92 * sc), (x + 85 * sc, y - 4 * sc)], HATC, INK, 5)
    p.R(x - 84 * sc, y - 36 * sc, x + 84 * sc, y - 14 * sc, (190, 60, 50))
    for i in range(6):
        p.L([(x - 70 * sc + i * 28 * sc, y - 88 * sc), (x - 74 * sc + i * 30 * sc, y - 40 * sc)], (200, 160, 80), 2)
    for i in range(flowers):
        flower(p, x - 60 * sc + i * 40 * sc, y - 26 * sc, 11 * sc, FLOWER_COLS[i % 5])


def scarf_on_neck(p, x, y, sh):
    p.R(x - 80, y - 18, x + 80, y + 18, (205, 50, 60), 14, INK, 4)
    for i in range(4):
        p.R(x - 60 + i * 36, y - 16, x - 48 + i * 36, y + 16, (245, 240, 230))
    p.R(x + 22 + sh, y + 8, x + 60 + sh, y + 140, (205, 50, 60), 10, INK, 4)
    for i in range(3):
        p.R(x + 24 + sh, y + 40 + i * 34, x + 58 + sh, y + 52 + i * 34, (245, 240, 230))


def bird(p, x, y, s, t, fly=False, face=1, col=None, hurt=False, shiver=0.0, carry=None, seed=0):
    breast, back = col or ((236, 102, 52), (126, 92, 62))
    if shiver:
        x += math.sin(t * 60 + seed) * 3 * shiver
    f = face
    p.E(x - 26 * s * f, y + 4 * s, 18 * s, 8 * s, back)  # cola
    p.P([(x - 20 * s * f, y), (x - 52 * s * f, y - 8 * s), (x - 50 * s * f, y + 12 * s)], back, INK, 3)
    p.E(x, y, 30 * s, 25 * s, back, INK, 4)
    p.E(x + 9 * s * f, y + 6 * s, 20 * s, 17 * s, breast)
    p.E(x + 18 * s * f, y - 22 * s, 18 * s, 17 * s, back, INK, 4)
    p.E(x + 22 * s * f, y - 16 * s, 11 * s, 9 * s, breast)
    p.P([(x + 33 * s * f, y - 26 * s), (x + 48 * s * f, y - 21 * s), (x + 33 * s * f, y - 17 * s)], (60, 50, 40))
    p.E(x + 24 * s * f, y - 26 * s, 4 * s, 4.5 * s, (20, 16, 20))
    if fly:
        a = math.sin(t * 26 + seed) * 0.9
        tip = (x - 6 * s * f - 10 * s * f, y - 4 * s - 46 * s * a)
        p.P([(x - 14 * s * f, y - 6 * s), (x + 10 * s * f, y - 6 * s), tip], back, INK, 3)
    else:
        p.E(x - 6 * s * f, y - 2 * s, 17 * s, 11 * s, mixc(back, (0, 0, 0), 0.15), INK, 3)
        p.L([(x - 4 * s, y + 22 * s), (x - 6 * s, y + 34 * s)], (90, 60, 40), 3)
        p.L([(x + 6 * s, y + 22 * s), (x + 6 * s, y + 34 * s)], (90, 60, 40), 3)
    if hurt:
        p.R(x - 16 * s * f - 9 * s, y - 6 * s, x - 16 * s * f + 9 * s, y + 4 * s, (250, 250, 250), 3, INK, 2)
    if carry is not None:
        flower(p, x + 50 * s * f, y - 20 * s, 9 * s, carry)


def crow(p, x, y, t, seed):
    a = math.sin(t * 18 + seed)
    p.E(x, y, 34, 16, (30, 30, 36))
    p.E(x + 30, y - 8, 14, 12, (30, 30, 36))
    p.P([(x + 40, y - 10), (x + 58, y - 6), (x + 40, y - 2)], (60, 60, 60))
    p.P([(x - 10, y - 4), (x + 16, y - 4), (x - 6, y - 4 - 50 * a)], (30, 30, 36))


def scarecrow(p, t, s):
    fill, sh = s["fill"], 0.0
    if s["shiver"]:
        sh = math.sin(t * 55) * 3 * s["shiver"]
    # poste y travesaño
    p.R(526, 930, 554, GROUND_Y + 20, (120, 84, 52), 4, INK, 4)
    p.R(286, BAR_Y - 12, 794, BAR_Y + 12, (120, 84, 52), 6, INK, 4)
    # brazos (mangas)
    for side in (-1, 1):
        x0, x1 = 540 + side * 120, 540 + side * 250
        p.L([(x0, BAR_Y), (x1, BAR_Y)], INK, 64)
        p.L([(x0, BAR_Y), (x1, BAR_Y)], SHIRT, 54)
        straw_tuft(p, x1 + side * 6, BAR_Y, 0 if side > 0 else math.pi, 8, 44, seed=3 + side)
    # cuerpo
    wt, wb = 150 * (0.55 + 0.45 * fill), 120 * (0.45 + 0.55 * fill)
    straw_tuft(p, 540 - wb * 0.5, 1286, math.pi / 2, 6, 40, 11)
    straw_tuft(p, 540 + wb * 0.5, 1286, math.pi / 2, 6, 40, 12)
    p.P([(540 - wt + sh, 932), (540 + wt + sh, 932), (540 + wb + sh, 1290), (540 - wb + sh, 1290)], SHIRT, INK, 5)
    p.R(540 - 40 + sh, 1150, 540 + 40 + sh, 1206, (150, 120, 70), 6, INK, 3)  # remiendo
    p.L([(540 - wb * 1.05 + sh, 1232), (540 + wb * 1.05 + sh, 1232)], (170, 130, 70), 10)
    if fill < 0.85:  # agujero por el que salió la paja
        hk = cl((0.85 - fill) / 0.3)
        p.E(540 - 30 + sh, 1040, 38 * hk, 30 * hk, (60, 46, 34))
        straw_tuft(p, 540 - 30 + sh, 1040, -math.pi / 2, 5, 26 * hk, 17)
    # abrigo (puesto → manta sobre el nido)
    c = s["coat"]
    if c < 0.999:
        cx, cy = lerp(540, NEST[0], c), lerp(1110, NEST[1] - 30, c)
        hw, hh = lerp(176, 120, c), lerp(190, 62, c)
        if c < 0.02:
            p.P([(540 - 176, 926), (540 + 176, 926), (540 + 150, 1300), (540 - 150, 1300)], COAT, INK, 5)
            p.P([(540 - 40, 926), (540, 1040), (540 + 40, 926)], SHIRT, INK, 4)
            for i in range(3):
                p.E(540 + 22, 1100 + i * 60, 9, 9, (230, 200, 120), INK, 2)
            p.L([(540 - 176, 940), (540 - 268, 950)], INK, 72)
            p.L([(540 + 176, 940), (540 + 268, 950)], INK, 72)
            p.L([(540 - 176, 940), (540 - 262, 950)], COAT, 62)
            p.L([(540 + 176, 940), (540 + 262, 950)], COAT, 62)
        else:
            p.R(cx - hw, cy - hh, cx + hw, cy + hh, COAT, 30, INK, 5)
    # bufanda en el cuello
    if s["scarf_nest"] < 0.02:
        scarf_on_neck(p, 540 + sh, 930, sh)
    # cabeza
    ang = s["tilt"]
    hx, hy = rot(540, 800, PIV[0], PIV[1], ang)
    hy += s["droop"]
    hx += sh
    straw_r = random.Random(5)
    for i in range(16):
        a = -math.pi + i * math.pi / 15 + ang
        l = 130 + straw_r.uniform(0, 30)
        p.L([(hx + math.cos(a) * 80, hy + math.sin(a) * 80), (hx + math.cos(a) * l, hy + math.sin(a) * l * 0.8)], STRAW if i % 2 else STRAW_D, 7)
    p.E(hx, hy, 112, 112, SACK, INK, 6)
    p.L([(hx - 80, hy + 76), (hx + 80, hy + 76)], (170, 130, 70), 8)  # cuerda del saco
    for dx in (-40, 40):
        ex, ey = rot(hx + dx, hy - 14, hx, hy, ang)
        lx, ly = s["look"]
        if s["closed"]:
            p.L([(ex - 18, ey + 2), (ex, ey + 9), (ex + 18, ey + 2)], INK, 6)
        else:
            p.E(ex + lx * 0.3, ey + ly * 0.3, 19, 19, (34, 30, 36))
            for hx2, hy2 in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
                p.E(ex + lx * 0.3 + hx2, ey + ly * 0.3 + hy2, 2.5, 2.5, (110, 100, 110))
    sm = s["smile"]
    pts = []
    for i in range(13):
        u = -1 + i / 6
        mx, my = rot(hx + u * 46, hy + 40 + sm * 22 * (1 - u * u), hx, hy, ang)
        pts.append((mx, my))
    p.L(pts, INK, 5)
    for mx, my in pts[1:-1:2]:
        p.L([(mx, my - 9), (mx, my + 9)], INK, 3)
    if sm > 0.6:
        for dx in (-62, 62):
            cx2, cy2 = rot(hx + dx, hy + 22, hx, hy, ang)
            p.E(cx2, cy2, 14, 9, (240, 150, 140))
    # nieve acumulada
    if s["snow"] > 0.01:
        sn = s["snow"]
        p.E(hx, hy - 98, 70 * sn + 10, 28 * sn + 4, (250, 252, 255))
        p.E(540 - 160, BAR_Y - 30, 70 * sn, 18 * sn, (250, 252, 255))
        p.E(NEST[0] + 10, NEST[1] - 98, 90 * sn, 24 * sn, (250, 252, 255))
    # flores
    for i in range(s["flowers"]):
        fx, fy = FLOWER_SPOTS[i]
        flower(p, 540 + fx, fy, 14, FLOWER_COLS[i % 5])
    return hx, hy


# ───── pájaro protagonista y bandada ─────
def hero(t):
    """(x, y, escala, vuela, mirando, visible, temblor)"""
    if t < 6.0 or 3.5 > t:
        return None
    if t < 7.2:
        u = (t - 6.0) / 1.2
        return (lerp(920, 660, u) + 30 * math.sin(u * 9), lerp(380, BIRD_G, u * u), 1.25, True, -1, 1.0)
    if t < 11.0:
        return (660, BIRD_G, 1.25, False, -1, 1.0)
    if t < 12.5:
        u = k(t, 11.0, 12.5)
        return (lerp(660, NEST[0], u), lerp(BIRD_G, NEST[1] - 70, u) - 220 * math.sin(math.pi * u), 1.25, True, 1, 0.0)
    if t < 45.4:
        return (NEST[0] + 6, NEST[1] - 78 if t < 25 else NEST[1] - 104, 1.05, False, -1, 0.0)
    if t < 46.5:
        u = k(t, 45.4, 46.0)
        return (NEST[0], NEST[1] - 104 - 60 * u, 1.25, u > 0.1, -1, 0.0)
    if t < 49.0:
        a = (t - 46.5) / 2.5 * 2 * math.pi
        return (540 + 300 * math.cos(a - math.pi / 2), 760 + 200 * math.sin(a - math.pi / 2) + 60, 1.25, True, -1 if math.sin(a) > 0 else 1, 0.0)
    if t < 50.6:
        u = k(t, 49.0, 50.6)
        return (lerp(540, 1250, u), lerp(620, 260, u), 1.25, True, 1, 0.0)
    return None


FLOCK_COLS = [((236, 102, 52), (126, 92, 62)), ((90, 150, 230), (60, 90, 160)), ((250, 214, 70), (150, 130, 60)),
              ((236, 102, 52), (126, 92, 62)), ((240, 240, 240), (120, 120, 130)), ((90, 150, 230), (60, 90, 160)),
              ((250, 214, 70), (150, 130, 60)), ((236, 102, 52), (126, 92, 62))]
PERCH = [(300, BAR_Y - 40), (370, BAR_Y - 40), (440, BAR_Y - 44), (650, BAR_Y - 44), (700, NEST[1] - 100), (880, NEST[1] - 96), (NEST[0] + 40, NEST[1] - 105),
         (540, 548)]


def flock(p, t, hat_pos):
    if t < 53.4:
        return
    for i in range(8):
        col = FLOCK_COLS[i]
        tx, ty = PERCH[i]
        if t < 55.6:
            u = k(t, 53.4 + i * 0.08, 55.6)
            x = lerp(1250 + (i % 3) * 90, 540 + 300 * math.cos(i * 0.8), u)
            y = lerp(380 + abs(i - 3.5) * 50, 700 + 200 * math.sin(i * 0.8), u)
            bird(p, x, y, 1.0, t, True, -1, col, carry=FLOWER_COLS[i % 5], seed=i)
        elif t < 60.6:
            a = t * 1.6 + i * 0.8
            x = 540 + 300 * math.cos(a)
            y = 790 + 230 * math.sin(a)
            if i == 7 and t > 58.6:  # el protagonista trae el sombrero de vuelta
                x, y = hat_pos[0] + 10, hat_pos[1] - 140
            bird(p, x, y, 1.0, t, True, -1 if math.sin(a) > 0 else 1, col, carry=FLOWER_COLS[i % 5] if t < 58 else None, seed=i)
        else:
            u = k(t, 60.6 + i * 0.1, 61.8 + i * 0.1)
            a = 60.6 * 1.6 + i * 0.8
            x = lerp(540 + 300 * math.cos(a), tx, u)
            y = lerp(790 + 230 * math.sin(a), ty, u)
            bird(p, x, y, 1.0, t, u < 0.95, 1 if tx < 540 else -1, col, seed=i)


# ───── partículas ─────
R = random.Random(9)
PARTS = [(R.uniform(0, W), R.uniform(0, H), R.uniform(0.6, 1.4), R.uniform(0, 6.28)) for _ in range(160)]


def particles(p, t, s):
    if 3.5 <= t < 14:  # hojas
        for i, (x0, y0, sp, ph) in enumerate(PARTS[:22]):
            y = (y0 + t * 120 * sp) % (H + 100) - 50
            x = (x0 + 60 * math.sin(t * sp + ph) + t * 30) % W
            p.E(x, y, 14, 7, [(220, 110, 40), (200, 70, 40), (240, 170, 60)][i % 3])
    wint = (t < 3.5) or (14.6 < t < 43)
    if wint:
        n = 60 if t < 22 else 100 if t < 35 else 160
        wind = 0 if t < 35 and t > 3.5 else 340
        dens = k(t, 14.6, 16) if t >= 3.5 else 1
        for x0, y0, sp, ph in PARTS[:int(n * dens)]:
            y = (y0 + t * 160 * sp) % (H + 40) - 20
            x = (x0 + 30 * math.sin(t * sp + ph) + t * wind * sp) % W
            p.E(x, y, 5 * sp, 5 * sp, (255, 255, 255))
    if t > 44:  # pétalos
        for i, (x0, y0, sp, ph) in enumerate(PARTS[:14 if t < 53 else 30]):
            y = (y0 + t * 70 * sp) % (H + 100) - 50
            x = (x0 + 80 * math.sin(t * sp * 0.7 + ph)) % W
            p.E(x, y, 9, 6, FLOWER_COLS[i % 5])


# ───── textos ─────
TEXTS = [  # (t0, t1, líneas[(texto, tamaño, color)])
    (0.15, 3.45, [("LO DIO TODO", 118, (255, 255, 255)), ("POR UN PÁJARO QUE NO CONOCÍA", 52, (255, 214, 90))]),
    (3.9, 6.6, [("OTOÑO", 84, (255, 255, 255))]),
    (9.2, 12.2, [("SU SOMBRERO", 84, (255, 255, 255))]),
    (14.8, 17.2, [("INVIERNO", 84, (255, 255, 255))]),
    (17.9, 20.8, [("SU BUFANDA", 84, (255, 255, 255))]),
    (23.3, 26.8, [("SU ABRIGO", 84, (255, 255, 255))]),
    (29.3, 33.2, [("SU PROPIA PAJA", 84, (255, 255, 255))]),
    (36.8, 41.6, [("LA NOCHE MÁS FRÍA,", 70, (255, 255, 255)), ("NO LO SOLTÓ", 70, (255, 214, 90))]),
    (44.3, 47.0, [("PRIMAVERA", 84, (255, 255, 255))]),
    (50.6, 53.4, [("SE QUEDÓ SIN NADA", 76, (255, 255, 255))]),
    (55.8, 59.2, [("PERO ÉL NO LO OLVIDÓ", 70, (255, 255, 255))]),
    (63.8, 67.4, [("LO QUE DAS,", 110, (255, 255, 255)), ("VUELVE.", 130, (255, 214, 90))]),
    (67.6, 71.5, [("ETIQUETA A QUIEN", 76, (255, 255, 255)), ("LO DIO TODO POR TI", 76, (255, 214, 90))]),
]


def text1(img, x, y, s, size, col=(255, 255, 255), stroke=7, alpha=1.0):
    if alpha <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((x, y), s, font=font(size, 1), fill=col + (255,), anchor="mm", stroke_width=stroke, stroke_fill=(25, 20, 30, 255))
    if alpha < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)


def texts(img, t):
    for t0, t1, lines in TEXTS:
        if t0 <= t <= t1:
            a = min(cl((t - t0) / 0.35), cl((t1 - t) / 0.35))
            y = 450
            for s, size, col in lines:
                text1(img, 540, y + (1 - a) * 20, s, size, col, 7, a)
                y += size * 1.05 + 10
    if t > 67.6:
        text1(img, 540, 1430, "NIVEL OCULTO", 40, (255, 255, 255), 5, cl((t - 67.6) / 0.4))


def frame(fi):
    t = fi / FPS
    a, b, m = season_mix(t)
    img = background(a).copy() if m <= 0 else (background(b).copy() if m >= 1 else Image.blend(background(a), background(b), m))
    p = Pen(img)
    s = state(t)
    if 3.5 <= t < 6.0:  # cuervos que huyen
        for i in range(3):
            u = (t - 3.5) / 2.5
            crow(p, 560 + i * 60 + u * 700, 700 - i * 50 - u * 500, t, i)
    hx, hy = scarecrow(p, t, s)
    # nido (sombrero en el brazo) y lo que lo cubre
    hn = s["hat_nest"]
    hpos = (lerp(hx, NEST[0], hn), lerp(hy - 95, NEST[1], hn) - 160 * math.sin(math.pi * hn))
    hb = hero(t)
    if hb and t < 45.4 and t >= 12.5:  # el pájaro dentro del nido (por detrás del ala del sombrero)
        x, y, sc, fl, face, sh = hb
        bird(p, x, y + (30 if s["coat"] > 0.5 else 0), sc, t, False, face, hurt=s["hurt"], shiver=(1.0 if 15.6 < t < 17.8 else 0.3 if t > 25 else 0))
    hat(p, *hpos, 1.0 if hn < 0.98 else 0.82, flowers=5 if t > 59 else 0)
    sn = s["scarf_nest"]
    if sn > 0.02:
        sx, sy = lerp(540, NEST[0], sn), lerp(930, NEST[1] - 40, sn) - 120 * math.sin(math.pi * sn)
        p.R(sx - 110, sy - 16, sx + 110, sy + 16, (205, 50, 60), 14, INK, 4)
        for i in range(5):
            p.R(sx - 90 + i * 40, sy - 14, sx - 78 + i * 40, sy + 14, (245, 240, 230))
    if s["coat"] > 0.98:
        p.R(NEST[0] - 120, NEST[1] - 92, NEST[0] + 120, NEST[1] + 32, COAT, 30, INK, 5)
        p.L([(NEST[0] - 100, NEST[1] - 60), (NEST[0] + 100, NEST[1] - 60)], (126, 46, 38), 4)
        if hb and t < 45.4:  # asoma la cabeza
            x, y, sc, fl, face, sh = hb
            bird(p, x, NEST[1] - 104, 0.9, t, False, face, hurt=s["hurt"], shiver=0.5 if 25 < t < 43 else 0)
    if 29.2 < t < 32.8:  # paja volando al nido
        for j in range(5):
            u = ((t - 29.2) / 1.2 + j * 0.2) % 1
            x = lerp(510, NEST[0], u)
            y = lerp(1040, NEST[1] - 60, u) - 140 * math.sin(math.pi * u)
            p.L([(x - 20, y), (x + 20, y - 6)], STRAW, 6)
    if hb and (t < 12.5 or t >= 45.4):
        x, y, sc, fl, face, sh = hb
        bird(p, x, y, sc, t, fl, face, hurt=s["hurt"], shiver=sh if 7.2 < t < 11 else 0)
    if t >= 60.6:  # el protagonista se posa en su sombrero
        u = k(t, 60.6, 61.6)
        bird(p, lerp(hpos[0] + 10, hx, u), lerp(hpos[1] - 140, hy - 210, u), 1.15, t, u < 0.95, -1)
    flock(p, t, hpos)
    particles(p, t, s)
    if 43 <= t < 44.2:  # destello de cambio de estación
        a = 1 - abs(t - 43.5) / 0.7
        lay = Image.new("RGBA", img.size, (255, 255, 255, int(255 * cl(a))))
        img.alpha_composite(lay)
    if 3.35 <= t < 3.75:
        a = 1 - abs(t - 3.5) / 0.25
        img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(255 * cl(a)))))
    cy = 920 - 70 * k(t, 62.8, 64.4)
    hw, hh = W / 2 / ZOOM, H / 2 / ZOOM
    img = img.crop((int((545 - hw) * S), int((cy - hh) * S), int((545 + hw) * S), int((cy + hh) * S))).resize((W, H), Image.LANCZOS)
    texts(img, t)
    return img.convert("RGB").tobytes()


# ───── música y sonido ─────
def note_hz(n):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    semi = names[n[0]] + (1 if "#" in n else 0)
    octv = int(n[-1])
    return 440.0 * 2 ** ((semi + 12 * (octv + 1) - 69) / 12)


def build_audio(path):
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    rng = np.random.default_rng(3)

    def add(t0, sig, gain=1.0, pan=0.0):
        i0 = int(t0 * SR)
        if i0 >= n:
            return
        sig = sig[: n - i0]
        out[i0:i0 + len(sig), 0] += sig * gain * (1 - pan) * 0.5 * 2 ** 0.5
        out[i0:i0 + len(sig), 1] += sig * gain * (1 + pan) * 0.5 * 2 ** 0.5

    def piano(t0, f, vel=0.5, dur=2.5):
        m = int((dur + 1.2) * SR)
        tt = np.arange(m) / SR
        tau = 1.6 * (220 / f) ** 0.35
        sig = sum(a * np.sin(2 * np.pi * f * h * tt) * np.exp(-tt * h ** 0.8 / tau) for h, a in ((1, 1), (2, 0.42), (3, 0.2), (4, 0.1), (5, 0.05)))
        sig *= np.minimum(1, tt / 0.004) * np.where(tt > dur, np.exp(-(tt - dur) / 0.25), 1)
        add(t0, sig, vel * 0.22, pan=(math.log2(f / 260)) * 0.25)

    def pad(t0, notes, dur, vel=0.4):
        m = int((dur + 1.5) * SR)
        tt = np.arange(m) / SR
        sig = np.zeros(m)
        for nn in notes:
            f = note_hz(nn)
            for det in (-0.003, 0.003):
                sig += np.sin(2 * np.pi * f * (1 + det) * tt + 0.4 * np.sin(2 * np.pi * 0.2 * tt))
        e = np.minimum(1, tt / 1.0) * np.where(tt > dur, np.exp(-(tt - dur) / 0.6), 1)
        add(t0, sig * e, vel * 0.03)

    beat = 60 / 72
    bar = 4 * beat
    CH = {"Am": ["A2", "E3", "A3", "C4", "E4"], "F": ["F2", "C3", "F3", "A3", "C4"], "C": ["C3", "G3", "C4", "E4", "G4"],
          "G": ["G2", "D3", "G3", "B3", "D4"], "Dm": ["D3", "A3", "D4", "F4", "A4"]}
    PADN = {"Am": ["A3", "C4", "E4"], "F": ["F3", "A3", "C4"], "C": ["C4", "E4", "G4"], "G": ["G3", "B3", "D4"], "Dm": ["D4", "F4", "A4"]}

    def section(t0, t1, prog, style, vel):
        t = t0
        i = 0
        while t < t1 - 0.5:
            ch = prog[i % len(prog)]
            nn = CH[ch]
            if style == "arp":
                order = [0, 2, 3, 4, 3, 2, 1, 2]
                for j, o in enumerate(order):
                    if t + j * beat / 2 < t1:
                        piano(t + j * beat / 2, note_hz(nn[o]), vel * (1.0 if j == 0 else 0.62))
            elif style == "sparse":
                for j, o in enumerate([0, 3, 2, 4]):
                    if t + j * beat < t1:
                        piano(t + j * beat, note_hz(nn[o]), vel * (1.0 if j == 0 else 0.55), 3)
            pad(t, PADN[ch], min(bar, t1 - t), 0.9 if style != "none" else 1.4)
            t += bar
            i += 1

    # gancho
    pad(0, PADN["Am"], 3.3, 1.2)
    piano(0.2, note_hz("E5"), 0.45, 3)
    piano(1.9, note_hz("C5"), 0.35, 2)
    section(3.5, 14.0, ["Am", "F", "C", "G"], "arp", 0.5)
    section(14.0, 35.0, ["Am", "F", "C", "G", "Am", "Dm", "F", "G"], "sparse", 0.55)
    for tt, nn in ((21.0, "E5"), (22.7, "D5"), (24.3, "C5"), (27.7, "B4"), (29.4, "C5"), (31.0, "A4")):
        piano(tt, note_hz(nn), 0.5, 1.6)
    section(35.0, 43.0, ["Am", "F"], "none", 0.5)
    section(44.0, 50.6, ["C", "G"], "sparse", 0.42)
    piano(51.0, note_hz("A4"), 0.4, 2)
    piano(52.4, note_hz("E4"), 0.32, 2)
    section(53.4, 64.0, ["C", "G", "Am", "F"], "arp", 0.62)
    mel = [("E5", 0, 2), ("G5", 2, 2), ("D5", 4, 2), ("B4", 6, 1), ("D5", 7, 1), ("C5", 8, 2), ("E5", 10, 2), ("A4", 12, 3), ("C5", 15, 1)]
    for nn, b0, bl in mel:
        piano(53.4 + 4 * beat + b0 * beat, note_hz(nn), 0.7, bl * beat)  # entra una frase tarde
    for nn, b0, bl in (("C6", 0, 2), ("B5", 2, 2), ("G5", 4, 4)):
        piano(53.4 + 12 * beat + b0 * beat, note_hz(nn), 0.35, bl * beat)
    section(64.0, 70.5, ["F", "C"], "arp", 0.55)
    piano(67.3, note_hz("C5"), 0.6, 3.5)
    piano(67.3, note_hz("E5"), 0.45, 3.5)
    pad(67.3, PADN["C"], 3.4, 1.4)

    # efectos
    def chirp(t0, g=0.25, pan=0.0):
        for j in range(3):
            m = int(0.07 * SR)
            tt = np.arange(m) / SR
            f = 3600 + 1600 * tt / 0.07
            sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.07)
            add(t0 + j * 0.09, sig, g, pan)

    def noise_burst(t0, dur, g, lp=60, hp=None):
        m = int(dur * SR)
        x = rng.standard_normal(m)
        y = np.convolve(x, np.ones(lp) / lp, mode="same")
        if hp:
            y = y - np.convolve(y, np.ones(hp) / hp, mode="same")
        e = np.sin(np.pi * np.arange(m) / m)
        add(t0, y * e, g)

    for t0 in (3.6, 3.85, 4.2):
        m = int(0.28 * SR)
        tt = np.arange(m) / SR
        f = 520 - 200 * tt / 0.28
        sig = (2 * ((np.cumsum(f) / SR) % 1) - 1) * np.exp(-tt * 6) * (0.6 + 0.4 * rng.standard_normal(m) * 0.3)
        add(t0, np.convolve(sig, np.ones(6) / 6, mode="same"), 0.12, 0.4)
    m = int(0.25 * SR)
    tt = np.arange(m) / SR
    add(7.2, np.sin(2 * np.pi * 85 * tt) * np.exp(-tt * 18), 0.5)
    for t0 in (7.6, 9.0, 11.2, 13.0, 16.0, 45.6, 46.8, 48.0, 49.2, 53.6, 54.0, 54.5, 55.2, 57.0, 59.4, 61.0, 62.2, 64.0):
        chirp(t0, 0.2, 0.3)
    for t0 in (9.0, 17.6, 23.0, 29.3, 58.6):
        noise_burst(t0, 0.6, 0.35, 30, 400)
    for i in range(16):
        m = int(0.08 * SR)
        tt = np.arange(m) / SR
        add(55.6 + i * (4.4 / 16), np.sin(2 * np.pi * np.cumsum(1500 - 600 * tt / 0.08) / SR) * np.exp(-tt * 40), 0.12, (i % 3 - 1) * 0.4)
    # viento
    m = n
    wn = np.convolve(rng.standard_normal(m), np.ones(90) / 90, mode="same")
    tt = np.arange(m) / SR
    lvl = np.interp(tt, [0, 3.4, 3.6, 14, 16, 34, 36, 42.8, 43.4, 71], [0.9, 0.9, 0.05, 0.05, 0.35, 0.45, 1.0, 1.0, 0.0, 0.0])
    lvl *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.23 * tt) * np.sin(2 * np.pi * 0.07 * tt + 1)
    out[:, 0] += wn * lvl * 0.6
    out[:, 1] += np.roll(wn, 900) * lvl * 0.6
    out *= np.minimum(1, tt / 0.03)[:, None] * np.minimum(1, (DUR - tt) / 1.2)[:, None]
    out /= max(1e-9, np.abs(out).max()) / 0.85
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def main(out):
    wav = out + ".wav"
    build_audio(wav)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
          f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", wav, "-af", ln + ",aresample=48000", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for buf in pool.imap(frame, range(int(DUR * FPS)), chunksize=4):
            p.stdin.write(buf)
    p.stdin.close()
    p.wait()
    os.remove(wav)


if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for t in sys.argv[3:]:
            Image.frombytes("RGB", (W, H), frame(int(float(t) * FPS))).save(f"{sys.argv[2]}/e_{float(t):05.1f}.png")
    else:
        main(sys.argv[1])
