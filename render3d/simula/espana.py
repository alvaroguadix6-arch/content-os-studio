"""¿Qué pasaría si España se convirtiera en una isla?  (mapa con las costas reales)"""
from __future__ import annotations

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from motor import CYAN, RED, WHITE, HERE, Person, Video, W, H, S, YEL, back_out, clamp, draw_car, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "alegre", 92
LON0, LON1, LAT0, LAT1 = -10.5, 5.5, 53.0, 31.9


def geo(lo, la):
    return ((lo - LON0) / (LON1 - LON0) * W, (LAT0 - la) / (LAT0 - LAT1) * H)


class VIDEO(Video):
    NAME = "espana"
    KEYWORDS = {"españa", "isla", "pirineos", "parten", "seiscientos", "francia", "portugal", "península", "europa", "quinientos", "ochenta",
                "triple", "marítimo", "suaves", "humedad", "camiones", "trenes", "barco", "túnel", "cincuenta", "kilómetros", "bolsillo",
                "exportaciones", "playa", "pirineo", "comentarios"}

    def setup(self):
        z = np.load(os.path.join(HERE, "mapa_iberia.npz"))
        h2, w2 = z["shape"]
        ib = np.unpackbits(z["iberia"])[: h2 * w2].reshape(h2, w2)
        rest = np.unpackbits(z["resto"])[: h2 * w2].reshape(h2, w2)
        self.border = [geo(lo, la) for lo, la in z["border"]]
        self.lay_ib = self.layer(ib, (250, 200, 70), (205, 145, 40))
        self.lay_rest = self.layer(rest, (165, 200, 140), (120, 160, 105))
        r = random.Random(2)
        self.trucks = [r.uniform(0, 1) for _ in range(6)]
        self.waves = [(r.uniform(0, W), r.uniform(0, H), r.uniform(20, 50)) for _ in range(140)]
        self.p_sun = Person(r, 600, 210, shirt=(235, 90, 70))
        self.t_crack = self.w("grieta", "parten", -0.2)
        self.t_sep = self.start("portugal") + 0.8
        self.shakes = [(self.t_crack + 0.3, 0.6)]

    @staticmethod
    def layer(mask, col, edge):
        a = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
        a = a.point(lambda v: 255 if v > 127 else 0).filter(ImageFilter.GaussianBlur(1.0))
        lay = Image.new("RGBA", a.size, edge + (0,))
        inner = a.filter(ImageFilter.MinFilter(7))
        base = Image.new("RGBA", a.size, col + (255,))
        lay.putalpha(a)
        lay.alpha_composite(Image.composite(base, Image.new("RGBA", a.size, (0, 0, 0, 0)), inner))
        return lay

    def build_scenes(self):
        st = self.start
        return [(0.0, "mapa"), (st("clima") - 0.15, "clima"), (st("transporte") - 0.15, "frontera"), (st("economia") - 0.15, "economia"),
                (st("playa") - 0.15, "playa"), (st("cta") - 0.1, "fin")]

    def sep(self, t):
        return smooth(self.t_crack, self.t_sep, t)

    def draw_map(self, img, d, t, sep_k=None):
        self.bg(img, "ocean", (60, 140, 205), (40, 110, 180))
        for x, y, ln in self.waves:  # olas
            xx = (x + t * 12) % (W + 60) - 30
            self.Ln(d, [(xx, y), (xx + ln * 0.5, y - 5), (xx + ln, y)], (110, 180, 230), 3)
        k = self.sep(t) if sep_k is None else sep_k
        dx, dy = -26 * k, 30 * k
        img.alpha_composite(self.lay_rest)
        if k > 0:  # espuma a lo largo del nuevo estrecho
            pts = [(x + dx * 0.5, y + dy * 0.5) for x, y in self.border]
            self.Ln(d, pts, (190, 225, 250), 6 + 22 * k)
            self.Ln(d, pts, (60, 140, 205), 2 + 14 * k)
        img.alpha_composite(self.lay_ib, (int(dx * S), int(dy * S)))
        return dx, dy

    def label(self, img, lo, la, txt, size, col=(40, 50, 60), alpha=1.0, off=(0, 0)):
        x, y = geo(lo, la)
        self.text(img, x + off[0], y + off[1], txt, size, col, alpha=alpha, shadow=False)

    def s_mapa(self, img, d, t, lt, u):
        dx, dy = self.draw_map(img, d, t)
        self.label(img, 2.4, 47.0, "FRANCIA", 46, (70, 100, 70))
        self.label(img, -3.7, 40.0, "ESPAÑA", 54, (120, 70, 20), off=(dx, dy))
        kp = smooth(self.start("portugal"), self.start("portugal") + 0.6, t)
        if kp > 0:
            self.label(img, -8.1, 39.6, "PORTUGAL", 30, (120, 70, 20), alpha=kp, off=(dx, dy))
        if t < self.t_crack + 0.2 and t > self.start("grieta"):  # grieta que avanza
            k = smooth(self.start("grieta"), self.t_crack + 0.2, t)
            n = max(2, int(len(self.border) * k))
            self.Ln(d, self.border[:n], (90, 50, 30), 8)

    def s_clima(self, img, d, t, lt, u):
        dx, dy = self.draw_map(img, d, t, 1.0)
        self.label(img, -3.7, 40.0, "ESPAÑA", 54, (120, 70, 20), off=(dx, dy))
        # viento marino que entra por el nuevo estrecho y nubes de lluvia en el nordeste
        for i in range(7):
            ph = (lt * 0.5 + i / 7) % 1
            x0, y0 = geo(4.5 - 3.5 * ph, 43.3 - 1.5 * ph + (i - 3) * 0.25)
            self.Ln(d, [(x0, y0), (x0 - 40, y0 + 20)], (240, 250, 255), 6)
            self.P(d, [(x0 - 40, y0 + 20), (x0 - 22, y0 + 4), (x0 - 28, y0 + 28)], (240, 250, 255))
        for i, (lo, la) in enumerate(((0.8, 42.6), (2.0, 42.2), (-0.8, 42.9))):
            x, y = geo(lo, la)
            x += 20 * math.sin(t + i) + dx
            self.cloud(d, x, y - 40 + dy, 0.6, (235, 240, 248))
            for j in range(5):
                yy = y + ((t * 1.2 + j / 5) % 1) * 90 + dy
                self.Ln(d, [(x - 40 + j * 20, yy), (x - 46 + j * 20, yy + 18)], (120, 170, 230), 3)

    def s_frontera(self, img, d, t, lt, u):
        dx, dy = self.draw_map(img, d, t, 1.0)
        bx, by = geo(2.87, 42.40)  # La Jonquera
        bx, by = bx + dx, by + dy
        sx, sy = geo(2.17, 41.38)  # Barcelona
        sx, sy = sx + dx, sy + dy
        self.Ln(d, [(sx, sy), (bx - 6, by + 4)], (90, 90, 100), 9)
        self.E(d, sx, sy, 9, (200, 60, 50))
        self.text(img, sx + 70, sy, "Barcelona", 22, (60, 60, 70), "Bold", shadow=False)
        for i, ph in enumerate(self.trucks):  # camiones que llegan al agua y se paran
            k = min(1.0, (lt * 0.25 + ph) % 1.6)
            x, y = sx + (bx - sx) * k, sy + (by - sy) * k
            self.R(d, x - 9, y - 6, x + 9, y + 6, (240, 240, 245), radius=2)
        # ferri cruzando y túnel bajo el mar
        fk = (lt * 0.18) % 1
        fx, fy = bx + 10 + 40 * fk, by - 50 * fk
        self.P(d, [(fx - 16, fy), (fx + 16, fy), (fx + 11, fy + 8), (fx - 11, fy + 8)], WHITE)
        tk = smooth(self.w("transporte", "túnel"), self.w("transporte", "túnel") + 1.0, t)
        if tk > 0:
            tx0, ty0 = geo(2.6, 42.25)
            tx1, ty1 = geo(2.8, 42.75)
            n = 14
            for j in range(int(n * tk)):
                a = j / n
                b = (j + 0.5) / n
                self.Ln(d, [(tx0 + (tx1 - tx0) * a + dx * 0.5, ty0 + (ty1 - ty0) * a + dy * 0.5),
                            (tx0 + (tx1 - tx0) * b + dx * 0.5, ty0 + (ty1 - ty0) * b + dy * 0.5)], (40, 40, 50), 4)

    def s_economia(self, img, d, t, lt, u):
        dx, dy = self.draw_map(img, d, t, 1.0)
        self.label(img, 2.4, 47.0, "FRANCIA", 52, (70, 100, 70))
        self.label(img, -3.7, 40.0, "ESPAÑA", 54, (120, 70, 20), off=(dx, dy))
        sx, sy = geo(-2.0, 41.2)
        fx, fy = geo(1.8, 46.3)
        for i in range(5):  # flujo de mercancías
            k = (lt * 0.5 + i / 5) % 1
            x, y = sx + (fx - sx) * k + dx * (1 - k), sy + (fy - sy) * k + dy * (1 - k)
            self.R(d, x - 22, y - 14, x + 22, y + 14, (255, 255, 255), radius=4)
            self.R(d, x - 22, y - 14, x - 6, y + 14, (230, 80, 60), radius=4)
        self.Ln(d, [(sx + dx, sy + dy), (fx, fy)], (230, 80, 60), 5)

    def s_playa(self, img, d, t, lt, u):
        self.bg(img, "beachsky", (110, 175, 235), (215, 236, 250))
        for x, y in ((200, 520), (750, 450)):
            self.cloud(d, (x + t * 10) % (W + 200) - 100, y, 0.9)
        # Pirineo nevado al fondo
        for i, (x, h_, w_) in enumerate(((150, 640, 380), (520, 760, 460), (900, 600, 360))):
            self.P(d, [(x - w_, 1250), (x, 1250 - h_), (x + w_, 1250)], mix((120, 130, 150), (140, 150, 165), i / 2))
            self.P(d, [(x - w_ * 0.28, 1250 - h_ * 0.72), (x, 1250 - h_), (x + w_ * 0.28, 1250 - h_ * 0.72)], WHITE)
        self.R(d, 0, 1240, W, 1420, (50, 140, 200))
        for j in range(5):
            y = 1260 + j * 34
            self.Ln(d, [(x, y + 6 * math.sin(x / 50 + t * 3 + j)) for x in range(0, W + 40, 40)], (150, 205, 240), 4)
        self.R(d, 0, 1410, W, H + 40, (240, 215, 160))
        self.E(d, 540, 1420, 600, (250, 230, 190), ry=26)
        # sombrilla y bañista
        self.Ln(d, [(780, 1700), (760, 1420)], (90, 70, 50), 8)
        self.P(d, [(600, 1450), (760, 1340), (920, 1450)], (230, 80, 70))
        self.P(d, [(680, 1450), (760, 1340), (840, 1450)], (250, 250, 250))
        self.R(d, 430, 1680, 780, 1745, (60, 150, 200), radius=10)
        self.person(img, self.p_sun, 480, 1700, "lie", "smile", "down", 0, -90 + 3 * math.sin(t * 2), scale=1.3)
        self.pop_text(img, 540, 1820, "PLAYA DEL PIRINEO", 50, t, self.w("playa", "playa"), YEL)

    def overlay(self, img, d, t, name, lt, u):
        if name == "mapa":
            if self.start("grieta") <= t < self.start("portugal"):
                self.pop_text(img, 540, 1640, "+600 km DE FRONTERA", 58, t, self.w("grieta", "seiscientos"), YEL)
            elif t >= self.start("grande"):
                self.pop_text(img, 540, 1640, "583.000 km²", 74, t, self.w("grande", "quinientos"), YEL)
                if t > self.w("grande", "triple"):
                    self.text(img, 540, 1730, "≈ 3 × GRAN BRETAÑA", 44, WHITE, alpha=clamp((t - self.w("grande", "triple")) / 0.4))
            else:
                return False
            return True
        if name == "clima":
            self.pop_text(img, 540, 1640, "INVIERNOS MÁS SUAVES", 56, t, self.w("clima", "inviernos"), CYAN)
            return True
        if name == "frontera":
            self.pop_text(img, 540, 1640, "TÚNEL ≈ 50 km", 60, t, self.w("transporte", "túnel"), YEL)
            return True
        if name == "economia":
            self.pop_text(img, 540, 1600, "FRANCIA", 70, t, self.w("economia", "francia"), YEL)
            if t > self.w("economia", "principal"):
                self.text(img, 540, 1690, "PRINCIPAL DESTINO DE LAS EXPORTACIONES", 34, WHITE, "Bold", alpha=clamp((t - self.w("economia", "principal")) / 0.4))
            return True
        return False

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def camera(self, t, name, lt, u):
        def at(lo, la):
            return geo(lo, la)

        if name == "mapa":
            # intro: península; grieta: zoom a los Pirineos; portugal/grande: plano general
            c_ib = (480, 1180)
            c_py = at(0.6, 42.7)
            kz = smooth(self.start("grieta") - 0.4, self.start("grieta") + 0.8, t) * (1 - smooth(self.start("portugal") - 0.4, self.start("portugal") + 0.8, t))
            z = 1.3 - 0.12 * smooth(0, 3.5, t) + 1.0 * kz
            cx = c_ib[0] + (c_py[0] - c_ib[0]) * kz + 30 * kz * math.sin(t * 0.5)
            cy = c_ib[1] + (c_py[1] - c_ib[1]) * kz
            return z, cx, cy
        if name == "clima":
            x, y = at(1.0, 42.4)
            return 1.8 + 0.1 * u, x, y + 60
        if name == "frontera":
            x, y = at(2.6, 42.1)
            return 2.4 + 0.15 * u, x, y
        if name == "economia":
            return 1.05 + 0.05 * u, 540, 1000
        return super().camera(t, name, lt, u)

    def hud(self, out, t):
        return out

    def sfx_events(self):
        st = self.start
        return [(0.3, "splash", 0.4), (self.t_crack, "crack", 0.9), (self.t_crack + 0.1, "rumble", 0.7), (self.t_crack + 0.6, "splash", 0.6),
                (self.w("grande", "quinientos"), "pop", 0.6), (st("clima") + 0.5, "wind", 0.5), (st("transporte") + 1.0, "horn", 0.4),
                (self.w("transporte", "túnel"), "pop", 0.5), (self.w("economia", "francia"), "pop", 0.6), (st("playa") + 0.3, "splash", 0.3),
                (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.5), (self.t_crack, 0.85), (st("clima"), 0.6), (st("playa"), 0.8), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
