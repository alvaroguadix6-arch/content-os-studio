"""NIVEL OCULTO · ¿Qué pasaría si la Tierra dejara de girar durante 5 segundos?"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, City, Person, Video, W, H, S, YEL, back_out, clamp, draw_car, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "suspense", 90


class VIDEO(Video):
    NAME = "rotacion"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"tierra", "cinco", "segundos", "ecuador", "mil", "seiscientos", "setenta", "españa", "doscientos", "golpe", "este",
                "despedidos", "avión", "atmósfera", "vientos", "océanos", "olas", "tsunami", "hipótesis", "luna", "dos", "milésimas",
                "siglo", "comentarios"}

    def setup(self):
        r = random.Random(21)
        self.city = City(seed=11)
        self.people = [Person(r, x, h, shirt=c) for (x, h), c in zip(((150, 205), (380, 220), (620, 200), (860, 215)),
                       ((70, 130, 210), (235, 185, 60), (60, 170, 140), (220, 90, 80)))]
        self.cars = [draw_car(c, 300, k) for c, k in (((215, 70, 70), "car"), ((250, 205, 60), "taxi"), ((235, 235, 240), "van"))]
        self.leaves = [(r.uniform(0, W), r.uniform(300, 1500), r.uniform(0.6, 1.4), r.uniform(0, 6)) for _ in range(70)]
        self.streaks = [(r.uniform(0, W), r.uniform(250, 1800), r.uniform(80, 260)) for _ in range(60)]
        self.t_stop = self.w("intro", "detiene", 0.05)
        self.t_jolt = self.start("frenazo") + 0.6
        self.shakes = [(self.t_stop, 0.9), (self.t_jolt, 1.0), (self.start("oceanos") + 1.6, 0.7)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "parada"), (st("velocidad") - 0.15, "velocidad"), (st("frenazo") - 0.15, "ciudad"),
                (st("viento") - 0.15, "viento"), (st("oceanos") - 0.15, "ola"), (st("hipotesis") - 0.15, "hipotesis"),
                (st("hecho") - 0.15, "hecho"), (st("cta") - 0.1, "fin")]

    def spin(self, t):
        """Ángulo acumulado del globo: muy rápido al principio, parado en seco, y vuelta a girar."""
        if t < self.t_stop:
            return t * 70
        return self.t_stop * 70

    def s_parada(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        self.stars(d, t, 1.0)
        moving = t < self.t_stop
        self.globe(img, 540, 1000, 380, 0, spin=0, rot0=self.spin(t))
        if moving:  # estelas de giro
            for i in range(8):
                y = 760 + i * 60
                self.Ln(d, [(170 + i * 8, y), (300 + i * 8, y - 10)], (180, 220, 255), 4)
        self.pop_text(img, 540, 1580, "¡STOP!", 150, t, self.t_stop, RED)

    def s_velocidad(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        self.stars(d, t, 1.0)
        self.globe(img, 540, 1000, 380, t, spin=20, rot0=-20)
        # ecuador y flechas de velocidad
        d.arc([(540 - 380) * S, (1000 - 60) * S, (540 + 380) * S, (1000 + 140) * S], 0, 180, fill=YEL, width=6 * S)
        for i in range(3):
            ph = (lt * 0.8 + i / 3) % 1
            x = 220 + ph * 640
            self.P(d, [(x, 1085), (x - 34, 1065), (x - 34, 1105)], YEL)
        self.pop_text(img, 540, 1500, "ECUADOR · 1.670 km/h", 64, t, self.w("velocidad", "mil"), YEL)
        self.pop_text(img, 540, 1610, "ESPAÑA · +1.200 km/h", 56, t, self.w("velocidad", "españa"), CYAN)

    def street(self, img, d, t, lt, fly=1.0, wind=0.0):
        self.bgdyn(img, (110, 165, 225), (200, 225, 242))
        jolt = smooth(self.t_jolt - 0.1, self.t_jolt + 0.1, t)
        self.city.draw(d, t)
        g = self.city.ground
        # todo lo que no está anclado sale disparado hacia el este (derecha)
        ft = max(0.0, t - self.t_jolt)
        for i, p in enumerate(self.people):
            x = p.x + (220 + 60 * i) * ft * fly
            lift = 120 * min(1, ft * 2) * fly + 30 * math.sin(ft * 3 + i)
            if x > W + 200:
                x = (x % (W + 400)) - 200
            pose, face, arms, rot = ("float", "scared", "up", 25 * min(1, ft) + 15 * math.sin(t * 4 + i)) if ft > 0 else ("stand", "normal", "down", 0)
            self.person(img, p, x, g - lift, pose, face, arms, t * 3, rot)
        for i, c in enumerate(self.cars):
            x0 = (200, 760, 480)[i]
            x = x0 + (300 + 80 * i) * ft * fly
            x = (x % (W + 500)) - 250 if ft > 0 else x
            y = g + (330 if i < 2 else 230) - 80 * min(1, ft) * fly * (1 + 0.5 * math.sin(ft * 2 + i))
            self.paste(img, c, x, y, rot=(-12 * min(1, ft) * fly if ft > 0 else 0))
        if ft > 0:  # líneas de velocidad
            k = min(1, ft * 2)
            for x, y, ln in self.streaks:
                xx = (x + ft * 1800) % (W + 300) - 150
                self.Ln(d, [(xx, y), (xx - ln * k, y)], (255, 255, 255), 3)
        return jolt

    def s_ciudad(self, img, d, t, lt, u):
        self.street(img, d, t, lt)
        self.pop_text(img, 540, 620, "ESTE →", 110, t, self.w("frenazo", "este"), YEL)
        self.pop_text(img, 540, 760, "> AVIÓN COMERCIAL", 56, t, self.w("personas", "avión"), WHITE)

    def s_viento(self, img, d, t, lt, u):
        self.street(img, d, t, lt, fly=1.0, wind=1.0)
        g = self.city.ground
        # árboles doblados por el viento y hojas/tejas volando
        for tx in (120, 520, 940):
            bend = 0.6 + 0.12 * math.sin(t * 9 + tx)
            self.Ln(d, [(tx, g), (tx + 40 * bend, g - 160), (tx + 120 * bend, g - 300)], (90, 65, 45), 22)
            self.E(d, tx + 150 * bend, g - 330, 90, (80, 160, 80), ry=55)
        for x, y, sp, ph in self.leaves:
            xx = (x + lt * 1500 * sp) % (W + 200) - 100
            self.R(d, xx - 12, y - 6, xx + 12, y + 6, (200, 90, 60) if ph > 3 else (100, 170, 80), radius=4)

    def s_ola(self, img, d, t, lt, u):
        self.bgdyn(img, (70, 90, 120), (150, 170, 190))
        self.city.draw(d, t)
        g = self.city.ground
        k = smooth(0.2, 4.8, lt)
        crest = -350 + 1700 * k  # la ola avanza de oeste a este
        peak = 470 + 20 * math.sin(t * 2)
        base = 640
        body = [(-60, H + 60)]
        for x in range(-60, int(crest) + 1, 20):
            rise = math.exp(-((x - crest) / 260) ** 2)
            body.append((x, base + 40 * math.sin(x / 110 + t * 3) * (1 - rise) - (base - peak) * rise))
        lip = [(crest + 80, peak + 10), (crest + 150, peak + 70), (crest + 170, peak + 120), (crest + 120, peak + 110), (crest + 70, peak + 90)]
        face = [(crest + 90, peak + 160), (crest + 230, g - 160), (crest + 380, g + 260), (crest + 380, H + 60)]
        self.P(d, body + lip + face, (35, 105, 170))
        self.P(d, [(crest - 40, peak + 40), (crest + 70, peak + 90), (crest + 90, peak + 160), (crest + 230, g - 160), (crest + 380, g + 260),
                   (crest + 200, g + 260), (crest + 40, g - 200)], (70, 150, 210))
        top = body[1:]
        if len(top) > 1:
            self.Ln(d, top + lip[:3], (235, 248, 255), 16)
        for i, (x, y, ln) in enumerate(self.streaks[:40]):  # espuma y salpicaduras delante de la ola
            ph = (lt * 1.5 + i / 40) % 1
            sx = crest + 120 + ph * 220 + (i % 5) * 18
            sy = peak + 60 - math.sin(ph * math.pi) * 160 + (i % 7) * 20
            self.E(d, sx, sy, 10 * (1 - ph) + 3, (235, 248, 255))
        self.pop_text(img, 540, 1600, "> CUALQUIER TSUNAMI", 60, t, self.w("oceanos", "tsunami"), YEL)

    def s_hipotesis(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        self.stars(d, t, 1.0)
        self.globe(img, 540, 1000, 360, t, spin=20, rot0=40)
        k = back_out((lt - 0.4) / 0.35)
        if k > 0:
            self.R(d, 540 - 300 * k, 1500 - 70 * k, 540 + 300 * k, 1500 + 70 * k, None, radius=24 * k, outline=YEL, width=10)
            self.text(img, 540, 1500, "HIPÓTESIS", 90 * k, YEL)

    def s_hecho(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        self.stars(d, t, 1.0)
        self.globe(img, 430, 950, 260, t, spin=15, rot0=10)
        mx, my = 860 + 20 * math.sin(t * 0.5), 760
        self.E(d, mx, my, 70, (215, 215, 222))
        self.E(d, mx - 20, my - 15, 14, (190, 190, 200))
        for i in range(5):  # tirón gravitatorio
            ph = (lt * 0.7 + i / 5) % 1
            x = mx - 80 - ph * 240
            y = my + (950 - my) * (ph * 0.95)
            self.E(d, x, y, 7, (255, 220, 120))
        self.text(img, 540, 1440, "DATO REAL", 46, CYAN)
        self.pop_text(img, 540, 1560, "+2 ms POR SIGLO", 84, t, self.w("hecho", "dos"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name == "parada" and t >= self.t_stop:
            return self.pill(out, "ROTACIÓN · 0 km/h", RED)
        if name in ("ciudad", "viento", "ola"):
            left = max(0.0, 5 - (t - self.start("frenazo")) * 5 / max(1, self.start("hipotesis") - self.start("frenazo")))
            return self.pill(out, f"TIERRA DETENIDA · {left:.1f} s", RED)
        return out

    def sfx_events(self):
        st = self.start
        return [(0.2, "riser", 0.4), (self.t_stop, "boom", 0.8), (self.t_stop, "click", 0.6), (self.w("velocidad", "mil"), "pop", 0.5),
                (self.t_jolt, "boom", 0.7), (self.t_jolt + 0.1, "whoosh", 0.8), (st("personas") + 0.3, "whoosh", 0.6),
                (st("viento"), "wind", 0.8), (st("viento") + 2.5, "wind", 0.6), (st("oceanos") + 0.5, "rumble", 0.7),
                (st("oceanos") + 1.6, "splash", 0.8), (st("hipotesis") + 0.4, "pop", 0.6), (self.w("hecho", "dos"), "pop", 0.5),
                (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.7), (st("velocidad"), 0.5), (st("frenazo"), 0.9), (st("hipotesis"), 0.45), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
