"""NIVEL OCULTO · ¿Qué pasaría si un agujero negro apareciera cerca de la Tierra?  (hipotético)

Hechos: un agujero negro de 1 masa solar tiene un radio de Schwarzschild de ~3 km (~6 km de diámetro); la gravedad
desvía la luz (lente gravitacional / anillo de Einstein); fuerzas de marea y «espaguetización» (término usado por la
NASA y en divulgación); dilatación gravitacional del tiempo; el agujero negro conocido más cercano es Gaia BH1, a
~1.560 años luz (Gaia/ESA, 2022). Lo demás (mareas gigantes, órbita alterada) es un escenario hipotético.
"""
from __future__ import annotations

import math
import random

from PIL import Image

from espacio import VIDEO as ESP
from motor import CYAN, RED, WHITE, City, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "espacio", 80


class VIDEO(Video):
    NAME = "agujero"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"agujero", "negro", "tierra", "notarías", "sol", "seis", "kilómetros", "ciudad", "cielo", "gravedad", "luz", "anillo",
                "marea", "olas", "gigantes", "órbita", "despedidos", "espagueti", "espaguetización", "horizonte", "tiempo", "despacio",
                "gaia", "bh1", "quinientos", "sesenta", "años", "luz", "sucesos", "comentarios"}
    astronaut = ESP.astronaut

    def setup(self):
        r = random.Random(66)
        self.city = City(seed=31)
        self.sky = [(r.uniform(0, W), r.uniform(0, 1500), r.uniform(1, 3)) for _ in range(260)]
        self.t_pop = self.w("intro", "agujero", 0.2)
        self.shakes = [(self.t_pop, 0.7), (self.start("mareas") + 2.0, 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "aparece"), (st("tamano") - 0.15, "tamano"), (st("luz") - 0.15, "lente"), (st("mareas") - 0.15, "marea"),
                (st("orbita") - 0.15, "orbita"), (st("espagueti") - 0.15, "espagueti"), (st("tiempo") - 0.15, "tiempo"),
                (st("dato") - 0.15, "gaia"), (st("cta") - 0.1, "fin")]

    def lensed_sky(self, d, t, cx, cy, R, k=1.0):
        """Estrellas desplazadas hacia fuera alrededor del agujero (lente gravitacional)."""
        for x, y, r in self.sky:
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy) + 1e-3
            push = k * R * R * 2.2 / dist
            nx, ny = cx + dx / dist * (dist + push), cy + dy / dist * (dist + push)
            tw = 0.6 + 0.4 * math.sin(t * 2 + x)
            c = int(230 * tw)
            stretch = 1 + k * 2.5 * R / dist
            self.E(d, nx, ny, r * stretch, (c, c, min(255, c + 20)), ry=r)

    def blackhole(self, img, d, cx, cy, R, t, disk=True, k=1.0):
        if R < 2:
            return
        self.glow(img, cx, cy, R * 2.6, (255, 170, 90), 110 * k, blur=R * 0.9)
        if disk:
            for i in range(6):
                rr = R * (2.4 - i * 0.18)
                col = mix((255, 120, 40), (255, 235, 180), i / 5)
                d.ellipse([(cx - rr) * S, (cy - rr * 0.26) * S, (cx + rr) * S, (cy + rr * 0.26) * S], outline=col, width=int(max(2, R * 0.08) * S))
        self.E(d, cx, cy, R, (0, 0, 0))
        d.arc([(cx - R * 1.12) * S, (cy - R * 1.12) * S, (cx + R * 1.12) * S, (cy + R * 1.12) * S], 0, 360, fill=(255, 220, 160), width=int(max(2, R * 0.05) * S))
        for i in range(4):
            a = t * 1.4 + i * 1.57
            self.E(d, cx + math.cos(a) * R * 2.1, cy + math.sin(a) * R * 0.55, max(2, R * 0.05), (255, 250, 220))

    # ───── escenas ─────
    def s_aparece(self, img, d, t, lt, u):
        self.bg(img, "night", (4, 6, 16), (16, 20, 40))
        k = back_out((t - self.t_pop) / 0.6)
        self.lensed_sky(d, t, 540, 620, 90 * max(0, k), clamp(k))
        self.blackhole(img, d, 540, 620, 90 * max(0, k), t)
        self.city.draw(d, t, night=1.0, lights=1.0)
        self.pop_text(img, 540, 1000, "¿AGUJERO NEGRO?", 80, t, self.t_pop + 0.3, YEL)

    def s_tamano(self, img, d, t, lt, u):
        self.bg(img, "night", (4, 6, 16), (16, 20, 40))
        self.stars(d, t, 0.7)
        self.city.draw(d, t, night=1.0, lights=1.0)
        k = ease_out(lt / 1.2)
        self.blackhole(img, d, 540, 820, 240 * k, t, disk=False)
        self.R(d, 300, 1120, 780, 1132, YEL)
        for x in (300, 780):
            self.R(d, x - 4, 1100, x + 4, 1152, YEL)
        self.pop_text(img, 540, 1200, "≈ 6 km", 90, t, self.w("tamano", "seis"), YEL)
        self.text(img, 540, 560, "MASA DEL SOL", 56, WHITE, alpha=smooth(0.3, 0.8, lt))

    def s_lente(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        k = smooth(0.2, 2.5, lt)
        self.lensed_sky(d, t, 540, 900, 160, 0.3 + 0.7 * k)
        self.blackhole(img, d, 540, 900, 160, t, disk=False)
        rr = 160 * 1.9
        d.ellipse([(540 - rr) * S, (900 - rr) * S, (540 + rr) * S, (900 + rr) * S], outline=(200, 220, 255, int(160 * k)), width=int(5 * S))
        self.pop_text(img, 540, 1500, "LENTE GRAVITACIONAL", 64, t, self.w("luz", "doblaría"), YEL)

    def s_marea(self, img, d, t, lt, u):
        self.bg(img, "night", (4, 6, 16), (16, 20, 40))
        self.stars(d, t, 0.7)
        self.blackhole(img, d, 540, 420, 60, t)
        self.city.draw(d, t, night=1.0, lights=1.0, dy=60)
        k = smooth(0.4, 4.0, lt)
        base = 1500
        bulge = 700 * k
        pts = [(-50, H + 50)]
        for x in range(-50, W + 60, 20):  # el mar se levanta hacia el agujero negro
            pts.append((x, base + 60 - bulge * math.exp(-((x - 540) / (380 + 200 * k)) ** 2) + 18 * math.sin(x / 60 + t * 3)))
        pts.append((W + 50, H + 50))
        self.P(d, pts, (35, 100, 165))
        self.Ln(d, pts[1:-1], (220, 240, 255), 10)
        self.text(img, 540, 1820, "ESCENARIO HIPOTÉTICO", 40, CYAN, "Bold")

    def s_orbita(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 0.8)
        cx, cy = 540, 960
        self.glow(img, cx, cy, 90, (255, 200, 100), 180)
        self.E(d, cx, cy, 55, (255, 205, 80))
        d.ellipse([(cx - 330) * S, (cy - 330) * S, (cx + 330) * S, (cy + 330) * S], outline=(90, 110, 160), width=int(3 * S))
        bx = -200 + lt * 230  # el agujero negro cruza el sistema solar
        self.blackhole(img, d, bx, 560, 40, t, disk=False)
        a = lt * 0.9
        for j, (dr, col) in enumerate(((-120, RED), (140, CYAN), (400, YEL))):
            k = smooth(1.2, 3.5, lt)
            pts = []
            for i in range(30):
                aa = a - i * 0.08
                r = 330 + dr * k * (1 - i / 30)
                pts.append((cx + math.cos(aa) * r, cy + math.sin(aa) * r))
            self.Ln(d, pts, col, 4)
            self.globe(img, pts[0][0], pts[0][1], 24, t, spin=40, glow_a=0) if j == 2 else self.E(d, pts[0][0], pts[0][1], 12, col)
        self.text(img, 540, 1500, "¿MÁS CERCA, MÁS LEJOS O FUERA?", 52, WHITE, alpha=smooth(1.2, 1.8, lt))

    def s_espagueti(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 0.8)
        self.blackhole(img, d, 540, 1480, 170, t)
        k = smooth(0.3, 4.0, lt)
        size = int(320 * S)
        tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
        self.astronaut(tmp, 540, 760, 1.1, 0)
        box = (int((540 - 180) * S), int((760 - 180) * S), int((540 + 180) * S), int((760 + 180) * S))
        a = tmp.crop(box)
        a = a.resize((max(2, int(a.width * (1 - 0.65 * k))), int(a.height * (1 + 2.2 * k))), Image.BICUBIC)
        img.alpha_composite(a, (int(540 * S - a.width / 2), int((760 + 260 * k) * S - a.height / 2)))
        self.pop_text(img, 540, 560, "ESPAGUETIZACIÓN", 80, t, self.w("espagueti", "espaguetización"), YEL)

    def s_tiempo(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 0.8)
        self.blackhole(img, d, 540, 860, 140, t)
        for (x, y, speed, lab) in ((230, 1450, 1.0, "LEJOS"), (850, 1450, 0.2, "CERCA")):
            self.E(d, x, y, 110, (240, 240, 250))
            self.E(d, x, y, 100, (30, 34, 50))
            a = t * 2.0 * speed
            self.Ln(d, [(x, y), (x + math.sin(a) * 80, y - math.cos(a) * 80)], YEL, 8)
            self.Ln(d, [(x, y), (x + math.sin(a / 12) * 55, y - math.cos(a / 12) * 55)], WHITE, 10)
            self.text(img, x, y + 160, lab, 40, WHITE, "Bold")

    def s_gaia(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0, drift=8)
        self.globe(img, 220, 1350, 90, t, spin=20)
        k = ease_out(lt / 2.0)
        self.Ln(d, [(320, 1300), (320 + 520 * k, 1300 - 520 * k)], (120, 140, 200), 4)
        self.blackhole(img, d, 860, 700, 50 * k, t, disk=False)
        self.text(img, 540, 1460, "DATO REAL", 46, CYAN)
        self.pop_text(img, 540, 1580, "GAIA BH1 · 1.560 AÑOS LUZ", 58, t, self.w("dato", "gaia"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name in ("marea", "orbita", "espagueti"):
            return self.pill(out, "HIPÓTESIS", CYAN, y=1835, size=42) if name != "marea" else out
        return out

    def sfx_events(self):
        st = self.start
        return [(0.1, "rumble", 0.5), (self.t_pop, "boom", 0.9), (self.w("tamano", "seis"), "pop", 0.5), (st("luz") + 0.3, "shimmer", 0.4),
                (st("mareas") + 0.5, "rumble", 0.6), (st("mareas") + 2.0, "splash", 0.7), (st("orbita") + 0.3, "whoosh", 0.5),
                (st("espagueti") + 0.3, "riser", 0.5), (st("tiempo") + 0.3, "tick", 0.5), (self.w("dato", "gaia"), "pop", 0.5),
                (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.6), (self.t_pop, 0.9), (st("luz"), 0.6), (st("mareas"), 0.9), (st("tiempo"), 0.6), (st("dato"), 0.45), (st("cta"), 0.4),
                (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
