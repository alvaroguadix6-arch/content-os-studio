"""«¿Qué pasaría si la gravedad desapareciera durante 10 segundos?» — estilo ilustración plana.

Estilo de vídeo explicativo: dibujos vectoriales planos con degradados suaves, edificios de colores
con ventanas encendidas, personajes sencillos, la Tierra girando y el texto arriba apareciendo
palabra a palabra con las palabras clave en amarillo subrayadas.

Todo se dibuja por código (sin imágenes generadas). Se dibuja al doble de resolución y se reduce,
para que los bordes queden limpios. La narración (narracion.json) marca cada momento.

    python plano.py --narracion dir/ --out frames/ [--only 10 200 ...]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from animar import Timeline as BaseTimeline

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
S = 2  # superresolución
GROUND = 1460  # acera (coordenadas de mundo, cámara por defecto)
FONTS = "/usr/share/fonts/opentype/inter/"
YEL = (255, 200, 60)


def font(name, size):
    k = (name, int(size))
    if k not in font.c:
        font.c[k] = ImageFont.truetype(os.path.join(FONTS, f"Inter-{name}.otf"), max(8, int(size)))
    return font.c[k]


font.c = {}


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(a, b, x):
    k = clamp((x - a) / (b - a)) if b != a else float(x >= b)
    return k * k * (3 - 2 * k)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back_out(x, s=1.7):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


def mix(c1, c2, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))


def shade(c, k):
    return tuple(int(clamp(v * k, 0, 255)) for v in c)


def vgrad(w, h, top, bottom):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    a = np.array(top, np.float32) * (1 - t) + np.array(bottom, np.float32) * t
    return Image.fromarray(np.repeat(a, w, axis=1).astype(np.uint8))


class Timeline(BaseTimeline):
    def __init__(self, nar):
        super().__init__(nar)
        L = self.lines

        def w(key, frag, default=None):
            for word, a, _ in L[key]["words"]:
                if frag in word.lower():
                    return a
            return default if default is not None else L[key]["start"]

        self.t_ciudad = L["ciudad"]["start"]
        self.t_despegue = L["despegue"]["start"]
        self.t_tierra = L["flotan"]["start"]
        self.t_anclado = w("flotan", "todo", L["flotan"]["start"] + 1.8) - 0.15
        self.named = {k: w("flotan", k) for k in ("personas", "coches", "papeleras", "perros")}
        self.t_fuente = L["agua"]["start"]
        self.t_agarra = w("agua", "gente") - 0.1
        self.named_grip = {k: w("agua", k) for k in ("farolas", "barandillas", "ventanas")}
        self.t_vuelve = L["vuelve"]["start"]
        self.t_caida = L["caida"]["start"]
        self.t_cristales = w("caida", "cristales")
        self.t_agua_cae = w("caida", "toneladas")
        self.t_planeta = L["consecuencias"]["start"]


KEYWORDS = {"gravedad", "diez", "segundos?", "segundos,", "ciudad:", "semáforo.", "despegan", "tierra", "personas,", "coches,",
            "papeleras,", "perros.", "volando.", "burbujas", "farolas,", "barandillas", "ventanas.", "golpe.", "aplastan",
            "estallan,", "empapan", "miles", "accidentes,", "planeta.", "sobrevivirías?", "comentarios!"}


# ───────────────────────── personajes y objetos ─────────────────────────
SKINS = [(241, 194, 160), (224, 172, 130), (180, 125, 90), (120, 80, 55), (250, 210, 180)]
HAIRS = [(60, 40, 30), (30, 25, 25), (150, 90, 40), (200, 190, 180), (90, 60, 40)]
SHIRTS = [(70, 130, 210), (90, 100, 115), (60, 170, 140), (220, 90, 80), (235, 185, 60), (150, 100, 190), (60, 160, 175)]


class Person:
    def __init__(self, rnd, x, h, shirt=None, kind="person"):
        self.x, self.h, self.kind = x, h, kind
        self.skin = rnd.choice(SKINS)
        self.hair = rnd.choice(HAIRS)
        self.shirt = shirt or rnd.choice(SHIRTS)
        self.pants = rnd.choice([(45, 55, 80), (60, 60, 65), (40, 45, 60), (90, 75, 60)])
        self.phase = rnd.uniform(0, 6.28)
        self.spin = rnd.uniform(-40, 40)
        self.rise = rnd.uniform(0.7, 1.3)
        self.spread_x = x
        self.long_hair = rnd.random() < 0.4

    def sprite(self, pose, face="normal", arms="down", walk=0.0, scale=1.0):
        """Personaje en un lienzo propio (a superresolución). Devuelve (imagen, ancla pies)."""
        h = self.h * S * scale
        size = int(h * 1.5)
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cx, fy = size / 2, size * 0.83  # pies
        hip = fy - 0.40 * h
        sh = fy - 0.70 * h
        lw = 0.10 * h
        aw = 0.075 * h

        def limb(x0, y0, ang, length, width, col):
            x1, y1 = x0 + math.sin(ang) * length, y0 + math.cos(ang) * length
            d.line([(x0, y0), (x1, y1)], fill=col, width=int(width))
            r = width / 2
            d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=col)
            d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=col)
            return x1, y1

        sw = math.sin(walk) * 0.45
        if pose == "float":
            la, ra = 0.35 + 0.15 * math.sin(walk), -0.3 - 0.15 * math.sin(walk + 1)
        elif pose == "lie":
            la, ra = 0.2, -0.2
        else:
            la, ra = sw, -sw
        # piernas
        limb(cx - 0.06 * h, hip, la, 0.38 * h, lw, self.pants)
        limb(cx + 0.06 * h, hip, ra, 0.38 * h, lw, self.pants)
        # zapatos
        for sx, ang in ((cx - 0.06 * h, la), (cx + 0.06 * h, ra)):
            x1, y1 = sx + math.sin(ang) * 0.38 * h, hip + math.cos(ang) * 0.38 * h
            d.ellipse([x1 - lw * 0.75, y1 - lw * 0.35, x1 + lw * 0.85, y1 + lw * 0.45], fill=(40, 40, 45))
        # brazos (detrás y delante del cuerpo)
        if arms == "up":
            a1, a2 = math.pi - 0.35 + 0.15 * math.sin(walk * 1.3), math.pi + 0.35 - 0.15 * math.sin(walk * 1.3 + 1)
        elif arms == "wave":
            a1, a2 = math.pi * 0.75 + 0.3 * math.sin(walk * 3), -math.pi * 0.75 - 0.3 * math.sin(walk * 3 + 1)
        elif arms == "hold":
            a1, a2 = math.pi - 0.1, math.pi + 0.1
        else:
            a1, a2 = 0.18 - sw * 0.6, -0.18 + sw * 0.6
        torso_col = self.shirt
        limb(cx - 0.15 * h, sh + 0.03 * h, a1, 0.30 * h, aw, shade(torso_col, 0.85))
        d.rounded_rectangle([cx - 0.16 * h, sh, cx + 0.16 * h, hip + 0.04 * h], radius=0.07 * h, fill=torso_col)
        hx, hy = limb(cx + 0.15 * h, sh + 0.03 * h, a2, 0.30 * h, aw, shade(torso_col, 0.92))
        # manos
        for ang, x0 in ((a1, cx - 0.15 * h), (a2, cx + 0.15 * h)):
            x1, y1 = x0 + math.sin(ang) * 0.30 * h, sh + 0.03 * h + math.cos(ang) * 0.30 * h
            d.ellipse([x1 - aw * 0.6, y1 - aw * 0.6, x1 + aw * 0.6, y1 + aw * 0.6], fill=self.skin)
        # cabeza
        r = 0.14 * h
        hcx, hcy = cx, sh - 0.02 * h - r
        d.rectangle([cx - 0.04 * h, sh - 0.05 * h, cx + 0.04 * h, sh + 0.01 * h], fill=shade(self.skin, 0.9))
        if self.long_hair:
            d.rounded_rectangle([hcx - r * 1.08, hcy - r * 0.9, hcx + r * 1.08, hcy + r * 1.25], radius=r * 0.6, fill=self.hair)
        d.ellipse([hcx - r, hcy - r * 1.05, hcx + r, hcy + r * 1.05], fill=self.skin)
        d.chord([hcx - r * 1.04, hcy - r * 1.12, hcx + r * 1.04, hcy + r * 0.7], 180, 360, fill=self.hair)
        # cara
        ey = hcy + r * 0.1
        er = r * 0.11
        for ex in (hcx - r * 0.38, hcx + r * 0.38):
            if face == "dizzy":
                d.line([(ex - er * 1.4, ey - er * 1.4), (ex + er * 1.4, ey + er * 1.4)], fill=(40, 30, 30), width=max(2, int(er * 0.7)))
                d.line([(ex - er * 1.4, ey + er * 1.4), (ex + er * 1.4, ey - er * 1.4)], fill=(40, 30, 30), width=max(2, int(er * 0.7)))
            else:
                k = 1.35 if face in ("scared", "wow") else 1.0
                d.ellipse([ex - er * k, ey - er * k * 1.2, ex + er * k, ey + er * k * 1.2], fill=(35, 30, 30))
        my = hcy + r * 0.55
        if face in ("scared", "wow"):
            d.ellipse([hcx - r * 0.16, my - r * 0.16, hcx + r * 0.16, my + r * 0.2], fill=(120, 40, 40))
        elif face == "smile":
            d.arc([hcx - r * 0.3, my - r * 0.3, hcx + r * 0.3, my + r * 0.1], 20, 160, fill=(120, 50, 50), width=max(2, int(r * 0.08)))
        else:
            d.line([(hcx - r * 0.18, my), (hcx + r * 0.18, my)], fill=(120, 60, 60), width=max(2, int(r * 0.07)))
        return im, (cx, fy)


def draw_car(color, w, kind="car", squash=1.0):
    """Coche de perfil, plano. Devuelve imagen (superresolución) con el ancla abajo al centro."""
    w *= S
    h = w * (0.55 if kind == "van" else 0.45)
    im = Image.new("RGBA", (int(w * 1.1), int(h * 1.35)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, base = w * 0.05, h * 1.25
    wr = h * 0.2
    body_top = base - h * 0.62
    if kind == "van":
        d.rounded_rectangle([ox, base - h * 0.95, ox + w * 0.78, base - wr * 0.6], radius=h * 0.08, fill=color)
        d.rounded_rectangle([ox + w * 0.7, base - h * 0.62, ox + w, base - wr * 0.6], radius=h * 0.1, fill=color)
        d.polygon([(ox + w * 0.76, base - h * 0.95), (ox + w * 0.86, base - h * 0.62), (ox + w * 0.76, base - h * 0.62)], fill=color)
        d.polygon([(ox + w * 0.785, base - h * 0.88), (ox + w * 0.85, base - h * 0.66), (ox + w * 0.785, base - h * 0.66)], fill=(170, 210, 235))
    else:
        d.rounded_rectangle([ox, body_top, ox + w, base - wr * 0.6], radius=h * 0.16, fill=color)
        cab = [(ox + w * 0.2, body_top + 2), (ox + w * 0.32, base - h * 0.98), (ox + w * 0.66, base - h * 0.98), (ox + w * 0.8, body_top + 2)]
        d.polygon(cab, fill=color)
        d.polygon([(ox + w * 0.25, body_top), (ox + w * 0.345, base - h * 0.9), (ox + w * 0.48, base - h * 0.9), (ox + w * 0.48, body_top)], fill=(170, 210, 235))
        d.polygon([(ox + w * 0.51, body_top), (ox + w * 0.51, base - h * 0.9), (ox + w * 0.645, base - h * 0.9), (ox + w * 0.745, body_top)], fill=(170, 210, 235))
        if kind == "taxi":
            d.rounded_rectangle([ox + w * 0.42, base - h * 1.1, ox + w * 0.56, base - h * 0.98], radius=4, fill=(250, 250, 250))
    d.rectangle([ox + w * 0.02, base - h * 0.42, ox + w * 0.98, base - h * 0.38], fill=shade(color, 0.8))
    d.ellipse([ox + w * 0.93, base - h * 0.55, ox + w * 1.0, base - h * 0.45], fill=(255, 235, 170))
    for wx in (ox + w * 0.22, ox + w * 0.78):
        d.ellipse([wx - wr, base - wr * 2, wx + wr, base], fill=(40, 40, 45))
        d.ellipse([wx - wr * 0.45, base - wr * 1.45, wx + wr * 0.45, base - wr * 0.55], fill=(170, 170, 175))
    if squash != 1.0:
        im = im.resize((im.width, max(2, int(im.height * squash))), Image.BILINEAR)
    return im


def draw_dog(w):
    w *= S
    im = Image.new("RGBA", (int(w * 1.3), int(w * 1.0)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (215, 160, 90)
    b = w * 0.75
    d.rounded_rectangle([w * 0.15, b - w * 0.42, w * 0.85, b - w * 0.12], radius=w * 0.14, fill=c)
    for lx in (0.22, 0.34, 0.66, 0.78):
        d.rounded_rectangle([w * lx - w * 0.04, b - w * 0.2, w * lx + w * 0.04, b + w * 0.05], radius=w * 0.03, fill=shade(c, 0.9))
    d.ellipse([w * 0.7, b - w * 0.66, w * 1.05, b - w * 0.32], fill=c)
    d.ellipse([w * 0.95, b - w * 0.5, w * 1.12, b - w * 0.38], fill=shade(c, 0.85))
    d.ellipse([w * 1.06, b - w * 0.48, w * 1.12, b - w * 0.42], fill=(40, 30, 30))
    d.ellipse([w * 0.72, b - w * 0.62, w * 0.86, b - w * 0.4], fill=shade(c, 0.7))
    d.ellipse([w * 0.9, b - w * 0.58, w * 0.95, b - w * 0.53], fill=(30, 25, 25))
    d.line([(w * 0.17, b - w * 0.38), (w * 0.02, b - w * 0.55)], fill=c, width=int(w * 0.06))
    return im


def draw_bin(w):
    w *= S
    im = Image.new("RGBA", (int(w * 1.1), int(w * 1.45)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([w * 0.08, w * 0.18, w * 1.02, w * 1.4], radius=w * 0.08, fill=(95, 135, 110))
    d.rounded_rectangle([w * 0.0, w * 0.06, w * 1.1, w * 0.22], radius=w * 0.05, fill=(75, 110, 90))
    for k in range(3):
        x = w * (0.3 + k * 0.25)
        d.line([(x, w * 0.35), (x, w * 1.25)], fill=(80, 118, 96), width=max(2, int(w * 0.05)))
    return im


class World:
    """Ciudad plana: edificios de colores, calle, semáforo, farola, fuente."""

    def __init__(self, seed=4):
        r = random.Random(seed)
        self.r = r
        cols = [(226, 128, 96), (232, 190, 92), (110, 140, 200), (205, 90, 95), (140, 180, 120), (220, 150, 120), (120, 120, 170)]
        self.back = []
        x = -200
        while x < W + 200:
            bw = r.randint(150, 230)
            self.back.append((x, bw, r.randint(500, 900), mix(r.choice(cols), (170, 190, 215), 0.55)))
            x += bw + r.randint(-20, 10)
        self.front = []
        x = -120
        while x < W + 150:
            bw = r.randint(200, 290)
            hgt = r.randint(560, 980)
            lit = [[r.random() < 0.45 for _ in range(6)] for _ in range(30)]
            self.front.append((x, bw, hgt, r.choice(cols), lit, r.random() < 0.5))
            x += bw + r.randint(0, 14)
        self.clouds = [(r.uniform(0, W), r.uniform(-1200, 380), r.uniform(0.7, 1.4), r.uniform(6, 16)) for _ in range(9)]
        self.birds = [(r.uniform(0, W), r.uniform(150, 420), r.uniform(40, 90) * r.choice((-1, 1)), r.uniform(0, 6)) for _ in range(5)]

    def sky(self, d, cam_y, t, top=(84, 130, 190), bottom=(198, 222, 238)):
        pass


# ───────────────────────── animador ─────────────────────────
class Animator:
    def __init__(self, nar, arte=None):
        self.tl = Timeline(nar)
        self.nar = nar
        r = random.Random(11)
        self.world = World()
        self.people = [Person(r, x, h) for x, h in ((150, 215), (330, 200), (520, 228), (700, 205), (900, 220))]
        self.people[2].shirt = (70, 130, 210)  # el protagonista (camisa azul)
        self.hero = self.people[2]
        for p, sx in zip(self.people, (110, 330, 540, 760, 960)):
            p.spread_x = sx
        # coches: (color, ancho, tipo, x, y suelo, velocidad)
        self.cars = [((215, 70, 70), 320, "car", 230, GROUND + 340), ((250, 205, 60), 320, "taxi", 840, GROUND + 340),
                     ((235, 235, 240), 380, "van", 540, GROUND + 230)]
        self.dog = (620, GROUND + 40)
        self.bin = (60, GROUND - 5)
        self.car_imgs = {i: draw_car(c, w_, k) for i, (c, w_, k, _, _) in enumerate(self.cars)}
        self.dog_img = draw_dog(110)
        self.bin_img = draw_bin(90)
        self.bubbles = [(r.uniform(120, 960), r.uniform(650, 1250), r.uniform(45, 120), r.uniform(0, 6.28)) for _ in range(11)]
        self.shards = [(r.uniform(-1, 1), r.uniform(-1.2, -0.2), r.uniform(5, 14)) for _ in range(40)]
        self.drops = [(r.uniform(0, W), r.uniform(-300, 0), r.uniform(0.8, 1.3)) for _ in range(120)]
        lat = np.unpackbits(np.load(os.path.join(HERE, "tierra_mask.npy")))[: 360 * 720].reshape(360, 720).astype(bool)
        self.land = lat
        self.alerts = [(r.uniform(-1, 1), r.uniform(-0.8, 0.8), r.uniform(0, 1)) for _ in range(140)]
        self.stars = [(r.uniform(0, W), r.uniform(0, H), r.uniform(1, 3)) for _ in range(140)]
        self._grad = {}

    # ─── utilidades ───
    def grad(self, key, top, bottom):
        if key not in self._grad:
            self._grad[key] = vgrad(W * S, H * S, top, bottom)
        return self._grad[key].copy()

    def landed_at(self, a):
        return self.tl.t_return + 0.15 + 0.35 * (a.kind == "car")

    @property
    def actors(self):
        class A:
            def __init__(self, kind):
                self.kind = kind
        return [A("car"), A("car"), A("person"), A("person"), A("car")]

    def lift(self, base, rise, t, phase=0.0):
        """Altura que gana un objeto al flotar (px), estable a media altura, y caída con g al volver."""
        tl = self.tl
        ft = max(0.0, min(t, tl.t_return) - tl.t_float)
        if ft <= 0:
            return 0.0
        lmax = base * rise
        h = lmax * (1 - math.exp(-ft / 3.0)) + 18 * math.sin(ft * 0.9 + phase) * min(1, ft)
        if t > tl.t_return:
            h0 = lmax * (1 - math.exp(-(tl.t_return - tl.t_float) / 3.0))
            h = max(0.0, h0 - 0.5 * 9.8 * 160 * (t - tl.t_return) ** 2)
        return h

    def paste(self, img, sp, x, y, anchor=(0.5, 1.0), rot=0.0):
        """Pega un recortable (superresolución) con su ancla en (x, y) de pantalla."""
        if rot:
            w0, h0 = sp.size
            ax, ay = w0 * anchor[0], h0 * anchor[1]
            sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True, center=(ax, ay))
            # tras expandir, el ancla se mueve: aproximamos con el centro
            img.alpha_composite(sp, (int(x * S - sp.width / 2), int(y * S - sp.height / 2 - h0 * (anchor[1] - 0.5))))
            return
        img.alpha_composite(sp, (int(x * S - sp.width * anchor[0]), int(y * S - sp.height * anchor[1])))

    def person(self, img, p, x, y, pose="stand", face="normal", arms="down", walk=0.0, rot=0.0, scale=1.0):
        sp, (ax, ay) = p.sprite(pose, face, arms, walk, scale)
        if rot:
            sp = sp.rotate(rot, resample=Image.BICUBIC, center=(ax, ay))
        img.alpha_composite(sp, (int(x * S - ax), int(y * S - ay)))

    # ─── decorado de ciudad ───
    def city(self, img, d, t, cam_y=0.0, zoom=1.0, fountain=False, broken=0.0):
        wd = self.world
        s = S
        # nubes
        for x0, y0, k, v in wd.clouds:
            x = (x0 + v * t) % (W + 400) - 200
            y = y0 + cam_y * 0.4
            for dx, dy, rr in ((0, 0, 60), (55, 10, 48), (-55, 12, 44), (25, -28, 42)):
                rr *= k
                d.ellipse([(x + dx * k - rr) * s, (y + dy * k - rr) * s, (x + dx * k + rr) * s, (y + dy * k + rr * 0.8) * s], fill=(250, 252, 255))
        # pájaros
        for x0, y0, v, ph in wd.birds:
            x = (x0 + v * t) % (W + 200) - 100
            y = y0 + cam_y * 0.5 + 10 * math.sin(t + ph)
            fl = math.sin(t * 9 + ph) * 8
            d.line([((x - 14) * s, (y - fl) * s), (x * s, (y + 4) * s), ((x + 14) * s, (y - fl) * s)], fill=(60, 70, 90), width=3 * s)
        # edificios del fondo
        for x, bw, hgt, col in wd.back:
            top = GROUND - 140 - hgt + cam_y * 0.75
            d.rectangle([x * s, top * s, (x + bw) * s, (GROUND + cam_y) * s], fill=col)
            for wy in range(int(top + 40), int(GROUND + cam_y - 200), 70):
                for wx in range(x + 22, x + bw - 30, 48):
                    d.rectangle([wx * s, wy * s, (wx + 22) * s, (wy + 30) * s], fill=shade(col, 0.88))
        # edificios delanteros
        for i, (x, bw, hgt, col, lit, balcony) in enumerate(wd.front):
            top = GROUND - hgt + cam_y
            bot = GROUND + cam_y
            d.rectangle([x * s, top * s, (x + bw) * s, bot * s], fill=col)
            d.rectangle([x * s, top * s, (x + bw) * s, (top + 16) * s], fill=shade(col, 0.82))
            nx = max(2, (bw - 40) // 58)
            gap = (bw - 40 - nx * 34) / max(1, nx - 1)
            for row, wy in enumerate(range(int(top + 50), int(bot - 150), 84)):
                for c in range(nx):
                    wx = x + 20 + c * (34 + gap)
                    on = lit[row % 30][c % 6]
                    wc = (255, 214, 120) if on else (70, 82, 104)
                    if broken > 0 and (row + c + i) % 3 == 0:
                        wc = mix(wc, (40, 45, 55), broken)
                    d.rectangle([wx * s, wy * s, (wx + 34) * s, (wy + 46) * s], fill=wc)
                    if broken > 0.3 and (row + c + i) % 3 == 0:
                        d.line([((wx + 4) * s, (wy + 6) * s), ((wx + 30) * s, (wy + 40) * s)], fill=(200, 220, 235), width=2 * s)
                        d.line([((wx + 30) * s, (wy + 8) * s), ((wx + 10) * s, (wy + 30) * s)], fill=(200, 220, 235), width=2 * s)
                if balcony and row % 2 == 1:
                    by = wy + 50
                    d.rectangle([(x + 12) * s, by * s, (x + bw - 12) * s, (by + 6) * s], fill=shade(col, 0.7))
                    for bx in range(int(x + 16), int(x + bw - 12), 14):
                        d.line([(bx * s, (by - 26) * s), (bx * s, by * s)], fill=shade(col, 0.6), width=2 * s)
                    d.line([((x + 12) * s, (by - 26) * s), ((x + bw - 12) * s, (by - 26) * s)], fill=shade(col, 0.6), width=3 * s)
            # puerta / escaparate
            d.rectangle([(x + bw * 0.3) * s, (bot - 120) * s, (x + bw * 0.7) * s, bot * s], fill=shade(col, 0.65))
        # acera y calzada
        g = GROUND + cam_y
        d.rectangle([0, g * s, W * s, (g + 150) * s], fill=(200, 200, 204))
        d.rectangle([0, (g + 150) * s, W * s, (g + 168) * s], fill=(160, 160, 166))
        d.rectangle([0, (g + 168) * s, W * s, (g + 600) * s], fill=(96, 100, 112))
        for k in range(-1, 8):
            x = k * 180 + 40
            d.rectangle([x * s, (g + 300) * s, (x + 90) * s, (g + 312) * s], fill=(235, 235, 235))
        # semáforo y farola
        tx = 980
        d.rectangle([(tx - 7) * s, (g - 420) * s, (tx + 7) * s, (g + 4) * s], fill=(55, 60, 70))
        d.rounded_rectangle([(tx - 30) * s, (g - 560) * s, (tx + 30) * s, (g - 410) * s], radius=12 * s, fill=(45, 48, 56))
        red = t < self.tl.t_float + 30
        for j, c in enumerate(((235, 70, 60), (240, 180, 50), (70, 200, 110))):
            on = (j == 0 and red)
            d.ellipse([(tx - 18) * s, (g - 550 + j * 46) * s, (tx + 18) * s, (g - 514 + j * 46) * s], fill=c if on else shade(c, 0.35))
        lx = self.lamp_x
        d.rectangle([(lx - 8) * s, (g - 520) * s, (lx + 8) * s, (g + 4) * s], fill=(55, 60, 70))
        d.rounded_rectangle([(lx - 8) * s, (g - 528) * s, (lx + 60) * s, (g - 514) * s], radius=7 * s, fill=(55, 60, 70))
        d.polygon([((lx + 36) * s, (g - 516) * s), ((lx + 70) * s, (g - 516) * s), ((lx + 62) * s, (g - 496) * s), ((lx + 44) * s, (g - 496) * s)], fill=(255, 225, 140))
        if fountain:
            fx = 540
            d.rounded_rectangle([(fx - 190) * s, (g + 40) * s, (fx + 190) * s, (g + 120) * s], radius=24 * s, fill=(170, 175, 185))
            d.rectangle([(fx - 165) * s, (g + 46) * s, (fx + 165) * s, (g + 70) * s], fill=(110, 170, 225))
            d.rectangle([(fx - 22) * s, (g - 90) * s, (fx + 22) * s, (g + 50) * s], fill=(160, 165, 175))
            d.ellipse([(fx - 80) * s, (g - 110) * s, (fx + 80) * s, (g - 76) * s], fill=(150, 155, 168))

    lamp_x = 840

    # ─── escenas ───
    def scene_street(self, img, d, t):
        tl = self.tl
        # cámara: plano general; al despegar acerca al protagonista; al saltar sube con él
        zoom_in = smooth(tl.t_despegue - 0.2, tl.t_despegue + 0.6, t) * (1 - smooth(tl.t_tierra - 0.4, tl.t_tierra, t))
        cam_y = 0.0
        if tl.t_sky <= t < tl.t_fuente:
            u = (t - tl.t_sky) / (tl.t_fuente - tl.t_sky)
            cam_y = 1400 * ease_out(smooth(0.1, 0.9, u))
        floating = t >= tl.t_float
        fountain = t >= tl.t_fuente
        broken = smooth(tl.t_cristales, tl.t_cristales + 0.3, t)
        if fountain and t >= tl.t_sky:
            cam_y = 380 * smooth(tl.t_fuente, tl.t_fuente + 0.01, t) * 0 + 0
        # cielo
        sky = self.grad("sky", (84, 132, 196), (200, 224, 240))
        img.paste(sky)
        self.city(img, d, t, cam_y, fountain=fountain, broken=broken)
        g = GROUND + cam_y
        objs = []
        # coches (detrás de la acera, en la calzada)
        for i, (col, cw, kind, x0, gy) in enumerate(self.cars):
            lift = self.lift(560 + 160 * i, 1.0, t, i) if floating else 0.0
            rot = (25 * (i - 1) * smooth(tl.t_float, tl.t_float + 6, t)) if floating and t < tl.t_return else 0.0
            x = x0 + (40 * (i - 1) * smooth(tl.t_float, tl.t_return, t))
            y = gy + cam_y - lift
            if t >= tl.t_return and i == 0:  # cae encima de la furgoneta: «coches que aplastan coches»
                x = x0 + (520 - x0) * smooth(tl.t_return, tl.t_return + 0.6, t)
                y = min(y, self.cars[2][4] + cam_y - 190)
            objs.append(("car", i, x, y, rot))
        for _, i, x, y, rot in sorted(objs, key=lambda o: o[1] != 2):
            im = self.car_imgs[i]
            if i == 2 and t >= tl.t_return + 0.55:  # la furgoneta queda aplastada
                im = draw_car(self.cars[2][0], self.cars[2][1], "van", squash=1 - 0.28 * smooth(tl.t_return + 0.5, tl.t_return + 0.65, t))
            self.paste(img, im, x, y, rot=rot)
        # papelera
        bl = self.lift(700, 1.1, t, 2.0)
        self.paste(img, self.bin_img, self.bin[0] + 60 * smooth(tl.t_float, tl.t_return, t), self.bin[1] + cam_y - bl,
                   rot=(30 * smooth(tl.t_float, tl.t_return, t) if t < tl.t_return else 0))
        # perro
        dl = self.lift(620, 1.0, t, 3.0)
        dx = self.dog[0] - 30 * min(t, tl.t_float)
        self.paste(img, self.dog_img, dx, self.dog[1] + cam_y - dl, rot=(-35 * smooth(tl.t_float, tl.t_return, t) if t < tl.t_return else 0))
        # personas
        for k, p in enumerate(self.people):
            walk_t = min(t, tl.t_float)
            x = p.x + (22 if k % 2 else -22) * walk_t
            x = (x + 100) % (W + 200) - 100
            pose, arms, face, rot = "stand", "down", "normal", 0.0
            walk = walk_t * 6 + p.phase if t < tl.t_float else 0.0
            y = g
            if t < tl.t_ciudad:  # intro: miran a cámara, se preguntan
                x, walk = p.x, 0.0
                face = "wow" if t > 1.4 else "normal"
            if floating:
                ft = t - tl.t_float
                lift = self.lift(380 + 120 * k, p.rise, t, p.phase)
                if p is self.hero and t > tl.t_jump:
                    jt = min(t, tl.t_return) - tl.t_jump
                    lift += 1700 * (1 - math.exp(-max(0, jt) / 0.9))
                x = x + (p.spread_x - x) * (1 - math.exp(-ft / 3.0))
                y = g - lift
                pose, arms, face = "float", "up", "scared"
                walk = t * 2 + p.phase
                rot = p.spin * min(1.0, ft / 4) * (1 if t < tl.t_return else 0)
                if t >= tl.t_agarra and t < tl.t_return and k == 1:  # agarrado a la farola
                    x, y, rot = self.lamp_x - 10, g - 430, -80 + 5 * math.sin(t * 3)
                    arms = "hold"
                if t >= tl.t_return:
                    pose, arms, rot = ("lie", "down", 90 if k % 2 else -90) if lift <= 0 else ("float", "up", 0)
                    face = "dizzy" if lift <= 0 else "scared"
                    y = g - lift + (0 if lift > 0 else -20)
            self.person(img, p, x, y, pose, face, arms, walk, rot)
        # burbujas de agua
        if t >= tl.t_fuente:
            for i, (bx, by, r, ph) in enumerate(self.bubbles):
                k = smooth(tl.t_fuente + 0.15 * i, tl.t_fuente + 0.15 * i + 0.9, t)
                if k <= 0:
                    continue
                y = g - 120 - (g - 120 - (by + cam_y)) * k
                x = 540 + (bx - 540) * k
                if t > tl.t_return:
                    y += 0.5 * 9.8 * 160 * (t - tl.t_return) ** 2
                    if y > g + 60:
                        continue
                rr = r * k
                wob = math.sin(t * 4 + ph) * 0.08
                d.ellipse([(x - rr * (1 + wob)) * S, (y - rr * (1 - wob)) * S, (x + rr * (1 + wob)) * S, (y + rr * (1 - wob)) * S],
                          fill=(120, 185, 240), outline=(220, 240, 255), width=4 * S)
                d.ellipse([(x - rr * 0.5) * S, (y - rr * 0.6) * S, (x - rr * 0.15) * S, (y - rr * 0.3) * S], fill=(235, 248, 255))
        # salpicadura y charcos al caer el agua
        if t > tl.t_return + 0.35:
            k = smooth(tl.t_return + 0.35, tl.t_return + 0.9, t)
            d.ellipse([60 * S, (g + 60) * S, 1020 * S, (g + 140) * S], fill=mix((200, 200, 204), (120, 180, 230), k * 0.8))
            for dx_, dy_, sz in self.shards:
                u = clamp((t - tl.t_return - 0.35) / 0.9)
                if u >= 1:
                    continue
                px, py = 540 + dx_ * 520 * u, g + 40 + dy_ * 500 * u + 600 * u * u
                d.ellipse([(px - sz) * S, (py - sz) * S, (px + sz) * S, (py + sz) * S], fill=(140, 195, 245))
        # cristales que estallan
        if tl.t_cristales <= t < tl.t_cristales + 1.2:
            u = (t - tl.t_cristales) / 1.2
            for j, (dx_, dy_, sz) in enumerate(self.shards):
                for bx in (230, 760):
                    px, py = bx + dx_ * 420 * u, 700 + cam_y + dy_ * 300 * u + 900 * u * u
                    d.polygon([(px * S, (py - sz) * S), ((px + sz * 0.7) * S, py * S), (px * S, (py + sz * 0.5) * S)], fill=(205, 230, 250))
        # intro: signo de interrogación
        if t < tl.t_ciudad:
            k = back_out((t - 1.5) / 0.5)
            if k > 0:
                self.qmark(img, 540, 1040, 150 * k)

    def qmark(self, img, x, y, size, col=(255, 200, 60)):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        f = font("ExtraBold", size * S)
        d.text((x * S + 6 * S, y * S + 8 * S), "?", font=f, fill=(0, 0, 0, 60), anchor="mm")
        d.text((x * S, y * S), "?", font=f, fill=col + (255,), anchor="mm")
        img.alpha_composite(lay)

    def scene_globe(self, img, d, t, alerts=False):
        bg = self.grad("space", (8, 16, 38), (20, 38, 70))
        img.paste(bg)
        for x, y, r in self.stars:
            tw = 0.6 + 0.4 * math.sin(t * 2 + x)
            c = int(200 * tw)
            d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(c, c, min(255, c + 30)))
        cx, cy, R = 540, 900, 330
        # Tierra (proyección ortográfica de la máscara real de tierra/mar)
        if not hasattr(self, "_gx"):
            n = int(2 * R * S)
            yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
            nx, ny = (xx - n / 2) / (n / 2), (yy - n / 2) / (n / 2)
            rr = nx ** 2 + ny ** 2
            inside = rr <= 1
            nz = np.sqrt(np.clip(1 - rr, 0, 1))
            tilt = math.radians(18)
            y2 = ny * math.cos(tilt) - nz * math.sin(tilt)
            z2 = ny * math.sin(tilt) + nz * math.cos(tilt)
            self._gx = (inside, np.degrees(np.arcsin(np.clip(-y2, -1, 1))), np.degrees(np.arctan2(nx, z2)), nz, rr, n)
        inside, lat, lon0, nz, rr, n = self._gx
        lon = (lon0 + t * 22 + 20) % 360 - 180
        li = np.clip(((90 - lat) / 180 * 360).astype(int), 0, 359)
        lj = np.clip(((lon + 180) / 360 * 720).astype(int), 0, 719)
        land = self.land[li, lj]
        ocean = np.array([45, 115, 200], np.float32)
        green = np.array([105, 180, 95], np.float32)
        col = np.where(land[..., None], green, ocean)
        light = (0.55 + 0.45 * np.clip(nz * 0.8 + 0.2 * (-(np.mgrid[0:n, 0:n][1] - n / 2) / (n / 2)), 0, 1))[..., None]
        col = col * light
        a = np.zeros((n, n, 4), np.uint8)
        a[..., :3] = col.clip(0, 255).astype(np.uint8)
        a[..., 3] = (inside * 255).astype(np.uint8)
        earth = Image.fromarray(a)
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([(cx - R - 30) * S, (cy - R - 30) * S, (cx + R + 30) * S, (cy + R + 30) * S], fill=(90, 160, 255, 90))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30 * S)))
        img.alpha_composite(earth, (int((cx - R) * S), int((cy - R) * S)))
        if not alerts:
            # flecha de giro
            d.arc([(cx - R - 60) * S, (cy - R - 60) * S, (cx + R + 60) * S, (cy + R + 60) * S], 200 + t * 30 % 10, 250 + t * 30 % 10, fill=(255, 200, 60), width=8 * S)
            return
        # alertas que aparecen por todo el planeta
        u = (t - self.tl.t_planeta) / 3.0
        for i, (ax, ay, ph) in enumerate(self.alerts):
            if ph > u or ax ** 2 + ay ** 2 > 0.9:
                continue
            k = back_out((u - ph) * 4)
            r = 9 * k
            px, py = cx + ax * R, cy + ay * R
            d.ellipse([(px - r) * S, (py - r) * S, (px + r) * S, (py + r) * S], fill=(240, 70, 60), outline=(255, 210, 200), width=2 * S)

    def scene_end(self, img, d, t):
        tl = self.tl
        bg = self.grad("end", (28, 48, 82), (14, 24, 44))
        img.paste(bg)
        if t < tl.t_cta:
            # el protagonista se levanta, mareado, entre los restos
            p = self.hero
            self.person(img, p, 540, 1350, "stand", "dizzy", "down", 0.0, 6 * math.sin(t * 3), scale=1.9)
            for k in range(3):
                a = t * 4 + k * 2.1
                sx, sy = 540 + math.cos(a) * 120, 650 + math.sin(a) * 30
                self.star(d, sx, sy, 22, (255, 210, 70))
            self.qmark(img, 800, 600, 180 * back_out((t - tl.t_question - 0.2) / 0.4))
        else:
            k = back_out((t - tl.t_cta) / 0.5)
            cx, cy = 540, 980 + 16 * math.sin(t * 3)
            w_, h_ = 320 * k, 230 * k
            d.rounded_rectangle([(cx - w_) * S, (cy - h_) * S, (cx + w_) * S, (cy + h_) * S], radius=int(80 * k * S), fill=(255, 200, 60))
            d.polygon([((cx - 120 * k) * S, (cy + h_ - 4) * S), ((cx - 190 * k) * S, (cy + h_ + 110 * k) * S), ((cx - 20 * k) * S, (cy + h_ - 4) * S)], fill=(255, 200, 60))
            for j in range(3):
                bounce = abs(math.sin(t * 5 - j * 0.6)) * 26 * k
                x = cx + (j - 1) * 150 * k
                r = 38 * k
                d.ellipse([(x - r) * S, (cy - r - bounce) * S, (x + r) * S, (cy + r - bounce) * S], fill=(28, 40, 70))

    @staticmethod
    def star(d, x, y, r, col):
        pts = []
        for i in range(10):
            rr = r if i % 2 == 0 else r * 0.45
            a = -math.pi / 2 + i * math.pi / 5
            pts.append(((x + rr * math.cos(a)) * S, (y + rr * math.sin(a)) * S))
        d.polygon(pts, fill=col)

    # ─── texto arriba (palabra a palabra) ───
    def chunks(self):
        if hasattr(self, "_chunks"):
            return self._chunks
        out = []
        for ln in self.nar["lines"]:
            cur = []
            for w in ln["words"]:
                cur.append(w)
                if len(cur) >= 7 or (w[0][-1:] in ",.:;!?" and len(cur) >= 3):
                    out.append(cur)
                    cur = []
            if cur:
                if out and len(cur) <= 2 and out[-1][-1][0][-1:] not in ".?!":
                    out[-1].extend(cur)
                else:
                    out.append(cur)
        self._chunks = out
        return out

    def caption(self, out, t):
        ch = self.chunks()
        cur = None
        for i, c in enumerate(ch):
            end = ch[i + 1][0][1] if i + 1 < len(ch) else self.tl.duration
            if c[0][1] - 0.05 <= t < end:
                cur = c
        if not cur:
            return out
        img = out.convert("RGBA")
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        size = 56
        fr, fb = font("SemiBold", size), font("ExtraBold", size)
        words = [(w, a, b) for w, a, b in cur]
        sp = fr.getlength(" ")
        lines, line, lw = [], [], 0.0
        for w in words:
            ww = fb.getlength(w[0])
            if line and lw + sp + ww > 900:
                lines.append(line)
                line, lw = [], 0.0
            line.append(w)
            lw += (sp if len(line) > 1 else 0) + ww
        lines.append(line)
        y = 250
        for line in lines:
            widths = [(fb if self.is_key(w) or (a <= t < b + 0.15) else fr).getlength(w) for w, a, b in line]
            total = sum(widths) + sp * (len(line) - 1)
            x = (W - total) / 2
            for (w, a, b), ww in zip(line, widths):
                if t >= a - 0.04:
                    k = clamp((t - a + 0.04) / 0.12)
                    key = self.is_key(w)
                    f = fb if key or (a <= t < b + 0.15) else fr
                    col = YEL if key else (255, 255, 255)
                    d.text((x + 2, y + 3), w, font=f, fill=(0, 0, 0, int(70 * k)), anchor="ls")
                    d.text((x, y), w, font=f, fill=col + (int(255 * k),), anchor="ls")
                    if key:
                        ul = ww * ease_out((t - a) / 0.3)
                        d.rounded_rectangle([x, y + 10, x + ul, y + 16], radius=3, fill=YEL + (int(255 * k),))
                x += ww + sp
            y += size * 1.25
        img.alpha_composite(lay)
        return img.convert("RGB")

    @staticmethod
    def is_key(w):
        return w.lower().strip("¿¡") in KEYWORDS or w.lower().strip("¿¡,.:;!?") in {k.strip(",.:;!?") for k in KEYWORDS if k in ("gravedad", "tierra", "miles", "burbujas", "barandillas", "aplastan", "empapan", "despegan", "diez")}

    def hud(self, out, t):
        tl = self.tl
        if not (tl.t_float - 0.3 <= t < tl.t_return + 1.2) or tl.t_tierra <= t < tl.t_anclado:
            return out
        img = out.convert("RGBA")
        d = ImageDraw.Draw(img, "RGBA")
        span = tl.t_return - tl.t_float
        left = max(0.0, 10.0 * (1 - (t - tl.t_float) / span))
        zero = tl.t_float <= t < tl.t_return
        box = [330, 1700, 750, 1810]
        d.rounded_rectangle(box, 55, fill=(20, 30, 50, 200))
        if zero:
            d.text((540, 1755), f"0 g  ·  {left:04.1f} s", font=font("ExtraBold", 54), fill=(130, 215, 255, 255), anchor="mm")
        else:
            d.text((540, 1755), "¡1 g!", font=font("ExtraBold", 58), fill=(255, 95, 80, 255), anchor="mm")
        return img.convert("RGB")

    # ─── fotograma ───
    def frame(self, f):
        tl = self.tl
        t = f / FPS
        img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)
        if tl.t_tierra <= t < tl.t_anclado:
            self.scene_globe(img, d, t)
        elif tl.t_planeta <= t < tl.t_question:
            self.scene_globe(img, d, t, alerts=True)
        elif t >= tl.t_question:
            self.scene_end(img, d, t)
        else:
            self.scene_street(img, d, t)
        out = img.convert("RGB").reduce(S)
        # cámara: zoom suave al protagonista al despegar; temblor al volver la gravedad
        z, cx, cy = 1.0, W / 2, H / 2
        if tl.t_despegue - 0.2 <= t < tl.t_tierra:
            z = 1.0 + 0.45 * smooth(tl.t_despegue - 0.2, tl.t_despegue + 0.6, t) * (1 - smooth(tl.t_tierra - 0.35, tl.t_tierra, t))
            cy = H / 2 + 330 * (z - 1) / 0.45
        if tl.t_return <= t < tl.t_return + 0.9:
            k = 1 - (t - tl.t_return) / 0.9
            z = max(z, 1.04)
            cx += math.sin(t * 80) * 16 * k
            cy += math.cos(t * 65) * 20 * k
        if z != 1.0:
            cw, ch = W / z, H / z
            cx = min(max(cx, cw / 2), W - cw / 2)
            cy = min(max(cy, ch / 2), H - ch / 2)
            out = out.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        # destellos en los cambios de plano
        for tt, s_, dur in ((tl.t_return, 0.5, 0.35), (tl.t_sky, 0.3, 0.2), (tl.t_fuente, 0.35, 0.22), (tl.t_tierra, 0.35, 0.2), (tl.t_anclado, 0.35, 0.2), (tl.t_planeta, 0.35, 0.2), (tl.t_question, 0.3, 0.2)):
            if 0 <= t - tt < dur:
                out = Image.blend(out, Image.new("RGB", (W, H), (255, 255, 255)), s_ * (1 - (t - tt) / dur))
        # ingravidez: tono algo más frío
        if tl.t_float < t < tl.t_return and not (tl.t_tierra <= t < tl.t_anclado):
            k = 0.10 * min(1, (t - tl.t_float) / 1.5)
            a = np.asarray(out).astype(np.float32)
            out = Image.fromarray((a * (1 - k) + np.array([120, 160, 220]) * k).clip(0, 255).astype(np.uint8))
        out = self.hud(out, t)
        return self.caption(out, t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracion", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="*", type=int)
    a = ap.parse_args()
    nar = json.load(open(os.path.join(a.narracion, "narracion.json"), encoding="utf-8"))
    an = Animator(nar)
    n = int(an.tl.duration * FPS)
    os.makedirs(a.out, exist_ok=True)
    frames = a.only or list(range(n))
    t0 = time.time()
    for i, f in enumerate(frames):
        an.frame(f).save(os.path.join(a.out, f"f{f:05d}.jpg"), quality=93)
        if i % 90 == 0:
            print(f"[plano] fotograma {f}/{n} · {time.time() - t0:.0f} s", flush=True)
    print(f"[plano] {len(frames)} fotogramas en {time.time() - t0:.0f} s · total {n}")


if __name__ == "__main__":
    main()
