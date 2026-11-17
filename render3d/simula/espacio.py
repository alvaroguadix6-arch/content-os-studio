"""10 cosas increíbles que no sabías sobre el espacio (datos verificables)."""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from motor import CYAN, RED, WHITE, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "espacio", 88


class VIDEO(Video):
    NAME = "espacio"
    KEYWORDS = {"diez", "espacio", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "nada", "aire", "venus", "día",
                "año", "noventa", "nueve", "masa", "huellas", "millones", "viento", "neutrones", "mil", "toneladas", "saturno", "flotaría",
                "bañera", "minutos", "olimpo", "marte", "everest", "estrellas", "arena", "agujero", "negro", "despacio", "sorprendido",
                "comentarios"}

    def setup(self):
        r = random.Random(12)
        self.warp = [(r.uniform(0, 2 * math.pi), r.uniform(0.05, 1.0), r.uniform(1, 3)) for _ in range(260)]
        self.sand = [(r.uniform(0, W), r.uniform(900, 1900), r.uniform(3, 7), r.choice(((235, 205, 150), (220, 185, 130), (245, 220, 170))))
                     for _ in range(700)]
        self.galaxy = [(r.uniform(0, 1), r.choice((0, math.pi)), r.gauss(0, 0.12)) for _ in range(900)]
        self.dust = [(r.uniform(-1, 1), r.uniform(-1, 1)) for _ in range(30)]

    def build_scenes(self):
        sc = [(0.0, "intro")]
        for i in range(1, 11):
            sc.append((self.start(f"d{i}") - 0.15, f"d{i}"))
        sc.append((self.start("cta") - 0.1, "fin"))
        return sc

    def space(self, img, d, t, drift=4.0):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0, drift)

    def planet(self, img, d, x, y, r, base, bands=None, t=0.0):
        self.E(d, x, y, r, base)
        if bands:
            for i, c in enumerate(bands):
                yy = y - r + (i + 1) * 2 * r / (len(bands) + 1)
                half = math.sqrt(max(0, r * r - (yy - y) ** 2))
                self.R(d, x - half + 4, yy - r * 0.07, x + half - 4, yy + r * 0.07, c, radius=r * 0.07)
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).chord([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], 300, 120, fill=(0, 0, 20, 90))
        img.alpha_composite(sh)

    def astronaut(self, img, x, y, sc, rot):
        size = int(320 * sc * S)
        a = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(a)
        c = size / 2
        u = size / 320
        wht, gr = (245, 246, 250), (200, 205, 215)
        d.rounded_rectangle([c - 70 * u, c - 30 * u, c + 70 * u, c + 90 * u], radius=30 * u, fill=gr)  # mochila
        for sx in (-1, 1):
            d.line([(c + sx * 45 * u, c + 10 * u), (c + sx * 95 * u, c + 50 * u)], fill=wht, width=int(32 * u))
            d.line([(c + sx * 25 * u, c + 80 * u), (c + sx * 40 * u, c + 140 * u)], fill=wht, width=int(36 * u))
        d.rounded_rectangle([c - 55 * u, c - 20 * u, c + 55 * u, c + 95 * u], radius=34 * u, fill=wht)
        d.ellipse([c - 60 * u, c - 110 * u, c + 60 * u, c + 10 * u], fill=wht)
        d.rounded_rectangle([c - 42 * u, c - 82 * u, c + 42 * u, c - 22 * u], radius=26 * u, fill=(30, 50, 90))
        d.ellipse([c - 30 * u, c - 75 * u, c - 8 * u, c - 58 * u], fill=(140, 180, 240))
        d.rectangle([c - 20 * u, c + 20 * u, c + 20 * u, c + 45 * u], fill=(220, 80, 70))
        a = a.rotate(rot, resample=Image.BICUBIC)
        img.alpha_composite(a, (int(x * S - size / 2), int(y * S - size / 2)))

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        sp = 0.4 + 2.0 * smooth(0, 2.5, lt)
        for ang, r0, w_ in self.warp:
            r = ((r0 + lt * sp * 0.35) % 1.0)
            r1, r2 = 60 + r * 1100, 60 + (r + 0.02 * sp) * 1100
            col = int(120 + 135 * r)
            self.Ln(d, [(540 + math.cos(ang) * r1, 960 + math.sin(ang) * r1), (540 + math.cos(ang) * r2, 960 + math.sin(ang) * r2)], (col, col, 255), w_)
        self.pop_text(img, 540, 960, "10", 300, t, 0.3, YEL)

    def s_d1(self, img, d, t, lt, u):
        self.space(img, d, t)
        self.astronaut(img, 420, 1050 + 20 * math.sin(t), 1.6, 12 * math.sin(t * 0.5))
        # ondas de sonido que no llegan a ninguna parte
        for i in range(4):
            ph = (lt * 0.8 + i / 4) % 1
            r = 60 + ph * 220
            a = int(200 * (1 - ph) * (1 - smooth(1.2, 2.2, lt)))
            if a > 5:
                d.arc([(600 - r) * S, (880 - r) * S, (600 + r) * S, (880 + r) * S], -50, 50, fill=(255, 255, 255, a), width=6 * S)
        k = smooth(1.8, 2.3, lt)
        if k > 0:
            self.E(d, 820, 880, 70 * k, None, RED, 10)
            self.Ln(d, [(820 - 50 * k, 880 - 50 * k), (820 + 50 * k, 880 + 50 * k)], RED, 10)
        self.pop_text(img, 540, 1550, "SIN AIRE = SIN SONIDO", 60, t, self.w("d1", "aire"), YEL)

    def s_d2(self, img, d, t, lt, u):
        self.space(img, d, t)
        cx, cy = 540, 960
        self.glow(img, cx, cy, 120, (255, 190, 80), 160)
        self.E(d, cx, cy, 70, (255, 200, 70))
        R = 330
        d.ellipse([(cx - R) * S, (cy - R * 0.45) * S, (cx + R) * S, (cy + R * 0.45) * S], outline=(120, 130, 170), width=3 * S)
        a = lt * 1.6
        vx, vy = cx + R * math.cos(a), cy + R * 0.45 * math.sin(a)
        self.planet(img, d, vx, vy, 56, (230, 190, 120), [(215, 170, 100), (240, 205, 140)])
        sp = lt * 0.12  # gira muy despacio sobre sí misma
        self.Ln(d, [(vx, vy), (vx + math.cos(sp) * 56, vy + math.sin(sp) * 56)], (120, 70, 40), 5)
        self.text(img, 540, 1450, "1 AÑO = 225 días", 54, CYAN)
        self.pop_text(img, 540, 1550, "1 DÍA = 243 días", 64, t, self.w("d2", "año") - 0.2, YEL)

    def s_d3(self, img, d, t, lt, u):
        self.space(img, d, t)
        tilt = math.radians(14 * ease_out(lt / 1.5))
        cx, cy = 540, 1050
        L = 400
        lx, ly = cx - L * math.cos(tilt), cy + L * math.sin(tilt)
        rx, ry = cx + L * math.cos(tilt), cy - L * math.sin(tilt)
        self.P(d, [(cx - 50, 1400), (cx + 50, 1400), (cx, cy)], (150, 160, 190))
        self.Ln(d, [(lx, ly), (rx, ry)], (200, 210, 230), 14)
        self.glow(img, lx, ly - 150, 200, (255, 180, 70), 140)
        self.E(d, lx, ly - 150, 140, (255, 200, 70))
        for i, (r, c) in enumerate(((10, (200, 190, 180)), (16, (230, 190, 120)), (17, (70, 140, 220)), (12, (220, 110, 70)), (40, (220, 180, 130)), (34, (230, 210, 160)), (24, (150, 220, 230)), (23, (80, 120, 230)))):
            px = rx - 150 + i * 40
            self.E(d, px, ry - 30 - r, r, c)
        self.pop_text(img, 540, 1560, "99,8 %", 120, t, self.w("d3", "noventa"), YEL)
        self.text(img, 540, 1670, "DE LA MASA DEL SISTEMA SOLAR", 36, WHITE, "Bold", alpha=smooth(self.w("d3", "masa"), self.w("d3", "masa") + 0.4, t))

    def s_d4(self, img, d, t, lt, u):
        self.space(img, d, t, 1.0)
        self.planet(img, d, 820, 520, 110, (70, 140, 220), None)
        self.E(d, 780, 500, 40, (110, 180, 100))
        self.P(d, [(-50, 1100), (300, 1060), (700, 1090), (1150, 1050), (1150, 1950), (-50, 1950)], (170, 170, 178))
        for x, y, r in ((200, 1300, 70), (800, 1250, 50), (520, 1700, 90), (900, 1650, 40)):
            self.E(d, x, y, r, (145, 145, 152), ry=r * 0.35)
        k = smooth(0.3, 0.9, lt)  # huella
        fx, fy = 540, 1420
        if k > 0:
            self.R(d, fx - 70 * k, fy - 130 * k, fx + 70 * k, fy + 130 * k, (130, 130, 138), radius=60 * k)
            for j in range(8):
                yy = fy - 110 * k + j * 30 * k
                self.R(d, fx - 60 * k, yy, fx + 60 * k, yy + 12 * k, (115, 115, 122), radius=5 * k)
        yrs = 10 ** (2 + 4 * smooth(1.0, 3.8, lt))
        self.text(img, 540, 1590, f"+{int(yrs):,} AÑOS".replace(",", "."), 64, YEL)

    def s_d5(self, img, d, t, lt, u):
        self.space(img, d, t)
        # cucharilla con un trocito de estrella de neutrones
        self.Ln(d, [(220, 1300), (620, 1060)], (200, 205, 215), 26)
        self.E(d, 700, 1010, 110, (210, 215, 225), ry=70)
        self.glow(img, 700, 990, 90, (150, 200, 255), 200)
        self.E(d, 700, 990, 46 + 4 * math.sin(t * 8), (235, 245, 255))
        n = 1e9 * ease_out(lt / 2.5)
        self.text(img, 540, 1450, f"{n:,.0f} t".replace(",", "."), 84, YEL)
        self.text(img, 540, 1560, "EN UNA CUCHARADITA", 44, WHITE, "Bold", alpha=smooth(0.8, 1.4, lt))

    def s_d6(self, img, d, t, lt, u):
        self.bg(img, "bath", (40, 50, 80), (20, 26, 46))
        self.stars(d, t, 0.6)
        # bañera
        self.R(d, 140, 1180, 940, 1560, (245, 245, 250), radius=110)
        for x in (220, 860):
            self.R(d, x - 20, 1540, x + 20, 1640, (220, 200, 120), radius=10)
        k = ease_out(lt / 1.4)
        y = 400 + (1180 - 400) * k + 10 * math.sin(t * 3) * k  # Saturno cae y flota
        self.R(d, 180, 1200, 900, 1420, (110, 180, 235), radius=80)
        self.E(d, 540, y + 30, 420 * 0.55, (210, 170, 110), ry=40)  # anillo detrás
        self.planet(img, d, 540, y - 40, 150, (225, 190, 130), [(205, 165, 105), (240, 210, 150), (210, 170, 110)])
        d.arc([(540 - 260) * S, (y - 10 - 46) * S, (540 + 260) * S, (y - 10 + 46) * S], 0, 180, fill=(230, 200, 140), width=16 * S)
        if k > 0.95:
            for i in range(3):  # ondas
                ph = (lt * 0.7 + i / 3) % 1
                d.ellipse([(540 - 200 - 200 * ph) * S, (1205 - 14 * ph) * S, (540 + 200 + 200 * ph) * S, (1225 + 14 * ph) * S],
                          outline=(230, 245, 255, int(200 * (1 - ph))), width=3 * S)
        self.pop_text(img, 540, 1715, "MENOS DENSO QUE EL AGUA", 52, t, self.w("d6", "flotaría"), YEL)

    def s_d7(self, img, d, t, lt, u):
        self.space(img, d, t)
        sx, ex, y = 170, 930, 980
        self.glow(img, sx, y, 160, (255, 190, 80), 170)
        self.E(d, sx, y, 110, (255, 200, 70))
        self.planet(img, d, ex, y, 60, (70, 140, 220), None)
        dur = self.end("d7") - self.start("d7")
        k = clamp(lt / max(1.0, dur - 0.3))
        px = sx + 110 + (ex - 60 - sx - 110) * k
        self.glow(img, px, y, 40, (255, 240, 180), 220)
        self.Ln(d, [(sx + 110, y), (px, y)], (255, 230, 150), 4)
        secs = 500 * k
        self.text(img, 540, 1350, f"{int(secs // 60)} min {int(secs % 60):02d} s", 96, YEL)

    def s_d8(self, img, d, t, lt, u):
        self.bg(img, "mars", (230, 150, 110), (250, 200, 160))
        base = 1500
        k = ease_out(lt / 1.6)
        h_ol = 1100 * k  # 21,9 km
        h_ev = 1100 * 8849 / 21900 * k
        self.P(d, [(-80, base), (180, base - h_ol * 0.9), (330, base - h_ol), (480, base - h_ol * 0.9), (740, base)], (200, 95, 60))
        self.R(d, 260, base - h_ol - 6, 400, base - h_ol + 14, (170, 75, 45), radius=8)
        self.P(d, [(740, base), (880, base - h_ev), (1020, base)], (140, 150, 170))
        self.P(d, [(845, base - h_ev + 70 * k), (880, base - h_ev), (915, base - h_ev + 70 * k)], WHITE)
        self.R(d, -10, base, W + 10, H + 40, (190, 100, 70))
        if k > 0.7:
            self.text(img, 330, base - h_ol - 70, "OLYMPUS MONS ≈ 21.900 m", 34, WHITE)
            self.text(img, 880, base - h_ev - 60, "EVEREST 8.849 m", 32, WHITE)
        self.pop_text(img, 540, 1660, "× 2,5", 110, t, self.w("d8", "dos"), YEL)

    def s_d9(self, img, d, t, lt, u):
        k = smooth(1.2, 3.2, lt)  # la arena se convierte en estrellas
        top = mix((240, 215, 160), (6, 10, 28), k)
        bot = mix((230, 200, 140), (16, 24, 52), k)
        self.bgdyn(img, top, bot)
        for x, y, r, c in self.sand:
            yy = y - (y - 960) * k * 0.6
            col = mix(c, (255, 255, 255), k)
            self.E(d, x, yy, r * (1 - 0.6 * k), col)
        if k > 0.3:
            g = smooth(0.3, 1.0, k)
            for a0, arm, off in self.galaxy:
                r = a0 * 330
                ang = arm + a0 * 5.5 + t * 0.3
                x = 540 + math.cos(ang) * r + off * 120
                y = 1000 + math.sin(ang) * r * 0.55 + off * 60
                self.E(d, x, y, 2.5, mix((180, 200, 255), (255, 230, 200), a0), None)
            self.glow(img, 540, 1000, 120, (255, 230, 200), 200 * g)
        self.pop_text(img, 540, 1600, "ESTRELLAS > GRANOS DE ARENA", 52, t, self.w("d9", "estrellas"), YEL)

    def s_d10(self, img, d, t, lt, u):
        self.space(img, d, t)
        cx, cy = 540, 980
        for i in range(6):  # disco de acreción
            r = 380 - i * 35
            col = mix((255, 120, 40), (255, 230, 160), i / 5)
            d.ellipse([(cx - r) * S, (cy - r * 0.28) * S, (cx + r) * S, (cy + r * 0.28) * S], outline=col, width=int(16 * S))
        self.glow(img, cx, cy, 200, (255, 160, 80), 120)
        self.E(d, cx, cy, 150, (0, 0, 0))
        d.arc([(cx - 175) * S, (cy - 175) * S, (cx + 175) * S, (cy + 175) * S], 180, 360, fill=(255, 200, 120), width=int(8 * S))
        for rr in range(4):  # brillo que gira
            a = t * 1.5 + rr * 1.57
            self.E(d, cx + math.cos(a) * 330, cy + math.sin(a) * 92, 10, (255, 250, 220))
        # dos relojes: lejos (normal) y cerca (lento)
        for (x, y, speed, lab) in ((230, 1500, 1.0, "LEJOS"), (850, 1500, 0.25, "CERCA")):
            self.E(d, x, y, 110, (240, 240, 250))
            self.E(d, x, y, 100, (30, 34, 50))
            a = t * 2.0 * speed
            self.Ln(d, [(x, y), (x + math.sin(a) * 80, y - math.cos(a) * 80)], YEL, 8)
            self.Ln(d, [(x, y), (x + math.sin(a / 12) * 55, y - math.cos(a / 12) * 55)], WHITE, 10)
            self.text(img, x, y + 160, lab, 40, WHITE, "Bold")

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name.startswith("d") and name != "d10" or name == "d10":
            if name.startswith("d"):
                return self.pill(out, f"DATO {name[1:]}/10", YEL, y=1835, size=42)
        return out

    def sfx_events(self):
        ev = [(0.2, "riser", 0.4), (0.3, "boom", 0.5)]
        for i in range(1, 11):
            ev.append((self.start(f"d{i}") + 0.05, "pop", 0.45))
        ev += [(self.start("d6") + 1.3, "splash", 0.7), (self.start("d10") + 0.3, "rumble", 0.5), (self.start("d5") + 0.5, "shimmer", 0.4),
               (self.start("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        return [(0, 0.6), (self.start("d5"), 0.7), (self.start("d10"), 0.9), (self.start("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
