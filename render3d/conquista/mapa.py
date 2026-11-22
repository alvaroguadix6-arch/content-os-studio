"""Mapa rasterizado de municipios con cámara libre (zoom cinematográfico) y coloreado rápido por municipio.

El mapa se dibuja UNA vez como imagen de identificadores (cada píxel = nº de municipio) a 1×, 2× y 4×.
En cada fotograma basta con una tabla de colores por municipio → colores por píxel (NumPy), así se pueden
animar 8.000 municipios cambiando de color, con bordes de municipio, provincia y territorio.
"""
from __future__ import annotations

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import datos

W, H = 1080, 1920
# proyección (coordenadas «mundo» = píxeles del vídeo con cámara en reposo)
K = 92.0
CX = math.cos(math.radians(40))
LON0, LAT0 = -9.45, 43.85
MX, MY = 50.0, 690.0
CAN = dict(lon0=-18.25, lat0=29.5, k=62.0, x=36.0, y=1418.0, w=300.0, h=135.0)  # recuadro de Canarias
WX0, WY0, WW, WH = 0, 620, 1080, 960  # zona del mundo rasterizada
LEVELS = (1, 2, 4)
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos", "raster.npz")


def proj(lon, lat, prov=None):
    if prov in ("35", "38"):
        return (CAN["x"] + 10 + (lon - CAN["lon0"]) * CAN["k"] * math.cos(math.radians(28.4)),
                CAN["y"] + 8 + (CAN["lat0"] - lat) * CAN["k"])
    return MX + (lon - LON0) * K * CX, MY + (LAT0 - lat) * K


def build():
    munis, provs = datos.load()
    out = {}
    order = sorted(range(len(munis)), key=lambda i: -munis[i]["area"])  # los pequeños (enclaves) encima
    for s in LEVELS:
        img = Image.new("I", (WW * s, WH * s), 0)
        d = ImageDraw.Draw(img)
        for i in order:
            m = munis[i]
            for poly in m["polys"]:
                pts = [((x - WX0) * s, (y - WY0) * s) for x, y in (proj(lo, la, m["prov"]) for lo, la in poly[0])]
                if len(pts) >= 3:
                    d.polygon(pts, fill=i + 1)
        out[f"l{s}"] = np.asarray(img, dtype=np.int32).astype(np.int16)
    np.savez_compressed(CACHE, **out)
    return out


_R = None


def raster():
    global _R
    if _R is None:
        if not os.path.exists(CACHE):
            build()
        z = np.load(CACHE)
        munis, _ = datos.load()
        prov_of = np.zeros(len(munis) + 1, np.int16)
        for i, m in enumerate(munis):
            prov_of[i + 1] = int(m["prov"])
        _R = {}
        for s in LEVELS:
            lab = z[f"l{s}"]
            pv = prov_of[lab]
            e_m = np.zeros(lab.shape, bool)
            e_m[:, :-1] |= lab[:, :-1] != lab[:, 1:]
            e_m[:-1, :] |= lab[:-1, :] != lab[1:, :]
            e_p = np.zeros(lab.shape, bool)
            e_p[:, :-1] |= pv[:, :-1] != pv[:, 1:]
            e_p[:-1, :] |= pv[:-1, :] != pv[1:, :]
            if s >= 2:  # bordes de provincia algo más gruesos
                e_p[1:, :] |= e_p[:-1, :].copy()
                e_p[:, 1:] |= e_p[:, :-1].copy()
            _R[s] = dict(lab=lab, em=e_m, ep=e_p)
    return _R


class Camera:
    def __init__(self, x=540.0, y=1100.0, z=1.0):
        self.x, self.y, self.z = x, y, z

    def to_screen(self, wx, wy):
        return (wx - self.x) * self.z + 540, (wy - self.y) * self.z + 1100

    def to_world(self, sx, sy):
        return (sx - 540) / self.z + self.x, (sy - 1100) / self.z + self.y


def render(cam: Camera, fill: np.ndarray, owner: np.ndarray | None = None, owner_col: np.ndarray | None = None,
           border_m=(70, 84, 170), border_p=(120, 205, 255), alpha_m=0.45, alpha_p=0.9, glow=True):
    """fill: (Nmuni+1, 3) colores (fila 0 = mar). owner: (Nmuni+1,) índice de territorio (-1 libre).
    Devuelve una capa RGBA 1080×1920 con el mapa visto por la cámara."""
    z = cam.z
    s = next((l for l in LEVELS if l >= 1.25 * z), LEVELS[-1])
    R = raster()[s]
    wx0, wy0 = cam.to_world(0, 0)
    wx1, wy1 = cam.to_world(W, H)
    # recorte en píxeles del nivel (con margen), limitado al raster
    fx0, fy0 = (wx0 - WX0) * s, (wy0 - WY0) * s
    fx1, fy1 = (wx1 - WX0) * s, (wy1 - WY0) * s
    hgt, wid = R["lab"].shape
    cx0, cy0 = max(0, int(math.floor(fx0)) - 1), max(0, int(math.floor(fy0)) - 1)
    cx1, cy1 = min(wid, int(math.ceil(fx1)) + 1), min(hgt, int(math.ceil(fy1)) + 1)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if cx1 <= cx0 or cy1 <= cy0:
        return out
    lab = R["lab"][cy0:cy1, cx0:cx1]
    rgb = fill[lab].astype(np.float32)
    em = R["em"][cy0:cy1, cx0:cx1]
    ep = R["ep"][cy0:cy1, cx0:cx1]
    am = alpha_m * min(1.0, 0.35 + 0.35 * z)  # de lejos, bordes de municipio más suaves
    rgb[em] = rgb[em] * (1 - am) + np.array(border_m, np.float32) * am
    rgb[ep] = rgb[ep] * (1 - alpha_p) + np.array(border_p, np.float32) * alpha_p
    edge_t = None
    if owner is not None:
        ow = owner[lab]
        edge_t = np.zeros(lab.shape, bool)
        edge_t[:, :-1] |= ow[:, :-1] != ow[:, 1:]
        edge_t[:-1, :] |= ow[:-1, :] != ow[1:, :]
        edge_t &= (ow >= 0) | np.roll(ow >= 0, 1, 0) | np.roll(ow >= 0, 1, 1)
        rgb[edge_t] = rgb[edge_t] * 0.15 + 255 * 0.85
    a = (lab > 0).astype(np.uint8) * 255
    arr = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), a])
    im = Image.fromarray(arr, "RGBA")
    # coloca el recorte en pantalla (EXTENT: zona del recorte que corresponde a toda la pantalla)
    ex = (fx0 - cx0, fy0 - cy0, fx1 - cx0, fy1 - cy0)
    scr = im.transform((W, H), Image.EXTENT, ex, resample=Image.BILINEAR)
    if glow and edge_t is not None and edge_t.any() and owner_col is not None:
        gl = np.zeros(lab.shape + (4,), np.uint8)
        ow = owner[lab]
        cols = owner_col[np.clip(ow, 0, None)]
        m = edge_t & (ow >= 0)
        gl[m, :3] = cols[m]
        gl[m, 3] = 255
        g = Image.fromarray(gl, "RGBA").transform((W, H), Image.EXTENT, ex, resample=Image.BILINEAR)
        g = g.filter(ImageFilter.GaussianBlur(6))
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        base.alpha_composite(g)
        base.alpha_composite(g)
        base.alpha_composite(scr)
        scr = base
    return scr


def canarias_box(cam: Camera, d: ImageDraw.ImageDraw):
    x0, y0 = cam.to_screen(CAN["x"], CAN["y"])
    x1, y1 = cam.to_screen(CAN["x"] + CAN["w"], CAN["y"] + CAN["h"])
    d.rounded_rectangle([x0, y0, x1, y1], max(4, int(14 * cam.z)), outline=(110, 150, 230, 160), width=max(2, int(3 * min(cam.z, 2))))


if __name__ == "__main__":
    import time
    t0 = time.time()
    build()
    print("raster en", round(time.time() - t0, 1), "s")
