"""NIVEL OCULTO · ¿Qué pasaría si todos los volcanes del mundo entraran en erupción a la vez?  (hipotético)

Hechos: unos 1.350 volcanes potencialmente activos en tierra (USGS); normalmente unos 40-50 en erupción a la vez
(Smithsonian Global Volcanism Program); Eyjafjallajökull 2010: unos 100.000 vuelos cancelados en Europa; Tambora 1815
→ «año sin verano» de 1816; los aerosoles de azufre reflejan la luz solar (Pinatubo 1991 enfrió ~0,5 °C); las
emisiones humanas de CO2 superan más de 100 veces las volcánicas (USGS). Lo demás es un escenario hipotético.
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, City, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "suspense", 88
LAVA = (255, 110, 30)


class VIDEO(Video):
    NAME = "volcanes"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"volcanes", "erupción", "vez", "trescientos", "cincuenta", "activos", "cuarenta", "cinco", "ceniza", "kilómetros",
                "aviones", "islandia", "cien", "vuelos", "frío", "azufre", "tambora", "verano", "cosechas", "grados", "lava",
                "pueblos", "dióxido", "carbono", "humanos", "veces", "peligroso", "comentarios"}

    def setup(self):
        r = random.Random(71)
        self.city = City(seed=41)
        self.cones = [(80, 1280, 300, 0.0), (380, 1220, 420, 0.4), (720, 1250, 360, 0.8), (1000, 1290, 280, 1.2)]
        self.bombs = [(r.uniform(-1, 1), r.uniform(0.6, 1.4), r.uniform(0, 1)) for _ in range(50)]
        self.ash = [(r.uniform(0, W), r.uniform(0, H), r.uniform(2, 5)) for _ in range(180)]
        self.grid = [(i % 15, i // 15) for i in range(135)]
        self.lit = set(r.sample(range(135), 5))
        self.t_boom = min(0.8, self.w("intro", "erupción", 0.0))
        self.shakes = [(self.t_boom, 1.0), (self.start("lava") + 0.3, 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "erupcion"), (st("cuantos") - 0.15, "cuantos"), (st("ceniza") - 0.15, "ceniza"), (st("vuelos") - 0.15, "vuelos"),
                (st("frio") - 0.15, "frio"), (st("cosechas") - 0.15, "cosechas"), (st("lava") - 0.15, "lava"),
                (st("dato") - 0.15, "co2"), (st("cta") - 0.1, "fin")]

    def volcano(self, img, d, x, base, h, t, power=1.0, ph=0.0):
        self.P(d, [(x - h * 1.1, base), (x - 40, base - h), (x + 40, base - h), (x + h * 1.1, base)], (90, 70, 60))
        self.P(d, [(x - 40, base - h), (x + 40, base - h), (x + 20, base - h + 50), (x - 20, base - h + 50)], (60, 45, 40))
        if power <= 0:
            return
        top = base - h
        self.glow(img, x, top, 110 * power, LAVA, 160 * power)
        for i in range(8):  # columna de ceniza
            k = ((t * 0.35 + i / 8 + ph) % 1)
            r = (40 + 140 * k) * power
            self.E(d, x + 30 * math.sin(i + t) * k, top - 40 - k * 700 * power, r, mix((120, 105, 100), (70, 65, 65), k))
        for bx, sp, b0 in self.bombs[:20]:  # bombas de lava
            k = ((t * 0.8 * sp + b0 + ph) % 1)
            self.E(d, x + bx * 260 * k, top - 400 * k * sp * power + 500 * k * k, 7, LAVA)
        for s_ in (-1, 1):  # coladas
            self.P(d, [(x + s_ * 20, top + 10), (x + s_ * 50, top + 10), (x + s_ * h * 0.7, base), (x + s_ * h * 0.5, base)], LAVA)

    # ───── escenas ─────
    def s_erupcion(self, img, d, t, lt, u):
        on = t >= self.t_boom
        self.bgdyn(img, (40, 30, 40) if on else (120, 150, 190), (200, 90, 50) if on else (210, 200, 190))
        for x, base, h, ph in self.cones:
            self.volcano(img, d, x, base, h, t, smooth(self.t_boom, self.t_boom + 0.6, t) if on else 0, ph)
        self.R(d, 0, 1280, W, H + 40, (70, 55, 50))
        self.pop_text(img, 540, 1500, "TODOS A LA VEZ", 90, t, self.w("intro", "vez"), YEL)

    def s_cuantos(self, img, d, t, lt, u):
        self.bg(img, "dark", (24, 18, 22), (12, 10, 12))
        allk = smooth(self.w("cuantos", "normalmente") + 1.0, self.w("cuantos", "normalmente") + 2.5, t)
        for i, (c, r) in enumerate(self.grid):  # cada icono = 10 volcanes
            x, y = 110 + c * 61, 600 + r * 80
            on = i in self.lit or (allk > 0 and i < 135 * allk)
            col = LAVA if on else (80, 70, 70)
            self.P(d, [(x - 22, y + 20), (x, y - 20), (x + 22, y + 20)], col)
        n1 = int(1350 * smooth(self.start("cuantos"), self.w("cuantos", "activos") + 0.3, t))
        self.text(img, 540, 1450, f"{n1:,} ACTIVOS".replace(",", "."), 72, WHITE)
        self.pop_text(img, 540, 1570, "≈ 45 EN ERUPCIÓN A LA VEZ", 52, t, self.w("cuantos", "cuarenta"), LAVA)

    def s_ceniza(self, img, d, t, lt, u):
        k = smooth(0, 4.0, lt)
        self.bgdyn(img, mix((110, 160, 220), (45, 40, 40), k), mix((200, 220, 235), (90, 80, 75), k))
        for i, x in enumerate((180, 560, 900)):  # columnas de ceniza en el horizonte
            for j in range(10):
                kk = ((lt * 0.3 + j / 10 + i * 0.3) % 1)
                self.E(d, x + 40 * math.sin(j + t), 1100 - kk * 1000 * (0.4 + 0.6 * k), 60 + 160 * kk, mix((140, 130, 125), (80, 75, 75), kk))
        self.city.draw(d, t, night=0.4 * k, lights=k)
        for x, y, r in self.ash:
            self.E(d, x, (y + t * 70) % H, r, (150, 145, 140))
        self.pop_text(img, 540, 620, "DECENAS DE KILÓMETROS", 62, t, self.w("ceniza", "decenas"), YEL)

    def s_vuelos(self, img, d, t, lt, u):
        self.bg(img, "ashsky", (90, 85, 85), (150, 140, 130))
        for i in range(8):
            self.E(d, (i * 170 + t * 30) % (W + 300) - 150, 600 + (i % 3) * 80, 160, (110, 105, 100))
        self.R(d, 0, 1460, W, H + 40, (70, 70, 75))
        x = 540
        self.R(d, x - 300, 1360, x + 300, 1430, (230, 232, 240), radius=35)
        self.P(d, [(x - 70, 1395), (x + 110, 1395), (x - 40, 1540)], (210, 214, 225))
        self.P(d, [(x - 270, 1370), (x - 230, 1260), (x - 180, 1370)], (210, 214, 225))
        for i in range(5):
            self.E(d, x - 200 + i * 80, 1395, 10, (100, 130, 170))
        k = back_out((t - self.w("vuelos", "cancelar")) / 0.4)
        if k > 0:
            self.R(d, 540 - 300 * k, 920 - 70 * k, 540 + 300 * k, 920 + 70 * k, None, radius=18 * k, outline=RED, width=10)
            self.text(img, 540, 920, "CANCELADO", 80 * k, RED)
        self.pop_text(img, 540, 1700, "ISLANDIA 2010 · ≈ 100.000 VUELOS", 46, t, self.w("vuelos", "cien"), YEL)

    def s_frio(self, img, d, t, lt, u):
        k = smooth(0, 3.0, lt)
        self.bgdyn(img, mix((120, 170, 230), (110, 110, 120), k), mix((210, 225, 240), (170, 168, 165), k))
        self.glow(img, 540, 620, 150, (255, 230, 160), 200 * (1 - 0.8 * k))
        self.E(d, 540, 620, 90, mix((255, 230, 140), (210, 205, 190), k))
        for i in range(5):  # velo de aerosoles
            y = 520 + i * 50
            self.R(d, 0, y, W, y + 26, (200, 200, 195) if k > 0.2 else (0, 0, 0, 0))
        tx, ty = 540, 1150
        self.R(d, tx - 26, ty - 160, tx + 26, ty + 120, WHITE, radius=26)
        self.E(d, tx, ty + 140, 52, WHITE)
        lvl = ty + 100 - 220 * (1 - 0.75 * k)
        self.R(d, tx - 14, lvl, tx + 14, ty + 130, mix(RED, (80, 160, 230), k), radius=14)
        self.E(d, tx, ty + 140, 40, mix(RED, (80, 160, 230), k))
        self.pop_text(img, 540, 1500, "1816: AÑO SIN VERANO", 64, t, self.w("frio", "verano"), CYAN)

    def s_cosechas(self, img, d, t, lt, u):
        k = smooth(0.3, 3.5, lt)
        self.bgdyn(img, (110, 110, 120), (170, 168, 165))
        self.R(d, 0, 1150, W, H + 40, mix((120, 160, 70), (150, 130, 90), k))
        for row in range(4):  # trigo que se marchita
            y = 1200 + row * 160
            for x in range(40, 1080, 55):
                bend = 0.9 * k * (1 if (x // 55) % 2 else -1)
                tipx, tipy = x + math.sin(bend) * 90, y - math.cos(bend) * 90
                self.Ln(d, [(x, y + 40), (tipx, tipy)], mix((200, 180, 80), (140, 110, 70), k), 6)
                self.E(d, tipx, tipy, 10, mix((230, 200, 90), (130, 100, 60), k), ry=20)
        for x, y, r in self.ash[:90]:
            self.E(d, x, (y + t * 60) % H, r, (225, 225, 230))
        self.text(img, 540, 650, "−VARIOS °C · AÑOS", 70, CYAN, alpha=smooth(0.6, 1.2, lt))
        self.text(img, 540, 760, "HIPÓTESIS", 50, YEL, alpha=smooth(0.6, 1.2, lt))

    def s_lava(self, img, d, t, lt, u):
        self.bgdyn(img, (50, 30, 35), (200, 90, 50))
        self.volcano(img, d, 760, 1100, 520, t, 1.0)
        k = smooth(0.3, 4.0, lt)
        for i in range(6):  # casas del pueblo
            x = 80 + i * 130
            burn = k > (1 - i / 6) * 0.9
            self.R(d, x - 45, 1420, x + 45, 1520, (120, 60, 40) if burn else (220, 205, 180))
            self.P(d, [(x - 55, 1420), (x, 1370), (x + 55, 1420)], (90, 40, 30) if burn else (180, 90, 60))
            if burn:
                self.glow(img, x, 1400, 60, LAVA, 160)
        front = 1080 - 1100 * k
        self.P(d, [(1080, 1300), (front, 1460), (front - 40, 1540), (1080, 1540)], LAVA)
        self.R(d, 0, 1520, W, H + 40, (60, 45, 40))
        self.pop_text(img, 540, 650, "RÍOS DE LAVA", 90, t, self.w("lava", "lava"), LAVA)

    def s_co2(self, img, d, t, lt, u):
        self.bg(img, "dark", (24, 28, 40), (12, 14, 22))
        k = ease_out(lt / 2.0)
        self.R(d, 200, 1500 - 12 * k, 400, 1500, LAVA)  # volcanes: 1
        self.R(d, 640, 1500 - 900 * k, 840, 1500, (180, 180, 190))  # humanos: >100
        self.text(img, 300, 1560, "VOLCANES", 42, LAVA)
        self.text(img, 740, 1560, "HUMANOS", 42, WHITE)
        self.text(img, 540, 1440 - 900 * k, "× 100", 80, YEL) if k > 0.8 else None
        self.text(img, 540, 1680, "DATO REAL · CO₂ AL AÑO", 46, CYAN)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def sfx_events(self):
        st = self.start
        return [(0.1, "rumble", 0.6), (self.t_boom, "boom", 1.0), (self.t_boom + 0.3, "rumble", 0.7), (self.w("cuantos", "activos"), "pop", 0.4),
                (st("ceniza") + 0.3, "wind", 0.5), (self.w("vuelos", "cancelar"), "click", 0.6), (st("frio") + 0.4, "wind", 0.5),
                (st("lava") + 0.3, "boom", 0.6), (st("lava") + 1.0, "rumble", 0.6), (st("dato") + 0.5, "pop", 0.5), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.6), (self.t_boom, 1.0), (st("cuantos"), 0.6), (st("ceniza"), 0.8), (st("frio"), 0.6), (st("lava"), 0.95), (st("dato"), 0.45),
                (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
