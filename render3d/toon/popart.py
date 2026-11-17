"""Estilo «pop-art de cómic» para Content-OS (inspirado en infografías animadas de TikTok).

Fondos de rayos de sol que giran con trama de puntos, escenarios planos con contorno negro,
infografías (contadores, etiquetas, reglas, comparaciones) y onomatopeyas de cómic.
Todo se dibuja por código: no necesita IA de imágenes ni recursos externos.

El personaje y los gags son los del director (director.py); aquí cambia el «mundo».

    python popart.py --out frames/ [--frames 0 1709] [--only ...]
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
from director import BEATS as _BEATS, Director, INK, ease_in, ease_out  # noqa: E402
from compose import smooth  # noqa: E402
from rig import CH, Pose, walk  # noqa: E402
from story import LIGHTNING_T, Story, StorySpec  # noqa: E402

W, H = 1080, 1920

# Paleta por escena: (color rayo A, color rayo B, centro de los rayos)
PALETTES = {
    "rayo": ((88, 60, 160), (60, 40, 120), (540, 700)),
    "siglo": ((40, 200, 230), (230, 60, 170), (540, 900)),
    "ruinas": ((214, 170, 90), (180, 130, 60), (540, 900)),
    "tierra": ((40, 70, 160), (25, 45, 120), (540, 1000)),
    "sol": ((255, 160, 20), (255, 110, 10), (540, 560)),
    "espacio": ((30, 18, 60), (16, 10, 36), (540, 900)),
}

# Onomatopeyas extra del estilo pop-art (además de las del director)
STICKERS = [
    (LIGHTNING_T, 0.9, "¡ZAS!", (760, 420)),
    (7.3, 0.7, "¡CRASH!", (300, 1250)),
    (13.25, 0.6, "¡PUF!", (190, 1080)),
    (14.05, 0.6, "¡PUF!", (900, 1080)),
    (45.6, 1.1, "¡BOOM!", (540, 820)),
]
BEATS = _BEATS


class PopDirector(Director):
    def __init__(self, story):
        super().__init__(story)
        r = random.Random(33)
        # trama de puntos (más densa en los bordes)
        yy, xx = np.mgrid[0:H, 0:W]
        cell = 18
        cx, cy = (xx // cell) * cell + cell / 2, (yy // cell) * cell + cell / 2
        dist = np.sqrt(((cx - W / 2) / (W / 2)) ** 2 + ((cy - H / 2) / (H / 2)) ** 2)
        rad = (2.0 + 4.5 * np.clip(dist - 0.25, 0, 1)) * (dist > 0.2)
        dots = (np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) < rad).astype(np.uint8) * 60
        self.halftone = Image.fromarray(np.dstack([np.zeros_like(dots)] * 3 + [dots]).astype(np.uint8), "RGBA")
        # rascacielos de cómic
        self.skyline = []
        x = -40
        cols = [(230, 60, 120), (250, 190, 40), (60, 170, 230), (130, 80, 200), (40, 190, 140), (240, 110, 40)]
        while x < W + 40:
            w = r.uniform(70, 150)
            self.skyline.append((x, w, r.uniform(250, 700), r.choice(cols), r.random()))
            x += w + r.uniform(-10, 12)
        # continentes (manchas en longitud/latitud)
        self.continents = []
        for i in range(6):
            lon, lat = i * 60 + r.uniform(-15, 15), r.uniform(-40, 45)
            base = r.uniform(20, 32)
            p1, p2, p3 = r.uniform(0, 6.28), r.uniform(0, 6.28), r.uniform(0, 6.28)
            pts = []
            for k in range(40):
                a = k * 2 * math.pi / 40
                rad = base * (1 + 0.28 * math.sin(2 * a + p1) + 0.16 * math.sin(3 * a + p2) + 0.08 * math.sin(5 * a + p3))
                pts.append((rad, math.degrees(a)))
            self.continents.append((lon, lat, pts))
        self.spots = [(r.uniform(0, 6.28), r.uniform(0.15, 0.8), r.uniform(0.05, 0.11)) for _ in range(12)]
        self.clouds = [(r.uniform(0, W), r.uniform(80, 520), r.uniform(0.8, 1.5), r.uniform(10, 30)) for _ in range(7)]
        self.heads = [(i % 5, i // 5) for i in range(20)]

    # ───────── piezas de dibujo ─────────
    def sunburst(self, name, t, zoom=1.0):
        a, b, (cx, cy) = PALETTES[name]
        img = Image.new("RGB", (W, H), b)
        d = ImageDraw.Draw(img)
        n = 28
        rot = t * 0.12
        R = 2600
        for i in range(0, n, 2):
            a0 = rot + i * 2 * math.pi / n
            a1 = rot + (i + 1) * 2 * math.pi / n
            d.polygon([(cx, cy), (cx + math.cos(a0) * R, cy + math.sin(a0) * R), (cx + math.cos(a1) * R, cy + math.sin(a1) * R)], fill=a)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([cx - 360, cy - 360, cx + 360, cy + 360], fill=(255, 250, 220, 90))
        img = img.convert("RGBA")
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
        return img

    def tag(self, d, x, y, text, size=56, fill=(255, 255, 255, 255), color=INK, k=1.0):
        if k <= 0:
            return
        f = self.font(int(size * (0.6 + 0.4 * ease_out(k))))
        w = d.textlength(text, font=f)
        pad = size * 0.35
        box = [x - w / 2 - pad, y - size * 0.62, x + w / 2 + pad, y + size * 0.62]
        d.rounded_rectangle([box[0] + 8, box[1] + 8, box[2] + 8, box[3] + 8], 18, fill=(0, 0, 0, 120))
        d.rounded_rectangle(box, 18, fill=fill, outline=INK, width=6)
        d.text((x, y), text, font=f, fill=color, anchor="mm")

    def sticker(self, d, x, y, text, t0, t, dur):
        k = (t - t0) / dur
        if not 0 <= k < 1:
            return
        s = ease_out(min(1, k / 0.15)) * (1 - 0.15 * k)
        f = self.font(int(120 * s))
        w = d.textlength(text, font=f)
        pts = []
        for i in range(20):
            a = i * math.pi / 10 + 0.2
            rr = (w / 2 + 50) if i % 2 == 0 else (w / 2 + 10)
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr * 0.55))
        d.polygon([(px + 10, py + 10) for px, py in pts], fill=(0, 0, 0, 140))
        d.polygon(pts, fill=(255, 255, 255, 255), outline=INK, width=7)
        d.text((x, y), text, font=f, fill=(230, 30, 40, 255), anchor="mm", stroke_width=6, stroke_fill=INK)

    def skyline_draw(self, d, ground, t, mode="hoy", k=0.0):
        for i, (x, w, h, col, rv) in enumerate(self.skyline):
            hh = h
            c = col
            if mode == "futuro":
                hh = h * (1 + 0.9 * k * (0.5 + rv))
                c = tuple(int(c[j] * (1 - 0.5 * k) + (40, 230, 255)[j] * 0.5 * k) for j in range(3))
            elif mode == "ruina":
                hh = h * (0.35 + 0.35 * rv)
                c = tuple(int(v * 0.45 + 60) for v in col)
            top = ground - hh
            if mode == "ruina":
                jag = [(x, top + 30), (x + w * 0.3, top), (x + w * 0.5, top + 45), (x + w * 0.75, top + 10), (x + w, top + 55)]
                d.polygon(jag + [(x + w, ground), (x, ground)], fill=(*c, 255), outline=INK, width=6)
                d.line([(x + w * 0.2, top + 40), (x + w * 0.25, ground - 20)], fill=(70, 140, 60, 255), width=10)  # enredadera
            else:
                d.rectangle([x, top, x + w, ground], fill=(*c, 255), outline=INK, width=6)
                for wy in range(int(top + 25), int(ground - 30), 44):
                    for wx in range(int(x + 16), int(x + w - 26), 34):
                        lit = (wx * 7 + wy * 3 + int(t * 2)) % 5 != 0
                        d.rectangle([wx, wy, wx + 16, wy + 22], fill=(255, 240, 160, 255) if lit else (40, 40, 60, 255))
            if mode == "futuro" and k > 0.4:
                d.line([(x + 6, top + 6), (x + w - 6, top + 6)], fill=(120, 255, 255, 255), width=8)
        d.rectangle([0, ground, W, H], fill=(70, 70, 90, 255), outline=INK, width=6)
        for xx in range(-200, W + 200, 200):
            d.rectangle([xx + (t * 0) % 200, ground + 70, xx + 110, ground + 84], fill=(240, 220, 120, 255))

    def cloud(self, d, x, y, s, col=(90, 80, 120)):
        for dx, dy, r in ((-60, 10, 60), (0, -20, 80), (70, 5, 65), (130, 20, 45)):
            d.ellipse([x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s], fill=(*col, 255), outline=INK, width=6)

    def comic_bolt(self, d, t):
        k = (t - LIGHTNING_T) / 0.3
        if not 0 <= k < 1:
            return
        pts = [(600, -40), (470, 420), (580, 440), (430, 900), (560, 910), (520, 1040), (720, 600), (600, 590), (730, 120)]
        d.polygon([(x + 12, y + 12) for x, y in pts], fill=(0, 0, 0, 160))
        d.polygon(pts, fill=(255, 235, 40, 255), outline=INK, width=8)

    def globe(self, img, cx, cy, R, t, lt):
        d = ImageDraw.Draw(img, "RGBA")
        ice = smooth(3.0, 4.2, lt) * (1 - smooth(5.6, 6.4, lt))
        desert = smooth(7.3, 10.5, lt)
        merge = smooth(4.3, 7.3, lt)
        ocean = tuple(int(v) for v in np.array((40, 140, 230)) * (1 - desert) + np.array((200, 130, 60)) * desert)
        ocean = tuple(int(v * (1 - ice) + w * ice) for v, w in zip(ocean, (180, 220, 245)))
        land = tuple(int(v) for v in np.array((70, 190, 80)) * (1 - desert) + np.array((150, 70, 30)) * desert)
        land = tuple(int(v * (1 - ice) + 250 * ice) for v in land)
        d.ellipse([cx - R + 14, cy - R + 14, cx + R + 14, cy + R + 14], fill=(0, 0, 0, 120))
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(*ocean, 255), outline=INK, width=10)
        rot = lt * 20
        for i, (lon, lat, pts) in enumerate(self.continents):
            lon_m = lon * (1 - merge) + 180 * merge + (i - 2.5) * 9 * merge
            lat_m = lat * (1 - merge) + 10 * merge
            poly, vis = [], 0
            for rad, ang in pts:
                la = math.radians(lat_m + rad * math.sin(math.radians(ang)) * 0.8)
                lo = math.radians(lon_m + rad * math.cos(math.radians(ang)) + rot)
                x3 = math.cos(la) * math.sin(lo)
                z3 = math.cos(la) * math.cos(lo)
                poly.append((cx + x3 * R * 0.97, cy - math.sin(la) * R * 0.97))
                vis += z3 > 0
            if vis > len(pts) * 0.6:
                d.polygon(poly, fill=(*land, 255), outline=INK, width=6)
        d.chord([cx - R * 0.8, cy - R * 0.85, cx + R * 0.2, cy + R * 0.15], 200, 260, fill=(255, 255, 255, 90))

    # ───────── fotograma ─────────
    def frame(self, f):
        st = self.st
        t = f / st.spec.fps
        name = st.scene(t)
        u, sh = st.local(t)
        lt = t - sh["start"]
        img = self.sunburst(name, t)
        d = ImageDraw.Draw(img, "RGBA")
        if name == "rayo":
            for x, y, s, sp in self.clouds:
                self.cloud(d, (x + t * sp) % (W + 300) - 150, y, s)
            self.skyline_draw(d, 1640, t)
            for x, y, sp in self.rain:
                yy = (y + t * 1900 * sp) % (H + 200) - 100
                xx = (x - t * 260 * sp) % W
                d.line([(xx, yy), (xx - 10 * sp, yy + 46 * sp)], fill=(220, 230, 255, 160), width=3)
            self.comic_bolt(d, t)
        elif name == "siglo":
            self.skyline_draw(d, 1640, t, "futuro", smooth(0.5, 6.5, lt))
        elif name == "ruinas":
            self.skyline_draw(d, 1640, t, "ruina")
            for x, y, r_, ph in self.dust:
                yy = (y - lt * 25) % H
                d.ellipse([x - r_, yy - r_, x + r_, yy + r_], fill=(255, 240, 200, 140))
        elif name == "tierra":
            for x, y, r_, ph in self.stars:
                a = int(140 + 110 * math.sin(t * 3 + ph))
                d.ellipse([x - r_, y - r_, x + r_, y + r_], fill=(255, 255, 255, max(0, a)))
        elif name == "sol":
            grow = smooth(0.0, 0.62, u)
            if lt < 6.6:
                R = 170 + 650 * grow + 12 * math.sin(lt * 6)
                col = tuple(int(v) for v in np.array((255, 220, 60)) * (1 - grow) + np.array((235, 60, 30)) * grow)
                d.ellipse([540 - R, 640 - R, 540 + R, 640 + R], fill=(*col, 255), outline=INK, width=10)
                for a0, rr_, sz in self.spots:  # manchas solares repartidas
                    a = a0 + lt * 0.15
                    sx, sy = 540 + math.cos(a) * R * rr_, 640 + math.sin(a) * R * rr_ * 0.85
                    d.ellipse([sx - R * sz, sy - R * sz * 0.75, sx + R * sz, sy + R * sz * 0.75], fill=(190, 40, 20, 150))
            else:
                img = self.sunburst("espacio", t)
                d = ImageDraw.Draw(img, "RGBA")
                for x, y, r_, ph in self.stars:
                    d.ellipse([x - r_, y - r_, x + r_, y + r_], fill=(255, 255, 255, 200))
                d.ellipse([530, 630, 550, 650], fill=(245, 250, 255, 255), outline=INK, width=3)
            # suelo agrietado
            d.rectangle([0, 1600, W, H], fill=(120, 40, 20, 255), outline=INK, width=8)
            for k in range(12):
                x0 = k * 95 + 20
                d.line([(x0, 1610), (x0 + 30, 1700), (x0 - 10, 1800), (x0 + 25, 1920)], fill=(255, 150, 30, 255), width=7)
        else:
            for x, y, r_, ph in self.stars:
                a = int(140 + 110 * math.sin(t * 3 + ph))
                d.ellipse([x - r_, y - r_, x + r_, y + r_], fill=(255, 255, 255, max(0, a)))
        img.alpha_composite(self.halftone)
        d = ImageDraw.Draw(img, "RGBA")
        if name == "tierra":
            self.pop_earth(img, d, t, lt, u)
        else:
            getattr(self, "act_" + name)(img, d, t, lt, u)
        self.infographics(img, d, name, t, lt, u)
        for t0, dur, text, (x, y) in STICKERS:
            self.sticker(d, x, y, text, t0, t, dur)
        out = img.convert("RGB")
        flash = 0.0
        if LIGHTNING_T <= t < LIGHTNING_T + 0.25:
            flash = 0.7 * (1 - (t - LIGHTNING_T) / 0.25)
        if 0 <= t - 45.6 < 0.4:
            flash = max(flash, 1 - (t - 45.6) / 0.4)
        if flash > 0:
            out = Image.blend(out, Image.new("RGB", (W, H), (255, 255, 255)), flash)
        z, sx, sy = self.camera(t)
        z = max(z, W / (W - 2 * abs(sx) - 2), H / (H - 2 * abs(sy) - 2))
        z *= 1.0 + 0.05 * (1 - u)  # alejamiento lento y constante dentro de cada escena
        cw, chh = W / z, H / z
        out = out.resize((W, H), Image.BILINEAR, box=(W / 2 - cw / 2 - sx, H / 2 - chh / 2 - sy, W / 2 + cw / 2 - sx, H / 2 + chh / 2 - sy))
        return self.whip(out, t)

    def draw_year(self, d, year, t):
        self.tag(d, 540, 530, f"AÑO {year}", size=70, fill=(255, 230, 60, 255))

    def infographics(self, img, d, name, t, lt, u):
        if name == "ruinas":
            # 20 generaciones: fila de cabecitas que se apagan una a una
            k = smooth(0.3, 6.5, lt)
            gone = int(20 * k)
            x0, y0 = 300, 600
            self.tag(d, 540, 530, "20 GENERACIONES", size=50, fill=(255, 230, 60, 255), k=min(1, lt / 0.3))
            for i, (cx_, cy_) in enumerate(self.heads):
                x, y = x0 + cx_ * 120, y0 + cy_ * 90 + 40
                col = (246, 244, 240, 255) if i >= gone else (120, 120, 130, 255)
                d.ellipse([x - 32, y - 30, x + 32, y + 30], fill=col, outline=INK, width=5)
                if i >= gone:
                    d.ellipse([x - 14, y - 8, x - 6, y], fill=INK)
                    d.ellipse([x + 6, y - 8, x + 14, y], fill=INK)
                else:
                    d.line([(x - 15, y - 6), (x - 5, y - 6)], fill=INK, width=4)
                    d.line([(x + 5, y - 6), (x + 15, y - 6)], fill=INK, width=4)
        if name == "espacio" and 1.5 < lt < 5.5:
            self.tag(d, 820, 760, "TÚ", size=60, fill=(255, 230, 60, 255), k=min(1, (lt - 1.5) / 0.3))
            d.line([(760, 800), (660, 880)], fill=INK, width=8)
        if name == "sol" and 1.2 < lt < 6.4:
            k = min(1, (lt - 1.2) / 0.3)
            self.tag(d, 280, 1520, "SOL HOY", size=40, k=k)
            d.ellipse([255, 1420, 305, 1470], fill=(255, 220, 60, 255), outline=INK, width=5)
            if lt > 3.0:
                self.tag(d, 790, 1520, "+100 VECES MAYOR", size=40, fill=(255, 120, 60, 255), k=min(1, (lt - 3.0) / 0.3))

    def pop_earth(self, img, d, t, lt, u):
        scale = 1.9 - 1.05 * ease_out(lt / 4.0)
        R = 430 * scale
        cx, cy = 540, 1150 + 380 * (scale - 0.85)
        self.globe(img, cx, cy, R, t, lt)
        d = ImageDraw.Draw(img, "RGBA")
        p = walk(Pose(face="asombrado"), t, speed=1.6, amp=20)
        ice = smooth(3.0, 4.2, lt) * (1 - smooth(5.6, 6.4, lt))
        desert = smooth(7.3, 10.5, lt)
        if ice > 0.3:
            p.face, p.shiver = "triste", 1.0
            for x, y, r_, sp in self.snow:
                yy = (y + lt * 160 * sp) % H
                d.ellipse([x - r_, yy - r_, x + r_, yy + r_], fill=(255, 255, 255, int(230 * ice)))
        if desert > 0.3:
            p.face, p.sweat = "sorprendido", True
            p.arm_r = 120 + 25 * math.sin(t * 14)
        self.put(img, p, cx, cy - R + 8, max(0.16, 0.3 * scale), t)
        # infografías de la Tierra
        if 4.3 < lt < 7.3:
            self.tag(d, 540, 540, "UN SOLO CONTINENTE", size=52, fill=(120, 230, 120, 255), k=min(1, (lt - 4.3) / 0.3))
        if lt > 7.3:
            lvl = 1 - smooth(7.6, 10.4, lt)
            x0, y0, h0 = 940, 1450, 520
            d.rectangle([x0 - 40, y0 - h0, x0 + 40, y0], fill=(255, 255, 255, 255), outline=INK, width=6)
            if h0 * lvl > 8:
                d.rectangle([x0 - 34, y0 - h0 * lvl, x0 + 34, y0 - 6], fill=(40, 140, 230, 255))
            for k in range(0, 11):
                y = y0 - h0 * k / 10
                d.line([(x0 - 40, y), (x0 - (10 if k % 5 else 0), y)], fill=INK, width=5)
            self.tag(d, x0 - 110, y0 + 70, f"OCÉANOS {int(100 * lvl)} %", size=42, fill=(255, 255, 255, 255))


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
    dr = PopDirector(st)
    os.makedirs(a.out, exist_ok=True)
    f0, f1 = a.frames if a.frames else (0, st.frames - 1)
    frames = a.only or list(range(f0, min(f1, st.frames - 1) + 1, a.every))
    t0 = time.time()
    for i, fr in enumerate(frames):
        dr.frame(fr).save(os.path.join(a.out, f"f{fr:05d}.jpg"), quality=92)
        if i % 60 == 0:
            print(f"[popart] fotograma {fr} ({st.scene(fr / spec.fps)}) · {time.time() - t0:.0f} s", flush=True)
    print(f"[popart] {len(frames)} fotogramas en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
