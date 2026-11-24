"""NIVEL OCULTO · Personajes de dibujos animados (rig propio, reutilizable).

Personaje de cabeza grande y contorno grueso, estilo cartoon plano:
  - expresiones: neutral, feliz, pillo, sorpresa, miedo, triste, enfado
  - parpadeo automático, mirada que sigue un punto, cejas y boca según la emoción
  - brazos articulados (hombro + codo) con poses: reposo, saludo, celebrar, manos arriba, correr, sujetar
  - piernas que caminan / corren, rebote al respirar
Se dibuja sobre la imagen a superresolución (coordenadas a 1×, multiplicadas por S).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from PIL import ImageDraw

INK = (34, 22, 26)


def _p(S, pts):
    return [(x * S, y * S) for x, y in pts]


@dataclass
class Look:
    skin: tuple = (240, 190, 150)
    hair: tuple = (60, 40, 30)
    shirt: tuple = (70, 90, 130)
    pants: tuple = (40, 44, 60)
    shoes: tuple = (30, 30, 34)
    hat: str | None = None        # "cap" (gorra de vigilante), "police", None
    hat_col: tuple = (40, 50, 80)
    badge: bool = False
    pattern: str | None = None    # "flowers" (camisa hawaiana)
    stubble: bool = True
    hair_style: str = "short"     # short, bald, long, curly
    extra: dict = field(default_factory=dict)


EXPR = {  # (cejas: inclinación, altura) (boca)
    "neutral": ((0.0, 0.0), "line"),
    "happy": ((-0.1, -0.08), "smile"),
    "grin": ((-0.15, -0.12), "grin"),
    "sly": ((0.35, 0.0), "smirk"),
    "shock": ((-0.25, -0.3), "O"),
    "scared": ((-0.45, -0.2), "wobble"),
    "sad": ((-0.5, 0.05), "sad"),
    "angry": ((0.5, 0.08), "shout"),
}


class Toon:
    def __init__(self, look: Look, height=700.0, seed=0):
        self.L = look
        self.h = height
        self.seed = seed

    # ───── primitivas con contorno ─────
    def ell(self, d, S, x, y, rx, ry, col, ow=5):
        d.ellipse([(x - rx - ow) * S, (y - ry - ow) * S, (x + rx + ow) * S, (y + ry + ow) * S], fill=INK)
        d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S], fill=col)

    def cap(self, d, S, a, b, w, col, ow=5):
        """Cápsula (brazo/pierna) con contorno."""
        for width, c in ((w + 2 * ow, INK), (w, col)):
            d.line(_p(S, [a, b]), fill=c, width=int(width * S))
            for (x, y) in (a, b):
                r = width / 2
                d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=c)

    def poly(self, d, S, pts, col, ow=5):
        d.polygon(_p(S, pts), fill=col, outline=INK)
        d.line(_p(S, pts + [pts[0]]), fill=INK, width=int(ow * S), joint="curve")

    # ───── personaje ─────
    def draw(self, img, x, y, t, expr="neutral", pose="idle", look_at=None, scale=1.0, face_dir=0.0, walk=0.0, S=2, bounce=True,
             mouth_open=None, flip=False):
        """(x, y) = pies. pose: idle, wave, cheer, hands_up, run, hold, shrug, point, dance, grab_bars."""
        d = ImageDraw.Draw(img)
        L = self.L
        u = self.h * scale / 100.0
        ow = max(3.0, 1.0 * u)
        by = (math.sin(t * 3.2 + self.seed) * 0.6 * u) if bounce else 0.0
        if pose in ("run", "dance"):
            by = abs(math.sin(walk * 2)) * -2.2 * u
        # ── piernas ──
        hip_y = y - 32 * u + by
        sw = math.sin(walk) * (0.55 if pose == "run" else 0.32) if (walk or pose in ("run", "dance")) else 0.0
        legs = []
        for side in (-1, 1):
            hx = x + side * 6 * u
            ang = sw * side
            if pose == "dance":
                ang = 0.35 * math.sin(t * 8 + side)
            fx, fy = hx + math.sin(ang) * 30 * u, hip_y + math.cos(ang) * 30 * u
            legs.append(((hx, hip_y), (fx, min(fy, y + by * 0.2))))
        for (a, b) in legs:
            self.cap(d, S, a, b, 11 * u, L.pants, ow)
            self.ell(d, S, b[0] + 3 * u * (-1 if flip else 1), b[1] + 1 * u, 8 * u, 4.2 * u, L.shoes, ow)
        # ── torso ──
        sh_y = y - 62 * u + by
        torso = [(x - 15 * u, sh_y), (x + 15 * u, sh_y), (x + 13 * u, hip_y + 2 * u), (x - 13 * u, hip_y + 2 * u)]
        # brazos de atrás primero? (todo plano: se dibujan después del torso para que se vean)
        if L.extra.get("coat"):
            self.poly(d, S, [(x - 16 * u, sh_y + 2 * u), (x + 16 * u, sh_y + 2 * u), (x + 19 * u, hip_y + 16 * u), (x - 19 * u, hip_y + 16 * u)], L.extra["coat"], ow)
        self.poly(d, S, torso, L.shirt, ow)
        if L.extra.get("tie"):
            self.poly(d, S, [(x - 2.5 * u, sh_y + 4 * u), (x + 2.5 * u, sh_y + 4 * u), (x + 3.5 * u, sh_y + 22 * u), (x, sh_y + 26 * u), (x - 3.5 * u, sh_y + 22 * u)], L.extra["tie"], ow * 0.6)
        if L.pattern == "flowers":
            for i in range(7):
                fx = x - 8 * u + (i % 3) * 8 * u
                fy = sh_y + 6 * u + (i // 3) * 9 * u
                for k in range(5):
                    a = k / 5 * 2 * math.pi
                    d.ellipse([(fx + math.cos(a) * 2 * u - 1.6 * u) * S, (fy + math.sin(a) * 2 * u - 1.6 * u) * S,
                               (fx + math.cos(a) * 2 * u + 1.6 * u) * S, (fy + math.sin(a) * 2 * u + 1.6 * u) * S], fill=(255, 220, 90))
        d.rectangle([(x - 13.5 * u) * S, (hip_y - 3 * u) * S, (x + 13.5 * u) * S, (hip_y + 1 * u) * S], fill=INK)  # cinturón
        if L.badge:
            self.poly(d, S, [(x - 9 * u, sh_y + 7 * u), (x - 4 * u, sh_y + 7 * u), (x - 4 * u, sh_y + 13 * u), (x - 6.5 * u, sh_y + 15 * u),
                             (x - 9 * u, sh_y + 13 * u)], (230, 190, 60), ow * 0.6)
        d.polygon(_p(S, [(x - 5 * u, sh_y), (x, sh_y + 7 * u), (x + 5 * u, sh_y)]), fill=(250, 250, 250), outline=INK)  # cuello camisa
        # ── brazos (hombro, codo, mano) ──
        arms = self.arm_angles(pose, t, walk)
        for side, (a1, a2) in zip((-1, 1), arms):
            sx, sy = x + side * 14 * u, sh_y + 4 * u
            ex, ey = sx + math.sin(a1) * 16 * u * side, sy + math.cos(a1) * 16 * u
            hx, hy = ex + math.sin(a1 + a2) * 15 * u * side, ey + math.cos(a1 + a2) * 15 * u
            self.cap(d, S, (sx, sy), (ex, ey), 9 * u, L.shirt, ow)
            self.cap(d, S, (ex, ey), (hx, hy), 8 * u, L.shirt if pose != "dance" else L.skin, ow)
            self.ell(d, S, hx, hy, 5 * u, 5 * u, L.skin, ow)
        # ── cabeza ──
        hx0, hy0 = x + face_dir * 2 * u, sh_y - 20 * u
        d.rectangle([(x - 4 * u) * S, (sh_y - 6 * u) * S, (x + 4 * u) * S, (sh_y + 1 * u) * S], fill=L.skin)
        self.ell(d, S, hx0 - 19 * u, hy0 + 2 * u, 4 * u, 5 * u, L.skin, ow)  # orejas
        self.ell(d, S, hx0 + 19 * u, hy0 + 2 * u, 4 * u, 5 * u, L.skin, ow)
        self.ell(d, S, hx0, hy0, 19 * u, 21 * u, L.skin, ow)
        if L.stubble:  # barba de tres días
            for i in range(26):
                a = math.pi * (0.15 + 0.7 * ((i * 0.37) % 1))
                rr = 15 * u * (0.75 + 0.25 * ((i * 0.61) % 1))
                px, py = hx0 + math.cos(a) * rr, hy0 + 6 * u + math.sin(a) * rr * 0.7
                d.ellipse([(px - 0.6 * u) * S, (py - 0.6 * u) * S, (px + 0.6 * u) * S, (py + 0.6 * u) * S], fill=(120, 90, 80))
        # pelo / gorra
        if L.hat in ("cap", "police"):
            self.poly(d, S, [(hx0 - 20 * u, hy0 - 10 * u), (hx0 - 17 * u, hy0 - 24 * u), (hx0 + 17 * u, hy0 - 24 * u), (hx0 + 20 * u, hy0 - 10 * u)], L.hat_col, ow)
            self.poly(d, S, [(hx0 - 21 * u, hy0 - 11 * u), (hx0 + 23 * u, hy0 - 11 * u), (hx0 + 26 * u, hy0 - 7 * u), (hx0 - 21 * u, hy0 - 7 * u)], INK, 1)
            self.ell(d, S, hx0, hy0 - 18 * u, 3.5 * u, 3 * u, (230, 190, 60), ow * 0.5)
        elif L.hair_style != "bald":
            pts = [(hx0 - 19 * u, hy0 - 2 * u), (hx0 - 17 * u, hy0 - 16 * u), (hx0 - 6 * u, hy0 - 23 * u), (hx0 + 10 * u, hy0 - 22 * u),
                   (hx0 + 19 * u, hy0 - 10 * u), (hx0 + 18 * u, hy0 - 3 * u), (hx0 + 8 * u, hy0 - 12 * u), (hx0 - 8 * u, hy0 - 11 * u)]
            self.poly(d, S, pts, L.hair, ow)
        # ojos
        (brow_tilt, brow_h), mouth = EXPR.get(expr, EXPR["neutral"])
        blink = (t * 0.9 + self.seed * 0.37) % 3.2 < 0.12
        lx, ly = 0.0, 0.0
        if look_at:
            dx, dy = look_at[0] - hx0, look_at[1] - hy0
            n = math.hypot(dx, dy) or 1
            lx, ly = dx / n, dy / n
        eye_r = 6.2 * u * (1.25 if expr in ("shock", "scared") else 1.0)
        for side in (-1, 1):
            ex, ey = hx0 + side * 8 * u, hy0 - 2 * u
            if blink:
                d.line(_p(S, [(ex - eye_r, ey), (ex + eye_r, ey)]), fill=INK, width=int(ow * S))
            else:
                self.ell(d, S, ex, ey, eye_r * 0.85, eye_r, (255, 255, 255), ow * 0.7)
                pr = 2.6 * u * (0.8 if expr in ("shock", "scared") else 1.0)
                px, py = ex + lx * 2.4 * u, ey + ly * 2.6 * u
                d.ellipse([(px - pr) * S, (py - pr) * S, (px + pr) * S, (py + pr) * S], fill=INK)
                d.ellipse([(px - pr * 0.3 - pr * 0.4) * S, (py - pr * 0.7 - pr * 0.3) * S, (px - pr * 0.3 + pr * 0.25) * S, (py - pr * 0.7 + pr * 0.35) * S], fill=(255, 255, 255))
            # ceja
            bt = brow_tilt * side if expr != "sly" else (brow_tilt if side > 0 else -0.1)
            byy = ey - eye_r - 3 * u + brow_h * 10 * u
            d.line(_p(S, [(ex - 6 * u, byy + bt * 5 * u), (ex + 6 * u, byy - bt * 5 * u)]), fill=INK, width=int(2.6 * u * S))
        # nariz
        self.ell(d, S, hx0 + face_dir * 2 * u, hy0 + 6 * u, 3.6 * u, 3.2 * u, tuple(max(0, c - 25) for c in L.skin), ow * 0.6)
        if L.extra.get("sunglasses"):
            for side in (-1, 1):
                self.ell(d, S, hx0 + side * 8 * u, hy0 - 2 * u, 7.5 * u, 5.5 * u, (25, 25, 32), ow * 0.6)
            d.line(_p(S, [(hx0 - 2 * u, hy0 - 3 * u), (hx0 + 2 * u, hy0 - 3 * u)]), fill=INK, width=int(1.5 * u * S))
        if L.extra.get("mustache"):
            c = L.extra.get("mustache_col", L.hair)
            self.ell(d, S, hx0 - 4 * u, hy0 + 9.5 * u, 5.5 * u, 2.2 * u, c, ow * 0.5)
            self.ell(d, S, hx0 + 4 * u, hy0 + 9.5 * u, 5.5 * u, 2.2 * u, c, ow * 0.5)
        # boca
        mx, my = hx0, hy0 + 13 * u
        mo = mouth_open if mouth_open is not None else None
        if mo is not None and mo > 0.05:
            self.ell(d, S, mx, my, 5 * u, 1.5 * u + 5 * u * mo, (120, 30, 40), ow * 0.6)
        elif mouth == "smile":
            d.arc([(mx - 7 * u) * S, (my - 6 * u) * S, (mx + 7 * u) * S, (my + 3 * u) * S], 20, 160, fill=INK, width=int(2.4 * u * S))
        elif mouth == "grin":
            d.chord([(mx - 9 * u) * S, (my - 6 * u) * S, (mx + 9 * u) * S, (my + 6 * u) * S], 0, 180, fill=(255, 255, 255), outline=INK, width=int(1.6 * u * S))
        elif mouth == "smirk":
            d.arc([(mx - 4 * u) * S, (my - 5 * u) * S, (mx + 8 * u) * S, (my + 2 * u) * S], 10, 120, fill=INK, width=int(2.4 * u * S))
        elif mouth == "O":
            self.ell(d, S, mx, my + 1 * u, 4.5 * u, 6 * u, (120, 30, 40), ow * 0.6)
        elif mouth == "wobble":
            pts = [(mx - 7 * u + i * 2 * u, my + (1.2 * u if i % 2 else -1.2 * u)) for i in range(8)]
            d.line(_p(S, pts), fill=INK, width=int(2 * u * S))
        elif mouth == "sad":
            d.arc([(mx - 6 * u) * S, (my - 1 * u) * S, (mx + 6 * u) * S, (my + 7 * u) * S], 200, 340, fill=INK, width=int(2.4 * u * S))
        elif mouth == "shout":
            self.ell(d, S, mx, my + 1 * u, 7 * u, 5 * u, (120, 30, 40), ow * 0.6)
        else:
            d.line(_p(S, [(mx - 5 * u, my), (mx + 5 * u, my)]), fill=INK, width=int(2.2 * u * S))
        if expr in ("scared", "shock"):  # gota de sudor
            self.ell(d, S, hx0 + 18 * u, hy0 - 10 * u + (t * 30 % 10) * u * 0.3, 2.2 * u, 3.2 * u, (140, 200, 255), ow * 0.4)
        return {"head": (hx0, hy0), "u": u, "hand_r": None}

    @staticmethod
    def arm_angles(pose, t, walk):
        """(ángulo hombro, ángulo codo) por brazo: 0 = hacia abajo; positivo = hacia fuera."""
        if pose == "wave":
            return [(0.15, 0.1), (2.6, 0.5 + 0.45 * math.sin(t * 9))]
        if pose == "cheer":
            return [(2.7 + 0.15 * math.sin(t * 8), 0.2), (2.7 + 0.15 * math.sin(t * 8 + 1), 0.2)]
        if pose == "hands_up":
            return [(2.4, 0.5), (2.4, 0.5)]
        if pose == "run":
            s = math.sin(walk)
            return [(0.6 * s, -1.2), (-0.6 * s, -1.2)]
        if pose == "hold":
            return [(0.7, -1.4), (0.7, -1.4)]
        if pose == "shrug":
            return [(1.2, -2.0), (1.2, -2.0)]
        if pose == "point":
            return [(0.15, 0.1), (1.55, 0.0)]
        if pose == "dance":
            return [(2.4 + 0.6 * math.sin(t * 8), 0.4), (0.8 + 0.6 * math.sin(t * 8 + 3), 0.6)]
        if pose == "grab_bars":
            return [(1.3, -0.4), (1.3, -0.4)]
        s = math.sin(walk) if walk else 0
        return [(0.12 + 0.35 * s, 0.15), (0.12 - 0.35 * s, 0.15)]
