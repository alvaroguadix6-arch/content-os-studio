"""NIVEL OCULTO · ¿Qué pasaría si un asteroide gigante cayera en el océano?"""
from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageFilter

from motor import CYAN, RED, WHITE, City, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "epico", 92


class VIDEO(Video):
    NAME = "asteroide"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"asteroide", "océano", "nadie", "sesenta", "mil", "kilómetros", "fuego", "cráter", "columna", "vapor", "kilómetro",
                "medio", "dinosaurios", "dos", "veintidós", "tsunamis", "avión", "ochocientos", "costas", "tierra", "adentro", "enfriar",
                "años", "nasa", "dart", "desviar", "preparados", "comentarios"}

    def setup(self):
        r = random.Random(51)
        self.rock = [(math.cos(a) * r.uniform(0.8, 1.1), math.sin(a) * r.uniform(0.8, 1.1)) for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]
        self.craters = [(r.uniform(-0.5, 0.5), r.uniform(-0.5, 0.5), r.uniform(0.1, 0.2)) for _ in range(5)]
        self.sparks = [(r.uniform(-1, 1), r.uniform(0, 1), r.uniform(3, 9)) for _ in range(60)]
        self.puffs = [(r.uniform(-1, 1), r.uniform(0, 1), r.uniform(0.6, 1.4)) for _ in range(26)]
        self.ash = [(r.uniform(0, W), r.uniform(0, H), r.uniform(2, 5)) for _ in range(150)]
        self.city = City(seed=17)
        # mapa del Atlántico (máscara real tierra/mar)
        land, _, _ = self.land_mask()
        lat0, lat1, lon0, lon1 = 70, -50, -100, 20
        sub = land[(90 - lat0) * 2:(90 - lat1) * 2, (lon0 + 180) * 2:(lon1 + 180) * 2]
        a = Image.fromarray((sub * 255).astype(np.uint8)).resize((W * S, W * S), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
        a = a.point(lambda v: 255 if v > 127 else 0)
        self.atl = Image.new("RGBA", a.size, (110, 170, 100, 255))
        self.atl.putalpha(a)
        self.map_geo = (lat0, lat1, lon0, lon1)
        self.t_hit = self.start("impacto") + 0.1
        self.shakes = [(self.t_hit, 1.0), (self.start("costas") + 0.8, 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "espacio"), (st("entrada") - 0.15, "bola"), (st("impacto") - 0.1, "crater"), (st("columna") - 0.15, "columna"),
                (st("ola") - 0.15, "ola"), (st("tsunami") - 0.15, "mapa"), (st("costas") - 0.15, "costa"), (st("clima") - 0.15, "clima"),
                (st("hecho") - 0.15, "dart"), (st("cta") - 0.1, "fin")]

    def asteroid(self, d, x, y, r, rot, col=(120, 105, 95)):
        c, s_ = math.cos(rot), math.sin(rot)
        self.P(d, [(x + (px * c - py * s_) * r, y + (px * s_ + py * c) * r) for px, py in self.rock], col)
        for cx, cy, cr in self.craters:
            self.E(d, x + (cx * c - cy * s_) * r, y + (cx * s_ + cy * c) * r, cr * r, shade(col, 0.75))

    def s_espacio(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0, drift=-30)
        self.globe(img, 760, 1350, 300, t, spin=10, rot0=60)
        k = ease_out(lt / 3.6)
        x, y, r = 120 + 360 * k, 420 + 380 * k, 80 + 200 * k
        for i in range(10):  # estela
            self.E(d, x - 40 * i, y - 40 * i, r * (1 - i / 12), (160, 150, 140) if i == 0 else (90 + i * 6, 80 + i * 6, 120 + i * 8))
        self.asteroid(d, x, y, r, t * 0.6)
        self.pop_text(img, 540, 1660, "RUMBO AL OCÉANO", 70, t, self.w("intro", "océano"), RED)

    def s_bola(self, img, d, t, lt, u):
        self.bgdyn(img, (40, 50, 90), (240, 150, 100))
        self.R(d, 0, 1300, W, H + 40, (30, 80, 140))
        for j in range(6):
            y = 1320 + j * 60
            self.Ln(d, [(x, y + 6 * math.sin(x / 50 + t * 2 + j)) for x in range(0, W + 40, 40)], (90, 150, 210), 3)
        k = lt / max(0.5, self.start("impacto") - self.start("entrada"))
        x, y = 1100 - 700 * k, 200 + 1050 * k
        for i in range(24):  # cola de fuego
            f = i / 24
            self.E(d, x + 300 * f, y - 450 * f, 70 * (1 - f) + 6, mix((255, 240, 180), (255, 80, 30), f))
        self.glow(img, x, y, 160, (255, 180, 90), 200)
        self.asteroid(d, x, y, 48, t * 2, (90, 60, 50))
        self.pop_text(img, 540, 650, "+60.000 km/h", 100, t, self.w("entrada", "sesenta"), YEL)

    def s_crater(self, img, d, t, lt, u):
        self.bg(img, "sect", (30, 40, 70), (20, 26, 46))
        k = ease_out(lt / 1.2)
        sea, bed = 900, 1350
        self.R(d, 0, sea, W, bed, (40, 110, 180))
        self.R(d, 0, bed, W, H + 40, (110, 90, 70))
        # el agua se aparta y se abre el cráter
        rw = 420 * k
        self.E(d, 540, bed, rw * 0.8, (50, 35, 30), ry=200 * k)  # cráter en el lecho marino
        ry = (bed - sea) * 0.95 * k + 1  # cavidad en forma de cuenco, llena de vapor
        d.chord([(540 - rw) * S, (sea - ry) * S, (540 + rw) * S, (sea + ry) * S], 0, 180, fill=(205, 198, 190))
        for sx_ in (-1, 1):  # el agua se levanta a los lados
            self.E(d, 540 + sx_ * rw, sea - 30 * k, 150 * k + 1, (40, 110, 180), ry=110 * k + 1)
            self.E(d, 540 + sx_ * rw, sea - 110 * k, 60 * k + 1, (230, 245, 255), ry=26 * k + 1)
        for sx, sy, sz in self.sparks:
            ph = clamp(lt / 1.6)
            self.E(d, 540 + sx * 600 * ph, sea - sy * 700 * ph + 500 * ph * ph, sz * (1 - ph) + 1, (255, 200, 120))
        if lt < 0.4:
            self.glow(img, 540, sea, 500, (255, 255, 230), 255 * (1 - lt / 0.4))
        self.text(img, 540, 760, "CRÁTER EN EL FONDO", 60, WHITE, alpha=smooth(0.4, 0.8, lt))

    def s_columna(self, img, d, t, lt, u):
        self.bgdyn(img, (60, 70, 100), (170, 150, 140))
        self.R(d, 0, 1350, W, H + 40, (40, 90, 140))
        k = ease_out(lt / 3.0)
        for px, py, s_ in self.puffs:
            y = 1350 - py * 1050 * k
            x = 540 + px * (80 + 220 * py * k)
            r = (70 + 80 * py) * s_ * (0.4 + 0.6 * k)
            self.E(d, x, y, r, mix((240, 240, 245), (130, 120, 115), py))
        self.pop_text(img, 540, 620, "KILÓMETROS DE ALTURA", 64, t, self.w("columna", "kilómetros"), YEL)

    def s_ola(self, img, d, t, lt, u):
        self.bgdyn(img, (70, 80, 110), (160, 170, 185))
        k = ease_out(lt / 2.5)
        base = 1600
        hw = 1500 * k  # 1,5 km
        scale = 0.62  # px por metro
        # rascacielos más alto del mundo (828 m) para comparar
        bx, bh = 820, 828 * scale
        self.P(d, [(bx - 40, base), (bx - 18, base - bh * 0.6), (bx - 6, base - bh), (bx + 6, base - bh), (bx + 18, base - bh * 0.6), (bx + 40, base)], (60, 66, 80))
        self.text(img, bx, base - bh - 40, "828 m", 36, WHITE)
        top = base - hw * scale
        pts = [(-40, H + 40), (-40, top + 40)]
        for x in range(-40, 640, 20):
            pts.append((x, top + 30 * math.sin(x / 80 + t * 3)))
        pts += [(640, top + 30), (700, top + 120), (660, top + 200), (720, base), (720, H + 40)]
        self.P(d, pts, (35, 105, 170))
        self.Ln(d, pts[2:-4], (230, 245, 255), 12)
        self.R(d, -10, base, W + 10, H + 40, (30, 80, 140))
        self.R(d, 40, top, 52, base, YEL)
        self.text(img, 70, top - 40, f"{1500 * k:,.0f} m".replace(",", "."), 52, YEL, anchor="lm")

    def s_mapa(self, img, d, t, lt, u):
        self.bg(img, "ocean", (40, 110, 180), (30, 90, 160))
        y0 = (H - W) / 2
        img.alpha_composite(self.atl, (0, int(y0 * S)))
        lat0, lat1, lon0, lon1 = self.map_geo
        ix = (-40 - lon0) / (lon1 - lon0) * W
        iy = y0 + (lat0 - 30) / (lat0 - lat1) * W
        for i in range(5):
            r = ((lt * 120 + i * 90) % 700)
            a = int(230 * (1 - r / 700))
            d.ellipse([(ix - r) * S, (iy - r) * S, (ix + r) * S, (iy + r) * S], outline=(230, 245, 255, a), width=int(6 * S))
        self.E(d, ix, iy, 14, RED)
        self.text(img, 540, y0 + W + 70, "OCÉANO ATLÁNTICO", 48, WHITE)

    def s_costa(self, img, d, t, lt, u):
        self.bg(img, "dayc", (110, 165, 225), (200, 225, 242))
        self.city.draw(d, t)
        g = self.city.ground
        k = smooth(0.6, 3.5, lt)
        lvl = g + 400 - 700 * k  # el agua entra tierra adentro
        front = -200 + 1500 * k
        self.P(d, [(-40, H + 40), (-40, lvl), (front - 120, lvl), (front, lvl + 120), (front + 80, H + 40)], (40, 110, 175))
        self.Ln(d, [(-40, lvl), (front - 120, lvl), (front, lvl + 120)], (230, 245, 255), 10)
        self.pop_text(img, 540, 650, "KILÓMETROS TIERRA ADENTRO", 58, t, self.w("costas", "tierra"), YEL)

    def s_clima(self, img, d, t, lt, u):
        k = smooth(0, 3, lt)
        self.bgdyn(img, mix((110, 165, 225), (60, 60, 66), k), mix((200, 225, 242), (100, 96, 92), k))
        self.glow(img, 760, 520, 120, (255, 230, 170), 160 * (1 - 0.8 * k))
        self.E(d, 760, 520, 70, mix((255, 230, 140), (190, 180, 160), k))
        self.city.draw(d, t, frost=0.6 * k)
        for x, y, r in self.ash:
            yy = (y + t * 60) % H
            self.E(d, x, yy, r, (170, 165, 160))
        tx, ty = 540, 640  # termómetro que baja
        self.R(d, tx - 26, ty - 160, tx + 26, ty + 120, WHITE, radius=26)
        self.E(d, tx, ty + 140, 52, WHITE)
        lvl = ty + 100 - 220 * (1 - 0.75 * k)
        self.R(d, tx - 14, lvl, tx + 14, ty + 130, mix((230, 70, 60), (80, 160, 230), k), radius=14)
        self.E(d, tx, ty + 140, 40, mix((230, 70, 60), (80, 160, 230), k))
        self.text(img, 540, 860, "CLIMA MÁS FRÍO DURANTE AÑOS", 46, WHITE, alpha=k)

    def s_dart(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        cx, cy = 540, 980
        self.asteroid(d, cx, cy, 160, t * 0.2, (130, 120, 110))  # Dídimo
        hit = self.w("hecho", "desviar") - 0.3
        a = t * (0.9 if t < hit else 1.05)
        mx, my = cx + math.cos(a) * 330, cy + math.sin(a) * 120
        self.asteroid(d, mx, my, 48, t, (150, 140, 128))  # Dimorfo
        k = clamp((t - self.start("hecho")) / max(0.5, hit - self.start("hecho")))
        if t < hit:  # la nave DART se acerca
            sx = 100 + (mx - 100) * k
            sy = 300 + (my - 300) * k
            self.R(d, sx - 14, sy - 14, sx + 14, sy + 14, (220, 220, 230))
            self.R(d, sx - 60, sy - 5, sx - 16, sy + 5, (60, 90, 160))
            self.R(d, sx + 16, sy - 5, sx + 60, sy + 5, (60, 90, 160))
        elif t - hit < 0.6:
            self.glow(img, mx, my, 120, (255, 230, 170), 255 * (1 - (t - hit) / 0.6))
        self.text(img, 540, 1440, "DATO REAL", 46, CYAN)
        self.pop_text(img, 540, 1560, "MISIÓN DART · 2022", 80, t, self.w("hecho", "dart"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name == "ola":
            return self.pill(out, "CHICXULUB · ESTUDIO 2022", CYAN, size=46)
        if name == "mapa":
            return self.pill(out, "TSUNAMI ≈ 800 km/h", RED)
        return out

    def sfx_events(self):
        st = self.start
        return [(0.1, "rumble", 0.5), (st("entrada"), "riser", 0.6), (st("entrada") + 0.2, "wind", 0.5), (self.t_hit, "boom", 1.0),
                (self.t_hit + 0.05, "splash", 0.8), (st("columna") + 0.2, "rumble", 0.6), (st("ola") + 0.3, "splash", 0.6),
                (st("tsunami") + 0.3, "whoosh", 0.5), (st("costas") + 0.6, "splash", 0.8), (st("clima") + 0.3, "wind", 0.5),
                (self.w("hecho", "desviar") - 0.3, "boom", 0.5), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.7), (self.t_hit, 1.0), (st("tsunami"), 0.85), (st("clima"), 0.5), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
