"""NIVEL OCULTO · Plantilla de «casos reales» en dibujos animados (misma estética que dioni2.py).

Cada caso hereda de Caso y define: escenas (s_<nombre>), hud_items(t) (marcador de «juego»), fin_text y el reparto.
Incluye fondos ilustrados y objetos (cuadros, maletín, paracaídas, diamantes, bocadillo, códice…), sellos, tarjetas de
fase, subtítulos tipo meme y tarjeta final con pregunta.
"""
from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

from motor import CYAN, RED, WHITE, W, H, S, YEL, Video, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401
from toon import INK, Look, Toon  # noqa: F401
from zona_segura import BOTTOM, RIGHT_ICONS, SIDE, TOP, clamp_text

FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts", "Anton-Regular.ttf")
_fc = {}
GOLD = (255, 205, 40)
CARD = (215, 40, 50)
GREEN = (140, 230, 160)


def anton(size):
    k = int(size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT, max(8, k))
    return _fc[k]


class Caso(Video):
    BRAND = None
    FIN = ("¿Y TÚ", "QUÉ CREES?")
    CARDS: dict = {}  # clave de frase → (título, icono)

    def setup(self):
        r = random.Random(3)
        self.bills = [(r.uniform(0, W), r.uniform(0, H), r.uniform(0.8, 1.3), r.uniform(0, 6.3)) for _ in range(36)]
        self.cast()

    def cast(self):
        pass

    # ───── dibujo con contorno ─────
    def box(self, d, x0, y0, x1, y1, col, ow=6, r=0):
        d.rounded_rectangle([(x0 - ow) * S, (y0 - ow) * S, (x1 + ow) * S, (y1 + ow) * S], radius=int((r + ow) * S), fill=INK)
        d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=int(r * S), fill=col)

    def poly(self, d, pts, col, ow=6):
        d.polygon([(x * S, y * S) for x, y in pts], fill=col)
        if ow:
            d.line([(x * S, y * S) for x, y in pts + [pts[0]]], fill=INK, width=int(ow * S), joint="curve")

    def oell(self, d, x, y, rx, ry, col, ow=6):
        d.ellipse([(x - rx - ow) * S, (y - ry - ow) * S, (x + rx + ow) * S, (y + ry + ow) * S], fill=INK)
        d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S], fill=col)

    def ot(self, img, x, y, txt, size, col=WHITE, stroke=8, anchor="mm", rot=0.0, alpha=255, safe=True):
        if safe and anchor == "mm" and txt:
            x, y = clamp_text(x, y, anton(size).getlength(txt) + 2 * stroke, size * 1.2)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.text((x * S, y * S), txt, font=anton(size * S), fill=tuple(col[:3]) + (alpha,), anchor=anchor, stroke_width=int(stroke * S),
                stroke_fill=INK + (alpha,))
        if rot:
            lay = lay.rotate(rot, center=(x * S, y * S), resample=Image.BICUBIC)
        img.alpha_composite(lay)

    def pop(self, img, x, y, txt, size, t, t0, col=WHITE, rot=0.0, stroke=8):
        k = back_out((t - t0) / 0.3)
        if k > 0.02:
            self.ot(img, x, y, txt, size * k, col, stroke, rot=rot)

    def stamp(self, img, x, y, txt, size, t, t0, col=CARD, rot=-8):
        k = back_out((t - t0) / 0.28)
        if k <= 0.02:
            return
        sc = 2 - k if k < 1 else 1
        x, y = clamp_text(x, y, anton(size).getlength(txt) + 90, size * 1.7)
        f = anton(size * S * sc)
        tw = f.getlength(txt)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([x * S - tw / 2 - 30 * S, y * S - size * S * 0.72 * sc, x * S + tw / 2 + 30 * S, y * S + size * S * 0.72 * sc],
                             radius=int(14 * S), fill=(255, 250, 240, 235), outline=col + (255,), width=int(10 * S))
        dl.text((x * S, y * S), txt, font=f, fill=col + (255,), anchor="mm")
        img.alpha_composite(lay.rotate(-rot, center=(x * S, y * S), resample=Image.BICUBIC))

    def label(self, img, d, x, y, txt, size, k=1.0, bg=(255, 250, 235), fg=(40, 30, 40)):
        if k <= 0.02:
            return
        f = anton(size * k)
        tw = f.getlength(txt)
        x, y = clamp_text(x, y, anton(size).getlength(txt) + 70, size * 1.6)
        self.box(d, x - tw / 2 - 26, y - size * 0.75 * k, x + tw / 2 + 26, y + size * 0.75 * k, bg, 6, 16)
        self.ot(img, x, y, txt, size * k, fg, 0, safe=False)

    def money_rain(self, d, t, k=1.0, speed=1.0):
        for x, y0, s, ph in self.bills:
            if (x * 13) % 100 / 100 > k:
                continue
            y = (y0 + t * 260 * s * speed) % (H + 200) - 100
            xx = x + 40 * math.sin(t * 2 + ph)
            a = math.sin(t * 3 + ph) * 0.7
            w, h = 110 * s, 54 * s
            c, sn = math.cos(a), math.sin(a)
            pts = [(xx + (px * c - py * sn), y + (px * sn + py * c)) for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
            self.poly(d, pts, (120, 190, 140), 4)
            self.E(d, xx, y, 12 * s, (80, 140, 100))

    # ───── objetos ─────
    def painting(self, img, d, x, y, w, h, kind="generic", empty=False, frame=(200, 150, 60)):
        self.box(d, x - w / 2 - 22, y - h / 2 - 22, x + w / 2 + 22, y + h / 2 + 22, frame, 6, 6)
        if empty:
            self.box(d, x - w / 2, y - h / 2, x + w / 2, y + h / 2, (90, 70, 60), 4)
            return
        if kind == "mona":  # retrato estilizado (obra de dominio público)
            self.box(d, x - w / 2, y - h / 2, x + w / 2, y + h / 2, (90, 110, 80), 4)
            self.poly(d, [(x - w / 2, y + h * 0.05), (x - w * 0.2, y - h * 0.1), (x + w * 0.25, y - h * 0.05), (x + w / 2, y + h * 0.1), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], (120, 120, 80), 0)
            self.poly(d, [(x - w * 0.36, y + h / 2), (x - w * 0.3, y + h * 0.05), (x + w * 0.3, y + h * 0.05), (x + w * 0.36, y + h / 2)], (60, 40, 30), 3)
            self.oell(d, x, y - h * 0.12, w * 0.17, h * 0.15, (60, 40, 30), 3)
            self.oell(d, x, y - h * 0.1, w * 0.12, h * 0.13, (230, 190, 130), 3)
            d.arc([(x - w * 0.04) * S, (y - h * 0.06) * S, (x + w * 0.04) * S, (y - h * 0.02) * S], 20, 160, fill=INK, width=int(2 * S))
            self.oell(d, x, y + h * 0.3, w * 0.12, h * 0.05, (230, 190, 130), 3)
        elif kind == "storm":  # marina con tormenta
            self.box(d, x - w / 2, y - h / 2, x + w / 2, y + h / 2, (60, 60, 70), 4)
            self.poly(d, [(x - w / 2, y + h * 0.2), (x + w / 2, y), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], (40, 70, 80), 0)
            self.poly(d, [(x - w * 0.2, y + h * 0.15), (x + w * 0.2, y + h * 0.1), (x + w * 0.1, y + h * 0.25), (x - w * 0.15, y + h * 0.28)], (110, 80, 50), 3)
            self.poly(d, [(x - w * 0.02, y + h * 0.12), (x + w * 0.02, y + h * 0.12), (x + w * 0.1, y - h * 0.3)], (220, 210, 180), 3)
        elif kind == "concert":
            self.box(d, x - w / 2, y - h / 2, x + w / 2, y + h / 2, (90, 80, 60), 4)
            for i, c in enumerate([(200, 60, 60), (230, 220, 190), (60, 80, 120)]):
                self.oell(d, x - w * 0.25 + i * w * 0.25, y, w * 0.08, h * 0.25, c, 3)
        else:
            self.box(d, x - w / 2, y - h / 2, x + w / 2, y + h / 2, (120, 160, 190), 4)
            self.oell(d, x, y, w * 0.25, h * 0.25, (230, 200, 120), 3)

    def briefcase(self, d, x, y, s=1.0, open_k=0.0):
        self.box(d, x - 90 * s, y - 60 * s, x + 90 * s, y + 60 * s, (90, 60, 40), 6, 10)
        self.box(d, x - 30 * s, y - 80 * s, x + 30 * s, y - 60 * s, (60, 40, 30), 5, 6)
        if open_k > 0:
            for i in range(5):
                self.box(d, x - 70 * s + i * 30 * s, y - 60 * s - 30 * open_k * s, x - 50 * s + i * 30 * s, y - 20 * s, (120, 190, 140), 3, 3)

    def parachute(self, d, x, y, s=1.0, col=(230, 90, 70)):
        self.poly(d, [(x - 170 * s, y), (x - 120 * s, y - 110 * s), (x, y - 150 * s), (x + 120 * s, y - 110 * s), (x + 170 * s, y)], col)
        for i in range(-2, 3):
            self.Ln(d, [(x + i * 70 * s, y), (x, y + 200 * s)], (240, 240, 240), 3)

    def diamond(self, d, x, y, s=1.0, t=0.0):
        self.poly(d, [(x - 30 * s, y - 12 * s), (x - 15 * s, y - 28 * s), (x + 15 * s, y - 28 * s), (x + 30 * s, y - 12 * s), (x, y + 30 * s)], (150, 230, 255), 4)
        self.poly(d, [(x - 30 * s, y - 12 * s), (x + 30 * s, y - 12 * s), (x, y + 30 * s)], (110, 200, 240), 3)
        if (t * 3 + x) % 2 < 0.4:
            self.star_shape(d, x + 18 * s, y - 24 * s, 14 * s, (255, 255, 255))

    def sandwich(self, d, x, y, s=1.0, bite=True):
        self.oell(d, x, y - 14 * s, 110 * s, 34 * s, (230, 180, 110), 6)
        self.box(d, x - 100 * s, y - 10 * s, x + 100 * s, y + 6 * s, (200, 70, 80), 4, 6)
        self.box(d, x - 104 * s, y + 6 * s, x + 104 * s, y + 18 * s, (120, 190, 90), 4, 6)
        self.oell(d, x, y + 32 * s, 110 * s, 24 * s, (230, 180, 110), 6)
        if bite:
            self.E(d, x + 100 * s, y, 44 * s, (0, 0, 0, 0)) if False else None

    def codex(self, img, d, x, y, s=1.0):
        self.box(d, x - 120 * s, y - 160 * s, x + 120 * s, y + 160 * s, (130, 40, 40), 7, 12)
        self.box(d, x - 95 * s, y - 135 * s, x + 95 * s, y + 135 * s, (160, 60, 50), 4, 8)
        for k in range(4):
            self.star_shape(d, x + (-50 if k % 2 else 50) * s, y + (-70 if k < 2 else 70) * s, 16 * s, GOLD)
        self.oell(d, x, y, 40 * s, 40 * s, GOLD, 4)

    def trunk(self, d, x, y, s=1.0, open_k=0.0):
        self.box(d, x - 200 * s, y - 100 * s, x + 200 * s, y + 100 * s, (140, 90, 50), 7, 14)
        for xx in (-120, 120):
            self.box(d, x + xx * s - 14 * s, y - 100 * s, x + xx * s + 14 * s, y + 100 * s, (90, 60, 35), 4)
        lid = 80 * open_k
        self.box(d, x - 200 * s, y - 100 * s - 60 * s - lid * s, x + 200 * s, y - 100 * s - lid * s, (160, 105, 60), 7, 14)

    def handcuffs(self, d, x, y, k=1.0):
        for sx in (-1, 1):
            d.ellipse([(x + sx * 60 - 50 * k) * S, (y - 50 * k) * S, (x + sx * 60 + 50 * k) * S, (y + 50 * k) * S], outline=INK, width=int(18 * S))
            d.ellipse([(x + sx * 60 - 46 * k) * S, (y - 46 * k) * S, (x + sx * 60 + 46 * k) * S, (y + 46 * k) * S], outline=(210, 210, 220), width=int(10 * S))
        self.Ln(d, [(x - 12, y), (x + 12, y)], (210, 210, 220), 10)

    def magnifier(self, d, x, y, s=1.0):
        self.oell(d, x, y, 100 * s, 100 * s, (200, 230, 250), 10)
        self.poly(d, [(x + 65 * s, y + 65 * s), (x + 85 * s, y + 45 * s), (x + 200 * s, y + 160 * s), (x + 180 * s, y + 180 * s)], (90, 60, 40))

    # ───── fondos ─────
    def bg_flat(self, img, top, bot):
        self.bgdyn(img, top, bot)

    def floor(self, d, y, col=(120, 90, 70), tile=None):
        self.box(d, -10, y, W + 10, H + 20, col, 6)
        if tile:
            for i in range(12):
                d.line([((i * 100 - 60) * S, y * S), ((i * 140 - 300) * S, H * S)], fill=tile, width=int(4 * S))

    def bg_museum(self, img, d, t, wall=(170, 60, 60), frames=(), floor_col=(150, 110, 70)):
        self.bg_flat(img, wall, mix(wall, (0, 0, 0), 0.25))
        self.box(d, -10, 300, W + 10, 340, mix(wall, (255, 255, 255), 0.3), 4)
        for (x, y, w, h, kind, empty) in frames:
            self.painting(img, d, x, y, w, h, kind, empty)
        self.floor(d, 1300, floor_col, mix(floor_col, (0, 0, 0), 0.2))

    def bg_city(self, img, d, t, sky=((120, 180, 240), (250, 220, 180)), cols=None, night=0.0):
        self.bg_flat(img, mix(sky[0], (20, 20, 50), night), mix(sky[1], (40, 30, 70), night))
        cols = cols or [(230, 210, 180), (210, 190, 160), (240, 225, 200), (200, 180, 150)]
        for i in range(7):
            x = i * 165 - 40
            h = 560 + (i * 131) % 280
            self.box(d, x, 1250 - h, x + 160, 1260, mix(cols[i % len(cols)], (30, 30, 60), night * 0.6), 6)
            self.poly(d, [(x - 6, 1250 - h), (x + 80, 1250 - h - 60), (x + 166, 1250 - h)], mix((90, 110, 140), (20, 20, 40), night), 6)
            for wy in range(1250 - h + 50, 1200, 110):
                for wx in (x + 25, x + 95):
                    lit = (wx + wy) % 3 == 0
                    self.box(d, wx, wy, wx + 40, wy + 64, (255, 220, 120) if (lit and night > 0.3) else (120, 160, 190), 4, 4)
        self.box(d, -10, 1250, W + 10, 1340, (180, 180, 190), 6)
        self.box(d, -10, 1340, W + 10, H + 20, (80, 80, 92), 6)

    def bg_night_sky(self, img, d, t, k=1.0):
        self.bg_flat(img, (10, 14, 40), (30, 30, 70))
        self.stars(d, t, 0.8 * k)
        self.E(d, 860, 420, 70, (240, 240, 220))
        self.E(d, 885, 400, 64, (10, 14, 40))

    def bg_forest(self, img, d, t, night=0.6):
        self.bg_flat(img, mix((120, 180, 230), (14, 18, 40), night), mix((200, 220, 230), (30, 34, 60), night))
        for layer, (y0, col) in enumerate(((1000, (40, 80, 60)), (1150, (30, 70, 50)))):
            for i in range(9):
                x = i * 140 - 40 + layer * 60
                self.poly(d, [(x, y0 + 200), (x + 70, y0 - 160 - (i * 37) % 120), (x + 140, y0 + 200)], mix(col, (10, 20, 20), night * 0.5), 5)
        self.box(d, -10, 1350, W + 10, H + 20, mix((90, 130, 70), (30, 40, 30), night), 6)
        self.box(d, -10, 1500, W + 10, 1640, mix((70, 140, 190), (30, 50, 80), night), 5)
        for j in range(3):
            y = 1530 + j * 35
            d.line([(x * S, (y + 6 * math.sin(x / 40 + t * 3 + j)) * S) for x in range(0, W + 40, 40)], fill=(200, 230, 250), width=int(3 * S))

    def bg_vault(self, img, d, t, open_n=0):
        self.bg_flat(img, (110, 115, 125), (80, 84, 94))
        n = 0
        for r in range(9):
            for c in range(7):
                x, y = 70 + c * 138, 330 + r * 110
                opened = n < open_n
                self.box(d, x, y, x + 124, y + 96, (60, 60, 66) if opened else (180, 184, 196), 4, 6)
                if not opened:
                    self.E(d, x + 98, y + 48, 9, (90, 90, 100))
                n += 1
        self.floor(d, 1330, (90, 92, 100))

    def bg_road(self, img, d, t, night=0.4):
        self.bg_flat(img, mix((150, 190, 230), (20, 24, 50), night), mix((230, 230, 220), (40, 40, 70), night))
        for i in range(6):
            x = i * 200 - 40
            self.poly(d, [(x, 1200), (x + 100, 900 - (i * 53) % 150), (x + 200, 1200)], mix((60, 110, 70), (20, 40, 30), night), 5)
        self.box(d, -10, 1200, W + 10, 1420, mix((110, 160, 80), (40, 60, 40), night), 6)
        self.box(d, -10, 1420, W + 10, H + 20, (70, 70, 80), 6)
        for i in range(6):
            x = (i * 220 - t * 300) % (W + 220) - 110
            d.rectangle([x * S, 1650 * S, (x + 120) * S, 1668 * S], fill=(240, 220, 120))

    def bg_cathedral(self, img, d, t):
        self.bg_flat(img, (60, 50, 70), (110, 90, 80))
        for i in range(5):  # arcos
            x = 60 + i * 200
            self.poly(d, [(x, 1300), (x, 700), (x + 90, 560), (x + 180, 700), (x + 180, 1300)], (150, 130, 110), 6)
            self.poly(d, [(x + 30, 1300), (x + 30, 720), (x + 90, 620), (x + 150, 720), (x + 150, 1300)], (70, 60, 80), 4)
        self.glow(img, 540, 500, 260, (255, 220, 160), 120)
        self.floor(d, 1300, (130, 110, 90), (110, 92, 76))

    def bg_garage(self, img, d, t):
        self.bg_flat(img, (140, 140, 150), (110, 110, 120))
        self.box(d, 100, 420, 980, 1300, (170, 170, 180), 8)
        for j in range(12):
            d.line([(110 * S, (450 + j * 72) * S), (970 * S, (450 + j * 72) * S)], fill=(130, 130, 140), width=int(6 * S))
        for i, c in enumerate([(200, 160, 90), (150, 120, 80), (180, 140, 100)]):
            self.box(d, 140 + i * 130, 1150 - i * 40, 250 + i * 130, 1300, c, 5, 4)
        self.floor(d, 1300, (100, 100, 108))

    def bg_police(self, img, d, t):
        on = int(t * 6) % 2
        self.bg_flat(img, (40, 40, 70), (20, 20, 40))
        self.glow(img, 150, 500, 380, (255, 40, 40) if on else (40, 90, 255), 200)
        self.glow(img, 930, 500, 380, (40, 90, 255) if on else (255, 40, 40), 200)
        self.floor(d, 1300, (80, 80, 92))

    def bg_newspaper(self, img, d, t, headline, sub="", tilt=-4):
        self.bg_flat(img, (60, 50, 50), (30, 26, 26))
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.rectangle([140 * S, 420 * S, 940 * S, 1500 * S], fill=(240, 235, 220), outline=INK, width=int(8 * S))
        dl.text((540 * S, 520 * S), "EDICIÓN ESPECIAL", font=anton(40 * S), fill=(80, 70, 60), anchor="mm")
        dl.line([(180 * S, 570 * S), (900 * S, 570 * S)], fill=INK, width=int(5 * S))
        for i, ln in enumerate(headline):
            dl.text((540 * S, (680 + i * 120) * S), ln, font=anton(104 * S), fill=INK, anchor="mm")
        for i in range(8):
            dl.line([(200 * S, (1000 + i * 50) * S), ((880 - (i % 3) * 120) * S, (1000 + i * 50) * S)], fill=(150, 140, 130), width=int(10 * S))
        img.alpha_composite(lay.rotate(tilt + 2 * math.sin(t * 2), center=(540 * S, 960 * S), resample=Image.BICUBIC))

    def bars(self, d):
        for i in range(8):
            x = 100 + i * 125
            self.box(d, x, 300, x + 30, 1700, (150, 154, 166), 5, 10)

    def plane(self, img, d, x, y, s, t, night=False):
        body = (235, 235, 245) if not night else (170, 175, 190)
        self.box(d, x - 220 * s, y - 50 * s, x + 220 * s, y + 50 * s, body, 6, 50 * s)
        self.poly(d, [(x - 40 * s, y), (x + 60 * s, y), (x - 80 * s, y + 170 * s), (x - 140 * s, y + 170 * s)], mix(body, (0, 0, 0), 0.1))
        self.poly(d, [(x - 200 * s, y - 30 * s), (x - 160 * s, y - 30 * s), (x - 230 * s, y - 140 * s)], (220, 60, 70))
        for i in range(6):
            self.E(d, x + 140 * s - i * 50 * s, y - 10 * s, 13 * s, (255, 230, 140) if night else (120, 180, 230))

    # ───── HUD, subtítulos, tarjetas, final ─────
    def hud_items(self, t):
        return []

    def hud(self, out, t):
        items = self.hud_items(t)
        if not items or t < 0.8 or t >= self.start("cta") - 0.1:
            return out
        img = out.convert("RGBA")
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        k = ease_out(clamp((t - 0.8) / 0.4))
        y0 = TOP + 12 - (1 - k) * 300  # por debajo de la barra de estado e iconos de la app
        w, gap = 272, 12
        x = (1080 - (3 * w + 2 * gap)) / 2
        for lab, val, col in items:
            d.rounded_rectangle([x, y0, x + w, y0 + 112], 18, fill=(20, 16, 24, 235), outline=(255, 255, 255, 90), width=4)
            fl = 30
            while anton(fl).getlength(lab) > w - 30 and fl > 18:
                fl -= 1
            d.text((x + 16, y0 + 26), lab, font=anton(fl), fill=(220, 210, 220), anchor="lm")
            if isinstance(val, int):  # estrellas
                for s in range(3):
                    cx, cy = x + 52 + s * 84, y0 + 74
                    pts = [(cx + (29 if i % 2 == 0 else 12) * math.cos(-math.pi / 2 + i * math.pi / 5),
                            cy + (29 if i % 2 == 0 else 12) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
                    d.polygon(pts, fill=(255, 200, 40) if s < val else (70, 66, 80), outline=INK)
            else:
                fv = 50
                while anton(fv).getlength(val) > w - 30 and fv > 26:
                    fv -= 2
                d.text((x + 16, y0 + 74), val, font=anton(fv), fill=col, anchor="lm", stroke_width=3, stroke_fill=INK)
            x += w + gap
        img.alpha_composite(lay)
        return img.convert("RGB")

    def caption(self, out, t):
        if t >= self.start("cta") - 0.1:
            return out
        cur = None
        for ln in self.nar["lines"]:
            if ln["start"] - 0.05 <= t <= ln["end"] + 0.25:
                cur = ln
        if not cur:
            return out
        words = cur["words"]
        idx = max([i for i, w in enumerate(words) if w[1] <= t + 0.02] or [0])
        g0 = (idx // 3) * 3
        grp = words[g0:g0 + 3]
        img = out.convert("RGBA")
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        fs0 = 96
        f = anton(fs0)
        toks = [w[0].upper() for w in grp]
        sp = f.getlength(" ")
        widths = [f.getlength(tk) for tk in toks]
        maxw = RIGHT_ICONS[0] - SIDE - 40
        while sum(widths) + sp * (len(toks) - 1) > maxw and len(toks) > 1:
            toks, widths, grp = toks[:-1], widths[:-1], grp[:-1]
        while sum(widths) + sp * (len(toks) - 1) > maxw and fs0 > 60:  # una palabra muy larga: letra algo menor
            fs0 -= 4
            f = anton(fs0)
            sp = f.getlength(" ")
            widths = [f.getlength(tk) for tk in toks]
        cx = (SIDE + RIGHT_ICONS[0]) / 2
        x = cx - (sum(widths) + sp * (len(toks) - 1)) / 2
        y = 1190
        for (w, a, b), tk, ww in zip(grp, toks, widths):
            if t < a - 0.03:
                x += ww + sp
                continue
            age = t - a
            sc = 1 + 0.12 * max(0, 1 - age / 0.12)
            key = self.is_key(w)
            d.text((x + ww / 2, y), tk, font=anton(fs0 * sc), fill=GOLD if key else (255, 255, 255), anchor="mm", stroke_width=10, stroke_fill=INK)
            if key:
                ul = ww * ease_out(age / 0.25)
                d.rounded_rectangle([x, y + fs0 * 0.5, x + ul, y + fs0 * 0.5 + 12], 6, fill=GOLD, outline=INK, width=3)
            x += ww + sp
        img.alpha_composite(lay)
        return img.convert("RGB")

    def overlay(self, ov, d, t, name, lt, u):
        """Tarjetas de fase (fijas en pantalla, sin zoom)."""
        drew = False
        for key, (title, icon) in self.CARDS.items():
            t0 = self.start(key) - 0.1
            lt2 = t - t0
            if 0 <= lt2 <= 1.6:
                k = back_out(lt2 / 0.3) * (1 - smooth(1.25, 1.6, lt2))
                if k > 0.02:
                    cx, cy = 540, 640
                    w, h = 420 * k, 170 * k
                    self.box(d, cx - w, cy - h, cx + w, cy + h, CARD, 8, 26)
                    self.box(d, cx - w + 22 * k, cy - h + 22 * k, cx + w - 22 * k, cy + h - 22 * k, (30, 22, 28), 4, 18)
                    self.oell(d, cx, cy - 50 * k, 48 * k, 48 * k, CARD, 5)
                    self.ot(ov, cx, cy - 50 * k, icon, 56 * k, WHITE, 4)
                    self.ot(ov, cx, cy + 70 * k, title, 88 * k, WHITE, 6)
                    drew = True
        return drew

    def end_card(self, img, d, t, lt, toon=None, expr="sly", pose="shrug"):
        self.bg_flat(img, (250, 200, 60), (250, 150, 50))
        k = back_out(lt / 0.4)
        self.box(d, 540 - 420 * k, 980 - 260 * k, 540 + 420 * k, 980 + 260 * k, WHITE, 8, 60 * k)
        self.poly(d, [(540 - 160 * k, 980 + 255 * k), (540 - 260 * k, 980 + 400 * k), (540 - 40 * k, 980 + 255 * k)], WHITE, 8)
        if k > 0.6:
            self.ot(img, 540, 900, self.FIN[0], 100, INK, 0)
            self.ot(img, 540, 1040, self.FIN[1], 110, CARD, 0)
        if toon:
            toon.draw(img, 800, 1700, t, expr=expr, pose=pose, scale=0.6)
        self.ot(img, 450, 1400, "NIVEL OCULTO", 64, WHITE, 6)

    def s_fin(self, img, d, t, lt, u):
        self.end_card(img, d, t, lt, getattr(self, "host", None))


def main(cls):
    import sys

    if sys.argv[1] == "plan":
        schedule(cls, sys.argv[2])
    else:
        render(cls, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
