"""NIVEL OCULTO · Sorteo de 10 € para PlayStation Store al llegar a 100 seguidores/suscriptores.

Dos versiones (sorteo_ig.py / sorteo_yt.py). En YouTube, por sus políticas de concursos, la participación es el
comentario; suscribirse y dar «me gusta» se sugiere, no se exige. Ambas incluyen el aviso de que la plataforma no
patrocina el sorteo y remiten a las bases. Tarjeta regalo genérica, sin logotipos de marcas.
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "alegre", 112
PS_BLUE = (0, 90, 200)


class Sorteo(Video):
    BRAND = "NIVEL OCULTO"
    PLATFORM = "IG"
    KEYWORDS = {"sorteo", "nivel", "oculto", "cien", "seguidores", "suscriptores", "diez", "euros", "playstation", "store", "tres",
                "uno", "dos", "sigue", "gusta", "comenta", "boleto", "suscríbete", "azar", "ganador", "españa", "menor", "padres",
                "bases", "suerte"}

    def setup(self):
        r = random.Random(5)
        self.confetti = [(r.uniform(0, W), r.uniform(-1, 0), r.uniform(6, 14), r.choice((YEL, (255, 90, 120), CYAN, (120, 230, 120), WHITE)),
                          r.uniform(0, 6)) for _ in range(140)]
        self.names = ["@l*****", "@p****", "@m******", "@s****", "@d*****", "@a*****", "@n****", "@i*******"]  # nombres ocultos de ejemplo
        self.shakes = [(0.3, 0.4)]

    def build_scenes(self):
        sc = [(0.0, "premio"), (self.start("reglas") - 0.15, "lista")]
        sc += [(self.start("como") - 0.15, "azar"), (self.start("legal") - 0.15, "legal"), (self.start("cta") - 0.1, "fiesta")]
        return sc

    # ───── piezas ─────
    def giftcard(self, img, d, x, y, s=1.0, rot=0.0):
        w_, h_ = 520 * s, 330 * s
        self.R(d, x - w_ / 2 + 12, y - h_ / 2 + 16, x + w_ / 2 + 12, y + h_ / 2 + 16, (0, 0, 0), radius=30 * s)
        self.R(d, x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2, PS_BLUE, radius=30 * s)
        self.R(d, x - w_ / 2, y + h_ * 0.18, x + w_ / 2, y + h_ / 2, (0, 60, 150), radius=30 * s)
        self.text(img, x, y - h_ * 0.08, "10 €", 150 * s, WHITE)
        self.text(img, x, y + h_ * 0.33, "PLAYSTATION STORE", 34 * s, WHITE, "Bold", shadow=False)

    def confetti_layer(self, d, t, t0, amount=1.0):
        if t < t0:
            return
        for x, y0, sz, col, ph in self.confetti[: int(len(self.confetti) * amount)]:
            y = (y0 * H + (t - t0) * 420 * (0.7 + 0.3 * math.sin(ph))) % (H + 200) - 100
            xx = x + 40 * math.sin((t - t0) * 2 + ph)
            a = (t - t0) * 4 + ph
            self.P(d, [(xx + math.cos(a) * sz, y + math.sin(a) * sz * 0.5), (xx - math.sin(a) * sz * 0.5, y + math.cos(a) * sz),
                       (xx - math.cos(a) * sz, y - math.sin(a) * sz * 0.5), (xx + math.sin(a) * sz * 0.5, y - math.cos(a) * sz)], col)

    def icon(self, d, kind, x, y, s=1.0):
        if kind == "seguir":
            self.E(d, x - 12 * s, y - 22 * s, 22 * s, WHITE)
            self.E(d, x - 12 * s, y + 26 * s, 36 * s, WHITE, ry=22 * s)
            self.R(d, x + 28 * s, y - 4 * s, x + 60 * s, y + 4 * s, YEL)
            self.R(d, x + 40 * s, y - 16 * s, x + 48 * s, y + 16 * s, YEL)
        elif kind == "like":
            self.E(d, x - 16 * s, y - 8 * s, 22 * s, (255, 80, 110))
            self.E(d, x + 16 * s, y - 8 * s, 22 * s, (255, 80, 110))
            self.P(d, [(x - 37 * s, y - 2 * s), (x + 37 * s, y - 2 * s), (x, y + 38 * s)], (255, 80, 110))
        elif kind == "comentar":
            self.R(d, x - 42 * s, y - 32 * s, x + 42 * s, y + 22 * s, WHITE, radius=16 * s)
            self.P(d, [(x - 20 * s, y + 20 * s), (x - 32 * s, y + 42 * s), (x - 4 * s, y + 20 * s)], WHITE)
            for j in range(3):
                self.E(d, x - 20 * s + j * 20 * s, y - 5 * s, 5 * s, (30, 40, 70))
        elif kind == "suscribir":  # campana de notificaciones genérica
            self.P(d, [(x - 34 * s, y + 22 * s), (x - 26 * s, y - 14 * s), (x, y - 34 * s), (x + 26 * s, y - 14 * s), (x + 34 * s, y + 22 * s)], YEL)
            self.R(d, x - 40 * s, y + 18 * s, x + 40 * s, y + 28 * s, YEL, radius=5 * s)
            self.E(d, x, y + 36 * s, 9 * s, YEL)

    def row(self, img, d, y, kind, txt, t, t_in, note=None, done_col=(110, 220, 120)):
        k = back_out((t - t_in + 0.1) / 0.35)
        if k <= 0:
            return
        x0 = 90 + (1 - min(1, k)) * -600
        self.R(d, x0, y - 75, x0 + 900, y + 75, (22, 30, 54), radius=38, outline=YEL, width=4)
        self.icon(d, kind, x0 + 95, y, 1.0)
        self.text(img, x0 + 190, y - (14 if note else 0), txt, 52, WHITE, anchor="lm")
        if note:
            self.text(img, x0 + 190, y + 34, note, 30, CYAN, "Bold", anchor="lm", shadow=False)
        c = clamp((t - t_in - 0.6) / 0.25)
        if c > 0:
            self.E(d, x0 + 830, y, 40 * c, done_col)
            self.Ln(d, [(x0 + 808, y), (x0 + 825, y + 18), (x0 + 855, y - 16)], WHITE, 9)

    # ───── escenas ─────
    def s_premio(self, img, d, t, lt, u):
        self.bg(img, "end", (28, 48, 82), (14, 24, 44))
        self.stars(d, t, 0.6)
        self.glow(img, 540, 900, 380, YEL, 70)
        k = back_out((lt - 0.15) / 0.5)
        if k > 0:
            self.giftcard(img, d, 540, 880 + 14 * math.sin(t * 2), k, 0)
        self.pop_text(img, 540, 560, "¡SORTEO!", 140, t, 0.1, YEL)
        # meta: barra de seguidores hacia 100
        meta = "SEGUIDORES" if self.PLATFORM == "IG" else "SUSCRIPTORES"
        kk = smooth(self.w("intro", "cien") - 0.3, self.end("intro"), t)
        self.R(d, 140, 1300, 940, 1370, (40, 50, 80), radius=35)
        self.R(d, 150, 1310, 150 + 780 * kk, 1360, YEL, radius=25)
        self.text(img, 540, 1450, f"META: 100 {meta}", 56, WHITE)
        self.confetti_layer(d, t, 0.3, 0.5)

    def s_lista(self, img, d, t, lt, u):
        self.bg(img, "end", (28, 48, 82), (14, 24, 44))
        self.stars(d, t, 0.4)
        self.text(img, 540, 520, "CÓMO PARTICIPAR", 80, YEL)
        if self.PLATFORM == "IG":
            self.row(img, d, 760, "seguir", "SIGUE LA CUENTA", t, self.start("r1"))
            self.row(img, d, 960, "like", "DALE ME GUSTA", t, self.start("r2"))
            self.row(img, d, 1160, "comentar", "COMENTA EL VÍDEO", t, self.start("r3"))
        else:
            self.row(img, d, 800, "comentar", "COMENTA EL VÍDEO", t, self.start("r1"), "ESTE ES TU BOLETO")
            self.row(img, d, 1030, "suscribir", "SUSCRÍBETE", t, self.w("r2", "suscríbete"), "OPCIONAL · APOYA EL CANAL", CYAN)
            self.row(img, d, 1230, "like", "DALE ME GUSTA", t, self.w("r2", "dale"), "OPCIONAL", CYAN)
        self.giftcard(img, d, 540, 1550, 0.55)

    def s_azar(self, img, d, t, lt, u):
        self.bg(img, "end", (28, 48, 82), (14, 24, 44))
        self.stars(d, t, 0.4)
        self.text(img, 540, 520, "GANADOR AL AZAR", 76, YEL)
        spin = max(0.0, 2.6 - lt)  # la ruleta de comentarios se frena
        off = (lt * 6 * spin) % len(self.names) if spin > 0 else 3.0
        for i in range(-2, 3):
            idx = int(off + i) % len(self.names)
            y = 980 + (i - (off % 1)) * 130
            sel = i == 0 and spin <= 0
            self.R(d, 160, y - 52, 920, y + 52, YEL if sel else (22, 30, 54), radius=26)
            self.icon(d, "comentar", 240, y, 0.6)
            self.text(img, 310, y, self.names[idx] if not sel else "¿SERÁS TÚ?", 46, (20, 20, 30) if sel else WHITE, anchor="lm", shadow=False)
        self.text(img, 540, 1400, "CUANDO LLEGUEMOS A 100", 50, CYAN)

    def s_legal(self, img, d, t, lt, u):
        self.bg(img, "end", (28, 48, 82), (14, 24, 44))
        plat = "INSTAGRAM" if self.PLATFORM == "IG" else "YOUTUBE"
        items = [("VÁLIDO EN ESPAÑA", self.w("legal", "españa")),
                 (f"{plat} NO PATROCINA", self.w("legal", "patrocina")), ("BASES EN LA DESCRIPCIÓN", self.w("legal", "bases"))]
        for i, (txt, ti) in enumerate(items):
            k = clamp((t - ti + 0.2) / 0.3)
            if k > 0:
                y = 700 + i * 210
                self.R(d, 120, y - 64, 960, y + 64, (22, 30, 54), radius=32)
                self.text(img, 540, y, txt, 48, WHITE, alpha=k)

    def s_fiesta(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))
        self.pop_text(img, 540, 620, "¡SUERTE!", 130, t, self.start("cta") + 0.2, YEL)
        self.confetti_layer(d, t, self.start("cta"), 1.0)

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name == "lista":
            return self.pill(out, "PREMIO · 10 € PLAYSTATION STORE", YEL, y=1835, size=40)
        return out

    def sfx_events(self):
        st = self.start
        ev = [(0.1, "boom", 0.5), (0.3, "shimmer", 0.6), (0.35, "pop", 0.6), (self.w("intro", "cien"), "riser", 0.4)]
        for k in [k for k in ("r1", "r2", "r3") if k in self.L]:
            ev += [(st(k), "pop", 0.5), (st(k) + 0.6, "beep", 0.4)]
        ev += [(st("como") + 0.1, "tick", 0.5)] + [(st("como") + 0.15 * i, "tick", 0.4) for i in range(16)]
        ev += [(st("como") + 2.7, "shimmer", 0.6), (st("cta"), "boom", 0.4), (st("cta") + 0.2, "shimmer", 0.6)]
        return ev

    def music_plan(self):
        return [(0, 0.9), (self.start("legal"), 0.5), (self.start("cta"), 0.8), (self.duration, 0.4)]


def main(cls):
    import sys

    if sys.argv[1] == "plan":
        schedule(cls, sys.argv[2])
    else:
        render(cls, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
