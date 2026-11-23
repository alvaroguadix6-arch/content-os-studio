"""NIVEL OCULTO · ¿Qué pasaría si un rayo cayera sobre tu coche?

Fuentes: NOAA / National Weather Service (Lightning Safety: un coche de techo metálico protege por su carrocería, no
por los neumáticos; la corriente va por la estructura exterior y salta al suelo; daños posibles: electrónica, antena,
pintura, neumáticos reventados; descapotables y coches de fibra/plástico no protegen igual; no tocar partes
metálicas, ventanillas subidas), NOAA (un rayo: ~30.000 A típicos; calienta el aire a ~30.000 °C ≈ 5 veces la
superficie del Sol, ~5.500 °C).
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, W, H, S, YEL, Video, back_out, clamp, draw_car, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "suspense", 92
BOLT = (200, 220, 255)
NIGHT = ((10, 12, 26), (34, 32, 52))


class VIDEO(Video):
    NAME = "rayo"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"rayo", "coche", "seguro", "dentro", "cree", "ruedas", "goma", "kilómetros", "aire", "parar", "treinta", "amperios",
                "grados", "cinco", "sol", "carrocería", "metal", "fuera", "chapa", "suelo", "jaula", "faraday", "corriente", "pintura",
                "antena", "electrónica", "reventada", "tormenta", "ventanillas", "metálicas", "descapotables", "fibra", "comentarios"}

    def setup(self):
        self.car = draw_car((200, 50, 60), 620, "car")
        self.car_s = draw_car((200, 50, 60), 420, "car")
        self.conv = draw_car((60, 130, 200), 560, "car")
        self.t_hit = self.w("intro", "rayo") + 0.2
        self.shakes = [(self.t_hit, 1.0), (self.start("jaula") + 0.5, 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "golpe"), (st("mito") - 0.12, "mito"), (st("potencia") - 0.12, "potencia"), (st("jaula") - 0.12, "jaula"),
                (st("faraday") - 0.12, "faraday"), (st("danos") - 0.12, "danos"), (st("consejo") - 0.12, "consejo"),
                (st("ojo") - 0.12, "ojo"), (st("cta") - 0.1, "fin")]

    # ───── piezas ─────
    def bolt(self, img, d, x0, y0, x1, y1, seed, alpha=1.0, width=10, branches=3):
        if alpha <= 0.05:
            return
        r = random.Random(seed)
        pts, n = [(x0, y0)], 14
        for i in range(1, n):
            f = i / n
            pts.append((x0 + (x1 - x0) * f + r.uniform(-60, 60), y0 + (y1 - y0) * f + r.uniform(-10, 10)))
        pts.append((x1, y1))
        lay_col = tuple(int(c * alpha + 0 * (1 - alpha)) for c in BOLT)
        for b in range(branches):
            i = r.randint(2, n - 4)
            bx, by = pts[i]
            ex, ey = bx + r.uniform(-220, 220), by + r.uniform(120, 300)
            self.Ln(d, [(bx, by), ((bx + ex) / 2 + r.uniform(-40, 40), (by + ey) / 2), (ex, ey)], lay_col, width * 0.4)
        self.Ln(d, pts, lay_col, width)
        if alpha > 0.5:
            self.Ln(d, pts, (255, 255, 255), width * 0.4)
        self.glow(img, (x0 + x1) / 2, (y0 + y1) / 2, abs(y1 - y0) * 0.5, (150, 170, 255), 120 * alpha)

    def storm(self, img, d, t, flash=0.0):
        self.bgdyn(img, mix(NIGHT[0], (180, 190, 230), flash), mix(NIGHT[1], (150, 160, 200), flash))
        for i in range(5):  # nubes
            x = (i * 260 + t * 12) % (W + 300) - 150
            self.cloud(d, x, 420 + 40 * (i % 2), 2.2, mix((40, 42, 60), (120, 125, 150), flash))
        for i in range(60):  # lluvia
            x = (i * 97 + t * 140) % W
            y = (i * 211 + t * 1600) % H
            self.Ln(d, [(x, y), (x - 12, y + 40)], (120, 140, 180), 2)

    def road(self, d, y, t):
        self.R(d, 0, y, W, H, (30, 30, 36))
        for i in range(6):
            x = (i * 220 - t * 160) % (W + 220) - 110
            self.R(d, x, y + 60, x + 120, y + 74, (220, 210, 120))

    def flash_k(self, t, t0):
        dt = t - t0
        if dt < 0:
            return 0.0
        return max(0.0, 1 - dt / 0.25) + 0.7 * max(0.0, 1 - abs(dt - 0.38) / 0.1) + 0.6 * max(0.0, 1 - abs(dt - 0.68) / 0.1)

    # ───── escenas ─────
    def s_golpe(self, img, d, t, lt, u):
        fk = self.flash_k(t, self.t_hit)
        self.storm(img, d, t, fk)
        self.road(d, 1350, t)
        self.paste(img, self.car, 540, 1380 + 3 * math.sin(t * 20))
        dt = t - self.t_hit
        for a0, a1 in ((0, 0.2), (0.32, 0.5), (0.62, 0.8)):  # un rayo real parpadea varias veces
            if a0 <= dt < a1:
                self.bolt(img, d, 600, 380, 560, 1150, seed=int(self.t_hit * 10), alpha=1 - (dt - a0) / (a1 - a0) * 0.5, width=18)
        if t > self.t_hit:  # la chapa brilla un instante
            g = max(0, 1 - (t - self.t_hit) / 0.8)
            self.glow(img, 540, 1250, 330, (160, 190, 255), 160 * g)
        self.pop_text(img, 540, 1640, "QUÉDATE DENTRO", 88, t, self.w("intro", "dentro"), YEL)

    def s_mito(self, img, d, t, lt, u):
        self.bg(img, "mito", (16, 18, 34), (34, 34, 56))
        tk = self.w("mito", "kilómetros") - 0.2
        if t < tk:
            # rueda de goma tachada
            self.E(d, 540, 960, 260, (26, 26, 30))
            self.E(d, 540, 960, 150, (150, 150, 160))
            self.E(d, 540, 960, 50, (90, 90, 100))
            for i in range(12):
                a = i / 12 * 2 * math.pi + t * 0.5
                self.Ln(d, [(540 + math.cos(a) * 200, 960 + math.sin(a) * 200), (540 + math.cos(a) * 250, 960 + math.sin(a) * 250)], (50, 50, 56), 14)
            k = smooth(self.w("mito", "salvan"), self.w("mito", "salvan") + 0.4, t)
            if k > 0:
                self.Ln(d, [(300, 720), (300 + 480 * k, 720 + 480 * k)], RED, 26)
                self.Ln(d, [(780, 720), (780 - 480 * k, 720 + 480 * k)], RED, 26)
            self.text(img, 540, 1360, "LAS RUEDAS NO TE SALVAN", 56, WHITE, alpha=smooth(0.3, 0.8, lt))
        else:  # comparación: kilómetros de aire vs centímetros de goma
            k = ease_out((t - tk) / 1.2)
            self.R(d, 300, 1600 - 1150 * k, 400, 1600, (120, 150, 230), radius=20)
            self.bolt(img, d, 350, 1600 - 1150 * k, 350, 1600, seed=7, alpha=0.8, width=8, branches=1)
            self.text(img, 350, 1660, "AIRE: km", 48, CYAN)
            self.R(d, 690, 1586, 790, 1600, (60, 60, 70))
            self.text(img, 740, 1660, "GOMA: cm", 48, (200, 200, 210))
            self.pop_text(img, 740, 1450, "← NO LO PARA", 50, t, self.w("mito", "parar"), RED)

    def s_potencia(self, img, d, t, lt, u):
        self.bg(img, "pot", (14, 12, 34), (40, 22, 52))
        ka = smooth(0.2, 1.4, lt)
        self.text(img, 540, 520, f"{int(30000 * ka):,} A".replace(",", "."), 110, (150, 180, 255))
        self.text(img, 540, 620, "AMPERIOS", 40, WHITE)
        tg = self.w("potencia", "grados") - 0.4
        kb = smooth(tg, tg + 1.4, t)
        if kb > 0:
            base = 1550
            hs = 140  # Sol: 5.500 °C
            hr = 140 * 30000 / 5500 * kb
            self.R(d, 230, base - hs, 430, base, (255, 190, 70), radius=16)
            self.E(d, 330, base - hs - 60, 46, (255, 214, 120))
            self.text(img, 330, base + 50, "SOL 5.500 °C", 40, (255, 200, 90))
            self.R(d, 650, base - hr, 850, base, (170, 190, 255), radius=16)
            self.bolt(img, d, 750, base - hr - 120, 750, base - hr, seed=3, alpha=0.9, width=8, branches=0)
            self.text(img, 750, base + 50, f"RAYO {int(30000 * kb):,} °C".replace(",", "."), 40, (170, 190, 255))
            self.pop_text(img, 540, 760, "×5 EL SOL", 80, t, self.w("potencia", "cinco"), YEL)

    def car_current(self, img, d, x, y, t, t0, scale=1.0):
        """La corriente recorre la chapa (techo → pilares → bajos) y salta al suelo."""
        w = 620 * scale
        path = [(x - 0.05 * w, y - 0.55 * w * 0.42), (x + 0.18 * w, y - 0.52 * w * 0.42), (x + 0.33 * w, y - 0.25 * w * 0.42),
                (x + 0.44 * w, y - 0.1 * w * 0.42), (x + 0.30 * w, y - 0.02 * w * 0.42), (x + 0.30 * w, y + 0.05 * w)]
        k = clamp((t - t0) / 1.2)
        n = max(2, int(len(path) * k + 1))
        pts = path[:n]
        self.Ln(d, pts, (190, 215, 255), 14)
        self.Ln(d, pts, WHITE, 5)
        if k >= 1:  # chispa al suelo
            ph = (t * 8) % 1
            self.bolt(img, d, x + 0.30 * w, y + 0.05 * w, x + 0.33 * w, y + 0.05 * w + 70, seed=int(t * 10), alpha=0.6 + 0.4 * ph, width=6, branches=0)

    def s_jaula(self, img, d, t, lt, u):
        self.storm(img, d, t, 0.15 * self.flash_k(t, self.start("jaula") + 0.3))
        self.road(d, 1350, t * 0)
        self.paste(img, self.car, 540, 1380)
        self.bolt(img, d, 540, 380, 520, 1090, seed=11, alpha=max(0, 1 - lt / 0.6), width=14)
        self.car_current(img, d, 540, 1380, t, self.start("jaula") + 0.4)
        self.E(d, 470, 1222, 30, (240, 200, 170))  # conductor
        self.glow(img, 470, 1210, 70, (90, 230, 140), 120 * smooth(0.8, 1.4, lt))


    def s_faraday(self, img, d, t, lt, u):
        self.bg(img, "far", (10, 14, 30), (24, 28, 52))
        k = ease_out(lt / 0.8)
        cx, cy, r = 540, 1000, 330
        for i in range(9):  # barrotes de la jaula
            x = cx - r + i * (2 * r / 8)
            self.Ln(d, [(x, cy - r * k), (x, cy + r)], (170, 175, 190), 8)
        for j in range(5):
            y = cy - r + j * (2 * r / 4)
            if y >= cy - r * k:
                self.Ln(d, [(cx - r, y), (cx + r, y)], (170, 175, 190), 8)
        p = (lt * 0.8) % 1  # chispa que corre por el contorno
        per = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r)]
        seg = 0 if p < 0.5 else 1
        f = (p % 0.5) * 2
        a, b = per[seg], per[seg + 1]
        sx, sy = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        self.glow(img, sx, sy, 60, (170, 200, 255), 220)
        self.E(d, sx, sy, 12, WHITE)
        from motor import Person
        if not hasattr(self, "_p"):
            self._p = Person(random.Random(3), 540, 300)
        self.person(img, self._p, cx, cy + r - 10, face="smile")
        self.pop_text(img, 540, 520, "JAULA DE FARADAY", 82, t, self.w("faraday", "faraday"), YEL)

    def s_danos(self, img, d, t, lt, u):
        self.bg(img, "dan", (14, 16, 30), (30, 32, 50))
        self.R(d, 0, 1360, W, H, (36, 36, 44))
        self.paste(img, self.car, 540, 1380)
        items = [("pintura", 400, 1180, "PINTURA"), ("antena", 700, 1020, "ANTENA"), ("electrónica", 560, 1240, "ELECTRÓNICA"), ("rueda", 720, 1340, "RUEDA")]
        for i, (frag, x, y, lab) in enumerate(items):
            tk = self.w("danos", frag)
            k = back_out((t - tk) / 0.35)
            if k <= 0:
                continue
            if frag == "pintura":
                for j in range(5):
                    self.E(d, x + j * 18 - 30, y + 8 * math.sin(j), 14 * k, (30, 24, 20))
            elif frag == "antena":
                self.Ln(d, [(x, y + 60), (x + 10, y - 40)], (255, 120, 40), 8 * k)
                self.glow(img, x + 10, y - 40, 40, (255, 140, 40), 200 * k)
            elif frag == "electrónica":
                self.R(d, x - 40 * k, y - 30 * k, x + 40 * k, y + 30 * k, (40, 60, 90), radius=6)
                self.Ln(d, [(x - 25 * k, y - 18 * k), (x + 25 * k, y + 18 * k)], RED, 6)
                self.Ln(d, [(x + 25 * k, y - 18 * k), (x - 25 * k, y + 18 * k)], RED, 6)
            else:
                self.star_shape(d, x, y, 60 * k, (255, 200, 80), rot=t)
            ly = 560 + i * 110
            self.text(img, 540, ly, "✕ " + lab if False else lab, 60, RED if frag != "pintura" else (255, 170, 120), alpha=clamp(k))

    def s_consejo(self, img, d, t, lt, u):
        self.storm(img, d, t, 0.0)
        self.R(d, 90, 520, 990, 1500, (16, 18, 34), radius=40, outline=(90, 110, 170), width=4)
        items = [("para", "PARA EN UN SITIO SEGURO"), ("dentro", "QUÉDATE DENTRO"), ("ventanillas", "VENTANILLAS SUBIDAS"), ("toques", "NO TOQUES EL METAL")]
        for i, (frag, lab) in enumerate(items):
            k = back_out((t - self.w("consejo", frag)) / 0.35)
            if k <= 0:
                continue
            y = 650 + i * 220
            self.E(d, 190, y, 44 * k, (70, 200, 110))
            self.Ln(d, [(168, y), (186, y + 20), (216, y - 22)], WHITE, 10)
            self.text(img, 260, y, lab, 50 * min(1, k), WHITE, anchor="lm")

    def s_ojo(self, img, d, t, lt, u):
        self.storm(img, d, t, self.flash_k(t, self.start("ojo") + 0.6) * 0.5)
        self.road(d, 1350, t * 0)
        self.paste(img, self.conv, 540, 1380)
        # capota de lona
        self.P(d, [(380, 1160), (470, 1070), (650, 1070), (720, 1160)], (220, 215, 200))
        if lt > 0.6:
            self.bolt(img, d, 560, 380, 560, 1080, seed=21, alpha=max(0, 1 - (lt - 0.6) / 0.6), width=12)
        k = back_out((t - self.w("ojo", "descapotables")) / 0.4)
        if k > 0:
            self.Ln(d, [(380, 900), (380 + 320 * k, 900 + 320 * k)], RED, 22)
            self.Ln(d, [(700, 900), (700 - 320 * k, 900 + 320 * k)], RED, 22)
        self.pop_text(img, 540, 620, "LONA Y FIBRA: NO", 76, t, self.w("ojo", "fibra"), RED)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def overlay(self, ov, d, t, name, lt, u):
        if name == "jaula":
            self.pop_text(ov, 540, 560, "LA CORRIENTE VA POR FUERA", 58, t, self.w("jaula", "fuera"), YEL)
            self.pop_text(ov, 540, 1620, "→ Y SALTA AL SUELO", 66, t, self.w("jaula", "suelo"), (190, 215, 255))
            return True
        return False

    def camera(self, t, name, lt, u):
        if name == "golpe":
            return 1.12 - 0.1 * smooth(0, 2.5, lt), 540, 1150
        if name == "jaula":
            k = smooth(0.3, 2.5, lt)
            return 1.0 + 0.45 * k, 540 + 60 * k, 1150 + 60 * k
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.1, "wind", 0.4), (self.t_hit, "crack", 0.9), (self.t_hit + 0.05, "boom", 1.0), (self.w("intro", "dentro"), "pop", 0.5),
                (self.w("mito", "salvan"), "click", 0.6), (self.w("mito", "kilómetros"), "whoosh", 0.4), (st("potencia") + 0.2, "riser", 0.4),
                (self.w("potencia", "cinco"), "boom", 0.6), (st("jaula") + 0.3, "crack", 0.7), (st("jaula") + 0.35, "boom", 0.6),
                (self.w("faraday", "faraday"), "shimmer", 0.5)] + \
               [(self.w("danos", f), "pop", 0.5) for f in ("pintura", "antena", "electrónica", "rueda")] + \
               [(self.w("consejo", f), "tick", 0.8) for f in ("para", "dentro", "ventanillas", "toques")] + \
               [(st("ojo") + 0.6, "crack", 0.6), (self.w("ojo", "descapotables"), "click", 0.5), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.6), (self.t_hit, 1.0), (st("mito"), 0.6), (st("potencia"), 0.85), (st("jaula"), 0.95), (st("faraday"), 0.6),
                (st("consejo"), 0.55), (st("ojo"), 0.75), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
