"""Personaje 2D original de Content-OS, estilo «cabeza redonda» de dibujos animados.

Cabeza redonda blanca con contorno negro grueso, ojos sencillos, coloretes y cuerpo de
viajero (abrigo marrón y bufanda roja). Se dibuja con Pillow a 4x y se reduce para
que los bordes salgan suaves. Genera PNG transparentes por expresión y pose.

    python character.py salida/      → crea un PNG por expresión
"""
from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

S = 4  # sobremuestreo
W, H = 600, 1200  # tamaño final (px) del personaje
INK = (22, 20, 24, 255)
SKIN = (246, 244, 240, 255)
BLUSH = (242, 150, 160, 170)
COAT = (122, 82, 52, 255)
COAT_DARK = (92, 60, 38, 255)
SCARF = (196, 44, 36, 255)
PANTS = (48, 50, 60, 255)
SHOE = (34, 30, 30, 255)
LW = 9 * S  # grosor del contorno

EXPRESSIONS = ["normal", "dormido", "sorprendido", "triste", "asombrado", "sonrisa"]


def _p(x, y):
    return (x * S, y * S)


def _ellipse(d, cx, cy, rx, ry, fill, width=LW):
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill, outline=INK, width=width)


def _poly(d, pts, fill, width=LW):
    pts = [_p(x, y) for x, y in pts]
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=INK, width=width, joint="curve")
    for x, y in pts:  # esquinas redondeadas
        r = width // 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=INK)


def _limb(d, a, b, width, color):
    d.line([_p(*a), _p(*b)], fill=INK, width=int((width + 18) * S))
    d.line([_p(*a), _p(*b)], fill=color, width=int(width * S))
    for x, y in (a, b):
        r = (width + 18) * S / 2
        d.ellipse([x * S - r, y * S - r, x * S + r, y * S + r], fill=INK)
        r2 = width * S / 2
        d.ellipse([x * S - r2, y * S - r2, x * S + r2, y * S + r2], fill=color)


def _face(d, cx, cy, expr):
    ex = 70
    ey = cy - 4
    if expr == "dormido":
        for sx in (-1, 1):
            d.arc([(cx + sx * ex - 28) * S, (ey - 18) * S, (cx + sx * ex + 28) * S, (ey + 20) * S], 20, 160, fill=INK, width=9 * S)
    elif expr in ("sorprendido", "asombrado"):
        for sx in (-1, 1):
            r = 26 if expr == "sorprendido" else 22
            d.ellipse([(cx + sx * ex - r) * S, (ey - r - 6) * S, (cx + sx * ex + r) * S, (ey + r - 6) * S], fill=INK)
            d.ellipse([(cx + sx * ex - 5) * S, (ey - r - 2) * S, (cx + sx * ex + 3) * S, (ey - r + 6) * S], fill=(255, 255, 255, 255))
    elif expr == "triste":
        for sx in (-1, 1):
            d.ellipse([(cx + sx * ex - 18) * S, (ey - 14) * S, (cx + sx * ex + 18) * S, (ey + 20) * S], fill=INK)
            d.line([_p(cx + sx * (ex - 34), ey - 46), _p(cx + sx * (ex + 22), ey - 32)], fill=INK, width=8 * S)
    else:
        for sx in (-1, 1):
            d.ellipse([(cx + sx * ex - 20) * S, (ey - 22) * S, (cx + sx * ex + 20) * S, (ey + 20) * S], fill=INK)
            d.ellipse([(cx + sx * ex - 9) * S, (ey - 16) * S, (cx + sx * ex + 2) * S, (ey - 5) * S], fill=(255, 255, 255, 255))
    # coloretes
    for sx in (-1, 1):
        d.ellipse([(cx + sx * 104 - 32) * S, (ey + 30) * S, (cx + sx * 104 + 32) * S, (ey + 56) * S], fill=BLUSH)
    # boca
    my = cy + 62
    if expr == "sonrisa":
        d.arc([(cx - 40) * S, (my - 34) * S, (cx + 40) * S, (my + 18) * S], 20, 160, fill=INK, width=9 * S)
    elif expr == "sorprendido":
        d.ellipse([(cx - 20) * S, (my - 14) * S, (cx + 20) * S, (my + 30) * S], fill=INK)
    elif expr == "asombrado":
        d.ellipse([(cx - 13) * S, (my - 6) * S, (cx + 13) * S, (my + 22) * S], fill=INK)
    elif expr == "triste":
        d.arc([(cx - 32) * S, (my + 2) * S, (cx + 32) * S, (my + 42) * S], 200, 340, fill=INK, width=9 * S)
    elif expr == "dormido":
        d.arc([(cx - 12) * S, (my - 8) * S, (cx + 12) * S, (my + 8) * S], 20, 160, fill=INK, width=6 * S)
    else:
        d.arc([(cx - 28) * S, (my - 22) * S, (cx + 28) * S, (my + 10) * S], 30, 150, fill=INK, width=9 * S)


def draw(expr="normal", arms="abajo", look_up=False):
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W / 2
    # piernas
    for sx in (-1, 1):
        _limb(d, (cx + sx * 42, 900), (cx + sx * 50, 1110), 46, PANTS)
        _ellipse(d, cx + sx * 64, 1128, 52, 28, SHOE)
    # brazos (detrás del abrigo si van abajo)
    if arms == "abiertos":
        for sx in (-1, 1):
            _limb(d, (cx + sx * 110, 560), (cx + sx * 235, 430), 40, COAT)
            _ellipse(d, cx + sx * 248, 418, 30, 30, SKIN)
    # abrigo largo
    coat = [(cx - 118, 520), (cx + 118, 520), (cx + 165, 960), (cx + 20, 985), (cx - 20, 985), (cx - 165, 960)]
    _poly(d, coat, COAT)
    d.line([_p(cx, 560), _p(cx, 975)], fill=COAT_DARK, width=6 * S)
    for y in (640, 740, 840):
        _ellipse(d, cx + 22, y, 9, 9, COAT_DARK, width=4 * S)
    # cinturón
    d.line([_p(cx - 135, 760), _p(cx + 135, 760)], fill=INK, width=16 * S)
    if arms == "abajo":
        for sx in (-1, 1):
            _limb(d, (cx + sx * 112, 560), (cx + sx * 140, 820), 40, COAT)
            _ellipse(d, cx + sx * 142, 850, 28, 28, SKIN)
    # bufanda
    _poly(d, [(cx - 110, 500), (cx + 110, 500), (cx + 96, 560), (cx - 96, 560)], SCARF)
    _poly(d, [(cx + 40, 540), (cx + 90, 545), (cx + 108, 690), (cx + 62, 700)], SCARF)
    # cabeza
    hy = 330 if not look_up else 320
    _ellipse(d, cx, hy, 175, 165, SKIN, width=11 * S)
    _face(d, cx, hy - (18 if look_up else 0), expr)
    out = img.resize((W, H), Image.LANCZOS)
    # sombra suave de contorno para integrarse con fondos detallados
    return out


def save_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for e in EXPRESSIONS:
        for arms in ("abajo", "abiertos"):
            p = os.path.join(out_dir, f"heroe_{e}_{arms}.png")
            draw(e, arms, look_up=e == "asombrado").save(p)
            paths[(e, arms)] = p
    return paths


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "personaje"
    save_all(out)
    sheet = Image.new("RGBA", (W * 4, H * 2), (70, 80, 100, 255))
    for i, (e, a) in enumerate([(e, "abajo") for e in EXPRESSIONS[:4]] + [("asombrado", "abiertos"), ("sonrisa", "abiertos"), ("triste", "abajo"), ("normal", "abiertos")]):
        sheet.alpha_composite(draw(e, a, e == "asombrado"), ((i % 4) * W, (i // 4) * H))
    sheet.convert("RGB").resize((W * 2, H)).save(os.path.join(out, "hoja_personaje.jpg"))
    print("ok")
