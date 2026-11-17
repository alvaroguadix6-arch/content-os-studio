"""¿Qué pasaría si la Tierra se quedara sin luz solar durante 5 años?"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, City, Person, Video, W, H, S, YEL, back_out, clamp, draw_car, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "suspense", 76


class VIDEO(Video):
    NAME = "sol"
    KEYWORDS = {"sol", "cinco", "años", "ocho", "minutos", "negro", "semana", "cero", "escarcha", "fotosíntesis", "cultivos", "setenta",
                "grados", "congelarían", "líquida", "bajo", "tierra", "geotérmico", "hidrotermales", "irreconocible", "sobrevivirías", "comentarios"}

    def setup(self):
        r = random.Random(8)
        self.city = City(seed=6)
        self.people = [Person(r, x, h, shirt=c) for (x, h), c in zip(((170, 210), (420, 225), (660, 205), (900, 220)),
                       ((70, 130, 210), (60, 170, 140), (235, 185, 60), (150, 100, 190)))]
        self.snow = [(r.uniform(0, W), r.uniform(0, H), r.uniform(2, 6), r.uniform(0.6, 1.4)) for _ in range(260)]
        self.cars = [draw_car(c, 300, k) for c, k in (((215, 70, 70), "car"), ((250, 205, 60), "taxi"))]
        self.plants = [(x, r.uniform(0.85, 1.15), r.uniform(0, 6)) for x in range(40, 1080, 62)]
        self.fish = [(r.uniform(0, W), r.uniform(1050, 1650), r.uniform(30, 70) * r.choice((-1, 1)), r.uniform(0.7, 1.3)) for _ in range(14)]
        self.worms = [(r.uniform(260, 820), r.uniform(0.8, 1.2), r.uniform(0, 6)) for _ in range(16)]
        self.bubbles = [(r.uniform(0, W), r.uniform(0, 1), r.uniform(4, 12)) for _ in range(40)]
        self.t_off = self.w("intro", "dejara")
        self.t_black = self.w("oscuro", "después")
        self.shakes = [(self.t_off, 0.6), (self.start("vuelta") + 0.5, 0.5)]

    def build_scenes(self):
        return [(0.0, "intro"), (self.start("oscuro") - 0.2, "ciudad"), (self.start("semana") - 0.15, "hielo"),
                (self.start("plantas") - 0.15, "campo"), (self.start("anio") - 0.15, "globo"), (self.start("oceano") - 0.15, "mar"),
                (self.start("refugio") - 0.15, "refugio"), (self.start("vida") - 0.15, "fondo"), (self.start("vuelta") - 0.15, "vuelta"),
                (self.start("cta") - 0.1, "fin")]

    # ───── escenas ─────
    def sun(self, img, d, x, y, R, k, t):
        """Sol con brillo k (0 apagado – 1 encendido)."""
        if k > 0.02:
            self.glow(img, x, y, R * 2.2, (255, 190, 80), 140 * k, blur=R * 0.9)
            for i in range(14):
                a = i / 14 * 2 * math.pi + t * 0.15
                l1, l2 = R * 1.15, R * (1.45 + 0.1 * math.sin(t * 3 + i))
                self.Ln(d, [(x + math.cos(a) * l1, y + math.sin(a) * l1), (x + math.cos(a) * l2, y + math.sin(a) * l2)], mix((80, 60, 40), (255, 210, 90), k), 10)
        self.E(d, x, y, R, mix((40, 30, 30), (255, 196, 60), k))
        self.E(d, x - R * 0.25, y - R * 0.25, R * 0.55, mix((50, 38, 36), (255, 222, 120), k))

    def s_intro(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        k = 1 - smooth(self.t_off - 0.05, self.t_off + 0.45, t)
        self.stars(d, t, 0.4 + 0.6 * (1 - k))
        self.sun(img, d, 300, 640, 210, k, t)
        self.globe(img, 760, 1220, 230, t, spin=18, night=1 - k, glow_a=90 * k)
        if t > self.t_off:
            self.pop_text(img, 540, 1580, "5 AÑOS", 120, t, self.t_off + 0.4, YEL)

    def s_ciudad(self, img, d, t, lt, u):
        n = smooth(self.t_black - 0.8, self.t_black + 1.2, t)
        top = mix((250, 160, 90), (5, 8, 20), n)
        bot = mix((255, 210, 150), (12, 16, 34), n)
        self.bgdyn(img, top, bot)
        if n > 0.3:
            self.stars(d, t, (n - 0.3) * 1.2)
        self.sun(img, d, 760, 470 + 260 * smooth(0, 1, (t - self.start("oscuro")) / 7), 120, 1 - n, t)
        self.city.draw(d, t, night=n, lights=n)
        g = self.city.ground
        self.paste(img, self.cars[0], 300, g + 330)
        self.paste(img, self.cars[1], 800, g + 330)
        for i, p in enumerate(self.people):
            look = n > 0.5
            self.person(img, p, p.x + (0 if look else 20 * math.sin(t * 0.6 + i)), g, "stand", "wow" if look else "normal",
                        "up" if look and i % 2 else "down", t * 2 if not look else 0)
        if n > 0.2:  # farolas
            for lx in (80, 560, 1000):
                self.Ln(d, [(lx, g + 4), (lx, g - 470)], (50, 55, 65), 14)
                self.glow(img, lx, g - 470, 90, (255, 214, 140), 150 * n)
                self.E(d, lx, g - 470, 18, (255, 230, 170))

    def s_hielo(self, img, d, t, lt, u):
        img.paste(Image_grad(self, "night", (5, 8, 20), (14, 20, 38)))
        self.stars(d, t, 0.8)
        fr = smooth(0, 4.5, lt)
        self.city.draw(d, t, night=1.0, frost=fr, lights=1.0)
        g = self.city.ground
        for i, p in enumerate(self.people):
            sh = math.sin(t * 40 + i) * 2.5 * fr  # tiritan
            self.person(img, p, p.x + sh, g, "stand", "scared", "down")
            if (t * 1.3 + i * 0.3) % 1 < 0.5:  # vaho
                k = ((t * 1.3 + i * 0.3) % 1) / 0.5
                self.E(d, p.x + 30 + 30 * k, g - p.h * 0.88 - 10 * k, 12 + 18 * k, (220, 230, 240, ), None)
        for x, y, r, sp in self.snow:
            yy = (y + t * 90 * sp) % H
            self.E(d, (x + 20 * math.sin(t + y)) % W, yy, r * 0.8, (235, 242, 250))
        # coches cubiertos de escarcha
        for i, cx in enumerate((300, 800)):
            self.paste(img, self.cars[i], cx, g + 330)
            self.R(d, cx - 150, g + 330 - 145, cx + 150, g + 330 - 120, (240, 246, 252), radius=12 * fr + 1)

    def s_campo(self, img, d, t, lt, u):
        img.paste(Image_grad(self, "field", (6, 10, 24), (20, 28, 46)))
        self.stars(d, t, 0.6)
        wil = smooth(0.3, 5.5, lt)
        gy = 1120
        self.R(d, 0, gy, W, H + 40, mix((70, 120, 60), (95, 80, 55), wil))
        for row in range(3):
            y = gy + 160 + row * 260
            sc = 0.9 + row * 0.35
            for x, k, ph in self.plants[::2]:
                xx = x + (row % 2) * 60 - 20
                hgt = 260 * k * sc * (1 - 0.25 * wil)
                droop = wil * (1.2 + 0.3 * math.sin(ph)) + 0.05 * math.sin(t * 1.5 + ph)
                stem = (90, 160, 80) if wil < 0.5 else mix((90, 160, 80), (120, 100, 60), (wil - 0.5) * 2)
                top = (xx + math.sin(droop) * hgt * 0.25, y - hgt)
                self.Ln(d, [(xx, y), (xx + math.sin(droop) * hgt * 0.1, y - hgt * 0.6), top], stem, 10 * sc)
                for side in (-1, 1):
                    lx, ly = xx + side * 30 * sc, y - hgt * 0.45 + 30 * wil * sc
                    self.P(d, [(xx, y - hgt * 0.4), (lx, ly - 14 * sc), (lx + side * 26 * sc, ly + 10 * sc * (1 + wil))], stem)
                # cabeza del girasol: se agacha y pierde el color
                hx, hy = top[0] + math.sin(droop) * 30 * sc, top[1] + (1 - math.cos(droop)) * 40 * sc
                pet = mix((255, 200, 40), (130, 95, 50), wil)
                R_ = 42 * sc
                for p_ in range(12):
                    a = p_ / 12 * 2 * math.pi
                    self.E(d, hx + math.cos(a) * R_ * 0.9, hy + math.sin(a) * R_ * 0.9 * math.cos(droop * 0.8), R_ * 0.4, pet,
                           ry=R_ * 0.4 * max(0.3, math.cos(droop * 0.8)))
                self.E(d, hx, hy, R_ * 0.6, mix((110, 70, 30), (70, 50, 35), wil), ry=R_ * 0.6 * max(0.3, math.cos(droop * 0.8)))
        # árbol que pierde las hojas
        tx, ty = 820, 1120
        self.R(d, tx - 22, ty - 380, tx + 22, ty, (90, 65, 45))
        leaves = 1 - wil
        if leaves > 0.05:
            self.E(d, tx, ty - 470, 150 * leaves ** 0.5, mix((80, 160, 80), (150, 120, 60), wil), ry=110 * leaves ** 0.5)
        for i in range(18):
            a = i / 18 * 2 * math.pi
            fx, fy = tx + math.cos(a) * 120, ty - 470 + math.sin(a) * 90
            if (i / 18) < leaves:
                self.E(d, fx, fy, 60, mix((80, 160, 80), (150, 120, 60), wil))
            else:
                fall = ((t * 0.7 + i * 0.13) % 1)
                self.E(d, fx + 40 * math.sin(t * 2 + i), fy + fall * 500, 10, (160, 120, 60))

    def s_globo(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        self.stars(d, t, 1.0)
        ice = smooth(0, 4.0, lt)
        self.globe(img, 540, 950, 360, t, spin=16, night=0.55, ice=0.15 + 0.85 * ice, glow_col=(170, 210, 255), glow_a=70)

    def s_mar(self, img, d, t, lt, u):
        img.paste(Image_grad(self, "sea", (40, 90, 150), (5, 20, 45)))
        ice = 140 + 160 * smooth(0, 4, lt)
        top = 520
        self.R(d, 0, 0, W, top, (10, 14, 28))
        self.stars(d, t, 0.5)
        self.R(d, 0, top - 20, W, top + ice, (225, 236, 248))
        for i in range(9):  # grietas del hielo
            x = 60 + i * 120
            self.Ln(d, [(x, top), (x + 20, top + ice * 0.4), (x - 10, top + ice * 0.8)], (180, 205, 230), 3)
        for x, y, v, k in self.fish:
            xx = (x + v * t) % (W + 200) - 100
            dirn = 1 if v > 0 else -1
            self.E(d, xx, y, 34 * k, (255, 160, 70), ry=16 * k)
            self.P(d, [(xx - dirn * 30 * k, y), (xx - dirn * 55 * k, y - 16 * k), (xx - dirn * 55 * k, y + 16 * k)], (255, 140, 60))
            self.E(d, xx + dirn * 18 * k, y - 4 * k, 4 * k, (20, 20, 30))
        for x, ph, r in self.bubbles:
            y = 1800 - ((t * 0.12 + ph) % 1) * (1800 - top - ice)
            self.E(d, x, y, r, None, (180, 220, 255), 2)
        self.text(img, 540, top + ice / 2, "HIELO", 64, (120, 160, 200), shadow=False, alpha=0.8)
        self.text(img, 540, top + ice + 150, "AGUA LÍQUIDA", 52, (170, 220, 255), shadow=False, alpha=smooth(0.8, 1.6, lt))

    def s_refugio(self, img, d, t, lt, u):
        img.paste(Image_grad(self, "night", (5, 8, 20), (14, 20, 38)))
        self.stars(d, t, 0.7)
        gy = 700
        self.R(d, 0, gy, W, gy + 60, (240, 246, 252))
        self.R(d, 0, gy + 60, W, H + 40, (70, 52, 42))
        for i in range(30):
            x = (i * 97) % W
            self.E(d, x, gy + 200 + (i * 53) % 1100, 18, (85, 64, 52))
        # túnel con luz cálida
        ty0, ty1 = 1050, 1500
        self.R(d, 60, ty0, 1020, ty1, (255, 196, 120), radius=60)
        self.glow(img, 540, (ty0 + ty1) / 2, 420, (255, 170, 80), 90)
        for lx in range(160, 1000, 200):
            self.E(d, lx, ty0 + 40, 14, (255, 245, 210))
        # tubería geotérmica con vapor
        px = 930
        self.R(d, px - 22, ty1, px + 22, H + 40, (150, 90, 60))
        for k in range(6):
            ph = (t * 0.6 + k / 6) % 1
            self.E(d, px - 60 * ph, ty1 - 30 - 260 * ph, 20 + 40 * ph, (255, 235, 210))
        for i, p in enumerate(self.people[:3]):
            x = 200 + ((t * 40 * (1 if i % 2 else -1) + i * 250) % 640)
            self.person(img, p, x, ty1 - 6, "stand", "smile", "down", t * 5 + i, scale=0.95)
        self.text(img, 540, gy + 200, "CALOR GEOTÉRMICO", 46, (255, 200, 140), alpha=smooth(0.3, 1.0, lt))

    def s_fondo(self, img, d, t, lt, u):
        img.paste(Image_grad(self, "deep", (6, 18, 40), (2, 6, 14)))
        gy = 1500
        self.R(d, 0, gy, W, H + 40, (40, 36, 40))
        # fumarola negra con penacho
        vx = 540
        self.P(d, [(vx - 90, gy + 10), (vx - 35, gy - 380), (vx + 35, gy - 380), (vx + 90, gy + 10)], (55, 48, 50))
        self.glow(img, vx, gy - 380, 120, (255, 120, 60), 120)
        for k in range(14):
            ph = (t * 0.35 + k / 14) % 1
            self.E(d, vx + 50 * math.sin(k + t) * ph, gy - 400 - ph * 900, 30 + 80 * ph, (45 + int(40 * ph),) * 3)
        for x, k, ph in self.worms:  # gusanos de tubo
            h_ = 140 * k
            sway = 12 * math.sin(t * 1.8 + ph)
            self.Ln(d, [(x, gy + 5), (x + sway * 0.5, gy - h_ * 0.5), (x + sway, gy - h_)], (235, 230, 220), 14)
            self.E(d, x + sway, gy - h_, 14, (220, 40, 50))
        for i in range(5):  # cangrejos
            x = (150 + i * 200 + 25 * t * (1 if i % 2 else -1)) % W
            self.E(d, x, gy - 8, 26, (240, 210, 200), ry=14)
            for s_ in (-1, 1):
                self.Ln(d, [(x + s_ * 20, gy - 10), (x + s_ * 40, gy - 30), (x + s_ * 50, gy - 18)], (240, 210, 200), 5)
        self.glow(img, 540, 1200, 600, (60, 140, 200), 40)

    def s_vuelta(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        k = smooth(0.3, 1.2, lt)
        self.stars(d, t, 1 - 0.5 * k)
        self.sun(img, d, 280, 600, 200, k, t)
        self.globe(img, 740, 1200, 260, t, spin=18, night=1 - k, ice=1.0 - 0.35 * smooth(1.0, 4.0, lt), glow_col=(170, 210, 255), glow_a=60 + 60 * k)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    # ───── indicador inferior ─────
    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name == "ciudad":
            left = max(0.0, 500 * (1 - (t - self.start("oscuro")) / max(0.5, self.t_black - self.start("oscuro"))))
            txt = f"LUZ EN CAMINO · {int(left // 60)} min {int(left % 60):02d} s" if left > 0 else "SIN LUZ SOLAR"
            return self.pill(out, txt, CYAN if left > 0 else RED, size=46)
        if name == "hielo":
            temp = 15 - 18 * smooth(self.start("semana"), self.end("semana"), t)
            return self.pill(out, f"SEMANA 1 · {temp:+.0f} °C", CYAN)
        if name == "campo":
            return self.pill(out, "MES 1 · SIN FOTOSÍNTESIS", (150, 230, 140), size=46)
        if name == "globo":
            temp = -3 - 67 * smooth(self.start("anio"), self.w("anio", "setenta") + 0.3, t)
            return self.pill(out, f"AÑO 1 · {temp:.0f} °C", CYAN)
        if name == "vuelta":
            return self.pill(out, "AÑO 5 · VUELVE LA LUZ", YEL)
        return out

    def sfx_events(self):
        return [(self.t_off, "click", 0.9), (self.t_off + 0.1, "boom", 0.6), (self.t_black, "rumble", 0.4),
                (self.start("semana"), "wind", 0.5), (self.start("semana") + 3, "wind", 0.4), (self.start("anio") + 0.5, "crack", 0.6),
                (self.start("oceano") + 0.5, "crack", 0.5), (self.start("vida"), "drip", 0.4), (self.start("vuelta") + 0.4, "riser", 0.5),
                (self.start("vuelta") + 1.2, "shimmer", 0.6), (self.start("cta"), "pop", 0.6)]

    def music_plan(self):
        return [(0, 0.3), (self.t_off, 0.6), (self.start("semana"), 0.5), (self.start("anio"), 0.8), (self.start("refugio"), 0.45),
                (self.start("vuelta"), 0.9), (self.start("cta"), 0.4), (self.duration, 0.3)]


_G = {}


def Image_grad(v, key, top, bottom):
    return v.grad(key, top, bottom)


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
