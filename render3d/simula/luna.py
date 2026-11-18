"""NIVEL OCULTO · ¿Qué pasaría si la Luna desapareciera?"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, Person, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "espacio", 80
MOON = (232, 232, 238)


class VIDEO(Video):
    NAME = "luna"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"luna", "mareas", "sol", "débiles", "playas", "puertos", "costas", "oscuras", "estrellas", "animales", "corales",
                "reproducción", "eclipses", "nunca", "eje", "extremos", "millones", "tres", "ocho", "centímetros", "comentarios"}

    def setup(self):
        r = random.Random(31)
        self.t_gone = self.w("intro", "ya", 0.0)
        self.hills = [(x, r.uniform(80, 200)) for x in range(-100, 1200, 160)]
        self.houses = [(x, r.randint(70, 140)) for x in range(80, 1000, 95)]
        self.spawn = [(r.uniform(0, W), r.uniform(0, 1), r.uniform(4, 9), r.uniform(0, 6)) for _ in range(140)]
        self.crabs = [(r.uniform(0, W), r.uniform(0, 6)) for _ in range(5)]
        self.walker = Person(r, 540, 210, shirt=(70, 130, 210))
        self.shakes = [(self.t_gone, 0.5)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "noche"), (st("mareas") - 0.15, "marea"), (st("costas") - 0.15, "costa"), (st("noches") - 0.15, "campo"),
                (st("animales") - 0.15, "coral"), (st("eclipses") - 0.15, "eclipse"), (st("eje") - 0.15, "eje"),
                (st("hecho") - 0.15, "aleja"), (st("cta") - 0.1, "fin")]

    def moon(self, img, d, x, y, r, a=1.0):
        if a <= 0.01:
            return
        self.glow(img, x, y, r * 1.8, (200, 210, 255), 110 * a, blur=r * 0.7)
        self.E(d, x, y, r, mix((20, 26, 50), MOON, a))
        for cx, cy, cr in ((-0.3, -0.2, 0.18), (0.25, 0.1, 0.14), (-0.05, 0.35, 0.1), (0.35, -0.35, 0.08)):
            self.E(d, x + cx * r, y + cy * r, cr * r, mix((20, 26, 50), (205, 205, 214), a))

    def landscape(self, img, d, t, light):
        for x, h_ in self.hills:
            self.E(d, x, 1450, 260, mix((10, 14, 24), (40, 60, 70), light), ry=h_)
        self.R(d, 0, 1440, W, H + 40, mix((8, 12, 20), (35, 55, 60), light))
        for x, h_ in self.houses:
            c = mix((14, 16, 26), (60, 70, 90), light)
            self.R(d, x, 1440 - h_, x + 70, 1442, c)
            self.P(d, [(x - 8, 1440 - h_), (x + 35, 1440 - h_ - 40), (x + 78, 1440 - h_)], c)
            if (x // 95) % 2:
                self.R(d, x + 25, 1440 - h_ + 25, x + 45, 1440 - h_ + 50, (255, 210, 120))

    def s_noche(self, img, d, t, lt, u):
        a = 1 - smooth(self.t_gone, self.t_gone + 0.8, t)
        self.bgdyn(img, mix((4, 6, 14), (20, 34, 70), a), mix((10, 14, 28), (60, 80, 120), a))
        self.stars(d, t, 1.0 - 0.4 * a)
        self.moon(img, d, 540, 760 - 30 * lt, 200, a)
        if 0 < t - self.t_gone < 1.2:  # destello al desaparecer
            k = (t - self.t_gone) / 1.2
            d.ellipse([(540 - 200 - 300 * k) * S, (760 - 200 - 300 * k) * S, (540 + 200 + 300 * k) * S, (760 + 200 + 300 * k) * S],
                      outline=(220, 230, 255, int(220 * (1 - k))), width=int(6 * S))
        self.landscape(img, d, t, a)
        self.qmark(img, 540, 760, 200 * back_out((t - self.t_gone - 0.6) / 0.4))

    def tide_scene(self, img, d, t, lt, amp):
        self.bg(img, "day", (110, 170, 230), (205, 230, 245))
        self.cloud(d, (200 + t * 14) % (W + 200) - 100, 520, 0.9)
        self.cloud(d, (760 + t * 10) % (W + 200) - 100, 460, 0.8)
        # playa en pendiente y nivel del agua que sube y baja
        self.P(d, [(-40, 1150), (1120, 1650), (1120, H + 40), (-40, H + 40)], (235, 210, 160))
        lvl = 1350 + amp * math.sin(lt * 1.6)
        self.R(d, 0, lvl, W, H + 40, (50, 130, 200))
        self.P(d, [(-40, 1150), (1120, 1650), (1120, H + 40), (-40, H + 40)], (235, 210, 160, ))
        x_edge = (lvl - 1150) / 500 * 1160 - 40
        self.P(d, [(x_edge, lvl), (1120, lvl), (1120, H + 40), (x_edge + (H + 40 - lvl) * 2.3, H + 40)], (50, 130, 200))
        self.Ln(d, [(x_edge, lvl), (1120, lvl)], (230, 245, 255), 8)
        # regla de marea
        self.R(d, 960, 1150, 976, 1600, (60, 60, 70))
        for i in range(10):
            self.R(d, 945, 1150 + i * 45, 990, 1154 + i * 45, (60, 60, 70))
        self.R(d, 940, lvl - 4, 1000, lvl + 4, RED)

    def s_marea(self, img, d, t, lt, u):
        amp = 170 * (1 - 0.65 * smooth(self.w("mareas", "sol") - 0.5, self.w("mareas", "sol") + 1.5, t))
        self.tide_scene(img, d, t, lt, amp)
        k = smooth(self.w("mareas", "sol") - 0.5, self.w("mareas", "sol") + 0.5, t)
        self.text(img, 540, 760, "CON LUNA" if k < 0.5 else "SOLO EL SOL", 70, WHITE if k < 0.5 else YEL)

    def s_costa(self, img, d, t, lt, u):
        self.tide_scene(img, d, t, lt + 10, 50)
        for x, ph in self.crabs:  # cangrejos y charcas que ya no se renuevan
            xx = (x + 60 * math.sin(t * 1.2 + ph))
            y = 1150 + (xx + 40) / 1160 * 500 - 20
            self.E(d, xx, y, 22, (220, 90, 60), ry=13)
            for s_ in (-1, 1):
                self.Ln(d, [(xx + s_ * 18, y - 6), (xx + s_ * 32, y - 22)], (220, 90, 60), 4)
        self.pop_text(img, 540, 760, "ECOSISTEMAS COSTEROS", 60, t, self.w("costas", "vida"), CYAN)

    def s_campo(self, img, d, t, lt, u):
        a = 1 - smooth(0.8, 2.2, lt)  # de noche con luna llena a noche sin luna
        self.bgdyn(img, mix((3, 4, 10), (20, 34, 70), a), mix((8, 10, 20), (60, 80, 120), a))
        self.stars(d, t, 1.0)
        self.moon(img, d, 820, 600, 110, a)
        self.landscape(img, d, t, a)
        x = 200 + lt * 60
        self.person(img, self.walker, x, 1440, "stand", "scared" if a < 0.5 else "normal", "down", t * 4)
        if a < 0.6:  # linterna
            self.glow(img, x + 140, 1420, 80, (255, 240, 180), 160 * (1 - a))
        self.text(img, 540, 760, "LUNA LLENA" if a > 0.5 else "SIN LUNA", 64, WHITE if a > 0.5 else CYAN, alpha=0.9)

    def s_coral(self, img, d, t, lt, u):
        self.bg(img, "reef", (10, 40, 80), (4, 14, 30))
        tc = self.w("animales", "usan")
        moon_k = smooth(tc - 0.3, tc + 0.4, t)  # primero desorientados (sin Luna); luego, con su luz, puesta sincronizada
        self.glow(img, 540, 300, 260, (180, 210, 255), 90 * moon_k)
        for i in range(9):  # corales
            x = 60 + i * 120
            c = ((240, 110, 120), (255, 170, 80), (180, 120, 230))[i % 3]
            for j in range(5):
                a = -math.pi / 2 + (j - 2) * 0.35 + 0.05 * math.sin(t + i)
                self.Ln(d, [(x, 1700), (x + math.cos(a) * 140, 1700 + math.sin(a) * 140)], c, 22)
                self.E(d, x + math.cos(a) * 140, 1700 + math.sin(a) * 140, 16, c)
        self.R(d, 0, 1690, W, H + 40, (60, 50, 50))
        for x, ph, r, sp in self.spawn:
            if moon_k > 0.5:  # puesta sincronizada: todos suben a la vez
                y = 1650 - ((lt * 0.35 + ph * 0.15) % 1) * 1100
            else:  # sin la señal de la Luna: dispersos y desordenados
                y = 1650 - ((lt * 0.08 * sp + ph) % 1) * 600
            self.E(d, x + 10 * math.sin(t * 2 + sp), y, r * 0.6, (255, 200, 210))
        self.text(img, 540, 760, "CON LUNA: PUESTA SINCRONIZADA" if moon_k > 0.5 else "SIN LUNA: DESORIENTADOS", 50, WHITE if moon_k > 0.5 else YEL)

    def s_eclipse(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        cx, cy = 540, 960
        k = smooth(0.2, 1.4, lt)
        gone = smooth(1.8, 2.4, lt)
        self.glow(img, cx, cy, 300, (255, 220, 160), 120 + 80 * k * (1 - gone))
        self.E(d, cx, cy, 230, (255, 205, 80))
        mx = cx + 520 * (1 - k)
        if gone < 1:
            self.E(d, mx, cy, 232, mix((10, 12, 22), (8, 10, 28), gone))
        if gone > 0:
            self.Ln(d, [(cx - 260, cy - 260), (cx + 260, cy + 260)], RED, 22)
            self.Ln(d, [(cx + 260, cy - 260), (cx - 260, cy + 260)], RED, 22)
        self.pop_text(img, 540, 1450, "ADIÓS ECLIPSES TOTALES", 60, t, self.w("eclipses", "nunca"), YEL)

    def s_eje(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        wob = smooth(1.5, 3.0, lt)
        ang = math.radians(23.4 + wob * 20 * math.sin(lt * 1.3))
        cx, cy = 540, 1000
        self.globe(img, cx, cy, 320, t, spin=18)
        L = 470
        self.Ln(d, [(cx - math.sin(ang) * L, cy - math.cos(ang) * L), (cx + math.sin(ang) * L, cy + math.cos(ang) * L)], YEL, 8)
        self.text(img, 540, 1520, f"INCLINACIÓN · {math.degrees(ang):.0f}°", 62, YEL)
        self.text(img, 540, 1620, "SEGÚN ALGUNOS MODELOS", 40, CYAN, "Bold", alpha=wob)

    def s_aleja(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        self.globe(img, 300, 1000, 200, t, spin=18)
        mx = 720 + 120 * smooth(0, 6, lt)
        self.moon(img, d, mx, 1000, 70, 1.0)
        self.Ln(d, [(320 + 200, 1150), (mx, 1150)], WHITE, 4)
        self.P(d, [(mx, 1150), (mx - 24, 1136), (mx - 24, 1164)], WHITE)
        self.text(img, 540, 1440, "DATO REAL", 46, CYAN)
        self.pop_text(img, 540, 1560, "+3,8 cm CADA AÑO", 84, t, self.w("hecho", "tres"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name == "marea":
            k = smooth(self.w("mareas", "sol") - 0.5, self.w("mareas", "sol") + 1.5, t)
            return self.pill(out, "MAREAS · NORMALES" if k < 0.5 else "MAREAS · MUCHO MÁS DÉBILES", CYAN if k < 0.5 else RED, size=46)
        return out

    def sfx_events(self):
        st = self.start
        return [(0.2, "shimmer", 0.3), (self.t_gone, "boom", 0.6), (self.t_gone, "shimmer", 0.5), (st("mareas") + 0.5, "splash", 0.4),
                (st("costas") + 0.5, "splash", 0.3), (st("noches") + 1.0, "wind", 0.4), (st("animales") + 1.6, "drip", 0.5),
                (self.w("eclipses", "nunca"), "click", 0.6), (st("eje") + 1.5, "rumble", 0.5), (self.w("hecho", "tres"), "pop", 0.5),
                (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.5), (self.t_gone, 0.8), (st("noches"), 0.45), (st("eje"), 0.85), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
