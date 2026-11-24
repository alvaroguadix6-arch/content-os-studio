"""NIVEL OCULTO · True crime: El Dioni, el vigilante que se llevó un furgón blindado (1989).

Fuentes: Wikipedia «El Dioni» (28-7-1989, empresa Candi S. A., 298 millones de pesetas, aprovechó la ausencia de sus
dos compañeros, repartió parte entre amigos, viajó a Brasil, detenido el 19-9-1989, diez meses en prisión en Brasil
antes de la extradición), Infobae (sin disparar un tiro; vida de lujo en Río; la policía lo confundió con un
narcotraficante), COPE (unos 140 millones de pesetas nunca aparecieron). 298.000.000 / 166,386 ≈ 1,79 M€ (al cambio).
Personaje representado solo como silueta (sin parecido con la persona real). Ilustración y estética propias.
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, W, H, S, YEL, Person, Video, back_out, clamp, draw_car, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "suspense", 96
NOIR = ((8, 10, 14), (24, 26, 34))
PAPER = (232, 222, 196)
BLOOD = (210, 40, 50)


class VIDEO(Video):
    NAME = "dioni"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"vigilante", "furgón", "blindado", "trescientos", "millones", "pesetas", "disparo", "dioni", "madrid", "julio", "ochenta",
                "nueve", "compañeros", "arranca", "doscientos", "noventa", "ocho", "euros", "amigos", "brasil", "río", "janeiro", "meses",
                "fiestas", "gastos", "atención", "septiembre", "policía", "detiene", "narcotraficante", "diez", "extraditado", "dinero",
                "recuperó", "cien", "nunca", "aparecieron", "falta", "comentarios"}

    def setup(self):
        r = random.Random(5)
        self.guard = Person(r, 540, 300, shirt=(40, 44, 60))
        self.guard.long_hair = False
        self.van = draw_car((150, 150, 160), 640, "van")
        self.bills = [(r.uniform(0, W), r.uniform(0, H), r.uniform(0.7, 1.3), r.uniform(0, 6.3), r.uniform(-300, 300)) for _ in range(40)]
        self.t_go = self.w("golpe", "arranca")
        self.shakes = [(self.t_go, 0.7), (self.w("caida", "detiene"), 0.8)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "expediente"), (st("fecha") - 0.1, "madrid"), (st("golpe") - 0.1, "golpe"), (st("botin") - 0.1, "botin"),
                (st("huida") - 0.1, "huida"), (st("rio") - 0.1, "rio"), (st("caida") - 0.1, "caida"), (st("carcel") - 0.1, "carcel"),
                (st("misterio") - 0.1, "misterio"), (st("cta") - 0.1, "fin")]

    # ───── piezas ─────
    def noir(self, img, d, t, tint=(0, 0, 0)):
        self.bgdyn(img, mix(NOIR[0], tint, 0.15), mix(NOIR[1], tint, 0.15))
        for i in range(18):  # polvo en el aire
            x = (i * 131 + t * 12) % W
            y = (i * 337 + t * 20 * (1 + i % 3)) % H
            self.E(d, x, y, 2 + i % 3, (70, 70, 80))

    def silhouette(self, img, x, y, scale=1.6, walk=0.0, pose="stand"):
        self.glow(img, x, y - 150 * scale, 150 * scale, (150, 170, 210), 110)  # contraluz
        sp, (ax, ay) = self.guard.sprite(pose, "normal", "down", walk, scale)
        from PIL import Image
        a = sp.getchannel("A")
        sil = Image.new("RGBA", sp.size, (12, 12, 16, 255))
        sil.putalpha(a)
        img.alpha_composite(sil, (int(x * S - ax), int(y * S - ay)))

    def stamp(self, img, x, y, txt, size, t, t0, col=BLOOD, rot=-10):
        k = back_out((t - t0) / 0.28)
        if k <= 0:
            return
        from PIL import Image, ImageDraw
        from motor import font
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        sc = 2 - k if k < 1 else 1
        f = font("ExtraBold", int(size * S * sc))
        tw = f.getlength(txt)
        dl.rectangle([x * S - tw / 2 - 26 * S, y * S - size * S * 0.72 * sc, x * S + tw / 2 + 26 * S, y * S + size * S * 0.72 * sc],
                     outline=col + (255,), width=int(8 * S))
        dl.text((x * S, y * S), txt, font=f, fill=col + (255,), anchor="mm")
        img.alpha_composite(lay.rotate(-rot, center=(x * S, y * S)))

    def money(self, d, t, k=1.0, wind=1.0):
        for x, y0, s, ph, vx in self.bills:
            if (x * 13) % 100 / 100 > k:
                continue
            xx = (x + vx * t * 0.3 * wind) % (W + 200) - 100
            y = (y0 + t * 180 * s) % (H + 200) - 100
            a = math.sin(t * 3 + ph) * 0.6
            w, h = 100 * s, 50 * s
            c, sn = math.cos(a), math.sin(a)
            pts = [(xx + (px * c - py * sn), y + (px * sn + py * c)) for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
            self.P(d, pts, (120, 150, 200))  # billetes de pesetas (tono azulado)
            self.E(d, xx, y, 10 * s, (80, 100, 150))

    def counter_txt(self, img, y, val, size, col):
        self.text(img, 540, y, f"{int(val):,}".replace(",", "."), size, col)

    # ───── escenas ─────
    def s_expediente(self, img, d, t, lt, u):
        self.noir(img, d, t)
        k = ease_out(clamp(lt / 0.6))
        self.R(d, 120, 620 + (1 - k) * 300, 960, 1480, (196, 160, 100), radius=14)  # carpeta
        self.R(d, 120, 560 + (1 - k) * 300, 420, 640 + (1 - k) * 300, (196, 160, 100), radius=14)
        self.R(d, 170, 700 + (1 - k) * 300, 910, 1430, PAPER)
        self.silhouette(img, 540, 1300 + (1 - k) * 300, 1.7)
        self.qmark(img, 540, 900 + (1 - k) * 300, 160, (232, 222, 196))
        self.stamp(img, 540, 760, "CASO 1989", 70, t, 0.5)
        n = 298e6 * ease_out(clamp((t - self.w("intro", "trescientos") + 0.2) / 1.2))
        if n > 0:
            self.counter_txt(img, 520, n, 84, YEL)
            self.text(img, 540, 600, "PESETAS", 40, WHITE)
        self.stamp(img, 540, 1580, "SIN UN SOLO DISPARO", 56, t, self.w("intro", "disparo"), WHITE, rot=4)

    def s_madrid(self, img, d, t, lt, u):
        self.noir(img, d, t, (40, 30, 10))
        for i in range(9):  # siluetas de edificios
            x = i * 130 - 20
            h = 300 + (i * 97) % 260
            self.R(d, x, 1300 - h, x + 120, 1300, (20, 22, 30))
            for wy in range(1300 - h + 30, 1280, 50):
                for wx in range(x + 16, x + 100, 34):
                    if (wx + wy + i) % 5 < 2:
                        self.R(d, wx, wy, wx + 14, wy + 20, (230, 190, 90))
        self.R(d, 0, 1300, W, H, (30, 30, 36))
        self.pop_text(img, 540, 520, "MADRID", 120, t, self.w("fecha", "madrid"), WHITE)
        k = back_out((t - self.w("fecha", "julio") + 0.3) / 0.4)
        if k > 0:
            self.R(d, 540 - 210 * k, 650, 540 + 210 * k, 760, PAPER, radius=12)
            self.text(img, 540, 705, "28 · JULIO · 1989", 46 * min(1, k), (40, 30, 20), shadow=False)
        kg = smooth(self.w("fecha", "vigilante") - 0.2, self.w("fecha", "vigilante") + 0.5, t)
        if kg > 0:
            self.silhouette(img, 540, 1290, 1.6)
            self.text(img, 540, 1560, "VIGILANTE DE SEGURIDAD", 56, YEL, alpha=kg)

    def s_golpe(self, img, d, t, lt, u):
        self.noir(img, d, t)
        self.R(d, 0, 1300, W, H, (30, 30, 36))
        for i in range(6):
            x = (i * 220 - (t - self.t_go) * 900 * (t > self.t_go)) % (W + 220) - 110
            self.R(d, x, 1380, x + 120, 1394, (200, 190, 120))
        go = max(0.0, t - self.t_go)
        vx = 540 + go * go * 900  # arranca y se va acelerando
        k2 = smooth(0.2, 1.2, lt)
        for j, sx in enumerate((200, 880)):  # los dos compañeros bajan
            if t < self.t_go + 0.5:
                self.silhouette(img, sx + (sx - 540) * 0.2 * k2, 1330, 1.2, walk=t * 6 * (k2 < 1))
        self.paste(img, self.van, vx, 1340 + 3 * math.sin(t * 25) * (go > 0))
        self.text(img, vx - 40, 1160, "CANDI S. A.", 40, (60, 60, 70), shadow=False)
        if go > 0:
            for i in range(8):
                self.Ln(d, [(vx - 360 - i * 40, 1230 + i * 12), (vx - 520 - i * 40, 1230 + i * 12)], (180, 180, 190), 4)
            self.pop_text(img, 540, 560, "Y ARRANCA", 110, t, self.t_go, YEL)
        else:
            self.text(img, 540, 560, "2 COMPAÑEROS BAJAN...", 64, WHITE, alpha=k2)

    def s_botin(self, img, d, t, lt, u):
        self.noir(img, d, t, (10, 30, 60))
        self.money(d, t, smooth(0, 1.2, lt))
        k = ease_out(clamp((lt - 0.2) / 1.6))
        self.counter_txt(img, 860, 298e6 * k, 120, YEL)
        self.text(img, 540, 980, "PESETAS", 56, WHITE)
        self.pop_text(img, 540, 1260, "≈ 1,8 MILLONES €", 84, t, self.w("botin", "cambio"), (120, 220, 140))
        self.text(img, 540, 1360, "al cambio", 40, (180, 180, 190), alpha=smooth(self.w("botin", "cambio"), self.w("botin", "cambio") + 0.4, t))

    def s_huida(self, img, d, t, lt, u):
        self.noir(img, d, t, (10, 20, 40))
        a = (180, 760)   # Madrid
        b = (860, 1380)  # Río
        self.E(d, *a, 22, YEL)
        self.text(img, a[0], a[1] - 60, "MADRID", 44, YEL)
        k = smooth(self.w("huida", "brasil") - 1.0, self.w("huida", "brasil") + 1.0, t)
        n = 40
        pts = [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f - 380 * math.sin(f * math.pi)) for f in [i / n for i in range(n + 1)]]
        m = max(2, int((n + 1) * k))
        for i in range(0, m - 1, 2):
            self.Ln(d, [pts[i], pts[i + 1]], WHITE, 5)
        px, py = pts[m - 1]
        self.P(d, [(px + 30, py), (px - 20, py - 14), (px - 10, py), (px - 20, py + 14)], WHITE)
        if k > 0.95:
            self.E(d, *b, 22, (120, 220, 140))
            self.text(img, b[0], b[1] + 60, "BRASIL", 44, (120, 220, 140))
        kf = smooth(self.w("huida", "amigos") - 0.3, self.w("huida", "amigos") + 0.4, t)
        for j in range(3):  # amigos con su parte
            if kf > 0:
                x = 300 + j * 240
                self.silhouette(img, x, 1650, 0.8 * kf + 0.01)
                self.R(d, x + 30, 1560, x + 80, 1590, (120, 150, 200))

    def s_rio(self, img, d, t, lt, u):
        self.bgdyn(img, (40, 10, 60), (240, 110, 90))
        self.P(d, [(560, 1300), (700, 900), (780, 860), (860, 960), (980, 1300)], (40, 20, 50))  # Pan de Azúcar
        self.P(d, [(0, 1300), (120, 1100), (260, 1200), (380, 1000), (500, 1300)], (50, 25, 60))
        self.R(d, 0, 1300, W, H, (20, 40, 80))
        for i in range(10):  # luces de fiesta
            c = [(255, 80, 160), (90, 230, 255), (255, 214, 70)][i % 3]
            x = 80 + i * 100
            self.glow(img, x, 600 + 60 * math.sin(t * 3 + i), 50, c, 140 + 80 * math.sin(t * 6 + i))
        self.money(d, t, 0.6, wind=2.0)
        self.silhouette(img, 540, 1520, 1.6, walk=t * 8)
        self.pop_text(img, 540, 480, "RÍO DE JANEIRO", 84, t, self.w("rio", "río"), WHITE)
        for j, (frag, lab) in enumerate((("hoteles", "HOTELES"), ("fiestas", "FIESTAS"), ("gastos", "GASTOS"))):
            k = back_out((t - self.w("rio", frag)) / 0.3)
            if k > 0:
                self.R(d, 120 + j * 290, 1660, 380 + j * 290, 1740, YEL, radius=18)
                self.text(img, 250 + j * 290, 1700, lab, 40 * min(1, k), (30, 20, 30), shadow=False)

    def s_caida(self, img, d, t, lt, u):
        on = int(t * 6) % 2
        self.noir(img, d, t, (60, 0, 0) if on else (0, 20, 80))
        self.glow(img, 200, 500, 300, (255, 40, 40) if on else (40, 80, 255), 170)
        self.glow(img, 880, 500, 300, (40, 80, 255) if on else (255, 40, 40), 170)
        self.silhouette(img, 540, 1450, 1.8)
        td = self.w("caida", "detiene")
        k = back_out((t - td) / 0.35)
        if k > 0:  # esposas
            for sx in (-1, 1):
                self.E(d, 540 + sx * 70, 1200, 52 * k, None, outline=(210, 210, 220), width=14)
            self.Ln(d, [(560 - 70, 1200), (470 + 140, 1200)], (210, 210, 220), 8)
        self.stamp(img, 540, 560, "DETENIDO · 19-9-1989", 60, t, td)
        self.pop_text(img, 540, 1650, "«CREÍAN QUE ERA UN NARCO»", 50, t, self.w("caida", "narcotraficante"), YEL)

    def s_carcel(self, img, d, t, lt, u):
        self.noir(img, d, t)
        self.silhouette(img, 540, 1420, 1.7)
        for i in range(9):  # barrotes
            x = 120 + i * 105
            self.R(d, x, 520, x + 24, 1500, (120, 124, 136))
        self.R(d, 100, 520, 980, 560, (120, 124, 136))
        self.R(d, 100, 1460, 980, 1500, (120, 124, 136))
        n = int(10 * ease_out(clamp((lt - 0.3) / 2.0)))
        self.text(img, 540, 1620, f"{n} MESES", 96, YEL)
        self.pop_text(img, 540, 1740, "EXTRADITADO A ESPAÑA", 50, t, self.w("carcel", "extraditado"), WHITE)

    def s_misterio(self, img, d, t, lt, u):
        self.noir(img, d, t, (20, 10, 40))
        for j in range(3):  # bolsas de dinero
            x = 270 + j * 270
            k = 1.0 if j == 0 else 1 - smooth(self.w("misterio", "nunca") - 0.2, self.w("misterio", "nunca") + 0.8, t)
            col = (190, 160, 100) if j == 0 else mix((40, 40, 50), (190, 160, 100), k)
            self.E(d, x, 1050, 110, col)
            self.R(d, x - 40, 920, x + 40, 960, col)
            self.text(img, x, 1060, "₧" if False else "PTA", 50, (60, 50, 30) if j == 0 else mix((70, 70, 80), (60, 50, 30), k), shadow=False)
            if j > 0 and k < 0.6:
                self.qmark(img, x, 1050, 150, YEL)
        self.pop_text(img, 270, 1240, "RECUPERADO", 40, t, self.w("misterio", "recuperó"), (120, 220, 140))
        self.stamp(img, 540, 1450, "+100 MILLONES DESAPARECIDOS", 50, t, self.w("misterio", "aparecieron"))
        self.pop_text(img, 540, 560, "¿Y EL DINERO?", 110, t, self.start("misterio") + 0.05, YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        if 1.5 < t < self.start("cta") - 0.2:
            return self.pill(out, "EXPEDIENTE: EL DIONI · 1989", BLOOD, y=1850, size=32)
        return out

    def camera(self, t, name, lt, u):
        if name in ("expediente", "carcel", "misterio"):
            return 1.0 + 0.08 * smooth(0, 4, lt), 540, 1000
        if name == "botin":
            return 1.0 + 0.05 * math.sin(t * 2) ** 2, 540, 960
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.1, "rumble", 0.5), (0.5, "boom", 0.7), (self.w("intro", "trescientos"), "riser", 0.4), (self.w("intro", "disparo"), "boom", 0.6),
                (st("fecha") + 0.2, "whoosh", 0.4), (self.w("fecha", "julio"), "pop", 0.5), (self.t_go, "horn", 0.4), (self.t_go + 0.1, "whoosh", 0.7),
                (st("botin") + 0.2, "shimmer", 0.5), (self.w("botin", "cambio"), "pop", 0.5), (self.w("huida", "brasil"), "whoosh", 0.6),
                (st("rio") + 0.2, "shimmer", 0.4), (self.w("rio", "hoteles"), "pop", 0.4), (self.w("rio", "fiestas"), "pop", 0.4),
                (self.w("rio", "gastos"), "pop", 0.4), (st("caida") + 0.1, "horn", 0.5), (self.w("caida", "detiene"), "boom", 0.9),
                (st("carcel") + 0.3, "click", 0.7), (st("misterio") + 0.1, "riser", 0.5), (self.w("misterio", "aparecieron"), "boom", 0.7),
                (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.8), (st("fecha"), 0.6), (st("golpe"), 0.9), (st("botin"), 0.75), (st("rio"), 0.85), (st("caida"), 1.0),
                (st("carcel"), 0.6), (st("misterio"), 0.85), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
