"""NIVEL OCULTO · ¿Cómo se construyeron las pirámides de Egipto?  (la Gran Pirámide, paso a paso)

Datos: tumba de Keops en Guiza, hacia el 2560 a. C. (~4.500 años); unos 2,3 millones de bloques; caliza local cortada
con cinceles de cobre y herramientas de piedra; caliza fina de Tura y granito de Asuán por el Nilo (papiros de Wadi
al-Jarf, «diario de Merer»); trineos sobre arena mojada (pintura de Djehutihotep; estudio de la Univ. de Ámsterdam,
2014); subida de los bloques: hipótesis de rampas (rectas, en zigzag o envolventes), sin consenso; poblado y tumbas de
trabajadores asalariados (Hawass y Lehner), pagados en raciones de pan y cerveza; unos 20 años; 146,6 m originales, la
estructura más alta del mundo durante unos 3.800 años.
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, Person, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "epico", 84
STONE = (214, 186, 140)
CASING = (245, 238, 220)
SAND = (232, 200, 140)
BASE_Y = 1560
BASE_W = 920
PH = 585  # altura en pantalla (proporción real 146,6 / 230,3)
COURSES = 26


class VIDEO(Video):
    NAME = "piramides"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"millones", "bloques", "máquina", "gran", "pirámide", "keops", "guiza", "caliza", "canteras", "cobre", "barco", "nilo",
                "merer", "trineos", "madera", "arena", "fuerza", "misterio", "hipótesis", "rampas", "esclavos", "trabajadores", "pan",
                "cerveza", "veinte", "ciento", "cuarenta", "seis", "metros", "cuatro", "comentarios"}

    def setup(self):
        r = random.Random(44)
        self.crew = [Person(r, 0, 110, shirt=c) for c in ((235, 230, 215), (220, 210, 190), (240, 236, 222), (225, 215, 195), (230, 225, 205))]
        for p in self.crew:
            p.pants = (200, 190, 170)
        self.dunes = [(r.uniform(-100, 1180), r.uniform(150, 300)) for _ in range(6)]
        self.chips = [(r.uniform(-1, 1), r.uniform(-1, 0), r.uniform(0, 1)) for _ in range(30)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("quien") - 0.15, "keops"), (st("cantera") - 0.15, "cantera"), (st("rio") - 0.15, "nilo"),
                (st("arena") - 0.15, "trineo"), (st("rampas") - 0.15, "rampas"), (st("obreros") - 0.15, "obreros"),
                (st("final") - 0.15, "final"), (st("cta") - 0.1, "fin")]

    # ───── escenario ─────
    def desert(self, img, d, t, sun=True):
        self.bg(img, "desert", (120, 175, 230), (250, 220, 170))
        if sun:
            self.glow(img, 860, 520, 120, (255, 230, 160), 160)
            self.E(d, 860, 520, 64, (255, 240, 190))
        for x, h_ in self.dunes:
            self.E(d, x, BASE_Y + 20, 320, (225, 190, 130), ry=h_ * 0.4)
        self.R(d, 0, BASE_Y, W, H + 40, SAND)

    def pyramid(self, d, cx, p, casing=0.0, base=BASE_Y, bw=BASE_W, ph=PH):
        """Pirámide construida hasta la fracción p (por hiladas de bloques)."""
        n = int(COURSES * p + 0.999)
        ch = ph / COURSES
        for i in range(n):
            y1 = base - i * ch
            y0 = y1 - ch
            w1 = bw / 2 * (1 - i / COURSES)
            w0 = bw / 2 * (1 - (i + 1) / COURSES)
            top_fill = 1.0 if i < n - 1 else (COURSES * p - i)
            col = mix(STONE, CASING, casing)
            pts = [(cx - w1, y1), (cx + w1, y1), (cx + w0, y0), (cx - w0, y0)]
            if top_fill < 1:  # hilada en construcción: solo parte de los bloques
                x_end = cx - w1 + 2 * w1 * top_fill
                pts = [(cx - w1, y1), (x_end, y1), (min(x_end, cx + w0), y0), (cx - w0, y0)]
            self.P(d, pts, col)
            if casing < 0.9:  # juntas de los bloques
                self.Ln(d, [(cx - w1, y1), (cx + w1 if top_fill >= 1 else pts[1][0], y1)], shade(col, 0.8), 2)
                step = 34
                xx = cx - w1 + (i % 2) * step / 2
                while xx < (cx + w1 if top_fill >= 1 else pts[1][0]) - 4:
                    self.Ln(d, [(xx, y1), (xx, y0)], shade(col, 0.82), 2)
                    xx += step
        # sombra de una cara
        if p >= 1:
            self.P(d, [(cx, base - ph), (cx + bw / 2, base), (cx + bw * 0.18, base)], shade(mix(STONE, CASING, casing), 0.86))
        return base - n * ch

    def sledge(self, d, x, y, s=1.0, block=STONE):
        self.R(d, x - 70 * s, y - 10 * s, x + 70 * s, y, (120, 85, 50), radius=5 * s)
        self.R(d, x - 55 * s, y - 80 * s, x + 55 * s, y - 10 * s, block)
        self.Ln(d, [(x - 55 * s, y - 45 * s), (x + 55 * s, y - 45 * s)], shade(block, 0.8), 2)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.desert(img, d, t)
        p = ease_out(lt / 3.6)
        top = self.pyramid(d, 540, p)
        if p < 0.99:  # bloque que cae a su sitio
            ph = (lt * 3) % 1
            self.R(d, 520, top - 120 + 100 * ph, 560, top - 90 + 100 * ph, STONE)
        self.pop_text(img, 540, 620, "+2.000.000", 120, t, 0.2, YEL)
        self.text(img, 540, 740, "BLOQUES DE PIEDRA", 54, WHITE, alpha=smooth(0.4, 0.8, lt))

    def s_keops(self, img, d, t, lt, u):
        self.desert(img, d, t)
        self.pyramid(d, 540, 0.08 + 0.06 * smooth(0, 4, lt))
        k = back_out((t - self.w("quien", "keops")) / 0.4)
        if k > 0:  # cartucho con el nombre
            self.R(d, 540 - 260 * k, 640 - 90 * k, 540 + 260 * k, 640 + 90 * k, (250, 230, 170), radius=80 * k, outline=(150, 100, 40), width=8)
            self.text(img, 540, 640, "KEOPS", 90 * k, (120, 70, 20), shadow=False)
        self.pop_text(img, 540, 800, "≈ 2560 a. C. · GUIZA", 56, t, self.w("quien", "guiza"), WHITE)

    def s_cantera(self, img, d, t, lt, u):
        self.bg(img, "quarry", (120, 175, 230), (250, 220, 170))
        self.P(d, [(0, 900), (380, 860), (520, 1000), (1080, 940), (1080, H + 40), (0, H + 40)], (205, 175, 125))
        for row in range(5):  # cara de la cantera con bloques marcados
            y = 1060 + row * 110
            for c in range(7):
                x = 60 + c * 150 + (row % 2) * 75
                self.R(d, x, y, x + 140, y + 100, (215, 185, 135), outline=(170, 140, 95), width=3)
        hit = (lt * 2.5) % 1 < 0.2
        for i, p_ in enumerate(self.crew[:3]):
            x = 260 + i * 280
            self.person(img, p_, x, 1060, "stand", "normal", "up" if hit else "down", 0, scale=1.1)
            self.Ln(d, [(x + 30, 1060 - 80 - (0 if hit else 30)), (x + 60, 1060 - 30 - (0 if hit else 30))], (200, 120, 60), 8)
            if hit:
                for sx, sy, s_ in self.chips[:8]:
                    self.E(d, x + 70 + sx * 40, 1030 + sy * 40, 5, (230, 210, 170))
        self.pop_text(img, 540, 650, "CINCELES DE COBRE", 70, t, self.w("cantera", "cobre"), YEL)

    def s_nilo(self, img, d, t, lt, u):
        self.bg(img, "nile", (120, 175, 230), (250, 220, 170))
        self.R(d, 0, 1150, W, 1250, (110, 160, 80))
        self.R(d, 0, 1250, W, 1600, (50, 120, 170))
        for j in range(5):
            y = 1280 + j * 60
            self.Ln(d, [(x, y + 5 * math.sin(x / 50 + t * 2 + j)) for x in range(0, W + 40, 40)], (120, 180, 220), 3)
        self.R(d, 0, 1600, W, H + 40, (110, 160, 80))
        for i in range(3):  # barcos con bloques
            x = ((lt * 70 + i * 420) % (W + 400)) - 200
            y = 1350 + i * 80
            self.P(d, [(x - 140, y), (x + 140, y), (x + 100, y + 40), (x - 100, y + 40)], (140, 95, 55))
            self.Ln(d, [(x, y), (x, y - 200)], (110, 75, 45), 6)
            self.P(d, [(x + 4, y - 190), (x + 4, y - 40), (x + 110, y - 60)], (240, 232, 210))
            self.R(d, x - 90, y - 50, x - 10, y, CASING if i != 1 else (170, 80, 80))
        self.pyramid(d, 870, 0.4, base=1150, bw=320, ph=205)
        k = back_out((t - self.w("rio", "merer")) / 0.4)
        if k > 0:  # papiro
            self.R(d, 540 - 300 * k, 640 - 110 * k, 540 + 300 * k, 640 + 110 * k, (240, 222, 170), radius=20)
            self.text(img, 540, 610, "DIARIO DE MERER", 54 * k, (100, 60, 20), shadow=False)
            self.text(img, 540, 680, "PAPIRO ≈ 4.500 AÑOS", 34 * k, (120, 80, 40), shadow=False)

    def s_trineo(self, img, d, t, lt, u):
        self.desert(img, d, t, sun=False)
        x = 860 - lt * 70
        y = 1500
        self.R(d, x - 160, y - 4, W, y + 14, (180, 140, 90))  # arena mojada detrás del trineo
        self.R(d, x - 320, y - 4, x - 160, y + 14, mix(SAND, (180, 140, 90), smooth(0, 1, (lt % 1.0))))
        self.sledge(d, x, y, 1.5)
        for i, p_ in enumerate(self.crew[:4]):  # tiran de cuerdas
            px = x - 260 - i * 110
            self.Ln(d, [(x - 100, y - 50), (px + 20, y - 80)], (150, 110, 60), 4)
            self.person(img, p_, px, y, "stand", "normal", "down", t * 5 + i, rot=-10, scale=1.05)
        wx = x - 190  # el que echa agua
        self.person(img, self.crew[4], wx, y, "stand", "normal", "down", 0, scale=1.05)
        self.E(d, wx + 40, y - 120, 22, (170, 110, 70))
        for j in range(5):
            ph = (lt * 3 + j / 5) % 1
            self.E(d, wx + 50 - ph * 40, y - 100 + ph * 100, 5, (80, 150, 220))
        self.pop_text(img, 540, 650, "ARENA MOJADA", 80, t, self.w("arena", "mojaban"), CYAN)
        self.text(img, 540, 770, "= MENOS FUERZA", 56, WHITE, alpha=smooth(self.w("arena", "menos") - 0.2, self.w("arena", "menos") + 0.3, t))

    def s_rampas(self, img, d, t, lt, u):
        self.desert(img, d, t)
        p = 0.55
        top = self.pyramid(d, 540, p)
        spiral = smooth(self.w("rampas", "alrededor") - 0.4, self.w("rampas", "alrededor") + 0.4, t)
        if spiral < 0.5:  # rampa recta
            self.P(d, [(1080, BASE_Y), (540 + BASE_W / 2 * (1 - p) + 20, top), (540 + BASE_W / 2 * (1 - p) + 60, top), (1080, BASE_Y - 30)], (170, 120, 80))
        else:  # rampa envolvente
            for i in range(5):
                y = BASE_Y - i * (BASE_Y - top) / 5
                w_ = BASE_W / 2 * (1 - i / 5 * p)
                self.Ln(d, [(540 - w_, y), (540 + w_, y - (BASE_Y - top) / 5)], (170, 120, 80), 12)
        self.sledge(d, 800 - 40 * math.sin(t), BASE_Y - 200 - 40 * math.sin(t), 0.6)
        self.pop_text(img, 540, 650, "¿RECTA O EN ESPIRAL?", 70, t, self.w("rampas", "rectas"), YEL)
        k = back_out((t - self.w("rampas", "hipótesis")) / 0.35)
        if k > 0:
            self.R(d, 540 - 260 * k, 780 - 55 * k, 540 + 260 * k, 780 + 55 * k, (20, 40, 80), radius=18 * k, outline=YEL, width=8)
            self.text(img, 540, 780, "HIPÓTESIS", 66 * k, YEL)

    def s_obreros(self, img, d, t, lt, u):
        self.desert(img, d, t)
        for i in range(6):  # poblado de los trabajadores
            x = 120 + i * 160
            self.R(d, x - 60, 1400, x + 60, 1560, (190, 150, 105))
            self.R(d, x - 20, 1480, x + 20, 1560, (120, 90, 60))
        for i, p_ in enumerate(self.crew):
            x = 160 + i * 190
            self.person(img, p_, x + 10 * math.sin(t + i), 1720, "stand", "smile", "down", 0, scale=1.1)
        k = back_out((t - self.w("obreros", "pan")) / 0.35)
        if k > 0:  # pan y cerveza
            self.E(d, 400, 1000, 80 * k, (200, 140, 70), ry=50 * k)
            self.R(d, 640 - 50 * k, 900, 640 + 50 * k, 1060, (160, 100, 60), radius=30 * k)
        self.pop_text(img, 540, 650, "NO ERAN ESCLAVOS", 80, t, self.w("obreros", "esclavos"), YEL)

    def s_final(self, img, d, t, lt, u):
        self.desert(img, d, t)
        p = 0.55 + 0.45 * ease_out(lt / 2.5)
        casing = smooth(2.6, 3.6, lt)
        top = self.pyramid(d, 540, p, casing)
        self.R(d, 60, top, 72, BASE_Y, YEL)
        self.text(img, 90, top - 40, f"{146 * p:.0f} m", 52, YEL, anchor="lm")
        self.pop_text(img, 540, 1760, "LA MÁS ALTA ≈ 3.800 AÑOS", 54, t, self.w("final", "cuatro"), WHITE)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name in ("keops", "cantera", "nilo", "trineo", "rampas", "obreros"):
            return self.pill(out, "OBRA · ≈ 20 AÑOS", YEL, y=1835, size=42)
        return out

    def sfx_events(self):
        st = self.start
        ev = [(0.1, "rumble", 0.4)] + [(0.2 + i * 0.3, "tick", 0.45) for i in range(11)]
        ev += [(self.w("quien", "keops"), "boom", 0.4)]
        ev += [(st("cantera") + i * 0.4, "click", 0.35) for i in range(10)]
        ev += [(st("rio") + 0.2, "splash", 0.3), (self.w("rio", "merer"), "pop", 0.5), (st("arena") + 0.3, "drip", 0.4),
               (self.w("rampas", "hipótesis"), "click", 0.5), (self.w("obreros", "esclavos"), "pop", 0.5), (st("final") + 0.2, "riser", 0.5),
               (st("final") + 2.8, "shimmer", 0.6), (st("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        st = self.start
        return [(0, 0.8), (st("cantera"), 0.6), (st("rampas"), 0.75), (st("final"), 0.95), (st("cta"), 0.4), (self.duration, 0.3)]


def shade(c, k=0.8):
    return tuple(int(v * k) for v in c[:3])


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
