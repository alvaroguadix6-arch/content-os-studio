"""NIVEL OCULTO · ¿Qué pasaría si intentaras aterrizar en Júpiter?

Fuentes: NASA (Júpiter: gigante gaseoso sin superficie sólida, sobre todo hidrógeno y helio; cabrían ~1.300 Tierras;
capas: hidrógeno molecular → hidrógeno líquido → hidrógeno metálico; núcleo denso, «difuso» según Juno), sonda
atmosférica de Galileo (7-12-1995): entrada a ~47,4 km/s ≈ 170.000 km/h, perdió más de la mitad de la masa de su
escudo térmico (≈80 de 152 kg), paracaídas, nubes de amoníaco, vientos de cientos de km/h, transmitió 58 minutos
hasta ~150 km bajo las nubes, a ~23 bar y ~153 °C.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from motor import CYAN, RED, WHITE, W, H, S, YEL, Video, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "espacio", 84
BANDS = [(226, 206, 178), (196, 150, 112), (236, 222, 200), (178, 128, 92), (230, 210, 182), (204, 164, 126), (238, 228, 210),
         (186, 138, 100), (224, 200, 170)]


class VIDEO(Video):
    NAME = "jupiter"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"aterrizar", "júpiter", "suelo", "grande", "mil", "trescientas", "tierras", "hidrógeno", "helio", "estrella", "gravedad",
                "acelera", "galileo", "noventa", "ciento", "setenta", "kilómetros", "fuego", "mitad", "escudo", "paracaídas",
                "amoníaco", "vientos", "cincuenta", "ocho", "minutos", "veintitrés", "grados", "presión", "aplastaría", "líquido",
                "metálico", "núcleo", "firme", "decenas", "planeta", "comentarios"}

    def setup(self):
        self.t_fire = self.w("fuego", "fuego")

    def build_scenes(self):
        st = self.start
        return [(0.0, "llegar"), (st("tamano") - 0.12, "tamano"), (st("llegada") - 0.12, "galileo"), (st("fuego") - 0.12, "fuego"),
                (st("nubes") - 0.12, "nubes"), (st("hundirse") - 0.12, "hundirse"), (st("abajo") - 0.12, "corte"), (st("cta") - 0.1, "fin")]

    # ───── Júpiter (bandas + Gran Mancha Roja) ─────
    def jupiter(self, img, cx, cy, R, t, glow=True):
        n_full = int(2 * R * S)
        if n_full < 4:
            return
        n = min(n_full, 1100)  # se calcula a resolución limitada y se escala (ahorra memoria con planetas gigantes)
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        u, v = (xx - n / 2) / (n / 2), (yy - n / 2) / (n / 2)
        r2 = u * u + v * v
        inside = r2 <= 1
        z = np.sqrt(np.clip(1 - r2, 0, 1))
        lat = np.arcsin(np.clip(v, -1, 1))
        lon = np.arctan2(u, z) + t * 0.08
        band = (lat * 9 + 0.25 * np.sin(lon * 3 + lat * 14) + 0.12 * np.sin(lon * 7 - t * 0.2)) % len(BANDS)
        i0 = band.astype(int) % len(BANDS)
        f = (band - np.floor(band))[..., None]
        pal = np.array(BANDS, np.float32)
        col = pal[i0] * (1 - f) + pal[(i0 + 1) % len(BANDS)] * f
        # Gran Mancha Roja
        sl, sw = (lon - 0.6 + 2 * np.pi) % (2 * np.pi) - np.pi, lat + 0.38
        spot = np.exp(-((sl / 0.32) ** 2 + (sw / 0.13) ** 2))
        col = col * (1 - spot[..., None] * 0.8) + np.array([200, 90, 60], np.float32) * spot[..., None] * 0.8
        light = 0.35 + 0.75 * np.clip(z * 0.8 - u * 0.25 - v * 0.1, 0, 1)
        col = col * light[..., None]
        a = np.zeros((n, n, 4), np.uint8)
        a[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
        a[..., 3] = (inside * 255).astype(np.uint8)
        if glow:
            self.glow(img, cx, cy, R * 1.08, (230, 190, 140), 70, blur=R * 0.12)
        im = Image.fromarray(a)
        if n != n_full:
            im = im.resize((n_full, n_full), Image.BILINEAR)
        img.alpha_composite(im, (int((cx - R) * S), int((cy - R) * S)))

    def probe(self, d, x, y, s=1.0, heat=0.0, rot=0.0):
        """Sonda de Galileo: cono con escudo térmico delante (abajo)."""
        pts = [(-60, -40), (60, -40), (90, 30), (-90, 30)]
        c, sn = math.cos(rot), math.sin(rot)
        P = [(x + (px * c - py * sn) * s, y + (px * sn + py * c) * s) for px, py in pts]
        self.P(d, P, (190, 190, 200))
        shield = [(x + (px * c - py * sn) * s, y + (px * sn + py * c) * s) for px, py in [(-90, 30), (90, 30), (60, 62), (-60, 62)]]
        self.P(d, shield, mix((120, 80, 60), (255, 200, 80), heat))

    # ───── escenas ─────
    def s_llegar(self, img, d, t, lt, u):
        self.bgdyn(img, (2, 4, 12), (12, 10, 26))
        self.stars(d, t, 1.0, drift=-6)
        R = 420 + 260 * ease_out(lt / 5)
        self.jupiter(img, 540, 1250 + 120 * ease_out(lt / 5), R, t)
        self.probe(d, 540, 760 + 140 * ease_out(lt / 4), 0.8, rot=0.0)
        k = smooth(self.w("intro", "suelo") - 0.3, self.w("intro", "suelo") + 0.3, t)
        if k > 0:  # «suelo» que no existe
            for i in range(9):
                x = 160 + i * 90
                self.R(d, x, 1020, x + 50, 1030, mix((60, 60, 70), RED, k))
            self.pop_text(img, 540, 960, "¿SUELO?", 80, t, self.w("intro", "suelo"), RED)
        self.pop_text(img, 540, 520, "NO TIENE SUELO", 92, t, self.w("intro", "suelo") + 0.2, YEL)

    def s_tamano(self, img, d, t, lt, u):
        self.bgdyn(img, (2, 4, 12), (12, 10, 26))
        self.stars(d, t, 0.8)
        R = 380
        self.jupiter(img, 540, 1000, R, t)
        k = smooth(0.4, self.w("tamano", "tierras") + 0.3 - self.start("tamano"), lt)
        n = int(1321 * k)  # Tierras de 1/11 del radio, en rejilla hexagonal dentro del disco
        er = R / 11.2
        c = 0
        for row in range(-11, 12):
            for col in range(-11, 12):
                if c >= min(n, 400):
                    break
                x = 540 + col * er * 2 + (row % 2) * er
                y = 1000 + row * er * 1.75
                if (x - 540) ** 2 + (y - 1000) ** 2 < (R - er) ** 2:
                    self.E(d, x, y, er * 0.9, (60, 130, 210))
                    c += 1
        self.text(img, 540, 520, f"{n:,} TIERRAS".replace(",", "."), 90, YEL)
        kh = smooth(self.w("tamano", "hidrógeno") - 0.2, self.w("tamano", "hidrógeno") + 0.3, t)
        if kh > 0:
            for i, (lab, x, col) in enumerate((("H", 380, (180, 220, 255)), ("He", 700, (255, 200, 220)))):
                kk = back_out((t - self.w("tamano", "hidrógeno" if i == 0 else "helio")) / 0.35)
                if kk > 0:
                    self.E(d, x, 1550, 80 * kk, col)
                    self.text(img, x, 1550, lab, 70 * kk, (30, 30, 50), shadow=False)

    def s_galileo(self, img, d, t, lt, u):
        self.bgdyn(img, (2, 4, 12), (12, 10, 26))
        self.stars(d, t, 0.6, drift=-30 * smooth(0, 4, lt))
        k = ease_out(lt / (self.end("llegada") - self.start("llegada")))
        self.jupiter(img, 540, 2100 - 200 * k, 1100 + 300 * k, t, glow=True)
        for i in range(8):  # líneas de velocidad
            x = 200 + i * 95
            ph = (t * 3 + i * 0.3) % 1
            self.Ln(d, [(x, 300 + ph * 900), (x, 300 + ph * 900 + 120 * k)], (150, 170, 220), 3)
        self.probe(d, 540, 820 + 20 * math.sin(t * 3), 1.2)
        self.Ln(d, [(540, 960), (540, 1060 + 60 * k)], YEL, 8)  # gravedad
        self.P(d, [(510, 1060 + 60 * k), (570, 1060 + 60 * k), (540, 1110 + 60 * k)], YEL)
        ks = smooth(self.w("llegada", "galileo"), self.end("llegada"), t)
        if t >= self.w("llegada", "galileo") - 0.1:
            self.text(img, 540, 520, f"{int(170000 * ks):,} km/h".replace(",", "."), 96, WHITE)
        self.pop_text(img, 540, 640, "SONDA GALILEO · 1995", 52, t, self.w("llegada", "galileo"), CYAN)

    def s_fuego(self, img, d, t, lt, u):
        self.bgdyn(img, (30, 10, 6), (90, 40, 20))
        heat = smooth(0, 1.0, lt)
        self.P(d, [(430, 930), (650, 930), (600 + 30 * math.sin(t * 9), 470), (480 + 30 * math.sin(t * 7), 470)], (255, 120, 40))  # estela
        self.P(d, [(470, 930), (610, 930), (570 + 20 * math.sin(t * 11), 520), (510 + 20 * math.sin(t * 8), 520)], (255, 200, 90))
        for i in range(14):  # chispas de plasma hacia arriba
            ph = (t * 3 + i / 14) % 1
            x = 540 + (i - 7) * 16 + 10 * math.sin(t * 5 + i)
            y = 900 - ph * 400
            self.Ln(d, [(x, y), (x, y - 70)], mix((255, 240, 180), (255, 90, 40), ph), 8)
        self.glow(img, 540, 1000, 260, (255, 170, 60), 230 * heat)
        self.glow(img, 540, 1060, 140, (255, 240, 200), 240 * heat)
        self.probe(d, 540, 960 + 6 * math.sin(t * 40), 1.4, heat=heat)
        sh = 1 - 0.53 * smooth(self.w("fuego", "perdió") - 0.2, self.w("fuego", "escudo") + 0.6, t)
        self.R(d, 190, 1430, 890, 1490, (50, 30, 30), radius=30)
        self.R(d, 190, 1430, 190 + 700 * sh, 1490, (255, 150, 60), radius=30)
        self.text(img, 540, 1385, f"ESCUDO TÉRMICO {int(sh * 100)}%", 48, WHITE)
        self.pop_text(img, 540, 1640, "BOLA DE FUEGO", 92, t, self.t_fire, (255, 170, 60))

    def s_nubes(self, img, d, t, lt, u):
        self.bgdyn(img, (196, 160, 122), (120, 80, 60))
        for j in range(7):  # capas de nubes que suben (la sonda baja)
            y = (j * 300 - lt * 220) % 2100 - 150
            col = (235, 225, 210) if j % 2 == 0 else (210, 175, 140)
            for i in range(6):
                x = (i * 230 + t * (300 + 120 * j)) % (W + 400) - 200
                self.E(d, x, y, 170, col, ry=60)
        for i in range(10):  # vientos
            y = 400 + i * 130
            x = (t * 1200 + i * 210) % (W + 600) - 300
            self.Ln(d, [(x, y), (x + 260, y)], (255, 250, 240), 5)
        sw = 20 * math.sin(t * 2)
        self.E(d, 540 + sw, 700, 150, (240, 120, 70), ry=90)  # paracaídas
        self.R(d, 380 + sw, 700, 700 + sw, 720, (240, 120, 70))
        for sx in (-1, 0, 1):
            self.Ln(d, [(540 + sw + sx * 140, 710), (540, 990)], (240, 240, 240), 3)
        self.probe(d, 540, 1030, 0.9)
        self.pop_text(img, 540, 1450, "NUBES DE AMONÍACO", 70, t, self.w("nubes", "amoníaco"), WHITE)
        self.pop_text(img, 540, 1560, "VIENTOS DE CIENTOS DE km/h", 52, t, self.w("nubes", "vientos"), YEL)

    def s_hundirse(self, img, d, t, lt, u):
        dur = self.end("hundirse") - self.start("hundirse")
        k = smooth(0, dur * 0.75, lt)
        self.bgdyn(img, mix((170, 120, 90), (80, 40, 30), k), mix((90, 50, 40), (30, 12, 10), k))
        for i in range(30):
            ph = (t * 0.8 + i / 30) % 1
            self.E(d, (i * 137) % W, H - ph * H, 3 + 4 * (i % 3), mix((230, 200, 170), (120, 70, 50), k))
        self.probe(d, 540, 960 + 8 * math.sin(t * 2), 1.2, heat=0.3 * k)
        self.glow(img, 540, 960, 120, (255, 160, 80), 120 * k)
        self.R(d, 80, 560, 1000, 760, (20, 10, 10), radius=28)
        cols = [("TIEMPO", f"{int(58 * k)} min", WHITE), ("PROFUNDIDAD", f"{int(150 * k)} km", CYAN), ("PRESIÓN", f"×{1 + int(22 * k)}", YEL),
                ("TEMPERATURA", f"{int(-110 + 263 * k)} °C", (255, 140, 90))]
        for i, (lab, val, col) in enumerate(cols):
            x = 195 + i * 230
            self.text(img, x, 625, val, 48, col)
            self.text(img, x, 700, lab, 24, (200, 190, 180))
        if lt > dur - 0.4:
            self.text(img, 540, 1400, "SEÑAL PERDIDA", 80, RED, alpha=0.5 + 0.5 * math.sin(t * 12))

    def s_corte(self, img, d, t, lt, u):
        self.bgdyn(img, (2, 4, 12), (12, 10, 26))
        self.stars(d, t, 0.6)
        cx, cy, R = 540, 1050, 470
        self.jupiter(img, cx, cy, R, t)
        k = ease_out(lt / 1.2)  # se abre un gajo y se ven las capas
        from PIL import ImageDraw
        a0, a1 = -90, -90 + 110 * k
        layers = [(1.0, (226, 206, 178), None), (0.97, (120, 170, 230), "líquido"), (0.78, (170, 160, 210), "metálico"), (0.45, (150, 110, 90), "núcleo")]
        for frac, col, key in layers:
            rr = R * frac
            d.pieslice([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], a0, a1, fill=col)

    def overlay(self, ov, d, t, name, lt, u):
        if name == "nubes":  # banda oscura para leer los subtítulos sobre las nubes claras
            for i in range(40):
                d.rectangle([0, (170 + i * 5) * S, W * S, (175 + i * 5) * S], fill=(30, 16, 10, int(190 * (1 - i / 40))))
            d.rectangle([0, 0, W * S, 170 * S], fill=(30, 16, 10, 190))
            return True
        if name != "corte":
            return False
        labels = [("abajo", "líquido", "HIDRÓGENO LÍQUIDO", (120, 170, 230)), ("abajo", "metálico", "HIDRÓGENO METÁLICO", (170, 160, 210)),
                  ("nucleo", "núcleo", "NÚCLEO", (150, 110, 90))]
        for i, (line, key_word, lab, col) in enumerate(labels):
            kk = smooth(self.w(line, key_word) - 0.2, self.w(line, key_word) + 0.3, t)
            if kk > 0:
                y = 1420 + i * 90
                self.R(d, 90, y - 26, 142, y + 26, col, radius=10)
                self.text(ov, 170, y, lab, 50, WHITE, alpha=kk, anchor="lm")
        kq = back_out((t - self.w("nucleo", "firme")) / 0.4)
        if kq > 0:
            self.text(ov, 540, 1720, "SIN SUELO FIRME", 80 * kq, RED)
        return True

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def camera(self, t, name, lt, u):
        if name == "corte":
            tz = self.start("nucleo")
            k = smooth(tz - 0.3, tz + 2.5, t)
            return 1.0 + 0.9 * k, 540 + 60 * k, 1050 - 20 * k
        if name == "fuego":
            return 1.04 + 0.02 * math.sin(t * 30), 540, 960
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.1, "riser", 0.4), (self.w("intro", "suelo"), "boom", 0.6), (st("tamano") + 0.4, "shimmer", 0.4),
                (self.w("tamano", "tierras"), "pop", 0.5), (st("llegada") + 0.2, "whoosh", 0.6), (self.w("llegada", "ciento"), "riser", 0.5),
                (st("fuego"), "rumble", 0.7), (self.t_fire, "boom", 0.8), (st("nubes") + 0.2, "wind", 0.6), (self.w("nubes", "vientos"), "wind", 0.5),
                (st("hundirse") + 0.3, "rumble", 0.4), (self.end("hundirse") - 0.3, "beep", 0.5), (st("abajo") + 0.3, "crack", 0.4),
                (self.w("abajo", "metálico"), "shimmer", 0.5), (self.w("nucleo", "firme"), "boom", 0.6), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.7), (st("tamano"), 0.55), (st("llegada"), 0.8), (st("fuego"), 1.0), (st("nubes"), 0.75), (st("hundirse"), 0.85),
                (st("abajo"), 0.65), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
