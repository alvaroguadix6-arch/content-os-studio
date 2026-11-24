"""NIVEL OCULTO · El Dioni en dibujos animados (estilo cartoon propio, personajes animados, HUD de «juego»).

Mismos hechos y fuentes que dioni.py (Wikipedia, Infobae, COPE). El protagonista es un personaje de dibujos genérico
(sin parecido con la persona real). 28-7-1989 → 19-9-1989 = 53 días libre.
"""
from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from motor import CYAN, RED, WHITE, W, H, S, YEL, Video, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401
from toon import INK, Look, Toon

MOOD, BPM = "suspense", 104
FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts", "Anton-Regular.ttf")
_fc = {}
GOLD = (255, 205, 40)
CARD = (215, 40, 50)
DAYS = 53


def anton(size):
    k = int(size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT, max(8, k))
    return _fc[k]


class VIDEO(Video):
    NAME = "dioni2"
    BRAND = None
    KEYWORDS = {"cien", "millones", "pesetas", "aparecer", "vigilarlos", "madrid", "dioni", "vigilante", "compañeros", "arranca",
                "doscientos", "noventa", "ocho", "euros", "amigos", "brasil", "río", "janeiro", "hoteles", "fiestas", "gastos", "atención",
                "septiembre", "policía", "detiene", "narcotraficante", "diez", "meses", "extraditado", "dinero", "recuperó", "nunca",
                "apareció", "falta", "comentarios"}

    def setup(self):
        self.dioni = Toon(Look(shirt=(70, 92, 140), hat="cap", hat_col=(36, 46, 78), badge=True, hair=(50, 36, 28)), seed=1)
        self.dioni_rio = Toon(Look(shirt=(235, 90, 120), pattern="flowers", hair=(50, 36, 28), pants=(220, 200, 150)), seed=1)
        self.mate1 = Toon(Look(shirt=(70, 92, 140), hat="cap", hat_col=(36, 46, 78), badge=True, skin=(200, 150, 110), hair=(20, 20, 20)), seed=4)
        self.mate2 = Toon(Look(shirt=(70, 92, 140), hat="cap", hat_col=(36, 46, 78), badge=True, skin=(250, 205, 170), stubble=False), seed=7)
        self.friends = [Toon(Look(shirt=c, hair=hc, skin=sk, stubble=st), seed=10 + i) for i, (c, hc, sk, st) in
                        enumerate([((90, 170, 90), (30, 20, 20), (230, 180, 140), False), ((240, 170, 60), (120, 70, 30), (250, 205, 170), True),
                                   ((150, 90, 190), (20, 20, 20), (180, 125, 90), False)])]
        self.cops = [Toon(Look(shirt=(60, 110, 190), hat="police", hat_col=(25, 50, 110), badge=True, skin=sk, stubble=False), seed=20 + i)
                     for i, sk in enumerate([(180, 125, 90), (230, 180, 140)])]
        r = random.Random(3)
        self.bills = [(r.uniform(0, W), r.uniform(0, H), r.uniform(0.8, 1.3), r.uniform(0, 6.3)) for _ in range(36)]
        self.t_go = self.w("golpe", "arranca")
        self.t_det = self.w("caida", "detiene")
        self.shakes = [(self.t_go, 0.8), (self.t_det, 0.9), (self.w("intro", "vigilarlos"), 0.5)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("fecha") - 0.1, "madrid"), (st("golpe") - 0.1, "golpe"), (st("botin") - 0.1, "botin"),
                (st("huida") - 0.1, "huida"), (st("rio") - 0.1, "rio"), (st("caida") - 0.1, "caida"), (st("carcel") - 0.1, "carcel"),
                (st("misterio") - 0.1, "misterio"), (st("cta") - 0.1, "fin")]

    # ───── utilidades de dibujo con contorno ─────
    def box(self, d, x0, y0, x1, y1, col, ow=6, r=0):
        d.rounded_rectangle([(x0 - ow) * S, (y0 - ow) * S, (x1 + ow) * S, (y1 + ow) * S], radius=int((r + ow) * S), fill=INK)
        d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=int(r * S), fill=col)

    def poly(self, d, pts, col, ow=6):
        d.polygon([(x * S, y * S) for x, y in pts], fill=col)
        d.line([(x * S, y * S) for x, y in pts + [pts[0]]], fill=INK, width=int(ow * S), joint="curve")

    def ot(self, img, x, y, txt, size, col=WHITE, stroke=8, anchor="mm", rot=0.0, alpha=255):
        """Texto Anton con contorno grueso."""
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
        f = anton(size * S * sc)
        tw = f.getlength(txt)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([x * S - tw / 2 - 30 * S, y * S - size * S * 0.72 * sc, x * S + tw / 2 + 30 * S, y * S + size * S * 0.72 * sc],
                             radius=int(14 * S), fill=(255, 250, 240, 235), outline=col + (255,), width=int(10 * S))
        dl.text((x * S, y * S), txt, font=f, fill=col + (255,), anchor="mm")
        img.alpha_composite(lay.rotate(-rot, center=(x * S, y * S), resample=Image.BICUBIC))

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

    def money_bag(self, img, d, x, y, s, col=(205, 165, 95), label="PTA", q=False):
        self.poly(d, [(x - 30 * s, y - 95 * s), (x + 30 * s, y - 95 * s), (x + 18 * s, y - 70 * s), (x - 18 * s, y - 70 * s)], col)
        d.ellipse([(x - 100 * s - 6) * S, (y - 80 * s - 6) * S, (x + 100 * s + 6) * S, (y + 90 * s + 6) * S], fill=INK)
        d.ellipse([(x - 100 * s) * S, (y - 80 * s) * S, (x + 100 * s) * S, (y + 90 * s) * S], fill=col)
        self.ot(img, x, y + 10 * s, "?" if q else label, (110 if q else 54) * s, GOLD if q else (90, 60, 30), 6 if q else 0)

    # ───── fondos ilustrados ─────
    def bg_sky(self, img, top, bot):
        self.bgdyn(img, top, bot)

    def bg_street(self, img, d, t, dusk=0.4):
        self.bg_sky(img, mix((120, 180, 240), (240, 140, 110), dusk), mix((250, 220, 180), (250, 190, 140), dusk))
        cols = [(230, 170, 120), (200, 120, 100), (240, 200, 150), (170, 140, 190), (220, 150, 110)]
        for i in range(7):
            x = i * 165 - 40
            h = 520 + (i * 131) % 300
            self.box(d, x, 1250 - h, x + 160, 1260, cols[i % 5], 6)
            for wy in range(1250 - h + 50, 1200, 110):
                for wx in (x + 25, x + 95):
                    self.box(d, wx, wy, wx + 40, wy + 60, (120, 190, 230) if (wx + wy) % 3 else (255, 220, 120), 4, 4)
        self.box(d, -10, 1250, W + 10, 1340, (180, 180, 190), 6)
        self.box(d, -10, 1340, W + 10, H + 20, (70, 72, 84), 6)
        for i in range(6):
            x = (i * 220 - t * 40) % (W + 220) - 110
            d.rectangle([x * S, 1600 * S, (x + 120) * S, 1618 * S], fill=(240, 220, 120))

    def bg_depot(self, img, d, t):
        self.bg_sky(img, (130, 70, 60), (90, 50, 45))
        for row in range(30):  # ladrillos
            y = 300 + row * 42
            off = 60 if row % 2 else 0
            for i in range(-1, 10):
                x = i * 120 + off
                d.rectangle([x * S, y * S, (x + 112) * S, (y + 36) * S], fill=(170, 85, 70) if (i + row) % 3 else (150, 75, 62))
        self.box(d, 140, 420, 940, 1250, (150, 156, 170), 8)  # puerta de garaje
        for j in range(12):
            d.line([(150 * S, (450 + j * 66) * S), (930 * S, (450 + j * 66) * S)], fill=(110, 116, 130), width=int(6 * S))
        self.box(d, -10, 1250, W + 10, H + 20, (90, 92, 100), 6)
        self.poly(d, [(400, 300), (680, 300), (620, 340), (460, 340)], (60, 60, 70))
        self.glow(img, 540, 360, 160, (255, 230, 160), 120)

    def van(self, img, d, x, y, s=1.0, driver=None, t=0.0, expr="grin"):
        """Furgón blindado (vista lateral, mirando a la derecha)."""
        self.box(d, x - 330 * s, y - 330 * s, x + 170 * s, y - 40 * s, (175, 180, 190), 8, 18)
        self.poly(d, [(x + 170 * s, y - 250 * s), (x + 290 * s, y - 250 * s), (x + 340 * s, y - 150 * s), (x + 340 * s, y - 40 * s), (x + 170 * s, y - 40 * s)], (175, 180, 190))
        self.poly(d, [(x + 190 * s, y - 230 * s), (x + 280 * s, y - 230 * s), (x + 318 * s, y - 155 * s), (x + 190 * s, y - 155 * s)], (150, 210, 240))
        if driver:
            driver(x + 245 * s, y - 165 * s)
        self.box(d, x - 300 * s, y - 280 * s, x + 140 * s, y - 210 * s, (200, 60, 60), 5, 8)
        self.ot(img, x - 80 * s, y - 245 * s, "CANDI S. A.", 48 * s, WHITE, 5)
        for wx in (x - 210 * s, x + 220 * s):
            self.E(d, wx, y - 30 * s, 72 * s, INK)
            self.E(d, wx, y - 30 * s, 58 * s, (60, 60, 66))
            self.E(d, wx, y - 30 * s, 26 * s, (190, 190, 200))
            a = t * 12
            d.line([((wx + math.cos(a) * 24 * s) * S, (y - 30 * s + math.sin(a) * 24 * s) * S), ((wx - math.cos(a) * 24 * s) * S, (y - 30 * s - math.sin(a) * 24 * s) * S)],
                   fill=INK, width=int(5 * S))

    def bg_beach(self, img, d, t):
        self.bg_sky(img, (250, 120, 120), (255, 200, 120))
        self.glow(img, 540, 700, 260, (255, 230, 150), 200)
        self.E(d, 540, 700, 130, (255, 225, 120))
        self.poly(d, [(560, 1050), (700, 690), (790, 650), (880, 760), (1000, 1050)], (120, 70, 110))  # Pan de Azúcar
        self.poly(d, [(-20, 1050), (110, 860), (240, 950), (380, 820), (520, 1050)], (140, 80, 120))
        self.box(d, -10, 1050, W + 10, 1260, (60, 160, 210), 6)
        for j in range(4):
            y = 1090 + j * 40
            d.line([((x) * S, (y + 8 * math.sin(x / 50 + t * 3 + j)) * S) for x in range(0, W + 40, 40)], fill=(220, 240, 250), width=int(4 * S))
        self.box(d, -10, 1260, W + 10, H + 20, (245, 215, 150), 6)
        for px, k in ((90, 1.0), (990, 1.1)):  # palmeras
            sw = 10 * math.sin(t * 1.4 + px)
            top = (px + 30 * k + sw, 760)
            self.poly(d, [(px - 18, 1300), (px + 18, 1300), (top[0] + 10, top[1]), (top[0] - 10, top[1])], (150, 100, 60))
            for i in range(6):
                a = -math.pi / 2 + (i - 2.5) * 0.6
                L = 200 * k
                self.poly(d, [top, (top[0] + math.cos(a) * L, top[1] + math.sin(a) * L * 0.5 + 60), (top[0] + math.cos(a) * L * 0.6, top[1] + math.sin(a) * L * 0.3 - 10)], (70, 170, 90), 4)

    def bg_police(self, img, d, t):
        on = int(t * 6) % 2
        self.bg_sky(img, (40, 40, 70), (20, 20, 40))
        self.glow(img, 150, 500, 380, (255, 40, 40) if on else (40, 90, 255), 200)
        self.glow(img, 930, 500, 380, (40, 90, 255) if on else (255, 40, 40), 200)
        self.box(d, -10, 1300, W + 10, H + 20, (80, 80, 92), 6)

    def bg_cell(self, img, d, t):
        self.bg_sky(img, (120, 120, 130), (90, 90, 100))
        for row in range(28):
            y = 300 + row * 50
            off = 70 if row % 2 else 0
            for i in range(-1, 9):
                x = i * 140 + off
                d.rectangle([x * S, y * S, (x + 132) * S, (y + 44) * S], fill=(140, 140, 150) if (i + row) % 2 else (130, 130, 140))
        self.box(d, 60, 1150, 420, 1260, (110, 80, 60), 6, 10)  # catre
        self.box(d, -10, 1300, W + 10, H + 20, (100, 100, 110), 6)
        self.box(d, 760, 520, 900, 640, (40, 40, 50), 6)  # ventanuco
        for i in range(3):
            d.line([((780 + i * 50) * S, 520 * S), ((780 + i * 50) * S, 640 * S)], fill=(160, 160, 170), width=int(8 * S))

    def bars(self, d):
        for i in range(8):
            x = 100 + i * 125
            self.box(d, x, 300, x + 30, 1700, (150, 154, 166), 5, 10)
        self.box(d, 80, 420, 1000, 460, (150, 154, 166), 5)
        self.box(d, 80, 1560, 1000, 1600, (150, 154, 166), 5)

    def plane(self, img, d, x, y, s, t):
        self.box(d, x - 220 * s, y - 50 * s, x + 220 * s, y + 50 * s, (245, 245, 250), 6, 50 * s)
        self.poly(d, [(x - 40 * s, y), (x + 60 * s, y), (x - 80 * s, y + 170 * s), (x - 140 * s, y + 170 * s)], (220, 225, 235))
        self.poly(d, [(x - 200 * s, y - 30 * s), (x - 160 * s, y - 30 * s), (x - 230 * s, y - 140 * s)], (220, 60, 70))
        for i in range(6):
            self.E(d, x + 140 * s - i * 50 * s, y - 10 * s, 13 * s, (120, 180, 230))
        self.ot(img, x + 140 * s, y - 10 * s, "", 10)

    # ───── HUD de «juego» ─────
    def hud(self, out, t):
        if t < 0.8 or t >= self.start("cta") - 0.1:
            return out
        img = out.convert("RGBA")
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        k = ease_out(clamp((t - 0.8) / 0.4))
        y0 = 40 - (1 - k) * 160
        botin = 0 if t < self.t_go else 298_000_000 * ease_out(clamp((t - self.start("botin")) / 2.0)) if t < self.start("botin") + 2.5 else 298_000_000
        dias = 0 if t < self.start("huida") else int(DAYS * clamp((t - self.start("huida")) / max(0.1, self.t_det - self.start("huida"))))
        stars = 0 + (t >= self.t_go) + (t >= self.start("huida")) + (t >= self.t_det)
        chips = [("DÍAS LIBRE", f"{dias}/{DAYS}", (255, 255, 255)), ("BOTÍN", f"{botin / 1e6:,.0f} M PTA".replace(",", "."), GOLD), ("BUSCADO", "", (255, 90, 90))]
        x = 22
        for lab, val, col in chips:
            w = 334
            d.rounded_rectangle([x, y0, x + w, y0 + 128], 20, fill=(20, 16, 24, 235), outline=(255, 255, 255, 90), width=4)
            d.text((x + 18, y0 + 28), lab, font=anton(34), fill=(220, 210, 220), anchor="lm")
            if lab == "BUSCADO":
                for s in range(3):
                    cx, cy = x + 62 + s * 100, y0 + 84
                    pts = []
                    for i in range(10):
                        rr = 34 if i % 2 == 0 else 14
                        a = -math.pi / 2 + i * math.pi / 5
                        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
                    d.polygon(pts, fill=(255, 200, 40) if s < stars else (70, 66, 80), outline=INK)
            else:
                d.text((x + 18, y0 + 84), val, font=anton(56), fill=col, anchor="lm", stroke_width=3, stroke_fill=INK)
            x += w + 9
        img.alpha_composite(lay.resize(img.size, Image.LANCZOS) if lay.size != img.size else lay)
        return img.convert("RGB")

    # ───── subtítulos tipo meme: 1-3 palabras, grandes, en el centro ─────
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
        f = anton(104)
        toks = [w[0].upper() for w in grp]
        sp = f.getlength(" ")
        widths = [f.getlength(tk) for tk in toks]
        while sum(widths) + sp * (len(toks) - 1) > 1000 and len(toks) > 1:
            toks, widths, grp = toks[:-1], widths[:-1], grp[:-1]
        x = 540 - (sum(widths) + sp * (len(toks) - 1)) / 2
        y = 1310
        for (w, a, b), tk, ww in zip(grp, toks, widths):
            if t < a - 0.03:
                x += ww + sp
                continue
            age = t - a
            sc = 1 + 0.12 * max(0, 1 - age / 0.12)
            key = self.is_key(w)
            col = GOLD if key else (255, 255, 255)
            fs = anton(104 * sc)
            d.text((x + ww / 2, y), tk, font=fs, fill=col, anchor="mm", stroke_width=10, stroke_fill=INK)
            if key:
                ul = ww * ease_out(age / 0.25)
                d.rounded_rectangle([x, y + 52, x + ul, y + 64], 6, fill=GOLD, outline=INK, width=3)
            x += ww + sp
        img.alpha_composite(lay)
        return img.convert("RGB")

    def phase_card(self, img, d, t, t0, title, icon):
        """Tarjeta de fase que entra de golpe (como un aviso de juego)."""
        lt = t - t0
        if lt < 0 or lt > 1.6:
            return
        k = back_out(lt / 0.3) * (1 - smooth(1.25, 1.6, lt))
        if k <= 0.02:
            return
        cx, cy = 540, 640
        w, h = 400 * k, 170 * k
        self.box(d, cx - w, cy - h, cx + w, cy + h, CARD, 8, 26)
        self.box(d, cx - w + 22 * k, cy - h + 22 * k, cx + w - 22 * k, cy + h - 22 * k, (30, 22, 28), 4, 18)
        self.E(d, cx, cy - 50 * k, 48 * k, CARD)
        self.ot(img, cx, cy - 50 * k, icon, 56 * k, WHITE, 4)
        self.ot(img, cx, cy + 70 * k, title, 92 * k, WHITE, 6)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        th = self.w("intro", "hombre") - 0.2
        tv = self.w("intro", "vigilarlos")
        if t < th:
            self.bg_sky(img, (40, 30, 60), (20, 16, 34))
            for j in range(3):
                x = 250 + j * 290
                k = 1 - smooth(0.4 + j * 0.3, 1.0 + j * 0.3, lt)
                bob = 8 * math.sin(t * 5 + j)
                self.money_bag(img, d, x, 1080 + bob, 1.1, mix((70, 60, 80), (205, 165, 95), k), q=k < 0.5)
            self.stamp(img, 540, 640, "+100 MILLONES", 110, t, -0.3)
            self.stamp(img, 540, 820, "DESAPARECIDOS", 84, t, -0.15, (30, 30, 40), rot=5)
        else:
            self.bg_sky(img, (30, 24, 50), (14, 12, 24))
            k = smooth(th, th + 0.4, t)
            self.poly(d, [(440, 180), (640, 180), (900, 1650), (180, 1650)], mix((30, 24, 50), (250, 230, 160), 0.35 * k), 0)
            sc = back_out((t - th) / 0.4)
            self.dioni.draw(img, 540, 1640, t, expr="sly" if t > tv - 0.3 else "neutral", pose="idle" if t < tv else "point",
                            look_at=(900, 900), scale=max(0.05, 1.15 * sc))
            self.stamp(img, 540, 560, "ERA EL VIGILANTE", 96, t, tv)

    def s_madrid(self, img, d, t, lt, u):
        self.bg_street(img, d, t)
        walk_end = 1.8
        x = -150 + 690 * ease_out(clamp(lt / walk_end))
        walking = lt < walk_end
        pose = "wave" if (not walking and t > self.w("fecha", "vigilante") - 0.3) else "idle"
        self.dioni.draw(img, x, 1640, t, expr="happy", pose=pose, walk=t * 9 if walking else 0.0, scale=1.05, look_at=(540, 1000))
        k = back_out((lt - 0.2) / 0.4)
        if k > 0.02:
            self.box(self.D(img), 540 - 240 * k, 470 - 70 * k, 540 + 240 * k, 470 + 70 * k, (255, 250, 235), 6, 18)
            self.ot(img, 540, 470, "MADRID · 1989", 70 * k, (40, 30, 40), 0)
        self.pop(img, 540, 1590, "VIGILANTE DE SEGURIDAD", 62, t, self.w("fecha", "vigilante"), GOLD)

    def D(self, img):
        return ImageDraw.Draw(img)

    def s_golpe(self, img, d, t, lt, u):
        self.bg_depot(img, d, t)
        go = max(0.0, t - self.t_go)
        vx = 520 + go * go * 1400
        for i, (m, dirx) in enumerate(((self.mate1, -1), (self.mate2, 1))):  # los compañeros se van andando
            k = smooth(0.1, 2.0, lt)
            mx = (230 if dirx < 0 else 860) + dirx * 520 * k
            m.draw(img, mx, 1700, t, expr="neutral", pose="idle", walk=t * 9 if k < 1 else 0, scale=0.85, flip=dirx < 0)
        if go <= 0:
            look = (100, 900) if math.sin(lt * 3) > 0 else (980, 900)
            self.van(img, d, 600, 1600, 1.0, t=0)
            self.dioni.draw(img, 300, 1720, t, expr="sly", pose="idle", look_at=look, scale=0.95)
        else:
            def driver(x, y):
                self.dioni.draw(img, x, y + 150, t, expr="grin", pose="idle", scale=0.42, bounce=False)
            self.van(img, d, vx, 1600 + 4 * math.sin(t * 30), 1.0, driver=driver, t=t)
            for i in range(10):  # humo y polvo
                ph = (go * 2 + i / 10) % 1
                self.E(d, vx - 360 - ph * 300, 1560 - 40 * math.sin(i), 30 + 50 * ph, (200, 200, 205))
            self.pop(img, 540, 560, "¡Y ARRANCA!", 140, t, self.t_go, GOLD, rot=4)
        self.phase_card(img, d, t, self.start("golpe") - 0.1, "EL GOLPE", "!")

    def s_botin(self, img, d, t, lt, u):
        self.bg_sky(img, (90, 96, 110), (60, 64, 76))
        for row in range(4):  # estanterías del furgón llenas de fajos
            y = 520 + row * 260
            self.box(d, 60, y + 150, 1020, y + 175, (110, 80, 60), 5)
            n = int(10 * clamp(lt * 2 - row * 0.4))
            for i in range(n):
                x = 80 + i * 92
                self.box(d, x, y + 60, x + 80, y + 150, (120, 190, 140), 4, 6)
                d.rectangle([(x + 34) * S, (y + 60) * S, (x + 46) * S, (y + 150) * S], fill=(240, 230, 200))
        self.money_rain(d, t, smooth(0.5, 1.5, lt))
        self.dioni.draw(img, 540, 1760, t, expr="grin", pose="cheer", scale=1.0, look_at=(540, 300))
        self.pop(img, 540, 430, "298.000.000 PTA", 104, t, self.w("botin", "doscientos"), GOLD)
        self.pop(img, 540, 1580, "≈ 1,8 M€ AL CAMBIO", 64, t, self.w("botin", "cambio"), (140, 230, 160))

    def s_huida(self, img, d, t, lt, u):
        tb = self.w("huida", "brasil") - 0.6
        if t < tb:
            self.bg_street(img, d, t, dusk=0.8)
            self.dioni.draw(img, 260, 1700, t, expr="grin", pose="hold", scale=0.9, look_at=(800, 1300))
            for i, f in enumerate(self.friends):
                x = 560 + i * 190
                k = back_out((lt - 0.2 - i * 0.25) / 0.35)
                if k > 0.02:
                    f.draw(img, x, 1720, t, expr="happy", pose="cheer", scale=0.75 * min(1, k))
                    self.money_bag(img, d, x, 1330, 0.35)
        else:
            self.bg_sky(img, (90, 170, 240), (200, 230, 250))
            for i in range(5):
                cx = (i * 260 - t * 120) % (W + 300) - 150
                self.cloud(d, cx, 600 + 180 * (i % 3), 1.6)
            k = ease_out(clamp((t - tb) / 2.0))
            self.plane(img, d, -260 + 1500 * k, 1100 - 260 * k, 1.1, t)
            self.pop(img, 540, 1620, "RUMBO A BRASIL", 110, t, tb + 0.4, GOLD)
        self.phase_card(img, d, t, self.start("huida") - 0.1, "LA HUIDA", "→")

    def s_rio(self, img, d, t, lt, u):
        self.bg_beach(img, d, t)
        self.money_rain(d, t, 0.5, 0.7)
        self.dioni_rio.draw(img, 540, 1760, t, expr="grin", pose="dance", walk=t * 6, scale=1.05)
        self.pop(img, 540, 450, "RÍO DE JANEIRO", 100, t, self.start("rio") + 0.2, WHITE)
        for j, (frag, lab, col) in enumerate((("hoteles", "HOTELES", (255, 120, 160)), ("fiestas", "FIESTAS", (120, 220, 255)), ("gastos", "GASTOS", GOLD))):
            k = back_out((t - self.w("rio", frag)) / 0.3)
            if k > 0.02:
                x = 200 + j * 340
                self.box(d, x - 140 * k, 1610 - 46 * k, x + 140 * k, 1610 + 46 * k, col, 6, 16)
                self.ot(img, x, 1610, lab, 56 * k, INK, 0)

    def s_caida(self, img, d, t, lt, u):
        self.bg_police(img, d, t)
        shock = t > self.t_det - 0.4
        self.dioni_rio.draw(img, 330, 1720, t, expr="shock" if shock else "grin", pose="hands_up" if shock else "dance", walk=t * 6, scale=1.0,
                            look_at=(900, 1200))
        for i, c in enumerate(self.cops):  # entran corriendo
            k = ease_out(clamp((t - self.start("caida") - 0.6 - i * 0.3) / 1.2))
            x = 1300 - (560 - i * 170) * k
            c.draw(img, x + i * 40, 1740, t, expr="angry", pose="run" if k < 1 else "point", walk=t * 12, scale=0.9, flip=True, look_at=(330, 1000))
        self.stamp(img, 540, 520, "DETENIDO · 19-9-1989", 76, t, self.t_det)
        self.pop(img, 540, 1600, "¿UN NARCO?", 96, t, self.w("caida", "narcotraficante"), GOLD, rot=-4)
        self.phase_card(img, d, t, self.start("caida") - 0.1, "LA CAÍDA", "!")

    def s_carcel(self, img, d, t, lt, u):
        self.bg_cell(img, d, t)
        self.dioni_rio.draw(img, 540, 1700, t, expr="sad", pose="grab_bars", scale=1.05, look_at=(540, 1400))
        self.bars(d)
        n = int(10 * ease_out(clamp((lt - 0.3) / 2.2)))
        self.box(d, 540 - 220, 470 - 80, 540 + 220, 470 + 80, (255, 250, 235), 6, 18)
        self.ot(img, 540, 470, f"{n} MESES", 96, (40, 30, 40), 0)
        self.pop(img, 540, 1640, "EXTRADITADO A ESPAÑA", 70, t, self.w("carcel", "extraditado"), GOLD)

    def s_misterio(self, img, d, t, lt, u):
        self.bg_sky(img, (60, 40, 30), (30, 20, 16))
        self.box(d, 60, 900, 1020, 1700, (150, 100, 60), 8, 20)  # mesa del detective
        self.box(d, 130, 960, 950, 1500, (240, 230, 200), 5, 6)  # mapa
        for i in range(6):
            d.line([((130 + i * 140) * S, 960 * S), ((130 + i * 140) * S, 1500 * S)], fill=(210, 200, 170), width=int(3 * S))
        for j in range(3):
            x = 280 + j * 260
            q = j > 0 and t > self.w("misterio", "nunca") - 0.3
            self.money_bag(img, d, x, 1250, 0.7, (205, 165, 95) if not q else (90, 80, 100), q=q)
        a = t * 1.6
        mx, my = 540 + 260 * math.cos(a), 1220 + 120 * math.sin(a * 1.3)
        self.E(d, mx, my, 110, INK)
        self.E(d, mx, my, 92, (200, 230, 250))
        self.poly(d, [(mx + 70, my + 70), (mx + 90, my + 50), (mx + 200, my + 160), (mx + 180, my + 180)], (90, 60, 40))
        self.pop(img, 540, 520, "¿Y EL DINERO?", 130, t, self.start("misterio") + 0.05, GOLD)
        self.pop(img, 280, 1560, "RECUPERADO", 52, t, self.w("misterio", "recuperó"), (140, 230, 160))
        self.stamp(img, 670, 1590, "+100 MILLONES: NUNCA APARECIERON", 44, t, self.w("misterio", "apareció"))
        self.phase_card(img, d, t, self.start("misterio") - 0.1, "EL MISTERIO", "?")

    def s_fin(self, img, d, t, lt, u):
        self.bg_sky(img, (250, 200, 60), (250, 150, 50))
        k = back_out(lt / 0.4)
        self.box(d, 540 - 400 * k, 980 - 260 * k, 540 + 400 * k, 980 + 260 * k, WHITE, 8, 60 * k)
        self.poly(d, [(540 - 160 * k, 980 + 255 * k), (540 - 260 * k, 980 + 400 * k), (540 - 40 * k, 980 + 255 * k)], WHITE, 8)
        if k > 0.6:
            self.ot(img, 540, 900, "¿DÓNDE ESTÁ", 110, INK, 0)
            self.ot(img, 540, 1040, "EL DINERO?", 120, CARD, 0)
        self.dioni.draw(img, 860, 1760, t, expr="sly", pose="shrug", scale=0.7)
        self.ot(img, 540, 1820, "NIVEL OCULTO", 64, WHITE, 6)

    def camera(self, t, name, lt, u):
        if name in ("rio", "botin"):
            return 1.02 + 0.03 * math.sin(t * 2), 540, 1000
        if name == "intro":
            return 1.0 + 0.1 * smooth(0, 5, lt), 540, 1050
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.0, "boom", 0.8), (0.15, "click", 0.6), (self.w("intro", "hombre") - 0.2, "whoosh", 0.5), (self.w("intro", "vigilarlos"), "boom", 0.8),
                (st("fecha") + 0.2, "pop", 0.5), (self.w("fecha", "vigilante"), "pop", 0.4), (st("golpe") - 0.1, "boom", 0.6),
                (self.t_go, "horn", 0.5), (self.t_go + 0.05, "whoosh", 0.8), (st("botin") + 0.2, "shimmer", 0.6), (self.w("botin", "cambio"), "pop", 0.5),
                (st("huida") - 0.1, "boom", 0.6), (self.w("huida", "brasil") - 0.4, "whoosh", 0.7), (st("rio") + 0.2, "shimmer", 0.5),
                (self.w("rio", "hoteles"), "pop", 0.5), (self.w("rio", "fiestas"), "pop", 0.5), (self.w("rio", "gastos"), "pop", 0.5),
                (st("caida") - 0.1, "boom", 0.6), (st("caida") + 0.6, "horn", 0.5), (self.t_det, "boom", 0.9), (self.w("caida", "narcotraficante"), "pop", 0.5),
                (st("carcel") + 0.2, "click", 0.7), (self.w("carcel", "extraditado"), "whoosh", 0.4), (st("misterio") - 0.1, "boom", 0.6),
                (self.w("misterio", "apareció"), "boom", 0.7), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.3), (self.w("intro", "vigilarlos"), 0.85), (st("fecha"), 0.7), (st("golpe"), 0.95), (st("botin"), 0.85), (st("rio"), 0.95),
                (st("caida"), 1.0), (st("carcel"), 0.55), (st("misterio"), 0.85), (st("cta"), 0.45), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
