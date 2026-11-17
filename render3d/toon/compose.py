"""Compositor 2D del vídeo «¿Qué pasaría si fueras inmortal?» en estilo dibujos animados.

Anima fondos ilustrados (movimiento de cámara), partículas (lluvia, polvo, estrellas),
efectos (rayo, time-lapse, cambio de color de la Tierra, colapso del Sol) y el personaje 2D.
No necesita Blender: Python + Pillow + NumPy.

    python compose.py --out frames/ [--frames 0 1709] [--every 1]
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "inmortal"))
from character import draw  # noqa: E402
from story import LIGHTNING_T, Story, StorySpec  # noqa: E402

W, H = 1080, 1920
MARGIN = 1.16
FONDOS = os.environ.get("FONDOS_DIR", os.path.join(HERE, "fondos"))
BG_FILES = {
    "rayo": "rayo.jpg", "siglo": "siglo.jpg", "ruinas": "ruinas.jpg",
    "tierra": "tierra.jpg", "sol": "sol.jpg", "espacio": "espacio.jpg",
}


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else float(x >= b)
    return t * t * (3 - 2 * t)


class Compositor:
    def __init__(self, story: Story):
        self.st = story
        self.bg = {}
        for k, f in BG_FILES.items():
            im = Image.open(os.path.join(FONDOS, f)).convert("RGB")
            self.bg[k] = im.resize((int(W * MARGIN), int(H * MARGIN)), Image.LANCZOS)
        self.char_cache = {}
        self.rnd = random.Random(9)
        r = self.rnd
        self.rain = [(r.uniform(0, W), r.uniform(0, H), r.uniform(0.6, 1.4)) for _ in range(260)]
        self.dust = [(r.uniform(0, W), r.uniform(0, H), r.uniform(1.5, 4.5), r.uniform(0, 6.28)) for _ in range(90)]
        self.stars = [(r.uniform(0, W), r.uniform(0, H), r.uniform(1, 2.6), r.uniform(0, 6.28)) for _ in range(160)]
        self.trails = [(r.uniform(1350, 1800), r.uniform(0, 1), r.choice([-1, 1]), r.choice([(255, 210, 120), (255, 70, 60), (120, 220, 255)])) for _ in range(22)]
        self.ghosts = []
        sh = {s["type"]: (s["start"], s["end"]) for s in story.shots}
        a, b = sh["ruinas"]
        for w in range(6):
            ws = a + 0.4 + w * (b - a - 1.2) / 6
            for k in range(4):
                depth = r.uniform(0.35, 0.8)
                self.ghosts.append({"t": ws + r.uniform(0, 0.6), "x": r.uniform(80, W - 80), "depth": depth,
                                    "face": r.choice(["normal", "sonrisa", "triste", "dormido"]), "flip": r.random() < 0.5})
        # rayo dentado (de arriba a la cabeza del personaje)
        pts, x, y = [], W / 2 + 40, -20
        while y < 1000:
            pts.append((x, y))
            y += r.uniform(40, 110)
            x += r.uniform(-70, 70)
        pts.append((W / 2, 1075))
        self.bolt = pts

    # ── personaje ──
    def char(self, face, arms, height, tint=None, alpha=1.0, flip=False):
        key = (face, arms, height, tint, round(alpha, 2), flip)
        if key in self.char_cache:
            return self.char_cache[key]
        base_key = (face, arms)
        if base_key not in self.char_cache:
            self.char_cache[base_key] = draw(face, arms, look_up=face == "asombrado")
        im = self.char_cache[base_key]
        im = im.resize((int(im.width * height / im.height), height), Image.LANCZOS)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if tint:
            arr = np.asarray(im).astype(np.float32)
            gray = arr[..., :3].mean(axis=2, keepdims=True)
            arr[..., :3] = gray * 0.35 + np.array(tint) * 0.65
            arr[..., 3] *= alpha
            im = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
        if len(self.char_cache) < 400:
            self.char_cache[key] = im
        return im

    def blink(self, t, face):
        if face in ("dormido", "sorprendido"):
            return face
        ph = (t + 0.7) % 3.3
        return "dormido" if ph < 0.13 and face in ("normal", "triste", "asombrado", "sonrisa") else face

    # ── fondo con movimiento de cámara ──
    def view(self, name, zoom, px=0.0, py=0.0, angle=0.0):
        im = self.bg[name]
        bw, bh = im.size
        cw, ch = bw / zoom, bh / zoom
        cx = bw / 2 + px * (bw - cw) / 2
        cy = bh / 2 + py * (bh - ch) / 2
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        out = im.resize((W, H), Image.BILINEAR, box=box)
        if angle:
            out = out.rotate(angle, resample=Image.BILINEAR, expand=False)
        return out

    def frame(self, f):
        st = self.st
        t = f / st.spec.fps
        name = st.scene(t)
        u, sh = st.local(t)
        dur = sh["end"] - sh["start"]
        lt = t - sh["start"]
        shake = (0, 0)
        if name == "rayo":
            if t < 2.2:
                z = 1.0 + 0.12 * smooth(0, 2.2, t)
            else:
                z = 1.12 + 0.04 * (lt - 2.2) / (dur - 2.2)
            if LIGHTNING_T <= t < LIGHTNING_T + 0.5:
                k = 1 - (t - LIGHTNING_T) / 0.5
                shake = (math.sin(t * 90) * 14 * k, math.cos(t * 77) * 10 * k)
            img = self.view("rayo", MARGIN * z / 1.12 if z < 1.12 else min(MARGIN, z), 0.0, 0.2)
            img = ImageEnhance.Brightness(img).enhance(0.8)
        elif name == "siglo":
            # time-lapse: la ciudad de hoy se convierte en la del futuro, con días y noches
            k = smooth(0.0, 0.45, u)
            a = self.view("rayo", 1.1 + 0.03 * u)
            b = self.view("siglo", 1.0 + 0.1 * u, 0.0, -0.2 + 0.4 * u)
            img = Image.blend(a, b, k)
            flick = 0.75 + 0.35 * math.sin(lt * 2 * math.pi * 1.1) * (1 - k * 0.6)
            img = ImageEnhance.Brightness(img).enhance(flick)
        elif name == "ruinas":
            img = self.view("ruinas", 1.0 + 0.12 * u, 0.15 * math.sin(u * 2), 0.0)
        elif name == "tierra":
            img = self.view("tierra", MARGIN - 0.14 * smooth(0, 1, u))
            img = self.grade_earth(img, lt)
        elif name == "sol":
            grow = smooth(0.0, 0.62, u)
            img = self.view("sol", 1.0 + 0.15 * grow, 0.0, -0.35 * grow)
            pulse = 1.0 + 0.06 * math.sin(lt * 5)
            img = ImageEnhance.Brightness(img).enhance(pulse)
            if lt > 6.6:  # colapso: queda una enana blanca en la oscuridad
                dark = smooth(6.6, 7.6, lt)
                img = Image.blend(img, self.view("espacio", 1.0), 0.0)
                img = ImageEnhance.Brightness(img).enhance(1 - 0.85 * dark)
                img = ImageEnhance.Color(img).enhance(1 - 0.8 * dark)
        else:
            img = self.view("espacio", 1.0 + 0.1 * (1 - u))
            if t > st.duration - 3.0:
                img = ImageEnhance.Brightness(img).enhance(1 - 0.45 * smooth(st.duration - 3.0, st.duration - 2.4, t))
        if shake != (0, 0):
            img = img.transform(img.size, Image.AFFINE, (1, 0, shake[0], 0, 1, shake[1]), resample=Image.BILINEAR)
        img = img.convert("RGBA")
        d = ImageDraw.Draw(img, "RGBA")

        # ── partículas y efectos por escena ──
        if name == "rayo":
            for x, y, sp in self.rain:
                yy = (y + t * 1900 * sp) % (H + 200) - 100
                xx = (x - t * 260 * sp) % W
                d.line([(xx, yy), (xx - 10 * sp, yy + 46 * sp)], fill=(200, 215, 255, 90), width=2)
        if name == "siglo":
            for y, ph, dr, col in self.trails:
                xx = ((ph + lt * 0.9 * (1 + ph)) % 1.4 - 0.2) * W
                if dr < 0:
                    xx = W - xx
                d.line([(xx, y), (xx - dr * 260, y)], fill=(*col, 170), width=6)
        if name == "ruinas":
            for x, y, r, ph in self.dust:
                yy = (y - lt * 25) % H
                xx = x + 20 * math.sin(lt * 0.6 + ph)
                d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 235, 190, 90))
            for g in self.ghosts:
                age = t - g["t"]
                if 0 <= age < 2.2:
                    a = math.sin(math.pi * age / 2.2)
                    h = int(760 * g["depth"])
                    im = self.char(g["face"], "abajo", h, tint=(170, 210, 255), alpha=0.55 * a, flip=g["flip"])
                    y0 = int(1180 + (1 - g["depth"]) * -260 + 760 - h)
                    img.alpha_composite(im, (int(g["x"] - im.width / 2), y0))
        if name in ("tierra", "espacio") or (name == "sol" and lt > 6.6):
            for x, y, r, ph in self.stars:
                a = int(120 + 120 * math.sin(t * 3 + ph))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, max(0, a)))
        if name == "sol" and lt > 6.6:
            # enana blanca lejana
            k = smooth(6.6, 7.4, lt)
            cx, cy, r = W / 2, 520, 7 + 10 * (1 - k)
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse([cx - r * 4, cy - r * 4, cx + r * 4, cy + r * 4], fill=(170, 200, 255, 160))
            img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(r * 2.5)))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 250, 255, 255))

        # ── personaje ──
        face, arms = st.expression(t)
        face = self.blink(t, face)
        if name in ("rayo", "siglo", "ruinas", "sol"):
            h = 760 if name != "sol" else 640
            bob = 6 * math.sin(t * 2.4)
            im = self.char(face, arms, h)
            img.alpha_composite(im, (int(W / 2 - im.width / 2 + shake[0]), int(1800 - h + bob + shake[1])))
        elif name == "espacio":
            scale = 1.0 - 0.6 * smooth(0.1, 1.0, u)
            h = max(120, int(720 * scale))
            im = self.char(face, arms, h).rotate(8 * math.sin(t * 0.7), resample=Image.BICUBIC, expand=True)
            cy = H * 0.45 + (H * 0.68 - H * 0.45) * smooth(0.1, 1.0, u)  # se aleja hacia abajo
            y = int(cy - im.height / 2 + 30 * math.sin(t * 1.1))
            img.alpha_composite(im, (int(W / 2 - im.width / 2), y))

        # ── rayo y destello ──
        if LIGHTNING_T <= t < LIGHTNING_T + 0.25:
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            gd.line(self.bolt, fill=(170, 200, 255, 200), width=28, joint="curve")
            glow = glow.filter(ImageFilter.GaussianBlur(14))
            img.alpha_composite(glow)
            ImageDraw.Draw(img).line(self.bolt, fill=(255, 255, 255, 255), width=7, joint="curve")
        flash = 0.0
        if LIGHTNING_T <= t < LIGHTNING_T + 0.3:
            flash = 0.85 * (1 - (t - LIGHTNING_T) / 0.3)
        for s in st.shots[1:]:  # destello breve en cada corte
            if 0 <= t - s["start"] < 0.25:
                flash = max(flash, 0.55 * (1 - (t - s["start"]) / 0.25))
        sol0 = next(s["start"] for s in st.shots if s["type"] == "sol")
        if 0 <= t - (sol0 + 6.6) < 0.5:
            flash = max(flash, 1.0 - (t - sol0 - 6.6) / 0.5)
        out = img.convert("RGB")
        if flash > 0:
            out = Image.blend(out, Image.new("RGB", (W, H), (255, 255, 255)), min(1, flash))
        # fundido cruzado al entrar en cada escena
        return self.finish(out, t)

    def grade_earth(self, img, lt):
        arr = np.asarray(img).astype(np.float32)
        ice = smooth(3.0, 4.2, lt) * (1 - smooth(5.6, 6.4, lt))
        desert = smooth(7.3, 10.5, lt)
        if ice > 0:
            g = arr.mean(axis=2, keepdims=True)
            arr = arr * (1 - ice) + (g * 0.6 + np.array([140, 165, 190]) * 0.5) * ice
        if desert > 0:
            g = arr.mean(axis=2, keepdims=True)
            arr = arr * (1 - desert) + (g * np.array([1.5, 0.95, 0.55])) * desert
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8))

    def finish(self, out, t):
        arr = np.asarray(out).astype(np.float32)
        yy, xx = np.ogrid[:H, :W]
        if not hasattr(self, "_vig"):
            r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
            self._vig = (1 - 0.35 * np.clip(r - 0.55, 0, 1) ** 1.4)[..., None]
        arr *= self._vig
        rng = np.random.default_rng(int(t * 1000))
        arr += rng.normal(0, 3.0, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


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
    comp = Compositor(st)
    os.makedirs(a.out, exist_ok=True)
    f0, f1 = a.frames if a.frames else (0, st.frames - 1)
    frames = a.only or list(range(f0, min(f1, st.frames - 1) + 1, a.every))
    t0 = time.time()
    for i, f in enumerate(frames):
        comp.frame(f).save(os.path.join(a.out, f"f{f:05d}.jpg"), quality=93)
        if i % 60 == 0:
            print(f"[toon] fotograma {f} ({st.scene(f / spec.fps)}) · {time.time() - t0:.0f} s", flush=True)
    print(f"[toon] {len(frames)} fotogramas en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
