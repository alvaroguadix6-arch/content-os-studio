"""Director del vídeo «¿Qué pasaría si fueras inmortal?» (versión dinámica).

Coreografía fotograma a fotograma: gags, personajes secundarios, accesorios, cámara con
golpes de zoom, temblores y barridos entre escenas. Todo en 2D (Pillow + NumPy), sin Blender.

    python director.py --out frames/ [--frames 0 1709] [--only 30 160 ...]
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "inmortal"))
from compose import Compositor, smooth  # noqa: E402
from rig import CH, CW, GROUND, Pose, draw_pose, walk  # noqa: E402
from story import LIGHTNING_T, Story, StorySpec  # noqa: E402
from overlay import _font  # noqa: E402

W, H = 1080, 1920
INK = (22, 20, 24, 255)

# Efectos de sonido sincronizados con la acción (los usa sound.py)
BEATS = [
    (LIGHTNING_T, "zap"), (2.7, "boing"), (3.3, "pop"), (4.75, "fall"), (5.3, "bonk"), (5.85, "crash"),
    (6.9, "car"), (7.3, "bonk"), (7.35, "fly"), (8.1, "thump"), (8.35, "sparkle"),
    (9.2, "pop"), (9.35, "pop"), (11.5, "pop"), (12.5, "pop"), (13.2, "sparkle"), (14.0, "sparkle"),
    (16.0, "whoosh"),
] + [(18.8 + i * 0.22, "thump") for i in range(11)] + [
    (21.5, "thump"), (24.0, "sparkle"),
    (31.2, "whoosh"), (35.6, "whoosh"),
    (40.75, "fall"), (41.0, "cling"), (45.6, "crash"), (45.95, "fly"),
    (49.6, "fly"), (53.9, "pop"),
]


def ease_out(x):
    x = min(1, max(0, x))
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = min(1, max(0, x))
    return x * x


def bounce(x):
    """0→1 con rebote al final (aparición tipo dibujos)."""
    x = min(1, max(0, x))
    return 1 + 0.25 * math.sin(x * math.pi * 1.5) * (1 - x) if x > 0.5 else ease_out(x * 2) * 1.0


class Director(Compositor):
    draw_char = False  # el personaje lo anima el director (la clase base solo pone fondo y efectos)

    def __init__(self, story):
        super().__init__(story)
        r = random.Random(21)
        self.graves = sorted([(r.uniform(60, 1020), r.uniform(1480, 1860), r.uniform(0.55, 1.0), 18.8 + i * 0.22) for i in range(11)], key=lambda g: g[1])
        self.snow = [(r.uniform(0, W), r.uniform(0, H), r.uniform(2, 5), r.uniform(0.5, 1.5)) for _ in range(160)]
        self.smoke = [(r.uniform(-60, 60), r.uniform(0, 1), r.uniform(18, 40)) for _ in range(14)]
        self.debris = [(r.uniform(-1, 1), r.uniform(-1.6, -0.6), r.uniform(-8, 8), r.choice([(20, 20, 24), (240, 240, 240)])) for _ in range(14)]
        # planeta: recorte circular de la Tierra del fondo
        tierra = Image.open(os.path.join(os.path.dirname(__file__), "fondos", "tierra.jpg")).convert("RGB")
        disk = tierra.crop((40, 460, 1040, 1460)).convert("RGBA")
        mask = Image.new("L", disk.size, 0)
        ImageDraw.Draw(mask).ellipse([30, 30, 970, 970], fill=255)
        disk.putalpha(mask.filter(ImageFilter.GaussianBlur(6)))
        self.planet = disk
        self.star_bg = Image.new("RGB", (W, H), (3, 5, 10))
        d = ImageDraw.Draw(self.star_bg)
        for _ in range(1100):
            x, y = r.uniform(0, W), r.uniform(0, H)
            s = r.choice([0.6, 0.8, 1, 1.4, 2])
            a = r.randint(80, 255)
            d.ellipse([x - s, y - s, x + s, y + s], fill=(a, a, min(255, a + 20)))
        self.fonts = {}

    # ───────── utilidades ─────────
    def font(self, size):
        size = max(10, int(size))
        if size not in self.fonts:
            self.fonts[size] = _font(size)
        return self.fonts[size]

    def put(self, img, pose, x, ground, scale, t, rot=0.0):
        ch = draw_pose(pose, t)
        w, h = int(CW * scale), int(CH * scale)
        ch = ch.resize((w, h), Image.BILINEAR)
        gy = GROUND * scale
        if rot:
            big = Image.new("RGBA", (int(w * 1.6), int(h * 1.6)), (0, 0, 0, 0))
            big.alpha_composite(ch, (int(w * 0.3), int(h * 0.3)))
            ch = big.rotate(-rot, resample=Image.BICUBIC, center=(big.width / 2, big.height / 2))
            img.alpha_composite(ch, (int(x - ch.width / 2), int(ground - gy - h * 0.3 + (h / 2 - gy) * 0)))
            return
        img.alpha_composite(ch, (int(x - w / 2), int(ground - gy)))

    def burst(self, d, cx, cy, r, text, t0, t):
        k = ease_out((t - t0) / 0.15)
        rr = r * (0.4 + 0.6 * k)
        pts = []
        for i in range(24):
            a = i * math.pi / 12
            rad = rr if i % 2 == 0 else rr * 0.62
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad * 0.8))
        d.polygon(pts, fill=(255, 214, 40, 255), outline=INK, width=8)
        f = self.font(int(110 * (0.5 + 0.5 * k)))
        d.text((cx, cy), text, font=f, fill=(230, 40, 30, 255), anchor="mm", stroke_width=8, stroke_fill=INK)

    def bubble(self, d, cx, cy, text, scale=1.0):
        w, h = 190 * scale, 130 * scale
        d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 40, fill=(255, 255, 255, 255), outline=INK, width=7)
        d.polygon([(cx - 20, cy + h / 2 - 4), (cx + 10, cy + h / 2 - 4), (cx - 30, cy + h / 2 + 45)], fill=(255, 255, 255, 255), outline=INK)
        d.text((cx, cy), text, font=self.font(int(90 * scale)), fill=INK, anchor="mm")

    def piano(self, d, cx, by, s=1.0):
        w, h = 520 * s, 300 * s
        d.rounded_rectangle([cx - w / 2, by - h, cx + w / 2, by - 70 * s], 18, fill=(28, 26, 30, 255), outline=INK, width=8)
        for k in range(14):
            x = cx - w / 2 + 30 * s + k * (w - 60 * s) / 14
            d.rectangle([x, by - 150 * s, x + (w - 60 * s) / 14 - 4, by - 90 * s], fill=(245, 245, 240, 255))
        for sx in (-1, 1):
            d.rectangle([cx + sx * (w / 2 - 40 * s) - 12 * s, by - 70 * s, cx + sx * (w / 2 - 40 * s) + 12 * s, by], fill=(28, 26, 30, 255), outline=INK, width=5)

    def car(self, d, cx, by, s=1.0):
        w = 560 * s
        d.rounded_rectangle([cx - w / 2, by - 170 * s, cx + w / 2, by - 50 * s], 50, fill=(220, 40, 40, 255), outline=INK, width=9)
        d.rounded_rectangle([cx - w / 4, by - 260 * s, cx + w / 5, by - 160 * s], 40, fill=(220, 40, 40, 255), outline=INK, width=9)
        d.rounded_rectangle([cx - w / 4 + 25 * s, by - 240 * s, cx + w / 5 - 25 * s, by - 175 * s], 20, fill=(170, 220, 255, 255), outline=INK, width=6)
        for sx in (-0.3, 0.3):
            x = cx + sx * w
            d.ellipse([x - 60 * s, by - 110 * s, x + 60 * s, by + 10 * s], fill=(30, 30, 34, 255), outline=INK, width=8)
            d.ellipse([x - 22 * s, by - 72 * s, x + 22 * s, by - 28 * s], fill=(190, 190, 195, 255))
        for k in range(4):  # líneas de velocidad
            y = by - 60 * s - k * 50 * s
            d.line([(cx - w / 2 - 60 - k * 40, y), (cx - w / 2 - 260 - k * 60, y)], fill=(255, 255, 255, 200), width=8)

    def grave(self, d, x, y, s, rise):
        if rise <= 0:
            return
        h = 210 * s * min(1, rise * 1.15)
        w = 130 * s
        d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], int(60 * s), fill=(120, 124, 130, 255), outline=INK, width=max(3, int(8 * s)))
        if rise > 0.8:
            d.line([(x, y - h + 40 * s), (x, y - h + 120 * s)], fill=INK, width=max(2, int(9 * s)))
            d.line([(x - 30 * s, y - h + 65 * s), (x + 30 * s, y - h + 65 * s)], fill=INK, width=max(2, int(9 * s)))
        d.ellipse([x - w * 0.7, y - 18 * s, x + w * 0.7, y + 18 * s], fill=(70, 56, 40, 200))

    def ring(self, img, cx, cy, r, alpha):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 240, 220, int(255 * alpha)), width=60)
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(12)))

    # ───────── cámara ─────────
    def camera(self, t):
        z, sx, sy = 1.0, 0.0, 0.0
        for t0, amp in ((0.05, 0.10), (LIGHTNING_T, 0.10), (3.3, 0.08), (5.3, 0.14), (7.3, 0.12), (8.1, 0.06), (13.2, 0.05),
                        (16.0, 0.06), (21.5, 0.05), (41.0, 0.08), (45.6, 0.16)):
            if t >= t0:
                z += amp * math.exp(-(t - t0) * 5)
        for t0, amp, dur in ((LIGHTNING_T, 26, 0.6), (5.3, 34, 0.6), (7.3, 24, 0.5), (8.1, 14, 0.3), (45.6, 40, 1.4)):
            if t0 <= t < t0 + dur:
                k = 1 - (t - t0) / dur
                sx += math.sin(t * 83) * amp * k
                sy += math.cos(t * 71) * amp * k
        return z, sx, sy

    # ───────── fotograma ─────────
    def frame(self, f):
        st = self.st
        t = f / st.spec.fps
        name = st.scene(t)
        u, sh = st.local(t)
        lt = t - sh["start"]
        if name == "tierra":
            img = self.earth(t, lt, u)
        else:
            base = super().frame(f)  # fondo + partículas base (lo de la versión anterior)
            img = base.convert("RGBA")
            img = self.base_overrides(img, name, t, lt, u)
        d = ImageDraw.Draw(img, "RGBA")
        getattr(self, "act_" + name)(img, d, t, lt, u)
        out = img.convert("RGB")
        # cámara: zoom de golpe + temblor
        z, sx, sy = self.camera(t)
        # zoom mínimo para que el temblor no muestre bordes vacíos
        z = max(z, W / (W - 2 * abs(sx) - 2), H / (H - 2 * abs(sy) - 2))
        if z != 1.0 or sx or sy:
            cw, chh = W / z, H / z
            box = (W / 2 - cw / 2 - sx, H / 2 - chh / 2 - sy, W / 2 + cw / 2 - sx, H / 2 + chh / 2 - sy)
            out = out.resize((W, H), Image.BILINEAR, box=box)
        out = self.whip(out, t)
        return out

    def base_overrides(self, img, name, t, lt, u):
        return img

    def whip(self, out, t):
        """Barrido rápido entre escenas (desenfoque de movimiento horizontal)."""
        for s in self.st.shots[1:]:
            dt = t - s["start"]
            if -0.18 <= dt < 0.18:
                k = 1 - abs(dt) / 0.18
                shift = int(260 * k) * (1 if dt < 0 else -1)
                arr = np.asarray(out).astype(np.float32)
                acc = np.zeros_like(arr)
                n = 7
                for i in range(n):
                    acc += np.roll(arr, int(shift * i / n), axis=1)
                out = Image.fromarray((acc / n).astype(np.uint8))
        return out

    # ───────── escenas: el personaje ya no lo dibuja la clase base ─────────
    def char(self, *a, **k):  # la base dibujaba al personaje; aquí solo se usa para fantasmas
        return super().char(*a, **k)

    def act_rayo(self, img, d, t, lt, u):
        x, g, s = 540, 1800, 0.62
        p = Pose(face="normal")
        rot = 0.0
        if t < LIGHTNING_T:
            walk(p, t, speed=1.4, amp=14)
            p.face = "sonrisa"
        elif t < 2.6:
            p.charred, p.hair, p.face, p.shiver = 1.0, "frizz", "sorprendido", 1.0
            p.arm_l = p.arm_r = 40
            for dx, ph, r in self.smoke:  # humo
                k = (lt * 0.8 + ph) % 1
                yy = g - 0.62 * CH * 0.8 - k * 260
                d.ellipse([x + dx - r * (1 + k), yy - r * (1 + k), x + dx + r * (1 + k), yy + r * (1 + k)], fill=(90, 90, 95, int(150 * (1 - k))))
        elif t < 3.2:
            k = (t - 2.6) / 0.6
            p.charred = max(0, 1 - k * 1.6)
            p.hair = "frizz" if k < 0.5 else "none"
            p.face = "dormido"
            p.lean = 14 * math.sin(k * math.pi * 6) * (1 - k)
            p.squash = 1 + 0.12 * math.sin(k * math.pi * 4) * (1 - k)
        elif t < 4.7:
            p.face, p.arm_l, p.arm_r, p.elbow_l, p.elbow_r = "asombrado", 70, 70, 60, 60
            self.bubble(d, x + 150, g - 0.62 * CH * 0.95, "?!", max(0.15, ease_out((t - 3.2) / 0.2)))
        elif t < 5.3:
            p.face, p.head_tilt = "sorprendido", -6
            k = ease_in((t - 4.7) / 0.6)
            r = 80 + 200 * k
            d.ellipse([x - r, g - r * 0.18, x + r, g + r * 0.18], fill=(0, 0, 0, int(140 * k)))
        if 4.7 <= t < 5.3:
            self.put(img, p, x, g, s, t)
            k = ease_in((t - 4.7) / 0.6)
            self.piano(d, x, -200 + (g + 200) * k, 1.0)
            return
        if 5.3 <= t < 5.85:
            self.piano(d, x, g, 1.0 + 0.1 * math.sin((t - 5.3) * 40) * (1 - (t - 5.3) / 0.55))
            self.burst(d, x + 250, g - 520, 230, "¡BONK!", 5.3, t)
            return
        if 5.85 <= t < 7.0:
            k = (t - 5.85)
            for dx, dy, rot_, col in self.debris:
                px = x + dx * 600 * k
                py = g - 200 + dy * 700 * k + 1400 * k * k
                d.rectangle([px - 30, py - 15, px + 30, py + 15], fill=(*col, 255), outline=INK, width=4)
            p.face, p.stars = "mareado", t
            p.squash = 1 + 0.35 * math.sin(min(1, k / 0.45) * math.pi) * (1 - min(1, k / 0.45)) if k < 0.45 else 1.0
            p.lean = 6 * math.sin(t * 6)
        if 6.9 <= t < 7.3:
            p.face = "sorprendido"
            k = (t - 6.9) / 0.4
            self.put(img, p, x, g, s, t)
            self.car(d, -400 + (x - 120 + 400) * ease_in(k), g + 40, 0.9)
            return
        if 7.3 <= t < 8.1:
            k = (t - 7.3) / 0.8
            px = x + 200 * math.sin(k * math.pi)
            py = g - 1300 * 4 * k * (1 - k)
            rot = 720 * k
            p.face, p.arm_l, p.arm_r, p.leg_l, p.leg_r = "sorprendido", 120, 120, 30, 30
            self.car(d, x + 200 + 1600 * k, g + 40, 0.9)
            self.put(img, p, px, py, s, t, rot=rot)
            return
        if t >= 8.1:
            k = (t - 8.1)
            if k < 0.25:
                p.squash = 0.75 + k
                r = 140 + 600 * k
                d.ellipse([x - r, g - 50 - r * 0.2, x + r, g - 50 + r * 0.2], fill=(200, 190, 170, int(160 * (1 - k * 4))))
            else:
                p.face, p.arm_l, p.arm_r = "sonrisa", 150, 150
                p.lean = 4 * math.sin(t * 9)
                for i in range(6):  # destellos
                    a = i * math.pi / 3 + t * 3
                    rr = 300 + 30 * math.sin(t * 10 + i)
                    cx, cy = x + math.cos(a) * rr, g - 420 + math.sin(a) * rr * 0.6
                    d.polygon([(cx, cy - 26), (cx + 8, cy - 8), (cx + 26, cy), (cx + 8, cy + 8), (cx, cy + 26), (cx - 8, cy + 8), (cx - 26, cy), (cx - 8, cy - 8)], fill=(255, 240, 150, 230))
        self.put(img, p, x, g, s, t, rot=rot)

    def act_siglo(self, img, d, t, lt, u):
        g, s = 1800, 0.6
        year = int(2026 + 100 * smooth(1.2, 8.5, lt))
        d.text((W / 2, 470), f"AÑO {year}", font=self.font(70), fill=(255, 255, 255, 255), anchor="mm", stroke_width=7, stroke_fill=INK)
        friends = [(175, (60, 90, 160, 255), (240, 200, 40, 255), 13.2), (905, (60, 130, 70, 255), (240, 240, 240, 255), 14.0)]
        for fx, coat, scarf, gone in friends:
            appear = ease_out((t - 9.15) / 0.3)
            if appear <= 0:
                continue
            fp = Pose(face="sonrisa", coat=coat, scarf=scarf)
            if t < 10.5:
                fp.arm_l = fp.arm_r = 120 + 30 * math.sin(t * 12)
            if t >= 11.5:
                fp.hair = "grey"
            if t >= 12.5:
                fp.cane, fp.lean = True, 8 if fx < 540 else -8
            ground = g
            if t >= gone:
                k = (t - gone) / 1.5
                if k > 1:
                    continue
                fp.tint, fp.alpha, fp.face = (170, 210, 255), 0.7 * (1 - k), "sonrisa"
                fp.cane = False
                ground = g - 500 * ease_in(k)
            self.put(img, fp, fx, ground, s * 0.82 * (0.6 + 0.4 * appear), t)
        p = Pose(face="asombrado" if t < 13.0 else "triste")
        if t >= 13.0:
            p.head_tilt = -10 if t < 13.8 else 10
        if t >= 15.5:
            p.head_tilt = 0
            walk(p, t, speed=0.8, amp=6)
        self.put(img, p, 540, g, s, t)
        if lt > 6.5:  # coches voladores por delante
            for k in range(3):
                xx = ((lt - 6.5) * 900 + k * 500) % 1800 - 400
                y = 1150 + k * 90
                d.rounded_rectangle([xx, y, xx + 170, y + 50], 25, fill=(40, 220, 255, 220), outline=INK, width=5)
                d.line([(xx, y + 25), (xx - 260, y + 25)], fill=(120, 240, 255, 150), width=14)

    def act_ruinas(self, img, d, t, lt, u):
        for gx, gy, gs, t0 in self.graves:
            self.grave(d, gx, gy, gs, (t - t0) / 0.25)
        p = Pose(face="triste")
        if t >= 21.5:
            p.sit = True
            self.grave(d, 540, 1830, 1.5, 1.0)
            p.arm_l = p.arm_r = 25
            if t >= 24.0:
                p.tear = (t - 24.0) * 0.8
                p.face = "lloro"
        # fantasmas que suben de las tumbas
        for i, (gx, gy, gs, t0) in enumerate(self.graves):
            tg = 22.0 + (i % 6) * 0.8
            if tg <= t < tg + 2.6:
                k = (t - tg) / 2.6
                gp = Pose(face=["sonrisa", "dormido", "normal"][i % 3], tint=(170, 210, 255), alpha=0.6 * math.sin(math.pi * k))
                self.put(img, gp, gx + 30 * math.sin(t * 2 + i), gy - 260 * k - 40, 0.32 * gs, t)
        self.put(img, p, 540, 1800, 0.6, t)

    def earth(self, t, lt, u):
        img = self.star_bg.copy().convert("RGBA")
        d = ImageDraw.Draw(img, "RGBA")
        for x, y, r, ph in self.stars:
            a = int(120 + 120 * math.sin(t * 3 + ph))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, max(0, a)))
        scale = 1.9 - 1.05 * ease_out(lt / 4.0)  # empieza cerca y se aleja
        R = 470 * scale
        cx, cy = 540, 1150 + 380 * (scale - 0.85)
        planet = self.planet.rotate(lt * 14, resample=Image.BICUBIC)
        pr = Image.fromarray(np.asarray(self.grade_earth(planet.convert("RGB"), lt)).astype(np.uint8)).convert("RGBA")
        pr.putalpha(planet.getchannel("A"))
        size = int(R * 2 * 1000 / 940)
        pr = pr.resize((size, size), Image.BILINEAR)
        img.alpha_composite(pr, (int(cx - size / 2), int(cy - size / 2)))
        # atmósfera
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10], outline=(110, 180, 255, 160), width=18)
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
        # personaje caminando sobre el planeta (como El Principito)
        p = walk(Pose(face="asombrado"), t, speed=1.6, amp=20)
        ice = smooth(3.0, 4.2, lt) * (1 - smooth(5.6, 6.4, lt))
        desert = smooth(7.3, 10.5, lt)
        if ice > 0.3:
            p.face, p.shiver = "triste", 1.0
        if desert > 0.3:
            p.face, p.sweat = "sorprendido", True
            p.arm_r = 120 + 25 * math.sin(t * 14)
            steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(steam)
            for k in range(26):  # vapor de los océanos (nubes difuminadas)
                a = -math.pi / 2 + ((k * 0.618) % 1 - 0.5) * 2.6
                ph = (lt * 0.35 + k * 0.071) % 1
                rr = R + ph * 260
                x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
                rad = 25 + 70 * ph
                sd.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(235, 235, 240, int(70 * desert * (1 - ph))))
            img.alpha_composite(steam.filter(ImageFilter.GaussianBlur(22)))
        cs = max(0.16, 0.3 * scale)
        self.put(img, p, cx, cy - R + 8, cs, t)
        if ice > 0.05:
            for x, y, r, sp in self.snow:
                yy = (y + lt * 160 * sp) % H
                d.ellipse([x - r, yy - r, x + r, yy + r], fill=(255, 255, 255, int(220 * ice)))
        return img

    def act_tierra(self, img, d, t, lt, u):
        pass

    def act_sol(self, img, d, t, lt, u):
        g, s = 1800, 0.55
        p = Pose(face="asombrado", sweat=lt > 1.0)
        if 40.7 <= t < 41.0:
            k = ease_in((t - 40.7) / 0.3)
            gx, gy = 540, -100 + (g - 0.55 * CH * 0.86 + 100) * k
            for sx in (-1, 1):
                d.rounded_rectangle([gx + sx * 38 - 27, gy - 18, gx + sx * 38 + 27, gy + 16], 8, fill=(15, 15, 20, 255), outline=INK, width=4)
        if t >= 41.0:
            p.glasses, p.face = True, "sonrisa"
            p.arm_l, p.arm_r, p.elbow_l, p.elbow_r = 25, 25, 95, 95  # brazos cruzados, chulo
            if t < 41.5:
                cx, cy = 540 + 60, g - 0.55 * CH * 0.9
                k = (t - 41.0) / 0.5
                d.polygon([(cx, cy - 40 * k), (cx + 10, cy - 10), (cx + 40 * k, cy), (cx + 10, cy + 10), (cx, cy + 40 * k), (cx - 10, cy + 10), (cx - 40 * k, cy), (cx - 10, cy - 10)], fill=(255, 255, 255, 240))
        if t >= 43.5:
            p.face = "sorprendido"
            p.arm_r, p.elbow_r = 130 + 25 * math.sin(t * 16), 30  # se abanica
        if t >= 45.6:
            k = (t - 45.6)
            self.ring(img, 540, 560, 100 + 2600 * k, max(0, 1 - k / 1.0))
            if k > 0.35:
                kk = (k - 0.35) / 0.9
                if kk < 1:
                    p.face, p.glasses = "sorprendido", kk < 0.3
                    p.arm_l = p.arm_r = 150
                    self.put(img, p, 540 + 900 * ease_in(kk), g - 1500 * ease_out(kk), s * (1 - 0.5 * kk), t, rot=900 * kk)
                elif 1.2 < k < 3.6:
                    kk2 = (k - 1.2) / 2.4  # a lo lejos, girando
                    self.put(img, Pose(face="sorprendido"), 100 + 900 * kk2, 900 - 200 * kk2, 0.1, t, rot=600 * kk2)
                return
        self.put(img, p, 540, g, s, t)

    def act_espacio(self, img, d, t, lt, u):
        p = Pose(face="triste", arm_l=45, arm_r=45, leg_l=12, leg_r=12)
        enter = ease_out(lt / 2.0)
        scale = (0.5 - 0.3 * smooth(0.25, 1.0, u))
        x = -300 + (540 + 300) * enter
        cy = 860 + (1350 - 860) * smooth(0.3, 1.0, u)
        rot = (1 - enter) * 540 + 8 * math.sin(t * 0.8)
        if lt < 1.0:
            p.face = "sorprendido"
        self.put(img, p, x, cy + 30 * math.sin(t * 1.1) + CH * scale * 0.45, scale, t, rot=rot)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="frames")
    ap.add_argument("--frames", nargs=2, type=int)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--spec")
    ap.add_argument("--only", nargs="*", type=int)
    a, _ = ap.parse_known_args()
    spec = StorySpec.from_json(a.spec) if a.spec else StorySpec()
    st = Story(spec)
    dr = Director(st)
    os.makedirs(a.out, exist_ok=True)
    f0, f1 = a.frames if a.frames else (0, st.frames - 1)
    frames = a.only or list(range(f0, min(f1, st.frames - 1) + 1, a.every))
    t0 = time.time()
    for i, f in enumerate(frames):
        dr.frame(f).save(os.path.join(a.out, f"f{f:05d}.jpg"), quality=92)
        if i % 60 == 0:
            print(f"[director] fotograma {f} ({st.scene(f / spec.fps)}) · {time.time() - t0:.0f} s", flush=True)
    print(f"[director] {len(frames)} fotogramas en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
