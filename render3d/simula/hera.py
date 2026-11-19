"""NIVEL OCULTO · Hera llega al asteroide que la NASA golpeó (noviembre de 2026).

Fuentes: ESA (primera luz y primeras imágenes de Dídimo y Dimorfo), Space.com, Smithsonian, Spektrum (cresta
ecuatorial, zonas rocosas y lisas, 25 bandas de color de HyperScout H, imágenes detalladas previstas para el
25-11-2026), NASA (DART acortó la órbita de Dimorfo unos 32 minutos; ninguno es un peligro para la Tierra).
"""
from __future__ import annotations

import math
import random

from asteroide import VIDEO as AST
from motor import CYAN, RED, WHITE, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "espacio", 88
ESA = (80, 150, 255)


class VIDEO(AST):
    NAME = "hera"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"nasa", "asteroide", "propósito", "dart", "dimorfo", "dídimo", "treinta", "dos", "minutos", "europea", "hera", "coche",
                "años", "llegar", "kilómetros", "cresta", "ecuador", "rocosas", "lisas", "veinticinco", "colores", "noviembre",
                "huella", "peligro", "tierra", "escudo", "comentarios"}

    def setup(self):
        import numpy as np
        r = random.Random(17)
        self.rock = [(math.cos(a) * r.uniform(0.8, 1.1), math.sin(a) * r.uniform(0.8, 1.1)) for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]
        self.craters = [(r.uniform(-0.5, 0.5), r.uniform(-0.5, 0.5), r.uniform(0.1, 0.2)) for _ in range(5)]
        self.boulders = [(r.uniform(-1, 1), r.uniform(-0.35, 0.35), r.uniform(6, 16)) for _ in range(40)]
        self.t_dart = self.w("intro", "estrelló", 0.3)
        self.shakes = [(self.t_dart, 0.8)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "golpe"), (st("dart") - 0.15, "orbita"), (st("hera") - 0.15, "nave"), (st("viaje") - 0.15, "viaje"),
                (st("cresta") - 0.15, "cresta"), (st("colores") - 0.15, "colores"), (st("crater") - 0.15, "crater"),
                (st("calma") - 0.15, "calma"), (st("cta") - 0.1, "fin")]

    def spacecraft(self, d, x, y, s=1.0, col=(225, 225, 235)):
        self.R(d, x - 26 * s, y - 22 * s, x + 26 * s, y + 22 * s, col, radius=4 * s)
        for sx in (-1, 1):
            self.R(d, x + sx * 30 * s, y - 9 * s, x + sx * 110 * s, y + 9 * s, (50, 80, 160))
            for i in range(4):
                xx = x + sx * (36 + i * 19) * s
                self.Ln(d, [(xx, y - 9 * s), (xx, y + 9 * s)], (90, 120, 200), 2)
        self.E(d, x, y - 34 * s, 18 * s, (240, 240, 245), ry=8 * s)

    def didymos(self, img, d, x, y, r, t, detail=1.0):
        """Dídimo: forma de peonza con cresta ecuatorial."""
        pts = []
        for i in range(40):
            a = i / 40 * 2 * math.pi
            rr = r * (1 + 0.16 * abs(math.cos(a)) ** 8 * detail + 0.03 * math.sin(7 * a + 1))
            pts.append((x + math.cos(a) * rr * 1.04, y + math.sin(a) * rr * 0.92))
        self.P(d, pts, (140, 128, 116))
        self.P(d, [p for p in pts if p[1] > y] + [(x - r, y)], (118, 108, 98))
        if detail > 0.3:
            self.Ln(d, [(x - r * 1.18, y), (x + r * 1.18, y)], (170, 160, 148), 6 * detail)
            for bx, by, br in self.boulders:
                px = x + bx * r * 0.9 * math.cos(t * 0.15)
                py = y + by * r
                self.E(d, px, py, br * r / 300, (100, 92, 84))

    def s_golpe(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        cx, cy = 540, 1000
        self.didymos(img, d, cx, cy, 170, t, 0.5)
        mx, my = cx + 320, cy - 140
        self.asteroid(d, mx, my, 50, t * 0.5, (150, 140, 128))
        if t < self.t_dart:
            k = clamp(t / max(0.5, self.t_dart))
            self.spacecraft(d, 100 + (mx - 100) * k, 300 + (my - 300) * k, 0.8)
        elif t - self.t_dart < 0.8:
            self.glow(img, mx, my, 160, (255, 230, 170), 255 * (1 - (t - self.t_dart) / 0.8))
        self.pop_text(img, 540, 1500, "DART · 2022", 90, t, self.t_dart + 0.2, YEL)

    def s_orbita(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        cx, cy = 540, 980
        shrink = smooth(self.w("dart", "acortó") - 0.2, self.w("dart", "acortó") + 1.2, t)
        R = 380 - 50 * shrink
        d.ellipse([(cx - 380) * S, (cy - 120) * S, (cx + 380) * S, (cy + 120) * S], outline=(80, 90, 120), width=3 * S)
        d.ellipse([(cx - R) * S, (cy - R * 0.32) * S, (cx + R) * S, (cy + R * 0.32) * S], outline=YEL, width=4 * S)
        a = t * 1.3
        mx, my = cx + math.cos(a) * R, cy + math.sin(a) * R * 0.32
        if math.sin(a) < 0:
            self.asteroid(d, mx, my, 40, t, (150, 140, 128))
        self.didymos(img, d, cx, cy, 150, t, 0.6)
        if math.sin(a) >= 0:
            self.asteroid(d, mx, my, 40, t, (150, 140, 128))
        self.text(img, 540, 650, "DÍDIMO + DIMORFO", 60, WHITE, alpha=smooth(0.2, 0.6, lt))
        self.pop_text(img, 540, 1450, "ÓRBITA −32 min", 84, t, self.w("dart", "treinta"), YEL)

    def s_nave(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        k = back_out(lt / 0.6)
        self.spacecraft(d, 540, 900 + 15 * math.sin(t), max(0.05, 2.4 * k))
        self.pop_text(img, 540, 620, "ESA · HERA", 96, t, self.w("hera", "hera") - 0.1, ESA)
        if t > self.w("hera", "coche"):
            from motor import draw_car
            car = getattr(self, "_car2", None) or draw_car((220, 80, 70), 300, "car")
            self._car2 = car
            self.paste(img, car, 540, 1390)
            self.text(img, 540, 1460, "≈ COCHE PEQUEÑO", 50, WHITE)

    def s_viaje(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        self.globe(img, 210, 1400, 120, t, spin=20)
        self.didymos(img, d, 860, 640, 70, t, 0.4)
        k = ease_out(lt / 3.5)
        pts = [(210 + (860 - 210) * f, 1400 + (640 - 1400) * f - 380 * math.sin(f * math.pi)) for f in [i / 30 for i in range(31)]]
        n = max(2, int(31 * k))
        for i in range(0, n - 1, 2):
            self.Ln(d, [pts[i], pts[i + 1]], ESA, 5)
        self.spacecraft(d, pts[n - 1][0], pts[n - 1][1], 0.6)
        self.text(img, 540, 1580, "2024 → 2026", 70, YEL)

    def s_cresta(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 0.6)
        self.didymos(img, d, 540, 1000, 360 + 30 * ease_out(lt / 3), t, 1.0)
        k = smooth(self.w("cresta", "cresta") - 0.2, self.w("cresta", "cresta") + 0.4, t)
        if k > 0:
            self.Ln(d, [(150, 1000), (930, 1000)], YEL, 6)
            self.text(img, 540, 560, "CRESTA ECUATORIAL", 66, YEL, alpha=k)
        self.text(img, 540, 1560, "A ≈ 30–60 km", 56, CYAN)

    def s_colores(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 0.6)
        self.didymos(img, d, 540, 1000, 330, t, 1.0)
        k = smooth(0.2, 2.6, lt)
        n = int(25 * k)
        for i in range(n):  # bandas de color que escanean el asteroide
            hue = i / 25
            col = tuple(int(127 + 127 * math.sin(2 * math.pi * (hue + off))) for off in (0, 1 / 3, 2 / 3))
            self.R(d, 120 + i * 33.6, 620, 150 + i * 33.6, 680, col)
        self.pop_text(img, 540, 1560, f"{max(1, n)} COLORES", 80, t, self.w("colores", "veinticinco"), YEL)

    def s_crater(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        self.didymos(img, d, 460, 1050, 250, t, 0.8)
        self.asteroid(d, 800, 820, 90, t * 0.2, (150, 140, 128))
        self.E(d, 760, 800, 26, (90, 82, 74))
        self.qmark(img, 800, 640, 120 * back_out((t - self.w("crater", "huella")) / 0.4))
        k = back_out((t - self.w("crater", "veinticinco")) / 0.4)
        if k > 0:
            self.R(d, 540 - 170 * k, 1420 - 120 * k, 540 + 170 * k, 1420 + 120 * k, WHITE, radius=24)
            self.R(d, 540 - 170 * k, 1420 - 120 * k, 540 + 170 * k, 1420 - 60 * k, (220, 60, 90), radius=24)
            if k > 0.7:
                self.text(img, 540, 1335, "NOVIEMBRE", 34, WHITE, shadow=False)
                self.text(img, 540, 1450, "25", 110, (40, 40, 50), shadow=False)

    def s_calma(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        self.globe(img, 540, 1000, 300, t, spin=18)
        k = back_out((lt - 0.3) / 0.4)
        if k > 0:
            self.E(d, 540, 1480, 80 * k, (90, 200, 110))
            self.Ln(d, [(500, 1480), (530, 1515), (590, 1445)], WHITE, 14)
        self.text(img, 540, 620, "SIN PELIGRO", 90, (120, 230, 140), alpha=smooth(0.3, 0.7, lt))

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name in ("viaje", "cresta", "colores"):
            return self.pill(out, "ESA · HERA · NOVIEMBRE 2026", ESA, size=44)
        return out

    def sfx_events(self):
        st = self.start
        return [(0.2, "riser", 0.4), (self.t_dart, "boom", 0.9), (self.w("dart", "treinta"), "pop", 0.5), (st("hera") + 0.2, "shimmer", 0.5),
                (st("viaje") + 0.3, "whoosh", 0.5), (self.w("cresta", "cresta"), "pop", 0.4), (st("colores") + 0.2, "riser", 0.3),
                (self.w("crater", "veinticinco"), "pop", 0.5), (st("calma") + 0.4, "shimmer", 0.4), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.7), (self.t_dart, 0.95), (st("hera"), 0.6), (st("cresta"), 0.75), (st("calma"), 0.45), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
