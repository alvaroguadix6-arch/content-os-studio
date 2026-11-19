"""NIVEL OCULTO · 378 días en «Marte» sin salir de la Tierra (misión CHAPEA 2 de la NASA).

Fuentes: NASA (CHAPEA Mission 2: 378 días, del 19-10-2025 al 31-10-2026, hábitat Mars Dune Alpha impreso en 3D en el
Johnson Space Center de Houston, ~1.700 pies² ≈ 160 m², sin ventanas ni llamadas en tiempo real; próximo análogo no
antes de agosto de 2027), Fox Weather, Chron.
"""
from __future__ import annotations

import math
import random

from espacio import VIDEO as ESP
from motor import CYAN, RED, WHITE, Person, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "espacio", 86
MARS = (200, 95, 60)


class VIDEO(Video):
    NAME = "marte"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"cuatro", "trescientos", "setenta", "ocho", "días", "marte", "tierra", "chapea", "nasa", "impreso", "houston", "mars",
                "dune", "alpha", "ciento", "sesenta", "metros", "ventanas", "retraso", "verduras", "ejercicio", "paseos", "diecinueve",
                "treinta", "salud", "rendimiento", "voluntarios", "veintisiete", "encerrado", "comentarios"}
    astronaut = ESP.astronaut

    def setup(self):
        r = random.Random(29)
        self.crew = [Person(r, 0, 170, shirt=c) for c in ((70, 90, 140), (70, 90, 140), (70, 90, 140), (70, 90, 140))]
        self.rocks = [(r.uniform(0, W), r.uniform(1350, 1800), r.uniform(10, 40)) for _ in range(30)]
        self.t_reveal = self.w("intro", "salir", -0.1)

    def build_scenes(self):
        st = self.start
        return [(0.0, "marte"), (st("donde") - 0.15, "impresora"), (st("tamano") - 0.15, "plano"), (st("reglas") - 0.15, "reglas"),
                (st("vida") - 0.15, "vida"), (st("fechas") - 0.15, "fechas"), (st("porque") - 0.15, "porque"),
                (st("siguiente") - 0.15, "siguiente"), (st("cta") - 0.1, "fin")]

    def mars_land(self, d, t, y0=1300):
        self.R(d, 0, y0, W, H + 40, MARS)
        for i, x in enumerate((-100, 300, 760)):
            self.E(d, x + 200, y0 + 10, 340, (180, 80, 50), ry=90 + 20 * (i % 2))
        for x, y, r in self.rocks:
            if y > y0:
                self.E(d, x, y, r, (160, 70, 45), ry=r * 0.5)

    def habitat(self, d, x, y, s=1.0):
        self.E(d, x, y, 260 * s, (225, 215, 200), ry=150 * s)
        self.R(d, x - 270 * s, y, x + 270 * s, y + 40 * s, (180, 100, 70))
        for i in range(5):
            yy = y - 120 * s + i * 26 * s
            self.Ln(d, [(x - 230 * s + i * 8 * s, yy), (x + 230 * s - i * 8 * s, yy)], (200, 190, 175), 3)
        self.R(d, x - 30 * s, y - 60 * s, x + 30 * s, y, (90, 80, 70), radius=10 * s)

    # ───── escenas ─────
    def s_marte(self, img, d, t, lt, u):
        self.bgdyn(img, (220, 150, 110), (240, 190, 150))
        self.mars_land(d, t)
        self.habitat(d, 540, 1240)
        self.astronaut(img, 820 + 20 * math.sin(t), 1180, 0.9, 4 * math.sin(t))
        self.pop_text(img, 540, 620, "378 DÍAS", 120, t, self.w("intro", "trescientos"), YEL)
        k = smooth(self.t_reveal, self.t_reveal + 0.8, t)
        if k > 0:  # la revelación: todo está dentro de un edificio en Houston
            m = 520 * (1 - k) + 60
            self.R(d, 0, 0, W, 300 + 60 * (1 - k), (60, 64, 76))
            self.R(d, 0, 0, m * k, H, (60, 64, 76))
            self.R(d, W - m * k, 0, W, H, (60, 64, 76))
            if k > 0.6:
                self.text(img, 540, 400, "HOUSTON, TEXAS", 64, WHITE, alpha=(k - 0.6) / 0.4)

    def s_impresora(self, img, d, t, lt, u):
        self.bg(img, "lab", (60, 64, 76), (36, 40, 50))
        k = smooth(0.2, 4.0, lt)
        layers = int(18 * k)
        for i in range(layers):  # capas impresas
            y = 1500 - i * 26
            w_ = 600 - (i * 8 if i > 12 else 0)
            self.R(d, 540 - w_ / 2, y - 22, 540 + w_ / 2, y, mix((215, 205, 190), (190, 175, 160), i % 2))
        hx = 540 + 280 * math.sin(lt * 3)  # cabezal de impresión
        hy = 1500 - layers * 26 - 40
        self.R(d, 100, hy - 90, 980, hy - 70, (40, 40, 48))
        self.R(d, hx - 30, hy - 70, hx + 30, hy - 10, (230, 180, 60))
        self.P(d, [(hx - 12, hy - 10), (hx + 12, hy - 10), (hx, hy + 14)], (230, 180, 60))
        self.pop_text(img, 540, 640, "IMPRESO EN 3D", 96, t, self.w("donde", "impreso"), YEL)
        self.text(img, 540, 1640, "NASA · HOUSTON", 56, CYAN)

    def s_plano(self, img, d, t, lt, u):
        self.bg(img, "lab", (60, 64, 76), (36, 40, 50))
        k = ease_out(lt / 1.2)
        x0, y0, x1, y1 = 180, 700, 900, 1400
        self.R(d, x0, y0, x0 + (x1 - x0) * k, y1, (230, 225, 215), radius=20)
        if k > 0.9:
            for (a, b, c, e, lab) in ((200, 720, 520, 1000, "LAB"), (540, 720, 880, 1000, "COCINA"), (200, 1020, 440, 1380, "HUERTO"),
                                      (460, 1020, 880, 1380, "DORMITORIOS")):
                self.R(d, a, b, c, e, (205, 200, 190), radius=10)
                self.text(img, (a + c) / 2, (b + e) / 2, lab, 34, (90, 90, 100), shadow=False)
        self.text(img, 540, 620, "MARS DUNE ALPHA", 64, WHITE, alpha=smooth(0.2, 0.6, lt))
        self.pop_text(img, 540, 1560, "≈ 160 m²", 100, t, self.w("tamano", "ciento"), YEL)

    def s_reglas(self, img, d, t, lt, u):
        self.bg(img, "inner", (90, 84, 80), (60, 56, 54))
        self.R(d, 340, 520, 740, 860, (120, 112, 106), radius=20)  # «ventana» tapiada
        self.Ln(d, [(360, 540), (720, 840)], RED, 16)
        self.Ln(d, [(720, 540), (360, 840)], RED, 16)
        self.text(img, 540, 920, "SIN VENTANAS", 60, WHITE)
        # mensaje que tarda en llegar
        x0, x1, y = 140, 940, 1300
        self.Ln(d, [(x0, y), (x1, y)], (150, 150, 160), 4)
        self.globe(img, x0, y, 60, t, spin=20, glow_a=0)
        self.E(d, x1, y, 50, MARS)
        ph = ((t - self.start("reglas")) * 0.22) % 1
        ex = x0 + (x1 - x0) * ph
        self.R(d, ex - 40, y - 28, ex + 40, y + 28, WHITE, radius=6)
        self.Ln(d, [(ex - 40, y - 28), (ex, y), (ex + 40, y - 28)], (180, 180, 190), 4)
        self.pop_text(img, 540, 1500, "MENSAJES CON RETRASO", 60, t, self.w("reglas", "retraso"), YEL)

    def s_vida(self, img, d, t, lt, u):
        self.bg(img, "inner", (90, 84, 80), (60, 56, 54))
        cells = [(270, 760, "verduras"), (810, 760, "ejercicio"), (270, 1320, "reparan"), (810, 1320, "paseos")]
        for i, (cx, cy, frag) in enumerate(cells):
            k = back_out((t - self.w("vida", frag) + 0.1) / 0.35)
            if k <= 0:
                continue
            self.R(d, cx - 240 * k, cy - 250 * k, cx + 240 * k, cy + 250 * k, (40, 40, 50), radius=30)
            if k < 0.8:
                continue
            if i == 0:  # verduras que crecen
                for j in range(4):
                    x = cx - 150 + j * 100
                    h_ = 60 + 80 * smooth(0, 3, lt) + 10 * math.sin(t * 2 + j)
                    self.Ln(d, [(x, cy + 150), (x, cy + 150 - h_)], (90, 180, 90), 8)
                    self.E(d, x - 20, cy + 150 - h_, 22, (110, 200, 100), ry=12)
                    self.E(d, x + 20, cy + 140 - h_, 22, (110, 200, 100), ry=12)
                self.R(d, cx - 200, cy + 150, cx + 200, cy + 180, (120, 90, 60))
            elif i == 1:  # cinta de correr
                self.R(d, cx - 170, cy + 150, cx + 170, cy + 180, (30, 30, 36), radius=10)
                self.person(img, self.crew[1], cx, cy + 150, "stand", "normal", "down", t * 10, scale=1.0)
            elif i == 2:  # llave inglesa reparando
                a = 0.4 * math.sin(t * 5)
                self.R(d, cx - 120, cy - 40, cx + 120, cy + 120, (90, 100, 120), radius=12)
                self.Ln(d, [(cx, cy - 120), (cx + math.sin(a) * 140, cy - 120 + math.cos(a) * 140)], (200, 205, 215), 22)
            else:  # paseo marciano simulado
                self.R(d, cx - 220, cy + 60, cx + 220, cy + 230, MARS, radius=20)
                self.astronaut(img, cx + 40 * math.sin(t), cy - 30, 0.8, 5 * math.sin(t * 2))

    def s_fechas(self, img, d, t, lt, u):
        self.bg(img, "lab", (60, 64, 76), (36, 40, 50))
        k = smooth(self.w("fechas", "salieron") - 0.3, self.w("fechas", "salieron") + 0.8, t)
        txt = "19 OCT 2025" if k < 0.5 else "31 OCT 2026"
        self.R(d, 270, 560, 810, 1100, WHITE, radius=30)
        self.R(d, 270, 560, 810, 680, (220, 60, 70), radius=30)
        self.text(img, 540, 620, "ENTRADA" if k < 0.5 else "SALIDA", 50, WHITE, shadow=False)
        self.text(img, 540, 890, txt, 72, (40, 40, 50), shadow=False)
        days = int(378 * smooth(self.start("fechas"), self.end("fechas"), t))
        self.text(img, 540, 1350, f"DÍA {days}", 110, YEL)

    def s_porque(self, img, d, t, lt, u):
        self.bg(img, "lab", (20, 30, 40), (10, 16, 24))
        self.R(d, 120, 600, 960, 1050, (10, 30, 20), radius=24)
        pts = []
        for i in range(84):
            x = 140 + i * 10
            ph = (i * 10 / 280 - t * 1.2) % 1
            y = 830 - (180 if 0.48 < ph < 0.52 else (-60 if 0.52 < ph < 0.56 else 0))
            pts.append((x, y))
        self.Ln(d, pts, (90, 255, 140), 5)
        for i, h_ in enumerate((0.6, 0.85, 0.45, 0.7)):
            x = 220 + i * 190
            hh = 220 * h_ * (0.85 + 0.15 * math.sin(t * 2 + i))
            self.R(d, x, 1450 - hh, x + 110, 1450, CYAN, radius=10)
        self.pop_text(img, 540, 1580, "SALUD Y RENDIMIENTO", 64, t, self.w("porque", "salud"), YEL)

    def s_siguiente(self, img, d, t, lt, u):
        self.bg(img, "lab", (60, 64, 76), (36, 40, 50))
        k = back_out(lt / 0.5)
        self.R(d, 540 - 330 * k, 980 - 420 * k, 540 + 330 * k, 980 + 420 * k, (245, 240, 225), radius=20)
        if k > 0.7:
            self.text(img, 540, 700, "SE BUSCAN", 70, (40, 40, 50), shadow=False)
            self.text(img, 540, 800, "VOLUNTARIOS", 70, RED, shadow=False)
            self.habitat(d, 540, 1050, 0.6)
            self.text(img, 540, 1260, "NO ANTES DE 2027", 50, (40, 40, 50), shadow=False)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name in ("impresora", "plano", "reglas", "vida"):
            return self.pill(out, "NASA · CHAPEA 2 · 378 DÍAS", CYAN, size=44)
        return out

    def sfx_events(self):
        st = self.start
        return [(0.2, "wind", 0.4), (self.w("intro", "trescientos"), "pop", 0.5), (self.t_reveal, "boom", 0.6), (st("donde") + 0.3, "rumble", 0.3),
                (self.w("tamano", "ciento"), "pop", 0.5), (self.w("reglas", "retraso"), "beep", 0.5), (self.w("vida", "verduras"), "pop", 0.3),
                (self.w("vida", "ejercicio"), "pop", 0.3), (self.w("vida", "reparan"), "click", 0.3), (self.w("vida", "paseos"), "pop", 0.3),
                (self.w("fechas", "salieron"), "shimmer", 0.4), (st("porque") + 0.3, "beep", 0.3), (st("siguiente") + 0.2, "pop", 0.5),
                (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.6), (self.t_reveal, 0.85), (st("vida"), 0.65), (st("siguiente"), 0.8), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
