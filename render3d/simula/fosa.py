"""NIVEL OCULTO · ¿Qué pasaría si bajaras al punto más profundo del océano?

Fuentes: NOAA (abismo Challenger, fosa de las Marianas, ~10.935 m; Everest 8.849 m → sobran >2 km; zona afótica
desde ~1.000 m; presión >1.000 veces la de superficie ≈ 1.086 bar ≈ 1,1 t/cm²; agua del fondo a 1-4 °C), batiscafo
Trieste (Piccard y Walsh, 23-1-1960), James Cameron (Deepsea Challenger, 26-3-2012, descenso de 2 h 36 min),
pez caracol filmado a 8.336 m (Univ. de Australia Occidental, 2022), anfípodos en el fondo, bolsa de plástico
registrada a 10.898 m (Chiba et al., Marine Policy 2018). Vasos de poliestireno que encogen con la presión (clásico
en expediciones).
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, W, H, S, YEL, Video, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "suspense", 80
SURF = (40, 120, 190)
DEEP = (2, 4, 12)


def depth_col(m):
    k = clamp(m / 1000) ** 0.6
    return mix(SURF, (6, 14, 40), k) if m < 1000 else mix((6, 14, 40), DEEP, clamp((m - 1000) / 9000))


class VIDEO(Video):
    NAME = "fosa"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"profundo", "océano", "everest", "sobrarían", "dos", "kilómetros", "challenger", "marianas", "pacífico", "once",
                "luz", "mil", "oscuridad", "total", "grados", "siempre", "presión", "veces", "tonelada", "centímetro", "agua",
                "pulmones", "aplastado", "submarinos", "esferas", "gruesísimas", "vida", "crustáceos", "pez", "caracol", "ocho",
                "trieste", "sesenta", "cameron", "solo", "horas", "plástico", "remoto", "comentarios"}

    def setup(self):
        r = random.Random(4)
        self.snow = [(r.uniform(0, W), r.uniform(0, H), r.uniform(1.5, 4), r.uniform(20, 60)) for _ in range(90)]
        self.d0 = self.start("luz") - 0.12
        self.d1 = self.end("presion") + 0.2

    def build_scenes(self):
        st = self.start
        return [(0.0, "everest"), (st("lugar") - 0.12, "globo"), (st("luz") - 0.12, "bajada"), (st("cuerpo") - 0.12, "esfera"),
                (st("vida") - 0.12, "vida"), (st("historia") - 0.12, "historia"), (st("plastico") - 0.12, "plastico"), (st("cta") - 0.1, "fin")]

    # ───── piezas ─────
    def depth_now(self, t):
        """Profundidad durante la bajada continua (luz → frío → presión)."""
        k = clamp((t - self.d0) / (self.d1 - self.d0))
        return 10935 * (k ** 1.6)

    def marine_snow(self, d, t, speed=1.0, alpha=1.0):
        for x, y, r, v in self.snow:
            yy = (y - t * v * speed) % H
            c = int(150 * alpha)
            self.E(d, x, yy, r, (c, c, min(255, c + 30)))

    def seabed(self, d, y, t, col=(40, 38, 46)):
        pts = [(x, y + 18 * math.sin(x / 90 + 1.3) + 8 * math.sin(x / 31)) for x in range(-20, W + 40, 20)]
        self.P(d, pts + [(W + 40, H), (-20, H)], col)

    def sphere_sub(self, d, x, y, r, wall=0.22):
        self.E(d, x, y, r, (150, 156, 170))
        self.E(d, x, y, r * (1 - wall), (30, 40, 60))
        self.E(d, x - r * 0.3, y - r * 0.3, r * 0.18, (255, 220, 120))

    def trieste(self, d, x, y, s=1.0):
        self.R(d, x - 230 * s, y - 120 * s, x + 230 * s, y + 10 * s, (60, 70, 90), radius=60 * s)  # flotador
        self.R(d, x - 30 * s, y - 175 * s, x + 30 * s, y - 115 * s, (60, 70, 90))
        self.Ln(d, [(x, y + 10 * s), (x, y + 50 * s)], (90, 90, 100), 12 * s)
        self.sphere_sub(d, x, y + 100 * s, 60 * s)

    def challenger(self, d, x, y, s=1.0):
        self.R(d, x - 40 * s, y - 260 * s, x + 40 * s, y + 160 * s, (90, 200, 90), radius=40 * s)
        self.R(d, x - 40 * s, y + 60 * s, x + 40 * s, y + 160 * s, (240, 240, 245), radius=30 * s)
        self.E(d, x, y + 140 * s, 18 * s, (255, 230, 140))

    def fish(self, d, x, y, s, t, col=(235, 225, 235)):
        wob = math.sin(t * 6) * 0.2
        self.E(d, x, y, 70 * s, col, ry=34 * s)
        self.P(d, [(x + 60 * s, y), (x + 120 * s, y - 34 * s + wob * 30 * s), (x + 120 * s, y + 34 * s + wob * 30 * s)], col)
        self.E(d, x - 42 * s, y - 6 * s, 7 * s, (30, 30, 40))

    def amphipod(self, d, x, y, s, t):
        for i in range(6):
            self.E(d, x + i * 16 * s, y - 6 * s * math.sin(i * 0.6), 14 * s, (245, 200, 190))
        for i in range(6):
            lx = x + i * 16 * s
            self.Ln(d, [(lx, y + 8 * s), (lx + 6 * s * math.sin(t * 12 + i), y + 24 * s)], (230, 180, 170), 3)

    # ───── escenas ─────
    def s_everest(self, img, d, t, lt, u):
        self.bg(img, "ev", (110, 170, 225), (8, 16, 40))
        sea = 520
        self.R(d, 0, sea, W, H, (20, 60, 120))
        for i in range(30):  # degradado del mar
            self.R(d, 0, sea + i * 48, W, sea + (i + 1) * 48, mix((30, 100, 170), (4, 8, 24), i / 30))
        self.Ln(d, [(x, sea + 6 * math.sin(x / 50 + t * 3)) for x in range(0, W + 20, 20)], (180, 220, 255), 6)
        bot = 1720
        scale = (bot - sea) / 10935  # px por metro
        self.P(d, [(0, sea + 900), (330, bot - 40), (420, bot), (660, bot), (750, bot - 40), (W, sea + 900), (W, H), (0, H)], (36, 34, 44))
        k = ease_out(lt / 2.0)
        top = bot - 8849 * scale * k  # el Everest sube desde el fondo
        self.P(d, [(380, bot), (540, top), (700, bot)], (130, 120, 115))
        self.P(d, [(500, top + 80 * k), (540, top), (580, top + 80 * k), (560, top + 60 * k), (540, top + 75 * k), (520, top + 60 * k)], WHITE)
        tw = self.w("intro", "sobrarían") - 0.2
        k2 = smooth(tw, tw + 0.6, t)
        if k2 > 0:
            self.Ln(d, [(800, sea), (800, sea + (top - sea) * k2)], YEL, 8)
            self.text(img, 900, (sea + top) / 2, "+2 km", 64, YEL, alpha=k2)
        self.text(img, 540, top - 50, "EVEREST", 52, WHITE, alpha=k)

    def s_globo(self, img, d, t, lt, u):
        self.bgdyn(img, (4, 6, 18), (12, 16, 40))
        self.stars(d, t, 0.8)
        tm = self.start("lugar") + 1.5
        spin = 6.0
        rot0 = 142 + 180 - spin * tm  # la fosa queda en el centro hacia la mitad de la frase
        self.globe(img, 540, 980, 360, t, spin=spin, rot0=rot0)
        c = (t * spin + rot0) % 360 - 180
        dl = math.radians(142.2 - c)
        px, py = 540 + 360 * math.cos(math.radians(11.35)) * math.sin(dl), 980 - 360 * math.sin(math.radians(11.35))
        k = back_out((lt - 0.8) / 0.4)
        if k > 0 and math.cos(dl) > 0:
            self.E(d, px, py, 22 * k, RED, outline=WHITE, width=5)
            self.Ln(d, [(px, py), (800, 700)], WHITE, 5)
        self.pop_text(img, 800, 650, "FOSA DE LAS MARIANAS", 46, t, self.w("lugar", "marianas"), WHITE)
        self.pop_text(img, 540, 1500, "≈ 11 km DE PROFUNDIDAD", 66, t, self.w("lugar", "once"), YEL)

    def s_bajada(self, img, d, t, lt, u):
        m = self.depth_now(t)
        self.bgdyn(img, depth_col(m * 0.85), depth_col(m * 1.1 + 200))
        sun = 1 - clamp(m / 1000)
        if sun > 0:  # haces de luz que se apagan
            for i in range(5):
                x = 180 + i * 180 + 40 * math.sin(t * 0.5 + i)
                self.P(d, [(x - 30, 0), (x + 30, 0), (x + 120, H), (x - 120, H)], mix((20, 60, 110), (120, 190, 240), 0.35 * sun))
        self.marine_snow(d, t, 2.0, 0.4 + 0.6 * (1 - sun))
        # la esfera bajando (con foco cuando ya es de noche)
        if sun < 0.6:
            self.glow(img, 540, 1180, 180, (255, 230, 150), 90 * (1 - sun))
        self.sphere_sub(d, 540, 960 + 10 * math.sin(t * 2), 90)
        # profundímetro a la derecha
        self.R(d, 930, 380, 970, 1640, (30, 40, 70), radius=20)
        yy = 380 + 1260 * m / 10935
        self.E(d, 950, yy, 24, YEL)
        self.text(img, 540, 620, f"{int(m):,} m".replace(",", "."), 104, WHITE)
        st = self.start
        if t >= st("frio") - 0.12:
            k = smooth(st("frio"), st("frio") + 0.4, t)
            self.text(img, 230, 1400, "1–2 °C", 74, CYAN, alpha=k)
        if t >= self.w("luz", "oscuridad") - 0.1 and t < st("frio"):
            self.pop_text(img, 540, 1420, "OSCURIDAD TOTAL", 70, t, self.w("luz", "oscuridad"), WHITE)
        if t >= st("presion") - 0.12:
            p = int(1 + m / 10.06)
            self.text(img, 540, 1560, f"PRESIÓN ×{p:,}".replace(",", "."), 66, YEL)
            kc = smooth(st("presion"), self.end("presion"), t)
            cw = 90 * (1 - 0.45 * kc)  # vaso de poliestireno que encoge
            self.P(d, [(260 - cw / 2, 1150 - cw), (260 + cw / 2, 1150 - cw), (260 + cw * 0.35, 1150), (260 - cw * 0.35, 1150)], (245, 245, 240))
            self.text(img, 260, 1220, "VASO", 34, WHITE, alpha=clamp(kc * 3))
            self.pop_text(img, 760, 1300, "1 t / cm²", 64, t, self.w("presion", "tonelada"), RED)

    def s_esfera(self, img, d, t, lt, u):
        self.bgdyn(img, (4, 8, 20), (1, 2, 8))
        self.marine_snow(d, t, 0.6, 0.8)
        tb = self.w("cuerpo", "submarinos")
        if t < tb - 0.15:  # cuerpo: pulmones que se aplastan
            k = smooth(self.w("cuerpo", "pulmones") - 0.2, self.w("cuerpo", "aplastado") + 0.3, t)
            self.E(d, 540, 600, 90, (60, 90, 140))  # silueta
            self.R(d, 380, 700, 700, 1400, (60, 90, 140), radius=150)
            for sx in (-1, 1):
                self.R(d, 540 + sx * 160 - 40, 740, 540 + sx * 160 + 40, 1240, (60, 90, 140), radius=40)
            self.text(img, 540, 1300, "≈ 60 % AGUA", 44, CYAN)
            for sx in (-1, 1):
                self.E(d, 540 + sx * 70, 950, 55 * (1 - 0.6 * k), (240, 130, 150), ry=110 * (1 - 0.55 * k))
            for i in range(8):  # flechas de presión hacia dentro
                a = i / 8 * 2 * math.pi
                x0, y0 = 540 + math.cos(a) * 330, 1000 + math.sin(a) * 420
                x1, y1 = 540 + math.cos(a) * 250, 1000 + math.sin(a) * 340
                self.Ln(d, [(x0, y0), (x1, y1)], YEL, 10)
            self.pop_text(img, 540, 1560, "AIRE APLASTADO", 72, t, self.w("cuerpo", "aplastado"), RED)
        else:  # corte de la esfera de paredes gruesas
            k = back_out((t - tb) / 0.5)
            self.sphere_sub(d, 540, 980, 300 * k, wall=0.3)
            self.Ln(d, [(540 + 210 * k, 980), (540 + 300 * k, 980)], YEL, 8)
            self.pop_text(img, 540, 1460, "PAREDES GRUESÍSIMAS", 68, t, self.w("cuerpo", "gruesísimas"), YEL)
            self.text(img, 540, 1560, "TRIESTE: 12,7 cm DE ACERO", 48, WHITE, alpha=smooth(self.w("cuerpo", "gruesísimas") + 0.3, self.w("cuerpo", "gruesísimas") + 0.7, t))

    def s_vida(self, img, d, t, lt, u):
        self.bgdyn(img, (2, 6, 18), (1, 2, 6))
        self.glow(img, 540, 1250, 420, (60, 110, 160), 80)
        self.marine_snow(d, t, 0.4, 0.7)
        self.seabed(d, 1520, t)
        for i in range(4):
            self.amphipod(d, 160 + i * 220 + 30 * math.sin(t + i), 1500 - 20 * (i % 2), 1.4, t + i)
        tf = self.w("vida", "pez")
        if t > tf - 0.3:
            k = ease_out((t - tf + 0.3) / 2.5)
            self.fish(d, 1150 - 700 * k, 1100 + 30 * math.sin(t * 2), 1.6, t)
        self.pop_text(img, 540, 620, "PEZ CARACOL · 8.336 m", 62, t, self.w("vida", "caracol"), CYAN)

    def s_historia(self, img, d, t, lt, u):
        self.bgdyn(img, (6, 12, 30), (1, 3, 10))
        self.marine_snow(d, t, 1.0, 0.6)
        tc = self.w("historia", "cameron") - 0.3
        if t < tc:
            y = 600 + 700 * smooth(0, tc - self.start("historia"), lt)
            self.trieste(d, 540, y, 1.4)
            self.pop_text(img, 540, 470, "TRIESTE · 1960", 80, t, self.start("historia") + 0.3, YEL)
        else:
            y = 500 + 600 * smooth(tc, self.end("historia"), t)
            self.challenger(d, 540, y, 1.3)
            self.pop_text(img, 540, 470, "CAMERON · 2012", 80, t, tc + 0.1, (90, 220, 110))
            k = smooth(self.w("historia", "horas") - 0.6, self.w("historia", "horas") + 0.6, t)
            mins = int(156 * k)
            self.text(img, 540, 1640, f"{mins // 60} h {mins % 60:02d} min", 80, WHITE, alpha=clamp(k * 3))

    def s_plastico(self, img, d, t, lt, u):
        self.bgdyn(img, (2, 6, 18), (1, 2, 6))
        self.glow(img, 540, 1300, 380, (90, 120, 150), 90)
        self.marine_snow(d, t, 0.3, 0.6)
        self.seabed(d, 1480, t)
        y = 520 + 860 * ease_out(lt / 3.2)
        sway = 50 * math.sin(t * 1.6)
        pts = [(540 + sway - 110, y - 40), (540 + sway + 110, y - 60), (540 + sway + 90, y + 120), (540 + sway - 80, y + 140)]
        self.P(d, pts, (230, 236, 245))
        self.Ln(d, [(540 + sway - 60, y - 46), (540 + sway - 40, y - 110), (540 + sway - 10, y - 50)], (230, 236, 245), 10)
        self.pop_text(img, 540, 1660, "10.898 m", 80, t, self.w("plastico", "plástico"), RED)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def camera(self, t, name, lt, u):
        if name == "everest":
            k = smooth(0, 3.0, lt)
            return 1.15 - 0.15 * k, 540, 900 + 160 * k
        if name == "esfera":
            return 1.0 + 0.12 * smooth(0, 4, lt), 540, 980
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        ev = [(0.1, "splash", 0.5), (0.4, "rumble", 0.4), (self.w("intro", "sobrarían"), "pop", 0.5), (st("lugar") + 0.8, "pop", 0.5),
              (st("luz"), "whoosh", 0.5), (self.w("luz", "oscuridad"), "boom", 0.4), (st("frio"), "wind", 0.3),
              (st("presion") + 0.3, "rumble", 0.5), (self.w("presion", "tonelada"), "crack", 0.5), (self.w("cuerpo", "aplastado"), "boom", 0.4),
              (self.w("cuerpo", "submarinos"), "click", 0.6), (st("vida") + 0.5, "drip", 0.5), (self.w("vida", "pez"), "shimmer", 0.4),
              (st("historia") + 0.3, "pop", 0.5), (self.w("historia", "cameron"), "pop", 0.5), (self.w("plastico", "plástico"), "boom", 0.5),
              (st("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        st = self.start
        return [(0, 0.7), (st("luz"), 0.6), (st("presion"), 0.9), (st("vida"), 0.55), (st("historia"), 0.7), (st("plastico"), 0.85),
                (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
