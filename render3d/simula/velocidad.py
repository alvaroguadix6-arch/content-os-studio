"""NIVEL OCULTO · Ranking: 10 cosas de la más lenta a la más rápida (formato ranking + comparación, tendencia 2026).

Datos: caracol de jardín ~0,05 km/h (~50 m/h); Usain Bolt, pico de ~44,7 km/h en el récord de 100 m (Berlín 2009);
guepardo ~93-100 km/h en carreras cortas (Wilson et al., Nature 2013: 25,9 m/s); halcón peregrino >300 km/h en picado;
avión comercial ~900 km/h; bala de fusil ~850-1.000 m/s ≈ 3.000-3.600 km/h; ISS ~28.000 km/h, una órbita cada ~92 min;
Tierra alrededor del Sol ~107.000 km/h; Parker Solar Probe, 692.000 km/h (récord, NASA 2024); luz 299.792 km/s ≈
1.079 millones de km/h ≈ 7,5 vueltas a la Tierra por segundo.
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, W, H, S, YEL, Person, Video, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "epico", 112
ITEMS = [  # clave, nombre, km/h, texto, color
    ("r10", "CARACOL", 0.05, "50 m/h", (150, 200, 110)),
    ("r9", "USAIN BOLT", 44.7, "44,7 km/h", (255, 214, 70)),
    ("r8", "GUEPARDO", 98, "≈100 km/h", (240, 170, 70)),
    ("r7", "HALCÓN PEREGRINO", 320, "+300 km/h", (200, 160, 120)),
    ("r6", "AVIÓN", 900, "900 km/h", (150, 200, 255)),
    ("r5", "BALA DE FUSIL", 3000, "3.000 km/h", (230, 190, 90)),
    ("r4", "ESTACIÓN ESPACIAL", 28000, "28.000 km/h", (200, 210, 230)),
    ("r3", "TÚ (CON LA TIERRA)", 107000, "107.000 km/h", (90, 160, 255)),
    ("r2", "SONDA PARKER", 692000, "692.000 km/h", (255, 150, 80)),
    ("r1", "LA LUZ", 1.079e9, "1.079 MILLONES km/h", (255, 255, 230)),
]
LOG0, LOG1 = -2.0, 9.5
COMP = ["EL CARACOL", "BOLT", "EL GUEPARDO", "EL HALCÓN", "EL AVIÓN", "LA BALA", "LA ESTACIÓN", "LA TIERRA", "LA PARKER"]


class VIDEO(Video):
    NAME = "velocidad"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"diez", "lenta", "rápida", "uno", "cabeza", "caracol", "cincuenta", "bolt", "cuarenta", "guepardo", "cien", "halcón",
                "trescientos", "animal", "avión", "novecientos", "bala", "tres", "estación", "veintiocho", "hora", "tú", "sofá", "tierra",
                "sol", "parker", "nasa", "setecientos", "humano", "luz", "millones", "segundo", "siete", "vueltas", "sorprendido", "comentarios"}

    def setup(self):
        self.runner = Person(random.Random(2), 540, 260, shirt=(255, 214, 70))
        self.runner.long_hair = False
        self.rnd = random.Random(11)
        self.streaks = [(self.rnd.uniform(0, W), self.rnd.uniform(620, 1220), self.rnd.uniform(60, 240)) for _ in range(40)]
        self.shakes = [(self.start("r1") + 0.3, 1.0)]

    def build_scenes(self):
        return [(0.0, "intro")] + [(self.start(k) - 0.1, "item") for k, *_ in ITEMS] + [(self.start("cta") - 0.1, "fin")]

    def item_at(self, t):
        cur = None
        for i, it in enumerate(ITEMS):
            if t >= self.start(it[0]) - 0.1:
                cur = i
        return cur

    # ───── escala logarítmica de abajo ─────
    def ladder(self, img, d, t, upto, anim=1.0):
        x0, x1, y = 90, 990, 1640
        self.R(d, x0, y - 10, x1, y + 10, (40, 44, 70), radius=10)
        for e in range(-2, 10, 2):  # marcas de potencias de 10
            x = x0 + (x1 - x0) * (e - LOG0) / (LOG1 - LOG0)
            self.Ln(d, [(x, y + 16), (x, y + 30)], (110, 110, 150), 3)
        self.text(img, x0, y + 56, "LENTO", 28, (150, 150, 190), anchor="lm")
        self.text(img, x1, y + 56, "RÁPIDO", 28, (150, 150, 190), anchor="rm")
        for i in range(upto + 1):
            _, _, v, _, col = ITEMS[i]
            f = (math.log10(v) - LOG0) / (LOG1 - LOG0)
            if i == upto:
                prev = (math.log10(ITEMS[i - 1][2]) - LOG0) / (LOG1 - LOG0) if i > 0 else 0
                f = prev + (f - prev) * ease_out(anim)
            x = x0 + (x1 - x0) * f
            r = 16 if i == upto else 10
            if i == upto:
                self.R(d, x0, y - 10, x, y + 10, col, radius=10)
                self.glow(img, x, y, 40, col, 160)
            self.E(d, x, y, r, col, outline=(20, 20, 30), width=3)

    # ───── objetos ─────
    def obj(self, img, d, i, t, lt):
        key, name, v, _, col = ITEMS[i]
        cx, cy = 540, 960
        if key == "r10":  # caracol que avanza despacito
            x = 300 + 40 * smooth(0, 4, lt)
            self.R(d, 120, cy + 92, 960, cy + 104, (60, 80, 60))
            self.E(d, x + 60, cy + 70, 150, (190, 160, 120), ry=28)
            self.E(d, x, cy, 100, (160, 110, 70))
            for k in range(3):
                self.E(d, x + 8 * k, cy - 4 * k, 70 - 22 * k, (190 - 20 * k, 140 - 15 * k, 90), outline=(120, 80, 50), width=4)
            for sx in (0, 1):
                self.Ln(d, [(x + 170 + 14 * sx, cy + 50), (x + 190 + 20 * sx, cy - 20 + 4 * math.sin(t * 4 + sx))], (190, 160, 120), 6)
                self.E(d, x + 190 + 20 * sx, cy - 22, 9, (60, 40, 30))
        elif key == "r9":  # corredor
            sp, (ax, ay) = self.runner.sprite("stand", "smile", "down", t * 14, 1.7)
            img.alpha_composite(sp, (int(540 * S - ax), int((cy + 190) * S - ay)))
            self.speed_lines(d, t, 0.6, col)
        elif key == "r8":  # guepardo estilizado
            b = 12 * math.sin(t * 20)
            self.E(d, cx, cy + b * 0.3, 210, (240, 175, 80), ry=62)
            self.E(d, cx + 210, cy - 40 + b * 0.3, 64, (240, 175, 80), ry=52)
            self.E(d, cx + 228, cy - 52, 10, (30, 30, 30))
            self.Ln(d, [(cx - 200, cy - 10), (cx - 330, cy - 70 + b)], (240, 175, 80), 18)
            for k, ph in enumerate((0, 1.6, 3.1, 4.7)):
                lx = cx - 130 + k * 85
                self.Ln(d, [(lx, cy + 40), (lx + 70 * math.sin(t * 20 + ph), cy + 170)], (220, 155, 70), 18)
            for k in range(14):
                self.E(d, cx - 160 + (k * 37) % 330, cy - 30 + (k * 23) % 60, 9, (60, 40, 25))
            self.speed_lines(d, t, 1.0, col)
        elif key == "r7":  # halcón en picado
            y = cy - 200 + ((lt * 1.6) % 1) * 450
            self.P(d, [(cx, y + 120), (cx - 160, y - 70), (cx - 20, y - 20), (cx, y - 120), (cx + 20, y - 20), (cx + 160, y - 70)], (150, 120, 95))
            self.E(d, cx, y + 70, 30, (230, 220, 200))
            for k in range(8):
                xx = cx - 140 + k * 40
                self.Ln(d, [(xx, y - 300), (xx, y - 140)], (190, 200, 230), 4)
        elif key == "r6":  # avión
            x = 540 + 30 * math.sin(t)
            self.R(d, x - 300, cy - 40, x + 300, cy + 40, (235, 238, 245), radius=40)
            self.P(d, [(x - 40, cy), (x + 80, cy), (x - 120, cy + 230), (x - 180, cy + 230)], (200, 205, 220))
            self.P(d, [(x - 40, cy), (x + 80, cy), (x - 120, cy - 230), (x - 180, cy - 230)], (200, 205, 220))
            self.P(d, [(x - 300, cy), (x - 240, cy), (x - 320, cy - 130)], (90, 140, 220))
            for k in range(8):
                self.E(d, x + 180 - k * 50, cy - 10, 11, (90, 140, 220))
            self.speed_lines(d, t, 1.4, (200, 220, 255))
        elif key == "r5":  # bala
            x = -200 + ((lt * 1.1) % 1) * 1500
            self.Ln(d, [(-50, cy), (x - 160, cy)], (255, 230, 170), 6)  # estela
            self.glow(img, x - 200, cy, 90, (255, 220, 150), 90)
            self.R(d, x - 160, cy - 34, x + 40, cy + 34, (200, 150, 70), radius=10)
            self.P(d, [(x + 40, cy - 34), (x + 160, cy), (x + 40, cy + 34)], (210, 160, 80))
            for k in range(10):
                self.Ln(d, [(x - 200 - k * 60, cy - 30 + k * 6), (x - 260 - k * 60, cy - 30 + k * 6)], (230, 230, 240), 4)
        elif key == "r4":  # ISS orbitando la Tierra
            self.globe(img, cx, cy + 40, 230, t, spin=40)
            a = lt * 2.2
            x, y = cx + math.cos(a) * 340, cy + 40 + math.sin(a) * 130
            self.R(d, x - 70, y - 6, x + 70, y + 6, (210, 210, 220))
            for sx in (-1, 1):
                self.R(d, x + sx * 70, y - 30, x + sx * 110, y + 30, (60, 90, 170))
            self.R(d, x - 18, y - 16, x + 18, y + 16, (230, 230, 240))
        elif key == "r3":  # la Tierra alrededor del Sol (con un sofá diminuto)
            self.glow(img, cx, cy, 160, (255, 210, 120), 200)
            self.E(d, cx, cy, 90, (255, 214, 120))
            d.ellipse([(cx - 360) * S, (cy - 150) * S, (cx + 360) * S, (cy + 150) * S], outline=(80, 90, 130), width=3 * S)
            a = lt * 1.2
            ex, ey = cx + math.cos(a) * 360, cy + math.sin(a) * 150
            self.globe(img, ex, ey, 58, t, spin=80, glow_a=40)
            self.R(d, ex - 22, ey - 98, ex + 22, ey - 80, (200, 60, 70), radius=6)  # sofá
            self.R(d, ex - 22, ey - 110, ex - 14, ey - 80, (200, 60, 70), radius=4)
        elif key == "r2":  # sonda Parker rozando el Sol
            self.glow(img, 180, cy, 320, (255, 160, 60), 230)
            self.E(d, 150, cy, 240, (255, 190, 90))
            a = 0.6 - min(lt, 6.0) * 0.17
            x, y = 540 + math.cos(a) * 260, cy + math.sin(a) * 380
            self.E(d, x, y, 60, (235, 235, 240))
            self.R(d, x + 10, y - 26, x + 90, y + 26, (90, 90, 110))
            for k in range(6):
                self.Ln(d, [(x + 100 + k * 30, y - 20 + k * 8), (x + 160 + k * 30, y - 20 + k * 8)], (255, 200, 120), 4)
        else:  # la luz: haz cegador
            k = smooth(0, 0.4, lt)
            for j in range(5):
                yy = cy - 120 + j * 60
                self.Ln(d, [(-50, yy), (W + 50, yy)], (255, 255, 235), 10 - j)
            self.glow(img, cx, cy, 380 * k, (255, 250, 220), 130 * k)
            self.globe(img, cx, cy + 20, 120, t, spin=7.5 * 360 / 4, glow_a=0)

    def speed_lines(self, d, t, k, col):
        for x, y, L in self.streaks:
            xx = (x - t * 900 * k) % (W + 300) - 150
            self.Ln(d, [(xx, y), (xx + L * k, y)], mix(col, (255, 255, 255), 0.5), 4)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.bgdyn(img, (8, 6, 24), (30, 14, 50))
        self.stars(d, t, 0.6, drift=-60)
        for j, (key, name, v, txt, col) in enumerate(ITEMS[::-1]):  # vistazo rápido de los 10 (de 1 a 10)
            ph = (t * 4 + j * 0.37) % 1
            self.Ln(d, [(W * ph - 300, 650 + j * 70), (W * ph, 650 + j * 70)], col, 6)
        self.pop_text(img, 540, 560, "DEL MÁS LENTO", 96, t, 0.2, WHITE)
        self.pop_text(img, 540, 680, "AL MÁS RÁPIDO", 96, t, 0.5, YEL)
        k = back_out((t - self.w("intro", "número")) / 0.4)
        if k > 0:
            self.E(d, 540, 1150, 190 * k, (255, 214, 70))
            self.text(img, 540, 1150, "#1", 170 * k, (30, 20, 50), shadow=False)
            self.qmark(img, 760, 990, 140 * k)
        self.pop_text(img, 540, 1450, "TE VA A VOLAR LA CABEZA", 64, t, self.w("intro", "volar"), RED)

    def s_item(self, img, d, t, lt, u):
        i = self.item_at(t)
        key, name, v, txt, col = ITEMS[i]
        top = mix((10, 10, 26), col, 0.12)
        self.bgdyn(img, top, (8, 8, 18))
        if key in ("r4", "r3", "r2"):
            self.stars(d, t, 0.8)
        rank = 10 - i
        k = back_out(lt / 0.35)
        self.obj(img, d, i, t, lt)
        if key == "r1":  # destello final (antes de los textos, para que se lean)
            fl = max(0.0, 1 - lt / 0.6)
            if fl > 0:
                from PIL import Image
                img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 240, int(230 * fl))))
        self.text(img, 540, 470, f"#{rank}", 170 * max(0.05, k), col if key != "r1" else YEL)
        self.pop_text(img, 540, 610, name, 70 if len(name) < 14 else 58, t, self.start(key) + 0.15, WHITE)
        ks = smooth(self.start(key) + 0.3, self.start(key) + 1.6, t)
        if key == "r1":
            shown = f"{int(1079 * ks):,}".replace(",", ".") + " MILLONES km/h"
        else:
            shown = txt if ks >= 1 else self.roll(v * ks, key)
        self.text(img, 540, 1330, shown, 78 if len(shown) < 14 else 62, col)
        if i > 0:
            f = v / ITEMS[i - 1][2]
            fs = f"×{f:,.0f}".replace(",", ".") if f >= 10 else f"×{f:.1f}".replace(".", ",")
            self.pop_text(img, 540, 1440, f"{fs} MÁS QUE {COMP[i - 1]}", 42, t, self.start(key) + 1.7, (200, 200, 230))
        self.ladder(img, d, t, i, anim=smooth(0.2, 1.4, lt))
        if key == "r1":
            self.pop_text(img, 540, 1530, "7,5 VUELTAS A LA TIERRA / SEGUNDO", 40, t, self.w("r1", "siete"), YEL)

    @staticmethod
    def roll(x, key):
        if key == "r10":
            return f"{int(x * 1000)} m/h"
        return f"{x:,.0f} km/h".replace(",", ".")

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def camera(self, t, name, lt, u):
        if name == "item":
            return 1.0 + 0.05 * smooth(0, 4, lt) + 0.01 * math.sin(t * 2), 540, 980
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        ev = [(0.15, "boom", 0.6), (0.5, "pop", 0.4), (self.w("intro", "número"), "riser", 0.5), (self.w("intro", "volar"), "boom", 0.5)]
        for k, *_ in ITEMS:
            st = self.start(k)
            ev += [(st - 0.1, "whoosh", 0.5), (st + 0.05, "pop", 0.55), (st + 1.6, "tick", 0.8)]
        ev += [(self.start("r1") + 0.1, "boom", 1.0), (self.start("r1") + 0.15, "shimmer", 0.7), (self.start("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        p = [(0, 0.8)]
        for j, (k, *_) in enumerate(ITEMS):
            p.append((self.start(k), 0.55 + 0.04 * j))
        return p + [(self.start("r1"), 1.0), (self.start("cta"), 0.45), (self.duration, 0.3)]

    def scene_label(self):
        return None


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
