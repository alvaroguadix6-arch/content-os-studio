"""NIVEL OCULTO · Lo más viral del primer día de GTA 6 (19-11-2026), sin spoilers.

Fuentes: Kotaku (lanzamiento a medianoche hora local; actualización de última hora de PS5; huevo de Pascua en la
torre de radio; chiste sobre GTA 7), GameSpot (huevos lanzables, ~7 min de escalada; vuelve Bigfoot, «muy
apestoso»), Gulf News y Sunday Guardian (vídeos virales de fallos: camión que sale volando, personajes que
atraviesan objetos). Recreación propia sin logotipos ni imágenes del juego.
"""
from __future__ import annotations

import math
import random

from gta6 import NEON, PINK, VIDEO as GTA
from gta6_trucos import VIDEO as TRUCOS
from motor import CYAN, RED, WHITE, Person, W, H, S, YEL, back_out, clamp, draw_car, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "epico", 108


class VIDEO(GTA):
    NAME = "gta6_dia1"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"gta", "seis", "descubrimientos", "virales", "spoilers", "uno", "medianoche", "playstation", "actualización", "dos",
                "torre", "siete", "minutos", "huevos", "pascua", "tres", "bigfoot", "fatal", "cuatro", "chiste", "cinco", "fallos",
                "camiones", "volando", "atraviesan", "trece", "años", "comentarios"}
    stamp = TRUCOS.stamp

    def setup(self):
        super().setup()
        r = random.Random(91)
        self.hearts = [(r.uniform(80, 1000), r.uniform(0, 1), r.uniform(0.7, 1.3)) for _ in range(30)]
        self.climber = Person(r, 0, 70, shirt=(60, 70, 90))
        self.victim = Person(r, 0, 120, shirt=(90, 100, 115))
        self.truck = draw_car((240, 240, 245), 320, "van")
        self.walker = Person(r, 0, 260, shirt=(230, 90, 150))

    def build_scenes(self):
        sc = [(0.0, "intro")]
        for i in range(1, 6):
            sc.append((self.start(f"d{i}") - 0.15, f"d{i}"))
        sc += [(self.start("espera") - 0.15, "espera"), (self.start("cta") - 0.1, "fin")]
        return sc

    def phone(self, d, x, y, s, t):
        self.R(d, x - 70 * s, y - 130 * s, x + 70 * s, y + 130 * s, (25, 25, 35), radius=22 * s)
        self.R(d, x - 60 * s, y - 115 * s, x + 60 * s, y + 115 * s, (90, 40, 120), radius=14 * s)
        self.P(d, [(x - 15 * s, y - 25 * s), (x - 15 * s, y + 25 * s), (x + 25 * s, y)], WHITE)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.85)
        for x, ph, s in self.hearts:  # reacciones que suben como en las redes
            y = 1700 - ((lt * 0.25 * s + ph) % 1) * 1300
            self.E(d, x - 10 * s, y, 12 * s, PINK)
            self.E(d, x + 10 * s, y, 12 * s, PINK)
            self.P(d, [(x - 22 * s, y + 4), (x + 22 * s, y + 4), (x, y + 28 * s)], PINK)
        for i, x in enumerate((250, 540, 830)):
            self.phone(d, x, 980 + 20 * math.sin(t * 2 + i), 1.0, t)
        self.pop_text(img, 540, 600, "DÍA 1 · GTA VI", 100, t, 0.2, WHITE)
        self.pop_text(img, 540, 1450, "SIN SPOILERS", 60, t, self.w("intro", "spoilers"), YEL)

    def s_d1(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        cx, cy = 540, 760  # reloj que llega a las 00:00
        self.E(d, cx, cy, 230, (240, 240, 250))
        self.E(d, cx, cy, 214, (30, 24, 50))
        for i in range(12):
            a = i / 12 * 2 * math.pi
            self.Ln(d, [(cx + math.sin(a) * 180, cy - math.cos(a) * 180), (cx + math.sin(a) * 200, cy - math.cos(a) * 200)], WHITE, 6)
        a = -0.6 * (1 - ease_out(lt / 1.2))
        self.Ln(d, [(cx, cy), (cx + math.sin(a) * 170, cy - math.cos(a) * 170)], YEL, 10)
        self.Ln(d, [(cx, cy), (cx, cy - 120)], WHITE, 14)
        self.pop_text(img, 540, 1080, "00:00", 90, t, 1.0 + self.start("d1"), NEON)
        k = smooth(self.w("d1", "actualización") - 0.2, self.end("d1"), t)
        self.R(d, 140, 1300, 940, 1370, (40, 30, 60), radius=35)
        self.R(d, 150, 1310, 150 + 780 * k, 1360, NEON, radius=25)
        self.text(img, 540, 1440, "ACTUALIZACIÓN PS5", 54, WHITE)

    def s_d2(self, img, d, t, lt, u):
        self.bgdyn(img, (30, 40, 90), (255, 150, 120))
        self.R(d, 0, 1700, W, H + 40, (40, 30, 60))
        tx, top, base = 540, 520, 1700  # torre de radio (celosía)
        for y in range(top, base, 60):
            w0 = 30 + (y - top) * 0.12
            w1 = 30 + (y + 60 - top) * 0.12
            self.Ln(d, [(tx - w0, y), (tx + w1, y + 60)], (60, 60, 70), 5)
            self.Ln(d, [(tx + w0, y), (tx - w1, y + 60)], (60, 60, 70), 5)
        self.Ln(d, [(tx - 30, top), (tx - 30 - (base - top) * 0.12, base)], (60, 60, 70), 10)
        self.Ln(d, [(tx + 30, top), (tx + 30 + (base - top) * 0.12, base)], (60, 60, 70), 10)
        self.E(d, tx, top - 20, 12, RED)
        climb = clamp((t - self.w("d2", "subió")) / max(0.5, self.w("d2", "nido") - self.w("d2", "subió")))
        cy = base - (base - top - 90) * climb
        self.person(img, self.climber, tx + 50, cy, "float" if climb < 1 else "stand", "normal", "up", t * 6, scale=1.0)
        mins = 7 * climb
        self.text(img, 860, 900, f"{int(mins)} min", 64, YEL)
        if t > self.w("d2", "nido") - 0.3:  # nido con huevos de colores
            self.E(d, tx - 70, top + 30, 70, (130, 90, 50), ry=26)
            for i, c in enumerate(((255, 110, 150), (110, 200, 255), (255, 220, 90), (150, 230, 120))):
                self.E(d, tx - 110 + i * 26, top + 12, 13, c, ry=17)
        tt = t - self.w("d2", "tirar")
        if tt > 0:  # un huevo cae hacia la gente de abajo
            y = top + 20 + 0.5 * 2200 * tt * tt
            if y < base - 20:
                self.E(d, tx - 60 - 60 * tt, y, 13, (255, 220, 90), ry=17)
            self.person(img, self.victim, tx - 200, base, "stand", "wow" if y > base - 200 else "normal", "down", 0)

    def s_d3(self, img, d, t, lt, u):
        self.bg(img, "forest", (20, 40, 40), (40, 70, 60))
        for i in range(9):  # bosque
            x = (i * 137 + 40) % 1100
            self.P(d, [(x - 90, 1500), (x, 900 + (i % 3) * 60), (x + 90, 1500)], (30, 70, 50))
        self.R(d, 0, 1500, W, H + 40, (40, 55, 40))
        x = 200 + lt * 90  # Bigfoot (silueta peluda)
        bob = abs(math.sin(lt * 4)) * 10
        c = (95, 70, 50)
        self.E(d, x, 1210 - bob, 110, c, ry=170)
        self.E(d, x, 1010 - bob, 62, c)
        for s_ in (-1, 1):
            self.Ln(d, [(x + s_ * 90, 1150 - bob), (x + s_ * 120, 1290 - bob)], c, 40)
            self.Ln(d, [(x + s_ * 40, 1350 - bob), (x + s_ * 50 + 20 * math.sin(lt * 4) * s_, 1500)], c, 46)
        self.E(d, x + 18, 1005 - bob, 7, WHITE)
        for i in range(3):  # olor
            ph = (lt * 0.8 + i / 3) % 1
            yy = 950 - ph * 250
            self.Ln(d, [(x - 60 + i * 60 + 15 * math.sin(yy / 30 + j), yy + j * 25) for j in range(5)], (140, 220, 90), 8)
        self.pop_text(img, 540, 620, "VUELVE BIGFOOT", 92, t, self.w("d3", "bigfoot") - 0.1, YEL)
        self.pop_text(img, 540, 1650, "HUELE FATAL", 70, t, self.w("d3", "fatal"), (140, 230, 100))

    def s_d4(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.9)
        k = back_out(lt / 0.5)
        self.R(d, 540 - 280 * k, 640, 540 + 280 * k, 880, (25, 15, 45), radius=40, outline=PINK, width=8)
        if k > 0.5:
            self.text(img, 540, 760, "GTA VII", 110, PINK)
        cx, cy = 540, 1130  # carita riendo
        r = 120 * back_out((lt - 0.5) / 0.4)
        if r > 2:
            self.E(d, cx, cy, r, YEL)
            self.Ln(d, [(cx - r * 0.5, cy - r * 0.25), (cx - r * 0.25, cy - r * 0.35)], (60, 40, 20), 8)
            self.Ln(d, [(cx + r * 0.25, cy - r * 0.35), (cx + r * 0.5, cy - r * 0.25)], (60, 40, 20), 8)
            d.chord([(cx - r * 0.55) * S, (cy - r * 0.2) * S, (cx + r * 0.55) * S, (cy + r * 0.65) * S], 0, 180, fill=(80, 30, 30))
        self.stamp(img, "CHISTE OCULTO", t, self.w("d4", "chiste"), y=1450, col=YEL, size=60)

    def s_d5(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.6)
        tt = max(0.0, t - self.w("d5", "camiones"))
        y = 1560 - 1400 * tt + 600 * tt * tt * 0.3
        self.paste(img, self.truck, 540 + 120 * tt, y, rot=(tt * 400) % 360 if tt > 0 else 0)
        # personaje que atraviesa una pared (mitad dentro)
        self.R(d, 120, 1300, 300, 1560, (110, 90, 120))
        self.person(img, self.walker, 300 + 30 * math.sin(t * 2), 1560, "stand", "normal", "down", t * 4, scale=0.9)
        self.R(d, 120, 1300, 250, 1560, (110, 90, 120))
        if int(t * 12) % 5 == 0:  # efecto de fallo
            for i in range(6):
                y0 = 380 + i * 230
                self.R(d, 0, y0, W, y0 + 18, (0, 255, 200) if i % 2 else (255, 0, 120))
        self.stamp(img, "BUG", t, self.w("d5", "fallos"), y=700, size=90)

    def s_espera(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.3)
        self.pop_text(img, 540, 640, "13 AÑOS", 140, t, self.w("espera", "trece"), YEL)
        self.text(img, 540, 800, "DE ESPERA", 64, WHITE)

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name.startswith("d"):
            return self.pill(out, f"VIRAL {name[1:]}/5", YEL, y=1835, size=42)
        return out

    def sfx_events(self):
        ev = [(0.2, "boom", 0.5), (0.25, "shimmer", 0.4)]
        for i in range(1, 6):
            ev.append((self.start(f"d{i}") + 0.05, "pop", 0.45))
        ev += [(self.start("d1") + 1.0, "beep", 0.5), (self.w("d2", "tirar") + 0.5, "splash", 0.3), (self.start("d3") + 0.3, "rumble", 0.4),
               (self.w("d4", "chiste"), "click", 0.6), (self.w("d5", "camiones"), "boom", 0.5), (self.w("d5", "fallos"), "click", 0.6),
               (self.start("espera"), "riser", 0.4), (self.start("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        return [(0, 0.85), (self.start("d3"), 0.75), (self.start("d5"), 0.9), (self.start("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
