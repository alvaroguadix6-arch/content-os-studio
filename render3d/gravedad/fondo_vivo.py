"""Fondos vivos: la ilustración deja de ser una foto fija.

A partir de la ilustración y de su mapa de profundidad (Depth Anything V2 Small, Apache 2.0):
  - cámara con perspectiva real (parallax): lo cercano se mueve más que lo lejano;
  - nubes que avanzan por el cielo y sombras de nubes que barren la calle;
  - rayos de sol que respiran, pájaros que cruzan y motas de polvo al sol.

    python fondo_vivo.py arte/        genera <fondo>_depth.png para calle, despues y cielo
"""
from __future__ import annotations

import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PLATES = ("calle", "despues", "cielo")


def fractal_noise(w, h, seed, base=6, octaves=5, aspect=1.0):
    """Ruido fractal suave (tipo nube) en [0, 1]."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw = max(2, int(base * aspect * 2 ** o))
        gh = max(2, int(base * 2 ** o * h / w))
        small = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8))
        acc += amp * np.asarray(small.resize((w, h), Image.BICUBIC), np.float32) / 255
        tot += amp
        amp *= 0.5
    acc /= tot
    return (acc - acc.min()) / max(1e-6, acc.max() - acc.min())


class LivingPlate:
    def __init__(self, img: Image.Image, depth: Image.Image | None, seed=0, clouds=0.55, cloud_speed=14.0,
                 shadows=0.0, rays=0.0):
        self.img = img.convert("RGB")
        self.size = self.img.size
        bw, bh = self.size
        if depth is None:  # sin mapa: degradado vertical (arriba lejos, abajo cerca)
            d = np.tile(np.linspace(0, 1, bh, dtype=np.float32)[:, None], (1, bw))
        else:
            d = np.asarray(depth.convert("L").resize((bw, bh), Image.BICUBIC), np.float32) / 255
        # margen (espejo) alrededor para que la cámara y el parallax nunca salgan de la imagen
        P = self.P = 90
        d = np.pad(d, P, mode="reflect")
        rgb = np.pad(np.asarray(self.img), ((P, P), (P, P), (0, 0)), mode="reflect")
        bh, bw = d.shape
        self.depth = d
        sky = (d < 0.07).astype(np.float32)
        sky[int(bh * 0.7):] = 0
        sky[: P + 1] = sky[P + 1]  # el cielo nunca está en la parte de abajo
        self.sky = np.asarray(Image.fromarray((sky * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
        self.base = rgb.astype(np.float32)
        self.clouds, self.cloud_speed, self.shadows, self.rays = clouds, cloud_speed, shadows, rays
        n = fractal_noise(bw * 2, bh, seed, base=4, octaves=5, aspect=2.2)
        self.cloud_tex = np.clip((n - 0.52) / 0.22, 0, 1) ** 1.6
        self.shadow_tex = fractal_noise(bw * 2, bh, seed + 1, base=2, octaves=3, aspect=1.6)
        self.ground_w = np.clip((d - 0.25) / 0.5, 0, 1)[..., None]  # las sombras de nubes caen sobre lo cercano
        self.rng = random.Random(seed)

    def plate_at(self, t):
        bh, bw = self.depth.shape
        a = self.base.copy()
        if self.clouds > 0:
            s = int(t * self.cloud_speed) % bw
            c = self.cloud_tex[:, s:s + bw][..., None] * self.sky * self.clouds
            a = a * (1 - c) + np.array([252, 250, 248], np.float32) * c
        if self.shadows > 0:
            s = int(t * self.cloud_speed * 3.2) % bw
            sh = np.clip((self.shadow_tex[:, s:s + bw] - 0.5) / 0.25, 0, 1)[..., None]
            a = a * (1 - self.shadows * sh * self.ground_w)
        return a

    def render(self, W, H, zoom=1.0, px=0.0, py=0.0, t=0.0, par=(0.0, 0.0)):
        """Vista W×H con cámara (zoom, encuadre) y desplazamiento de parallax par=(dx, dy) en px."""
        a = self.plate_at(t)
        zoom *= 1.07  # reserva de imagen para el parallax (sin bordes ni costuras)
        bw, bh = self.size
        P = self.P
        cw, ch = bw / zoom, bh / zoom
        cx = bw / 2 + px * (bw - cw) / 2
        cy = bh / 2 + py * (bh - ch) / 2
        m = 56  # margen para que el parallax no deje bordes vacíos
        sx, sy = cw / W, ch / H
        box = (P + cx - cw / 2 - m * sx, P + cy - ch / 2 - m * sy, P + cx + cw / 2 + m * sx, P + cy + ch / 2 + m * sy)
        VW, VH = W + 2 * m, H + 2 * m
        col = np.asarray(Image.fromarray(a.clip(0, 255).astype(np.uint8)).resize((VW, VH), Image.BILINEAR, box=box), np.float32)
        dep = np.asarray(Image.fromarray(self.depth).resize((VW, VH), Image.BILINEAR, box=box), np.float32)
        dx, dy = par
        yy, xx = np.mgrid[m:m + H, m:m + W].astype(np.float32)
        dv = dep[m:m + H, m:m + W]
        X = np.clip(xx - dx * dv, 0, VW - 1.001)
        Y = np.clip(yy - dy * dv, 0, VH - 1.001)
        x0, y0 = X.astype(np.int32), Y.astype(np.int32)
        fx, fy = (X - x0)[..., None], (Y - y0)[..., None]
        out = (col[y0, x0] * (1 - fx) * (1 - fy) + col[y0, x0 + 1] * fx * (1 - fy)
               + col[y0 + 1, x0] * (1 - fx) * fy + col[y0 + 1, x0 + 1] * fx * fy)
        if self.rays > 0:
            out = out + self.ray_layer(W, H, t) * self.rays
        return Image.fromarray(out.clip(0, 255).astype(np.uint8))

    def ray_layer(self, W, H, t):
        if not hasattr(self, "_rays"):
            lay = Image.new("L", (W // 4, H // 4), 0)
            d = ImageDraw.Draw(lay)
            for i, ang in enumerate((18, 27, 34, 43, 52)):
                a0, a1 = math.radians(ang - 2.2), math.radians(ang + 2.2)
                L = 900
                d.polygon([(-20, -20), (-20 + L * math.cos(a0), -20 + L * math.sin(a0)), (-20 + L * math.cos(a1), -20 + L * math.sin(a1))], fill=90 + 25 * (i % 2))
            lay = lay.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BICUBIC)
            r = np.asarray(lay, np.float32)[..., None] / 255
            self._rays = (r, np.array([255, 225, 170], np.float32))
        r, c = self._rays
        k = 0.55 + 0.25 * math.sin(t * 0.7) + 0.2 * math.sin(t * 1.9)
        return r * c * 0.45 * k


class Ambient:
    """Pájaros que cruzan el cielo y motas de polvo que brillan al sol."""

    def __init__(self, W, H, seed=3):
        r = random.Random(seed)
        self.W, self.H = W, H
        self.birds = [(r.uniform(-300, W), r.uniform(120, 650), r.uniform(45, 110) * r.choice((1, -1)), r.uniform(9, 20), r.uniform(0, 6.28))
                      for _ in range(9)]
        self.motes = [(r.uniform(0, W), r.uniform(0, H), r.uniform(1.5, 4.5), r.uniform(0, 6.28), r.uniform(4, 18)) for _ in range(70)]

    def birds_layer(self, img, t, ymax=900, scale=1.0, alpha=230):
        d = ImageDraw.Draw(img, "RGBA")
        span = self.W + 600
        for x0, y0, v, s, ph in self.birds:
            x = (x0 + v * t) % span - 300
            y = y0 + 18 * math.sin(t * 0.8 + ph)
            if y > ymax:
                continue
            s *= scale
            flap = math.sin(t * 9 + ph)
            wy = -flap * s * 0.55
            d.line([(x - s, y + wy), (x - s * 0.35, y - s * 0.1), (x, y + s * 0.12), (x + s * 0.35, y - s * 0.1), (x + s, y + wy)],
                   fill=(45, 45, 52, alpha), width=max(2, int(s / 6)))

    def motes_layer(self, img, t, rise=0.0, alpha=1.0):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for x0, y0, r, ph, sp in self.motes:
            x = (x0 + 25 * math.sin(t * 0.4 + ph) + sp * t * 0.6) % self.W
            y = (y0 - sp * t * (0.3 + 4 * rise)) % self.H
            tw = 0.5 + 0.5 * math.sin(t * 2.2 + ph * 3)
            a = int(150 * tw * alpha)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 205, a))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.6)))


def make_depths(arte):
    """Calcula el mapa de profundidad de cada fondo (requiere transformers + torch)."""
    from transformers import pipeline

    p = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device="cpu")
    for n in PLATES:
        im = Image.open(os.path.join(arte, n + ".png")).convert("RGB")
        d = np.asarray(p(im)["predicted_depth"].squeeze(), np.float32)
        d = (d - d.min()) / max(1e-6, d.max() - d.min())
        Image.fromarray((d * 255).astype(np.uint8)).resize(im.size, Image.BICUBIC).save(os.path.join(arte, n + "_depth.png"))
        print("[profundidad]", n, flush=True)


if __name__ == "__main__":
    make_depths(sys.argv[1] if len(sys.argv) > 1 else "arte")
