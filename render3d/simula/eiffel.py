"""NIVEL OCULTO · ¿Cómo se construyó la Torre Eiffel?  (construcción paso a paso)

Datos: obra del 28-1-1887 al 31-3-1889 (unos 2 años y 2 meses) para la Exposición Universal de 1889; más de 5.300
planos y unas 18.000 piezas de hierro pudelado fabricadas en el taller de Eiffel (Levallois-Perret); 2,5 millones de
remaches colocados en caliente por equipos de 4 operarios; 4 cimientos de hormigón; patas sobre andamios de madera y
ajuste en el primer piso con gatos hidráulicos y cajas de arena; 300 m (312 con el asta); la más alta del mundo hasta
1930; permiso inicial de 20 años. Fuente principal: Société d'Exploitation de la Tour Eiffel (toureiffel.paris).
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, City, Person, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "epico", 92
IRON = (120, 78, 52)
WOOD = (190, 150, 100)
BASE_Y = 1640
TOWER_H = 1240


class VIDEO(Video):
    NAME = "eiffel"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"millones", "remaches", "torre", "eiffel", "exposición", "universal", "planos", "piezas", "hierro", "cimientos",
                "hormigón", "patas", "andamios", "madera", "primer", "piso", "gatos", "hidráulicos", "arena", "rojo", "operarios",
                "trescientos", "metros", "cuarenta", "temporal", "veinte", "comentarios"}

    def setup(self):
        r = random.Random(33)
        self.city = City(seed=21, palette=[(225, 215, 195), (210, 200, 180), (230, 222, 205), (200, 190, 172)])
        self.workers = [Person(r, 0, 120, shirt=c) for c in ((70, 90, 140), (150, 110, 80), (90, 100, 115), (120, 70, 60))]
        self.sparks = [(r.uniform(-1, 1), r.uniform(-1, 0.2), r.uniform(0, 1)) for _ in range(40)]
        self.rivets = [(r.uniform(150, 930), r.uniform(-1, 0), r.uniform(0.6, 1.4)) for _ in range(60)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("origen") - 0.15, "paris"), (st("planos") - 0.15, "planos"), (st("cimientos") - 0.15, "cimientos"),
                (st("patas") - 0.15, "patas"), (st("union") - 0.15, "union"), (st("remaches") - 0.15, "remaches"),
                (st("final") - 0.15, "final"), (st("dato") - 0.15, "dato"), (st("cta") - 0.1, "fin")]

    # ───── la torre ─────
    @staticmethod
    def wo(f):
        return 12 + 368 * (1 - f) ** 2.6

    def tower(self, d, cx, p, scaff=0.0, col=IRON, base=BASE_Y, hgt=TOWER_H, line=False):
        """Dibuja la torre hasta la fracción de altura p (0–1), con su celosía."""
        N = 70
        y_of = lambda f: base - f * hgt  # noqa: E731
        lw = 3 if line else 2
        for i in range(N):
            f0, f1 = i / N, (i + 1) / N
            if f0 >= p:
                break
            f1 = min(f1, p)
            y0, y1 = y_of(f0), y_of(f1)
            w0, w1 = self.wo(f0), self.wo(f1)
            if f0 < 0.19:  # cuatro patas (vistas de lado: dos)
                lg0 = 120 * (1 - 0.45 * f0 / 0.19)
                lg1 = 120 * (1 - 0.45 * f1 / 0.19)
                for sgn in (-1, 1):
                    pts = [(cx + sgn * w0, y0), (cx + sgn * (w0 - lg0), y0), (cx + sgn * (w1 - lg1), y1), (cx + sgn * w1, y1)]
                    if line:
                        self.Ln(d, pts + [pts[0]], col, lw)
                    else:
                        self.P(d, pts, col)
                        self.Ln(d, [pts[0], pts[2]], shade(col), 2)
                        self.Ln(d, [pts[1], pts[3]], shade(col), 2)
            else:
                pts = [(cx - w0, y0), (cx + w0, y0), (cx + w1, y1), (cx - w1, y1)]
                if line:
                    self.Ln(d, pts + [pts[0]], col, lw)
                else:
                    self.P(d, pts, col)
                    self.Ln(d, [pts[0], pts[2]], shade(col), 2)
                    self.Ln(d, [pts[1], pts[3]], shade(col), 2)
        # arco decorativo entre las patas
        if p > 0.17:
            r_ = self.wo(0.0) - 120
            d.arc([(cx - r_) * S, (y_of(0.17) - 30) * S, (cx + r_) * S, (y_of(0.0) + 260) * S], 180, 360, fill=col, width=int(10 * S))
        for fl, ext in ((0.19, 40), (0.385, 26)):  # plataformas
            if p >= fl:
                w_ = self.wo(fl) + ext
                self.R(d, cx - w_, y_of(fl) - 10, cx + w_, y_of(fl) + 16, shade(col, 0.85))
        if p >= 0.92:
            self.R(d, cx - 30, y_of(0.92) - 30, cx + 30, y_of(0.92), shade(col, 0.85))
        if p >= 0.99:
            self.Ln(d, [(cx, y_of(0.97)), (cx, y_of(1.0) - 30)], col, 5)
        if scaff > 0:  # andamios de madera bajo las patas inclinadas
            for sgn in (-1, 1):
                for k in range(3):
                    fx = 0.03 + k * 0.05
                    if fx < p:
                        x = cx + sgn * (self.wo(fx) - 80)
                        top = y_of(fx + 0.02)
                        self.Ln(d, [(x - 30, base), (x - 30, top)], WOOD, 6)
                        self.Ln(d, [(x + 30, base), (x + 30, top)], WOOD, 6)
                        for yy in range(int(top), base, 60):
                            self.Ln(d, [(x - 30, yy), (x + 30, yy + 50)], WOOD, 3)
        return y_of(p)

    def crane(self, d, x, y, t, sgn=1):
        self.Ln(d, [(x, y), (x, y - 70)], (60, 60, 70), 6)
        arm = 0.3 * math.sin(t * 1.2)
        ex, ey = x + sgn * 110 * math.cos(arm), y - 70 - 110 * math.sin(arm) * 0.3
        self.Ln(d, [(x, y - 70), (ex, ey)], (60, 60, 70), 5)
        hy = ey + 60 + 20 * math.sin(t * 2)
        self.Ln(d, [(ex, ey), (ex, hy)], (40, 40, 45), 2)
        self.R(d, ex - 20, hy, ex + 20, hy + 10, IRON)

    def paris_bg(self, img, d, t, sky=((150, 185, 220), (235, 220, 200))):
        self.bg(img, "paris", *sky)
        self.cloud(d, (180 + t * 10) % (W + 200) - 100, 560, 0.8)
        self.cloud(d, (760 + t * 7) % (W + 200) - 100, 480, 0.7)
        self.R(d, 0, BASE_Y, W, H + 40, (160, 150, 120))
        for x in range(-40, W + 60, 70):
            self.E(d, x, BASE_Y + 6, 46, (90, 120, 70), ry=26)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.paris_bg(img, d, t)
        p = ease_out(lt / 3.2)
        self.tower(d, 540, p)
        for x, y0, sp in self.rivets:  # lluvia de remaches
            y = (y0 * H + lt * 500 * sp) % (H + 100) - 50
            self.E(d, x, y, 9, (255, 120, 50))
        self.pop_text(img, 540, 620, "2.500.000", 120, t, 0.2, YEL)
        self.text(img, 540, 740, "REMACHES", 60, WHITE, alpha=smooth(0.4, 0.8, lt))

    def s_paris(self, img, d, t, lt, u):
        self.paris_bg(img, d, t)
        self.city.draw(d, t, haze=(210, 200, 185))
        self.pop_text(img, 540, 620, "EXPOSICIÓN UNIVERSAL", 64, t, self.w("origen", "exposición"), YEL)
        self.pop_text(img, 540, 740, "1889", 130, t, self.w("origen", "nueve"), WHITE)

    def s_planos(self, img, d, t, lt, u):
        self.bg(img, "blue", (20, 60, 120), (14, 44, 92))
        for x in range(0, W, 40):
            self.Ln(d, [(x, 0), (x, H)], (40, 90, 160), 1)
        for y in range(0, H, 40):
            self.Ln(d, [(0, y), (W, y)], (40, 90, 160), 1)
        p = ease_out(lt / 4.0)
        self.tower(d, 540, p, col=(230, 240, 255), base=1560, hgt=1000, line=True)
        n = int(5300 * smooth(self.w("planos", "cinco") - 0.4, self.w("planos", "planos") + 0.3, t))
        if n > 0:
            self.text(img, 280, 1680, f"{n:,} PLANOS".replace(",", "."), 52, YEL)
        m = int(18000 * smooth(self.w("planos", "dieciocho") - 0.3, self.w("planos", "hierro") + 0.3, t))
        if m > 0:
            self.text(img, 800, 1680, f"{m:,} PIEZAS".replace(",", "."), 52, CYAN)

    def s_cimientos(self, img, d, t, lt, u):
        self.bg(img, "dig", (150, 185, 220), (235, 220, 200))
        g = 1100
        self.R(d, 0, g, W, H + 40, (130, 100, 70))
        for i in range(4):  # fosos que se llenan de hormigón
            x = 150 + i * 260
            k = clamp((lt - 0.3 - i * 0.5) / 1.0)
            self.R(d, x - 90, g, x + 90, g + 360, (90, 68, 48))
            if k > 0:
                self.R(d, x - 90, g + 360 - 360 * k, x + 90, g + 360, (175, 175, 180))
                for j in range(int(6 * k)):
                    y = g + 360 - j * 60
                    self.Ln(d, [(x - 90, y), (x + 90, y)], (150, 150, 155), 3)
            self.person(img, self.workers[i], x + 110, g, "stand", "normal", "down", t * 3 + i, scale=1.0)
        self.pop_text(img, 540, 760, "4 BASES DE HORMIGÓN", 66, t, self.w("cimientos", "cuatro"), YEL)

    def s_patas(self, img, d, t, lt, u):
        self.paris_bg(img, d, t)
        p = 0.02 + 0.17 * ease_out(lt / max(1, self.end("patas") - self.start("patas")))
        top = self.tower(d, 540, p, scaff=1.0)
        for sgn in (-1, 1):
            self.crane(d, 540 + sgn * (self.wo(p) - 60), top, t, sgn)
        self.text(img, 540, 620, "1887 – 1888", 80, WHITE, alpha=smooth(0.2, 0.6, lt))

    def s_union(self, img, d, t, lt, u):
        self.paris_bg(img, d, t)
        k = smooth(1.0, 3.5, lt)
        self.tower(d, 540, 0.19 if k < 0.95 else 0.2, scaff=1.0)
        y1 = BASE_Y - 0.19 * TOWER_H
        if k < 1:  # la plataforma baja y encaja sobre las cuatro patas
            w_ = self.wo(0.19) + 40
            yy = y1 - 120 * (1 - k)
            self.R(d, 540 - w_, yy - 10, 540 + w_, yy + 16, YEL)
        for sgn in (-1, 1):  # gatos hidráulicos y cajas de arena
            x = 540 + sgn * (self.wo(0.0) - 60)
            self.R(d, x - 40, BASE_Y - 40, x + 40, BASE_Y, (220, 200, 150))
            self.R(d, x - 14, BASE_Y - 80 - 8 * math.sin(t * 4), x + 14, BASE_Y - 40, (90, 90, 100))
            self.P(d, [(x, BASE_Y - 130 - 8 * math.sin(t * 4)), (x - 18, BASE_Y - 100), (x + 18, BASE_Y - 100)], YEL)
        self.pop_text(img, 540, 620, "GATOS HIDRÁULICOS", 70, t, self.w("union", "gatos"), YEL)
        self.pop_text(img, 540, 730, "+ CAJAS DE ARENA", 56, t, self.w("union", "arena"), WHITE)

    def s_remaches(self, img, d, t, lt, u):
        self.bg(img, "dark", (40, 34, 30), (24, 20, 18))
        # dos chapas de hierro superpuestas
        self.R(d, 120, 760, 760, 960, IRON)
        self.R(d, 320, 900, 960, 1100, shade(IRON, 0.85))
        # forja y remache al rojo que vuela al agujero
        self.glow(img, 180, 1450, 140, (255, 120, 40), 200)
        self.R(d, 90, 1450, 270, 1600, (60, 50, 45), radius=12)
        ph = (lt * 0.7) % 1
        rx, ry = 180 + (540 - 180) * ph, 1430 - 600 * ph + 500 * ph * ph
        self.glow(img, rx, ry, 30, (255, 150, 60), 230)
        self.E(d, rx, ry, 14, (255, 110, 40))
        hit = (lt * 2.2) % 1 < 0.25  # martillazo
        hx, hy = 620, 830 - (0 if hit else 60)
        self.R(d, hx, hy - 30, hx + 120, hy + 10, (90, 90, 100))
        self.Ln(d, [(hx + 120, hy - 10), (hx + 260, hy - 70)], (150, 110, 70), 14)
        self.E(d, 540, 930, 22, (255, 90, 40) if not hit else (200, 70, 40))
        if hit:
            for sx, sy, s_ in self.sparks:
                self.E(d, 540 + sx * 80, 930 + sy * 80, 4, (255, 210, 120))
        for i, p_ in enumerate(self.workers):
            self.person(img, p_, 300 + i * 160, 1640, "stand", "normal", "down", t * 2 + i, scale=1.0)
        self.pop_text(img, 540, 620, "4 OPERARIOS", 72, t, self.w("remaches", "cuatro"), YEL)

    def s_final(self, img, d, t, lt, u):
        self.paris_bg(img, d, t, sky=((110, 160, 220), (250, 210, 160)))
        p = 0.2 + 0.8 * ease_out(lt / 3.0)
        top = self.tower(d, 540, p)
        if p < 0.995:
            self.crane(d, 540, top, t)
        h = 300 * p
        self.R(d, 960, top, 972, BASE_Y, YEL)
        self.text(img, 940, top - 40, f"{h:.0f} m", 52, YEL, anchor="rm")
        self.pop_text(img, 540, 1690, "MÁS ALTA DEL MUNDO · 40 AÑOS", 46, t, self.w("final", "cuarenta"), WHITE)

    def s_dato(self, img, d, t, lt, u):
        self.paris_bg(img, d, t, sky=((60, 80, 140), (240, 160, 120)))
        self.tower(d, 540, 1.0)
        k = back_out((t - self.w("dato", "temporal")) / 0.35)
        if k > 0:
            self.R(d, 540 - 300 * k, 620 - 80 * k, 540 + 300 * k, 620 + 80 * k, None, radius=20 * k, outline=RED, width=10)
            self.text(img, 540, 620, "TEMPORAL", 90 * k, RED)
        self.pop_text(img, 540, 1760, "PERMISO: 20 AÑOS", 60, t, self.w("dato", "veinte"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        yrs = {"paris": "1887", "cimientos": "1887", "patas": "1887–1888", "union": "1888", "remaches": "1888", "final": "1889"}
        if name in yrs:
            return self.pill(out, f"AÑO {yrs[name]}", YEL, y=1835, size=42)
        return out

    def sfx_events(self):
        st = self.start
        ev = [(0.1, "riser", 0.4)] + [(0.2 + i * 0.25, "tick", 0.5) for i in range(12)]
        ev += [(self.w("origen", "nueve"), "pop", 0.5), (st("planos") + 0.2, "whoosh", 0.4), (st("cimientos") + 0.3, "rumble", 0.4),
               (st("patas") + 0.3, "rumble", 0.3), (self.w("union", "gatos"), "click", 0.5), (st("union") + 3.5, "boom", 0.4)]
        ev += [(st("remaches") + i * 0.45, "click", 0.45) for i in range(10)]
        ev += [(st("final") + 0.2, "riser", 0.5), (st("final") + 3.0, "shimmer", 0.5), (self.w("dato", "temporal"), "click", 0.6),
               (st("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        st = self.start
        return [(0, 0.8), (st("planos"), 0.55), (st("patas"), 0.7), (st("final"), 0.95), (st("dato"), 0.5), (st("cta"), 0.4), (self.duration, 0.3)]


def shade(c, k=0.8):
    return tuple(int(v * k) for v in c[:3])


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
