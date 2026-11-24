"""NIVEL OCULTO · GTA VI: el récord de su primer día (tendencia, 24-11-2026).

Fuentes: nota de Take-Two a la SEC (20-11-2026) y Variety, Kotaku, GameSpot, Quartz: 3.790 M$ en ventas minoristas
estimadas el primer día (hasta el final del 19-11), 32,5 millones de copias vendidas antes del lanzamiento; Metacritic
99, empatado con «The Legend of Zelda: Ocarina of Time»; GTA V hizo ~800 M$ en su primer día (2013, Reuters);
Vengadores: Endgame recaudó ~2.799 M$ en cines en total. 3.790 M$ / 86.400 s ≈ 43.866 $/s. España ≈ 49 M hab.
Decorado de estilo propio (sin logotipos ni personajes del juego).
"""
from __future__ import annotations

import math
import random

from gta6 import NEON, PINK, VIDEO as GTA
from motor import CYAN, RED, WHITE, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "epico", 104
GREEN = (90, 200, 110)
PER_S = 3.79e9 / 86400


class VIDEO(GTA):
    NAME = "gta6_record"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"gta", "seis", "día", "endgame", "historia", "take-two", "setecientos", "noventa", "millones", "veinticuatro", "marvel",
                "ochocientos", "supera", "mil", "cinco", "veces", "treinta", "copias", "españoles", "noventa", "nueve", "zelda",
                "segundo", "cuarenta", "cuatro", "dos", "estimadas", "beneficios", "lanzamiento", "comentarios"}

    def setup(self):
        super().setup()
        r = random.Random(8)
        self.bills = [(r.uniform(0, W), r.uniform(-H, 0), r.uniform(0.7, 1.3), r.uniform(0, 6.28), r.uniform(220, 420)) for _ in range(46)]
        self.shakes = [(self.w("intro", "endgame"), 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "golpe"), (st("cifra") - 0.12, "reloj"), (st("endgame") - 0.12, "vsend"), (st("gta5") - 0.12, "vsgta5"),
                (st("copias") - 0.12, "copias"), (st("nota") - 0.12, "nota"), (st("segundo") - 0.12, "segundo"), (st("ojo") - 0.12, "ojo"),
                (st("cta") - 0.1, "fin")]

    # ───── piezas ─────
    def money_rain(self, d, t, k=1.0):
        for x, y0, s, ph, v in self.bills:
            y = (y0 + t * v) % (H + 300) - 150
            if k < 1 and (x * 7) % 1000 / 1000 > k:
                continue
            a = math.sin(t * 2 + ph) * 0.5
            w, h = 90 * s, 44 * s
            c, sn = math.cos(a), math.sin(a)
            pts = [(x + (px * c - py * sn), y + (px * sn + py * c)) for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
            self.P(d, pts, (110, 190, 110))
            self.E(d, x, y, 12 * s, (70, 140, 80))

    def bars(self, img, d, t, t0, items, maxv, y_base=1460, hmax=760):
        n = len(items)
        for i, (lab, sub, v, col, delay) in enumerate(items):
            if t < t0 + delay:
                continue
            k = ease_out(clamp((t - t0 - delay) / 1.2))
            x = 540 + (i - (n - 1) / 2) * 380
            h = hmax * v / maxv * k
            self.R(d, x - 130, y_base - h, x + 130, y_base, col, radius=18)
            self.text(img, x, y_base - h - 60, f"{v * k:,.0f}".replace(",", ".") + " M$", 58, WHITE)
            self.text(img, x, y_base + 50, lab, 46, col)
            self.text(img, x, y_base + 100, sub, 30, (210, 200, 230))

    # ───── escenas ─────
    def s_golpe(self, img, d, t, lt, u):
        self.sunset(img, d, t, night=0.55)
        self.money_rain(d, t, smooth(0, 1.5, lt))
        k = ease_out(clamp(lt / 2.2))
        self.pop_text(img, 540, 530, "GTA VI", 150, t, 0.1, PINK)
        self.text(img, 540, 690, f"{3790 * k:,.0f}".replace(",", ".") + " M$", 120, YEL)
        self.pop_text(img, 540, 810, "EN 1 DÍA", 90, t, 0.6, WHITE)
        tk = self.w("intro", "endgame")
        kk = back_out((t - tk) / 0.4)
        if kk > 0:
            self.R(d, 540 - 440 * kk, 1430 - 120 * kk, 540 + 440 * kk, 1430 + 120 * kk, (20, 10, 40), radius=34, outline=PINK, width=7)
            self.text(img, 540, 1385, "MÁS QUE ENDGAME", 70 * kk, NEON)
            self.text(img, 540, 1475, "EN TODA SU VIDA", 70 * kk, WHITE)

    def s_reloj(self, img, d, t, lt, u):
        self.bgdyn(img, (16, 8, 34), (40, 14, 60))
        self.money_rain(d, t, 0.4)
        k = smooth(0.2, self.end("cifra") - self.start("cifra"), lt)
        cx, cy, r = 540, 960, 300
        self.E(d, cx, cy, r + 20, (30, 18, 50))
        d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], -90, -90 + 360 * k, fill=PINK, width=int(34 * S))
        self.text(img, cx, cy - 40, f"{int(24 * k)} h", 110, WHITE)
        self.text(img, cx, cy + 80, f"{3790 * k:,.0f} M$".replace(",", "."), 70, YEL)
        self.pop_text(img, 540, 1440, "SEGÚN TAKE-TWO", 56, t, self.w("cifra", "take"), NEON)

    def s_vsend(self, img, d, t, lt, u):
        self.bgdyn(img, (14, 10, 30), (34, 18, 54))
        self.bars(img, d, t, self.start("endgame"), [("ENDGAME", "toda su vida en cines", 2799, (150, 120, 220), 0.2),
                                                     ("GTA VI", "solo el primer día", 3790, PINK, self.w("endgame", "supera") - self.start("endgame"))], 3790)
        k = back_out((t - self.w("endgame", "día") - 0.1) / 0.4)
        if k > 0:
            self.pop_text(img, 540, 560, "+ ≈1.000 M$", 96, t, self.w("endgame", "supera") + 0.5, YEL)

    def s_vsgta5(self, img, d, t, lt, u):
        self.bgdyn(img, (14, 10, 30), (34, 18, 54))
        self.bars(img, d, t, self.start("gta5"), [("GTA V", "primer día (2013)", 800, NEON, 0.2), ("GTA VI", "primer día (2026)", 3790, PINK, 0.9)], 3790)
        self.pop_text(img, 350, 900, "×4,7", 150, t, self.w("gta5", "veces") - 0.3, YEL)

    def s_copias(self, img, d, t, lt, u):
        self.bgdyn(img, (12, 10, 30), (30, 18, 50))
        k = smooth(0.2, 2.0, lt)
        self.text(img, 540, 560, f"{32.5 * k:.1f}".replace(".", ",") + " MILLONES", 92, YEL)
        self.text(img, 540, 660, "DE COPIAS ANTES DE SALIR", 44, WHITE)
        for i in range(int(36 * k)):  # cajas que se apilan
            x = 160 + (i % 9) * 95
            y = 1060 - (i // 9) * 70
            self.R(d, x, y, x + 80, y + 60, (40, 26, 70), radius=8, outline=PINK, width=3)
        tp = self.w("copias", "españoles")
        kp = back_out((t - tp + 0.6) / 0.4)
        if kp > 0:
            for j in range(3):
                x = 360 + j * 180
                col = PINK if j < 2 else (90, 80, 120)
                self.E(d, x, 1300, 46 * kp, col)
                self.R(d, x - 60 * kp, 1350, x + 60 * kp, 1500, col, radius=40)
            self.text(img, 540, 1580, "2 DE CADA 3 ESPAÑOLES", 60, WHITE, alpha=clamp(kp))

    def s_nota(self, img, d, t, lt, u):
        self.sunset(img, d, t, night=0.8)
        k = back_out((lt - 0.2) / 0.5)
        if k > 0:
            self.R(d, 540 - 190 * k, 900 - 190 * k, 540 + 190 * k, 900 + 190 * k, GREEN, radius=30)
            self.text(img, 540, 900, "99", 230 * k, WHITE)
        kz = back_out((t - self.w("nota", "zelda")) / 0.4)
        if kz > 0:
            self.R(d, 540 - 360 * kz, 1180, 540 + 360 * kz, 1290, (20, 10, 40), radius=26, outline=YEL, width=5)
            self.text(img, 540, 1235, "= ZELDA: OCARINA OF TIME", 44 * kz, YEL)
            pts = [(450, 640), (450, 580), (495, 615), (540, 560), (585, 615), (630, 580), (630, 640)]  # corona
            self.P(d, pts, YEL)

    def s_segundo(self, img, d, t, lt, u):
        self.bgdyn(img, (10, 8, 26), (30, 14, 46))
        self.money_rain(d, t, 0.6)
        tick = (lt % 1)
        self.text(img, 540, 620, f"{PER_S * min(1, tick * 1.6):,.0f} $".replace(",", "."), 120, YEL)
        self.text(img, 540, 740, "CADA SEGUNDO", 60, WHITE)
        d.arc([(540 - 120) * S, (1000 - 120) * S, (540 + 120) * S, (1000 + 120) * S], -90, -90 + 360 * tick, fill=NEON, width=int(20 * S))
        self.text(img, 540, 1000, "1 s", 70, WHITE)
        kv = back_out((t - self.w("segundo", "vídeo")) / 0.4)
        if kv > 0:
            tot = PER_S * self.duration
            self.R(d, 540 - 420 * kv, 1330, 540 + 420 * kv, 1490, (20, 10, 40), radius=30, outline=PINK, width=6)
            self.text(img, 540, 1385, "EN LO QUE DURA ESTE VÍDEO", 38 * kv, WHITE)
            self.text(img, 540, 1450, f"≈ {tot / 1e6:.1f} MILLONES $".replace(".", ","), 56 * kv, YEL)

    def s_ojo(self, img, d, t, lt, u):
        self.bgdyn(img, (14, 10, 30), (34, 18, 54))
        self.money_rain(d, t, 0.25)
        k = back_out((lt - 0.1) / 0.4) * (1 + 0.03 * math.sin(t * 4))
        self.text(img, 540, 760, "VENTAS ESTIMADAS", 76 * max(0.05, k), YEL)
        self.text(img, 540, 900, "≠", 140 * max(0.05, k), WHITE)
        self.text(img, 540, 1040, "BENEFICIOS", 76 * max(0.05, k), (200, 190, 230))
        self.pop_text(img, 540, 1360, "RÉCORD DE LA HISTORIA", 64, t, self.w("ojo", "ningún"), PINK)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        if 2.0 < t < self.start("cta") - 0.2:  # contador que no para: al ritmo del día 1
            return self.pill(out, f"MIENTRAS LO VES (RITMO DÍA 1): {PER_S * t:,.0f} $".replace(",", "."), PINK, size=40)
        return out

    def camera(self, t, name, lt, u):
        if name == "golpe":
            return 1.0 + 0.08 * smooth(0, 3, lt), 540, 1000
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        ev = [(0.1, "riser", 0.5), (0.6, "boom", 0.7), (self.w("intro", "endgame"), "boom", 0.8), (st("cifra") + 0.2, "whoosh", 0.4),
              (self.w("cifra", "take"), "pop", 0.4), (st("endgame") + 0.3, "riser", 0.4), (self.w("endgame", "supera") + 0.5, "boom", 0.6),
              (self.w("gta5", "veces") - 0.3, "pop", 0.6), (st("copias") + 0.2, "whoosh", 0.4), (self.w("copias", "españoles"), "pop", 0.5),
              (st("nota") + 0.2, "boom", 0.5), (self.w("nota", "zelda"), "shimmer", 0.5), (self.w("segundo", "vídeo"), "pop", 0.6),
              (st("ojo") + 0.1, "click", 0.6), (st("cta"), "pop", 0.6)]
        ev += [(st("segundo") + k, "tick", 0.7) for k in range(int(self.end("segundo") - st("segundo")))]
        return ev

    def music_plan(self):
        st = self.start
        return [(0, 0.85), (st("cifra"), 0.7), (st("endgame"), 0.9), (st("copias"), 0.7), (st("nota"), 0.8), (st("segundo"), 0.75),
                (st("ojo"), 0.5), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
