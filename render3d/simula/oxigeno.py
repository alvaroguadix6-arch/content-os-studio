"""NIVEL OCULTO · ¿Qué pasaría si desapareciera todo el oxígeno de la Tierra durante 10 segundos?  (hipotético)

Hechos: el O2 es ~21 % del aire (N2 ~78 %); quitar ese 21 % bajaría la presión a ~800 hPa, como a ~2.000 m de altitud;
la combustión necesita oxígeno; el ozono (O3) filtra la radiación UV; el oxígeno es ~46 % del peso de la corteza
terrestre y forma parte del agua; Gran Oxidación: hace ~2.400 millones de años, por cianobacterias. El resto es un
escenario hipotético (se distinguen el caso «solo del aire» y el caso extremo «todos los átomos de oxígeno»).
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, City, Person, Video, W, H, S, YEL, back_out, clamp, draw_car, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "suspense", 92
O2 = (230, 80, 80)


class VIDEO(Video):
    NAME = "oxigeno"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"diez", "segundos", "oxígeno", "suficientes", "veintiuno", "aire", "presión", "dos", "mil", "metros", "pop", "fuego",
                "motores", "ozono", "ultravioleta", "filtro", "átomos", "agua", "mitad", "corteza", "hormigón", "rocas", "hidrógeno",
                "bacterias", "notarías", "comentarios"}

    def setup(self):
        r = random.Random(81)
        self.city = City(seed=51)
        self.people = [Person(r, x, h, shirt=c) for (x, h), c in zip(((180, 210), (420, 225), (680, 205), (900, 220)),
                       ((70, 130, 210), (235, 185, 60), (60, 170, 140), (220, 90, 80)))]
        self.mols = [(r.uniform(0, W), r.uniform(350, 1500), r.uniform(0, 6)) for _ in range(40)]
        self.debris = [(r.uniform(-1, 1), r.uniform(0, 1), r.uniform(6, 18)) for _ in range(60)]
        self.car = draw_car((215, 70, 70), 300, "car")
        self.t_off = self.w("intro", "desaparece", 0.0)
        self.t_end = self.t_off + 10.0  # ventana de 10 s
        self.shakes = [(self.t_off, 0.5), (self.start("hormigon") + 0.4, 0.9)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "calle"), (st("aire") - 0.15, "aire"), (st("presion") - 0.15, "presion"), (st("fuego") - 0.15, "fuego"),
                (st("ozono") - 0.15, "ozono"), (st("extremo") - 0.15, "extremo"), (st("hormigon") - 0.15, "derrumbe"),
                (st("dato") - 0.15, "bacterias"), (st("cta") - 0.1, "fin")]

    def molecule(self, d, x, y, s=1.0, col=O2):
        self.E(d, x - 12 * s, y, 14 * s, col)
        self.E(d, x + 12 * s, y, 14 * s, col)

    # ───── escenas ─────
    def s_calle(self, img, d, t, lt, u):
        self.bg(img, "day", (110, 165, 225), (200, 225, 242))
        self.city.draw(d, t)
        g = self.city.ground
        gone = smooth(self.t_off, self.t_off + 0.5, t)
        for x, y, ph in self.mols:  # moléculas de O2 en el aire que desaparecen
            if gone < 1:
                s = 1 - gone
                self.molecule(d, x + 20 * math.sin(t + ph), y + 15 * math.cos(t * 0.8 + ph), s)
        for i, p in enumerate(self.people):
            self.person(img, p, p.x + (0 if gone else 15 * math.sin(t + i)), g, "stand", "wow" if gone else "normal", "down", 0 if gone else t * 3)
        self.pop_text(img, 540, 620, "SIN OXÍGENO", 100, t, self.t_off + 0.1, RED)

    def s_aire(self, img, d, t, lt, u):
        self.bg(img, "dark", (24, 30, 46), (12, 16, 26))
        cx, cy, R = 540, 950, 330
        gone = smooth(self.w("aire", "veintiuno") + 0.8, self.w("aire", "veintiuno") + 1.6, t)
        d.pieslice([(cx - R) * S, (cy - R) * S, (cx + R) * S, (cy + R) * S], -90, -90 + 360 * 0.78, fill=(110, 150, 220))
        d.pieslice([(cx - R) * S, (cy - R) * S, (cx + R) * S, (cy + R) * S], -90 + 360 * 0.78, -90 + 360 * 0.99,
                   fill=mix(O2, (24, 30, 46), gone))
        d.pieslice([(cx - R) * S, (cy - R) * S, (cx + R) * S, (cy + R) * S], -90 + 360 * 0.99, 270, fill=(200, 200, 210))
        self.text(img, 470, 1000, "78 % N₂", 54, WHITE)
        self.text(img, 820, 640, "21 % O₂", 54, mix(O2, (80, 80, 90), gone))
        self.pop_text(img, 540, 1450, "−21 % DEL AIRE", 70, t, self.w("aire", "veintiuno") + 0.9, RED)

    def s_presion(self, img, d, t, lt, u):
        self.bg(img, "day", (110, 165, 225), (200, 225, 242))
        cx, cy = 540, 860  # barómetro
        self.E(d, cx, cy, 250, (240, 240, 245))
        self.E(d, cx, cy, 230, (30, 34, 50))
        for i in range(11):
            a = math.radians(-220 + i * 26)
            self.Ln(d, [(cx + math.cos(a) * 190, cy + math.sin(a) * 190), (cx + math.cos(a) * 220, cy + math.sin(a) * 220)], WHITE, 5)
        k = smooth(0.3, 1.6, lt)
        hpa = 1013 - 213 * k
        a = math.radians(-220 + (hpa - 700) / 400 * 260)
        self.Ln(d, [(cx, cy), (cx + math.cos(a) * 180, cy + math.sin(a) * 180)], RED, 10)
        self.text(img, cx, cy + 120, f"{hpa:.0f} hPa", 54, YEL)
        p = self.people[1]
        self.person(img, p, 540, 1700, "stand", "wow", "down", 0, scale=1.4)
        if (lt * 2) % 1 < 0.5 and lt > 1.0:
            self.text(img, 380, 1380, "POP!", 64, YEL)
            self.text(img, 700, 1380, "POP!", 64, YEL)
        self.pop_text(img, 540, 500, "COMO A ≈ 2.000 m", 64, t, self.w("presion", "dos"), WHITE)

    def s_fuego(self, img, d, t, lt, u):
        self.bg(img, "dark", (40, 40, 52), (20, 20, 28))
        off = smooth(0.5, 1.2, lt)
        for i, x in enumerate((220, 540, 860)):  # hoguera, fogón, motor
            y = 1050
            if i == 0:
                for j in range(4):
                    self.Ln(d, [(x - 60, y + 60 - j * 6), (x + 60, y + 40 - j * 6)], (110, 70, 40), 14)
            elif i == 1:
                self.R(d, x - 110, y + 40, x + 110, y + 70, (90, 90, 100), radius=10)
            else:
                self.paste(img, self.car, x, y + 120)
            if off < 1:
                for j in range(3):
                    hh = (90 + 40 * math.sin(t * 9 + j)) * (1 - off)
                    self.P(d, [(x - 40 + j * 40 - 20, y + 30), (x - 40 + j * 40, y + 30 - hh), (x - 40 + j * 40 + 20, y + 30)],
                           (255, 160, 40) if j % 2 else (255, 90, 30))
            else:
                for j in range(3):  # humo de apagado
                    ph = (lt * 0.6 + j / 3) % 1
                    self.E(d, x + 10 * math.sin(t + j), y - ph * 300, 20 + 30 * ph, (120, 120, 130))
        self.pop_text(img, 540, 620, "SIN FUEGO", 100, t, self.w("fuego", "fuego"), RED)

    def s_ozono(self, img, d, t, lt, u):
        self.bg(img, "day", (90, 140, 210), (190, 215, 235))
        k = smooth(0.4, 1.4, lt)
        self.R(d, 0, 380, W, 470, mix((120, 180, 255), (90, 140, 210), k))
        self.text(img, 540, 425, "OZONO", 44, mix(WHITE, (90, 140, 210), k), shadow=False)
        for i in range(9):  # rayos UV que ahora atraviesan
            x = 80 + i * 115
            reach = 470 + (900 * k)
            for j in range(int((reach - 300) / 50)):
                y = 300 + j * 50 + (t * 200) % 50
                if y < reach:
                    self.Ln(d, [(x + 10 * math.sin(y / 20), y), (x + 10 * math.sin((y + 30) / 20), y + 30)], (170, 90, 255), 5)
        self.city.draw(d, t, dy=120)
        self.pop_text(img, 540, 620, "UV SIN FILTRO", 80, t, self.w("ozono", "ultravioleta"), (200, 140, 255))

    def s_extremo(self, img, d, t, lt, u):
        self.bg(img, "dark", (40, 20, 24), (20, 10, 12))
        k = back_out(lt / 0.4)
        self.R(d, 540 - 400 * k, 560 - 70 * k, 540 + 400 * k, 560 + 70 * k, None, radius=18 * k, outline=RED, width=10)
        self.text(img, 540, 560, "ESCENARIO EXTREMO", 62 * k, RED)
        cx, cy = 300, 1080  # molécula de agua que pierde su oxígeno
        sep = smooth(1.5, 3.0, lt)
        self.E(d, cx, cy, 70 * (1 - sep) + 1, O2)
        for s_ in (-1, 1):
            self.E(d, cx + s_ * (80 + 60 * sep), cy + 60 + 40 * sep, 42, (230, 230, 240))
        self.text(img, cx, cy + 200, "H₂O", 54, WHITE)
        R = 200  # corteza: ~46 % oxígeno
        d.pieslice([(780 - R) * S, (1080 - R) * S, (780 + R) * S, (1080 + R) * S], -90, -90 + 360 * 0.46, fill=O2)
        d.pieslice([(780 - R) * S, (1080 - R) * S, (780 + R) * S, (1080 + R) * S], -90 + 360 * 0.46, 270, fill=(150, 120, 100))
        self.text(img, 780, 1340, "CORTEZA ≈ 46 % O", 44, WHITE)

    def s_derrumbe(self, img, d, t, lt, u):
        self.bgdyn(img, (60, 50, 50), (150, 120, 110))
        k = smooth(0.3, 3.5, lt)
        self.city.draw(d, t, dy=300 * k * k)  # los edificios se hunden y desmoronan
        for i in range(12):  # grietas en las fachadas
            x = 60 + i * 85
            self.Ln(d, [(x, 700 + 300 * k * k), (x + 20, 900 + 300 * k * k), (x - 10, 1100 + 300 * k * k)], (40, 30, 30), 5 * k + 1)
        for dx, dy, sz in self.debris:
            y = 900 + dy * 800 + 900 * k * dy
            self.R(d, 540 + dx * 520, y, 540 + dx * 520 + sz, y + sz, (170, 160, 150))
        for i in range(40):  # el agua se convierte en gas y sube
            ph = (lt * 0.5 + i / 40) % 1
            self.E(d, (i * 97) % W, 1800 - ph * 1200, 6 + 10 * ph, (200, 220, 255))
        self.text(img, 540, 620, "HIPÓTESIS EXTREMA", 60, YEL)

    def s_bacterias(self, img, d, t, lt, u):
        self.bg(img, "ancient", (40, 90, 110), (10, 40, 60))
        self.R(d, 0, 1500, W, H + 40, (90, 80, 60))
        for i in range(7):  # estromatolitos
            x = 80 + i * 150
            self.E(d, x, 1500, 70, (90, 120, 80), ry=90)
            for j in range(5):
                ph = (lt * 0.4 + j / 5 + i * 0.1) % 1
                self.molecule(d, x + 10 * math.sin(j + t), 1420 - ph * 700, 0.6)
        self.text(img, 540, 1640, "DATO REAL", 46, CYAN)
        self.pop_text(img, 540, 1760, "HACE ≈ 2.400 M DE AÑOS", 56, t, self.w("dato", "dos"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        if self.t_off <= t < self.start("extremo"):
            span = self.start("extremo") - self.t_off
            left = max(0.0, 10.0 * (1 - (t - self.t_off) / span))
            return self.pill(out, f"SIN OXÍGENO · {left:04.1f} s", RED)
        return out

    def sfx_events(self):
        st = self.start
        return [(0.2, "riser", 0.4), (self.t_off, "boom", 0.8), (self.t_off, "shimmer", 0.4), (self.w("aire", "veintiuno") + 0.9, "pop", 0.5),
                (st("presion") + 1.2, "pop", 0.6), (st("presion") + 1.7, "pop", 0.6), (st("fuego") + 0.6, "click", 0.6),
                (st("ozono") + 0.5, "riser", 0.4), (st("extremo") + 0.1, "boom", 0.6), (st("hormigon") + 0.4, "rumble", 0.9),
                (st("hormigon") + 0.6, "boom", 0.7), (st("dato") + 0.4, "drip", 0.4), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.6), (self.t_off, 0.95), (st("fuego"), 0.75), (st("extremo"), 1.0), (st("dato"), 0.45), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
