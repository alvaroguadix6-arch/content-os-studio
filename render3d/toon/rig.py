"""Personaje 2D articulado (marioneta digital) en el estilo de Content-OS.

Se dibuja en cada fotograma a partir de una «pose»: ángulos de brazos y piernas, cara,
inclinación, estiramiento y accesorios. Así puede andar, saltar, girar y reaccionar.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFilter

INK = (22, 20, 24, 255)
SKIN = (246, 244, 240, 255)
CHAR = (70, 66, 64, 255)  # cara chamuscada
BLUSH = (242, 150, 160, 170)

S = 2  # sobremuestreo
CW, CH = 640, 1240  # lienzo local (px finales) con margen para brazos/accesorios
GROUND = 1160  # los pies tocan el suelo en esta y


@dataclass
class Pose:
    face: str = "normal"  # normal, dormido, sorprendido, triste, asombrado, sonrisa, mareado, lloro
    arm_l: float = 12.0  # grados desde la vertical (positivo = hacia fuera)
    arm_r: float = 12.0
    elbow_l: float = 0.0
    elbow_r: float = 0.0
    leg_l: float = 4.0
    leg_r: float = 4.0
    head_tilt: float = 0.0
    lean: float = 0.0  # rotación de todo el cuerpo (grados)
    squash: float = 1.0  # 1 = normal; <1 aplastado; >1 estirado
    sit: bool = False
    coat: tuple = (122, 82, 52, 255)
    scarf: tuple = (196, 44, 36, 255)
    pants: tuple = (48, 50, 60, 255)
    hair: str = "none"  # none, grey, frizz, beard
    glasses: bool = False
    cane: bool = False
    charred: float = 0.0  # 0..1
    sweat: bool = False
    stars: float = -1.0  # fase de las estrellitas de mareo (<0 = no)
    tear: float = -1.0  # fase de la lágrima (<0 = no)
    shiver: float = 0.0
    alpha: float = 1.0
    tint: tuple | None = None  # fantasma
    extras: dict = field(default_factory=dict)


def _p(x, y):
    return (x * S, y * S)


def _ellipse(d, cx, cy, rx, ry, fill, width=9):
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill, outline=INK, width=width * S)


def _poly(d, pts, fill, width=9):
    q = [_p(x, y) for x, y in pts]
    d.polygon(q, fill=fill)
    d.line(q + [q[0]], fill=INK, width=width * S, joint="curve")


def _limb(d, pts, width, color):
    q = [_p(x, y) for x, y in pts]
    d.line(q, fill=INK, width=int((width + 16) * S), joint="curve")
    for x, y in q:
        r = (width + 16) * S / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=INK)
    d.line(q, fill=color, width=int(width * S), joint="curve")
    for x, y in q:
        r = width * S / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def _arm(d, sx, sy, ang, elbow, side, color, hand=SKIN):
    a = math.radians(ang) * side
    ex, ey = sx + math.sin(a) * 130, sy + math.cos(a) * 130
    b = a + math.radians(elbow) * side
    hx, hy = ex + math.sin(b) * 120, ey + math.cos(b) * 120
    _limb(d, [(sx, sy), (ex, ey), (hx, hy)], 38, color)
    _ellipse(d, hx, hy, 27, 27, hand, 7)
    return hx, hy


def _leg(d, hx, hy, ang, side, color, sit=False):
    a = math.radians(ang) * side
    if sit:
        kx, ky = hx + side * 20, hy + 10
        fx, fy = kx + side * 10, ky + 150
        _limb(d, [(hx, hy), (hx + side * 10, hy + 5), (fx, fy)], 44, color)
    else:
        fx, fy = hx + math.sin(a) * 230, hy + math.cos(a) * 230
        _limb(d, [(hx, hy), (fx, fy)], 44, color)
    _ellipse(d, fx + side * 18, fy + 16, 50, 27, (34, 30, 30, 255), 7)


def _face(d, cx, cy, p: Pose):
    ex, ey = 70, cy - 4
    f = p.face
    if f == "dormido":
        for sx in (-1, 1):
            d.arc([(cx + sx * ex - 28) * S, (ey - 18) * S, (cx + sx * ex + 28) * S, (ey + 20) * S], 20, 160, fill=INK, width=9 * S)
    elif f == "mareado":
        for sx in (-1, 1):
            c = cx + sx * ex
            for k in range(3):
                r = 8 + k * 7
                d.arc([(c - r) * S, (ey - r) * S, (c + r) * S, (ey + r) * S], k * 90, k * 90 + 260, fill=INK, width=5 * S)
    elif f in ("sorprendido", "asombrado"):
        for sx in (-1, 1):
            r = 26 if f == "sorprendido" else 22
            d.ellipse([(cx + sx * ex - r) * S, (ey - r - 6) * S, (cx + sx * ex + r) * S, (ey + r - 6) * S], fill=INK)
            d.ellipse([(cx + sx * ex - 9) * S, (ey - r) * S, (cx + sx * ex + 1) * S, (ey - r + 10) * S], fill=(255, 255, 255, 255))
    elif f in ("triste", "lloro"):
        for sx in (-1, 1):
            d.ellipse([(cx + sx * ex - 18) * S, (ey - 14) * S, (cx + sx * ex + 18) * S, (ey + 20) * S], fill=INK)
            d.line([_p(cx + sx * (ex - 34), ey - 46), _p(cx + sx * (ex + 22), ey - 32)], fill=INK, width=8 * S)
    else:
        for sx in (-1, 1):
            d.ellipse([(cx + sx * ex - 20) * S, (ey - 22) * S, (cx + sx * ex + 20) * S, (ey + 20) * S], fill=INK)
            d.ellipse([(cx + sx * ex - 9) * S, (ey - 16) * S, (cx + sx * ex + 2) * S, (ey - 5) * S], fill=(255, 255, 255, 255))
    if p.charred < 0.5:
        for sx in (-1, 1):
            d.ellipse([(cx + sx * 104 - 32) * S, (ey + 30) * S, (cx + sx * 104 + 32) * S, (ey + 56) * S], fill=BLUSH)
    my = cy + 62
    if f in ("sonrisa",):
        d.arc([(cx - 40) * S, (my - 34) * S, (cx + 40) * S, (my + 18) * S], 20, 160, fill=INK, width=9 * S)
    elif f == "sorprendido":
        d.ellipse([(cx - 20) * S, (my - 14) * S, (cx + 20) * S, (my + 30) * S], fill=INK)
    elif f in ("asombrado", "mareado"):
        d.ellipse([(cx - 13) * S, (my - 6) * S, (cx + 13) * S, (my + 22) * S], fill=INK)
    elif f in ("triste", "lloro"):
        d.arc([(cx - 32) * S, (my + 2) * S, (cx + 32) * S, (my + 42) * S], 200, 340, fill=INK, width=9 * S)
    elif f == "dormido":
        d.arc([(cx - 12) * S, (my - 8) * S, (cx + 12) * S, (my + 8) * S], 20, 160, fill=INK, width=6 * S)
    else:
        d.arc([(cx - 28) * S, (my - 22) * S, (cx + 28) * S, (my + 10) * S], 30, 150, fill=INK, width=9 * S)


def draw_pose(p: Pose, t: float = 0.0) -> Image.Image:
    """Devuelve el personaje en un lienzo CW×CH con los pies en (CW/2, GROUND)."""
    img = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = CW / 2
    jit = math.sin(t * 60) * 4 * p.shiver
    cx += jit
    hip_y = 900 if not p.sit else 990
    top = 520 if not p.sit else 610
    # piernas
    for side, ang in ((-1, p.leg_l), (1, p.leg_r)):
        _leg(d, cx + side * 44, hip_y, ang, side, p.pants, p.sit)
    # brazo trasero (izquierdo del dibujo detrás del abrigo si va abajo)
    hands = {}
    # abrigo
    coat = [(cx - 118, top), (cx + 118, top), (cx + 165, hip_y + 60), (cx + 20, hip_y + 85), (cx - 20, hip_y + 85), (cx - 165, hip_y + 60)]
    _poly(d, coat, p.coat)
    darker = tuple(max(0, int(c * 0.75)) for c in p.coat[:3]) + (255,)
    d.line([_p(cx, top + 40), _p(cx, hip_y + 75)], fill=darker, width=6 * S)
    for y in (top + 120, top + 220, top + 320):
        _ellipse(d, cx + 22, y, 9, 9, darker, 4)
    d.line([_p(cx - 135, top + 240), _p(cx + 135, top + 240)], fill=INK, width=16 * S)
    for side, ang, el in ((-1, p.arm_l, p.elbow_l), (1, p.arm_r, p.elbow_r)):
        hands[side] = _arm(d, cx + side * 112, top + 40, ang, el, side, p.coat)
    if p.cane:
        hx, hy = hands[1]
        d.line([_p(hx, hy), _p(hx + 30, GROUND + 10)], fill=(90, 60, 30, 255), width=12 * S)
        d.arc([(hx - 30) * S, (hy - 30) * S, (hx + 10) * S, (hy + 10) * S], 180, 360, fill=(90, 60, 30, 255), width=12 * S)
    # bufanda
    _poly(d, [(cx - 110, top - 20), (cx + 110, top - 20), (cx + 96, top + 40), (cx - 96, top + 40)], p.scarf)
    _poly(d, [(cx + 40, top + 20), (cx + 90, top + 25), (cx + 108, top + 170), (cx + 62, top + 180)], p.scarf)
    # cabeza
    hy = top - 190
    head = Image.new("RGBA", (420 * S, 420 * S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(head)
    hc = 210
    skin = SKIN
    if p.charred > 0:
        k = p.charred
        skin = tuple(int(SKIN[i] * (1 - k) + CHAR[i] * k) for i in range(3)) + (255,)
    if p.hair == "frizz" or p.charred > 0.3:
        for i in range(14):
            a = math.pi * (0.1 + 0.8 * i / 13)
            x0, y0 = hc + math.cos(a) * 150, hc - math.sin(a) * 140
            x1, y1 = hc + math.cos(a) * 205, hc - math.sin(a) * 200
            hd.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=INK, width=10 * S)
    _ellipse(hd, hc, hc, 175, 165, skin, 11)
    if p.hair == "grey":
        hd.chord([(hc - 176) * S, (hc - 166) * S, (hc + 176) * S, (hc + 60) * S], 180, 360, fill=(205, 205, 210, 255), outline=INK, width=9 * S)
    if p.hair == "beard":
        hd.chord([(hc - 150) * S, (hc - 40) * S, (hc + 150) * S, (hc + 230) * S], 0, 180, fill=(205, 205, 210, 255), outline=INK, width=9 * S)
    _face(hd, hc, hc, p)
    if p.glasses:
        for sx in (-1, 1):
            hd.rounded_rectangle([(hc + sx * 70 - 48) * S, (hc - 40) * S, (hc + sx * 70 + 48) * S, (hc + 22) * S], 16 * S, fill=(15, 15, 20, 255), outline=INK, width=6 * S)
            hd.line([((hc + sx * 70 - 30) * S, (hc - 28) * S), ((hc + sx * 70 - 12) * S, (hc - 32) * S)], fill=(255, 255, 255, 200), width=5 * S)
        hd.line([((hc - 22) * S, (hc - 20) * S), ((hc + 22) * S, (hc - 20) * S)], fill=INK, width=8 * S)
    if p.sweat:
        for k, (sx, sy) in enumerate(((150, -60), (-160, -20))):
            yy = hc + sy + (t * 160 + k * 40) % 90
            hd.ellipse([(hc + sx - 10) * S, (yy - 16) * S, (hc + sx + 10) * S, (yy + 12) * S], fill=(140, 200, 255, 230), outline=INK, width=3 * S)
    if p.tear >= 0:
        yy = hc + 30 + (p.tear % 1) * 150
        hd.ellipse([(hc - 80 - 10) * S, (yy - 14) * S, (hc - 80 + 10) * S, (yy + 14) * S], fill=(140, 200, 255, 240), outline=INK, width=3 * S)
    if p.head_tilt:
        head = head.rotate(-p.head_tilt, resample=Image.BICUBIC, center=(hc * S, (hc + 150) * S))
    img.alpha_composite(head, (int((cx - hc) * S), int((hy - hc) * S)))
    # estrellitas de mareo
    if p.stars >= 0:
        for k in range(4):
            a = p.stars * 5 + k * math.pi / 2
            sx, sy = cx + math.cos(a) * 190, hy - 175 + math.sin(a) * 40
            r = 22
            pts = [(sx + math.cos(i * math.pi / 5 - math.pi / 2) * (r if i % 2 == 0 else r * 0.45), sy + math.sin(i * math.pi / 5 - math.pi / 2) * (r if i % 2 == 0 else r * 0.45)) for i in range(10)]
            _poly(d, pts, (255, 220, 40, 255), 4)
    out = img.resize((CW, CH), Image.LANCZOS)
    if p.squash != 1.0 or p.lean:
        sx, sy = 1 / math.sqrt(p.squash), p.squash
        nw, nh = int(CW * sx), int(CH * sy)
        out = out.resize((nw, nh), Image.BILINEAR)
        canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        canvas.alpha_composite(out.crop((max(0, (nw - CW) // 2), max(0, nh - CH), max(0, (nw - CW) // 2) + min(CW, nw), nh)), (max(0, (CW - nw) // 2), max(0, CH - nh)))
        out = canvas
        if p.lean:
            out = out.rotate(-p.lean, resample=Image.BICUBIC, center=(CW / 2, GROUND))
    if p.tint or p.alpha < 1:
        import numpy as np

        arr = np.asarray(out).astype("float32")
        if p.tint:
            g = arr[..., :3].mean(axis=2, keepdims=True)
            arr[..., :3] = g * 0.35 + np.array(p.tint) * 0.65
        arr[..., 3] *= p.alpha
        out = Image.fromarray(arr.clip(0, 255).astype("uint8"), "RGBA")
    return out


def walk(p: Pose, t: float, speed=2.2, amp=24):
    s = math.sin(t * speed * 2 * math.pi)
    p.leg_l, p.leg_r = 4 + amp * s, 4 - amp * s
    p.arm_l, p.arm_r = 12 - amp * 0.8 * s, 12 + amp * 0.8 * s
    return p


if __name__ == "__main__":
    import sys

    poses = [Pose(), Pose(face="mareado", stars=0.3), Pose(charred=1.0, face="sorprendido", hair="frizz"),
             Pose(face="sonrisa", arm_l=150, arm_r=150), Pose(face="triste", sit=True, tear=0.4),
             Pose(face="normal", glasses=True, sweat=True), Pose(hair="grey", cane=True, coat=(60, 90, 160, 255), face="sonrisa"),
             walk(Pose(face="asombrado"), 0.1)]
    sheet = Image.new("RGBA", (CW * 4, CH * 2), (70, 80, 100, 255))
    for i, ps in enumerate(poses):
        sheet.alpha_composite(draw_pose(ps, 0.2), ((i % 4) * CW, (i // 4) * CH))
    sheet.convert("RGB").resize((CW * 2, CH)).save(sys.argv[1] if len(sys.argv) > 1 else "rig.jpg")
