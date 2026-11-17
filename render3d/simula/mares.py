"""¿Qué pasaría si todos los mares se secaran?"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, City, Person, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "epico", 80


class VIDEO(Video):
    NAME = "mares"
    KEYWORDS = {"mares", "secarse", "setenta", "ciento", "costa", "kilómetros", "puertos", "barcos", "fondo", "marino", "cordillera",
                "cuatro", "mil", "metros", "marianas", "once", "everest", "sal", "ciento", "cincuenta", "plancton", "mitad", "oxígeno",
                "evaporación", "nubes", "lluvia", "desierto", "comentarios"}

    def setup(self):
        r = random.Random(4)
        self.r = r
        self.t_drain = self.w("intro", "mares", -0.2)
        self.boats = [(560, 0.9, (235, 90, 70)), (760, 1.1, (245, 245, 245)), (940, 0.8, (70, 130, 210))]
        self.fish = [(r.uniform(420, 1040), r.uniform(0, 6)) for _ in range(8)]
        self.plankton = [(r.uniform(0, W), r.uniform(700, 1700), r.uniform(4, 11), r.uniform(0, 1)) for _ in range(160)]
        self.cracks = []
        for i in range(26):
            x, y = r.uniform(0, W), r.uniform(1150, 1900)
            pts = [(x, y)]
            for _ in range(4):
                x += r.uniform(-90, 90)
                y += r.uniform(-60, 60)
                pts.append((x, y))
            self.cracks.append(pts)
        self.salt_sp = [(r.uniform(0, W), r.uniform(0, 1), r.uniform(3, 8)) for _ in range(90)]
        self.shakes = [(self.start("fosa") + 0.4, 0.4)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "globo"), (st("nivel") - 0.15, "porcentaje"), (st("costa") - 0.15, "puerto"), (st("fondo") - 0.15, "fondo"),
                (st("fosa") - 0.15, "fosa"), (st("sal") - 0.15, "sal"), (st("oxigeno") - 0.15, "plancton"), (st("clima") - 0.15, "desierto"),
                (st("cta") - 0.1, "fin")]

    def drop(self, t):
        return 0.55 * smooth(self.t_drain, self.start("nivel") + 0.5, t)

    def s_globo(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        self.stars(d, t, 1.0)
        self.globe(img, 540, 1000, 380, t, spin=24, rot0=-30, sea_drop=self.drop(t))

    def s_porcentaje(self, img, d, t, lt, u):
        self.bg(img, "space", (8, 14, 34), (18, 32, 62))
        self.stars(d, t, 1.0)
        self.globe(img, 540, 1000, 330, t, spin=24, rot0=-30, sea_drop=0.0)
        k = ease_out(lt / 1.6)
        ext = 71 * k
        R = 400
        d.arc([(540 - R) * S, (1000 - R) * S, (540 + R) * S, (1000 + R) * S], -90, -90 + 360 * ext / 100, fill=(80, 170, 255), width=26 * S)
        d.arc([(540 - R) * S, (1000 - R) * S, (540 + R) * S, (1000 + R) * S], -90 + 360 * ext / 100, 270, fill=(60, 70, 90), width=26 * S)
        self.text(img, 540, 1500, f"{ext:.0f} %", 120, (110, 190, 255))
        self.text(img, 540, 1600, "DEL PLANETA ES OCÉANO", 40, WHITE, "Bold", alpha=k)

    def s_puerto(self, img, d, t, lt, u):
        self.bg(img, "dayport", (110, 170, 230), (210, 232, 245))
        for i, (x, y) in enumerate(((150, 520), (620, 430), (900, 600))):
            self.cloud(d, (x + t * 12) % (W + 200) - 100, y, 0.9)
        k = smooth(0.2, 5.0, lt)  # el agua se retira
        # pueblo y acantilado a la izquierda
        self.P(d, [(0, 1150), (380, 1150), (430, 1300), (470, 1900), (0, 1900)], (190, 160, 120))
        for i, (bx, bw, bh, c) in enumerate(((20, 110, 170, (245, 240, 230)), (140, 120, 210, (240, 200, 150)), (270, 100, 150, (230, 230, 240)))):
            self.R(d, bx, 1150 - bh, bx + bw, 1150, c)
            self.P(d, [(bx - 8, 1150 - bh), (bx + bw / 2, 1150 - bh - 50), (bx + bw + 8, 1150 - bh)], (200, 90, 70))
            for wx in range(bx + 18, bx + bw - 20, 36):
                self.R(d, wx, 1150 - bh + 40, wx + 18, 1150 - bh + 70, (90, 130, 170))
        # faro
        self.R(d, 330, 880, 380, 1150, (245, 245, 245))
        for yy in (930, 1010, 1090):
            self.R(d, 330, yy, 380, yy + 30, (220, 70, 60))
        self.glow(img, 355, 870, 60, (255, 240, 180), 160)
        # fondo marino (barro) y agua que baja
        self.P(d, [(430, 1300), (1080, 1380), (1080, 1900), (470, 1900)], (120, 100, 75))
        level = 1180 + 520 * k
        wx0 = 430 + 500 * k
        self.P(d, [(wx0, level), (1080, level), (1080, 1900), (wx0 + 40, 1900)], (60, 130, 200))
        self.R(d, wx0, level - 6, 1080, level + 4, (150, 200, 240))
        # muelle con pilotes que quedan al aire
        self.R(d, 380, 1140, 760, 1165, (140, 100, 70))
        for px in range(420, 760, 70):
            self.R(d, px, 1165, px + 14, 1420, (110, 80, 55))
        # barcos: flotan y luego quedan tumbados en el barro
        for i, (bx, sc, col) in enumerate(self.boats):
            grounded = clamp((k - 0.25 - i * 0.12) / 0.3)
            by = min(level, 1330 + i * 40) if grounded < 1 else 1330 + i * 40
            rot = 18 * grounded * (1 if i % 2 else -1) + (1 - grounded) * 3 * math.sin(t * 2 + i)
            self.boat(d, bx, by - 8 + (1 - grounded) * 4 * math.sin(t * 2 + i), sc, col, rot)
        for x, ph in self.fish:  # peces que saltan en los charcos
            if k > 0.5:
                j = abs(math.sin(t * 4 + ph)) * 40
                self.E(d, x, 1500 + 30 * math.sin(ph) - j, 18, (190, 200, 210), ry=8)

    def boat(self, d, x, y, sc, col, rot):
        a = math.radians(rot)

        def tr(px, py):
            return (x + (px * math.cos(a) - py * math.sin(a)) * sc, y + (px * math.sin(a) + py * math.cos(a)) * sc)

        self.P(d, [tr(-90, -40), tr(90, -40), tr(65, 10), tr(-65, 10)], col)
        self.P(d, [tr(-30, -40), tr(30, -40), tr(30, -85), tr(-30, -85)], (240, 240, 240))
        self.Ln(d, [tr(0, -85), tr(0, -170)], (90, 70, 50), 6 * sc)
        self.P(d, [tr(4, -165), tr(4, -95), tr(60, -100)], (250, 250, 250))

    def s_fondo(self, img, d, t, lt, u):
        self.bg(img, "dayport", (110, 170, 230), (210, 232, 245))
        k = smooth(0.3, 5.5, lt)
        off = lt * 60  # travelling lateral
        pts = [(-50, 1900)]
        for x in range(-50, W + 60, 20):
            xx = x + off
            ridge = 520 * math.exp(-((xx - 700) / 180) ** 2) + 80 * math.sin(xx / 60) * math.exp(-((xx - 700) / 260) ** 2)
            plain = 30 * math.sin(xx / 140) + 15 * math.sin(xx / 37)
            pts.append((x, 1500 - ridge - plain))
        pts.append((W + 60, 1900))
        water = 750 + 900 * k
        self.R(d, 0, water, W, 1900, (50, 120, 190))
        self.P(d, pts, (150, 120, 92))
        for i in range(0, len(pts) - 2, 3):
            self.Ln(d, [pts[i + 1], (pts[i + 1][0], pts[i + 1][1] + 40)], (130, 104, 80), 4)
        if k > 0.5:
            a = clamp((k - 0.5) * 3)
            self.text(img, 700 - off, 900, "DORSAL OCEÁNICA", 44, YEL, alpha=a)
            self.text(img, 700 - off, 960, "≈ 65.000 km", 40, WHITE, "Bold", alpha=a)
            self.text(img, 220, 1600, "−4.000 m", 48, CYAN, alpha=a)

    def s_fosa(self, img, d, t, lt, u):
        self.bg(img, "trench", (210, 232, 245), (60, 40, 30))
        k = smooth(0.0, 3.2, lt)
        rim, depth = 640, 1180
        # paredes de la fosa
        self.P(d, [(0, rim), (330, rim), (470, rim + depth), (0, rim + depth + 200)], (140, 110, 85))
        self.P(d, [(W, rim), (750, rim), (610, rim + depth), (W, rim + depth + 200)], (125, 98, 76))
        for i in range(8):
            y = rim + i * depth / 8
            self.Ln(d, [(330 + 140 * i / 8 - 30, y), (330 + 140 * i / 8, y)], (110, 86, 66), 4)
        # Everest a escala (8.849 m de 10.935 m)
        e = 8849 / 10935 * depth
        ek = smooth(1.5, 2.6, lt)
        base = rim + depth
        top = base - e * ek
        self.P(d, [(400, base), (540, top), (680, base)], (235, 238, 245))
        self.P(d, [(505, top + 70 * ek), (540, top), (575, top + 70 * ek)], WHITE)
        if ek > 0.6:
            self.text(img, 540, top - 40, "EVEREST 8.849 m", 36, WHITE, "Bold", alpha=clamp((ek - 0.6) * 3))
        # medidor de profundidad
        dep = 10935 * k
        self.R(d, 900, rim, 916, rim + depth * k, YEL)
        self.text(img, 860, rim + depth * k, f"−{dep:,.0f} m".replace(",", "."), 44, YEL, anchor="rm")

    def s_sal(self, img, d, t, lt, u):
        self.bg(img, "dayport", (110, 170, 230), (210, 232, 245))
        city = getattr(self, "_city", None) or City(seed=9)
        self._city = city
        city.draw(d, t)
        g = city.ground
        k = smooth(0.3, 4.5, lt)
        h150 = 1000  # 150 m en pantalla
        top = g + 120 - h150 * k
        self.R(d, 0, top, W, H + 40, (245, 245, 248))
        for x, ph, r in self.salt_sp:
            y = top + 30 + ((ph + t * 0.05) % 1) * (H - top)
            tw = 0.5 + 0.5 * math.sin(t * 4 + x)
            self.star_shape(d, x, y, r * tw, (200, 220, 240))
        # regla de 150 m
        self.R(d, 960, g + 120 - h150, 972, g + 120, (40, 40, 50))
        for i in range(6):
            yy = g + 120 - h150 * i / 5
            self.R(d, 940, yy - 3, 990, yy + 3, (40, 40, 50))
        self.text(img, 930, g + 120 - h150 - 50, "150 m", 52, (40, 40, 50), anchor="rm", shadow=False)
        self.text(img, 540, top + 90, "SAL", 72, (190, 200, 215), alpha=smooth(0.3, 1.2, lt), shadow=False)

    def s_plancton(self, img, d, t, lt, u):
        self.bg(img, "sea2", (20, 90, 140), (4, 20, 40))
        k = smooth(1.0, 4.5, lt)
        from PIL import Image as _I, ImageDraw as _D, ImageFilter as _F
        gl = _I.new("RGBA", (W, H), (0, 0, 0, 0))  # un único halo para todas las partículas (rápido)
        gd = _D.Draw(gl)
        pts = []
        for x, y, r, ph in self.plankton:
            alive = ph > k
            xx = x + 14 * math.sin(t * 0.8 + ph * 9)
            yy = y + 12 * math.cos(t * 0.6 + ph * 7) + (0 if alive else (k - ph) * 300)
            pts.append((xx, yy, r, alive))
            if alive:
                gd.ellipse([xx - r * 2.2, yy - r * 2.2, xx + r * 2.2, yy + r * 2.2], fill=(90, 255, 160, 70))
        img.alpha_composite(gl.filter(_F.GaussianBlur(10)).resize(img.size, _I.BILINEAR))
        for xx, yy, r, alive in pts:
            self.E(d, xx, yy, r if alive else r * 0.8, (120, 255, 170) if alive else (90, 100, 105))
        self.text(img, 540, 620, "FITOPLANCTON", 52, (140, 255, 190), alpha=smooth(0.2, 0.8, lt))
        self.pop_text(img, 540, 1500, "≈ 50 % DEL OXÍGENO", 64, t, self.w("oxigeno", "mitad"), YEL)

    def s_desierto(self, img, d, t, lt, u):
        self.bg(img, "hot", (240, 190, 120), (255, 225, 170))
        self.glow(img, 540, 480, 220, (255, 240, 200), 200)
        self.E(d, 540, 480, 120, (255, 245, 210))
        for i, (x, y, s) in enumerate(((180, 1080, 1.2), (620, 1050, 1.6), (980, 1100, 1.0))):
            self.E(d, x, y + 40, 330 * s, mix((225, 175, 110), (210, 160, 100), i / 2), ry=90 * s)
        self.R(d, 0, 1120, W, H + 40, (215, 165, 105))
        for pts in self.cracks:
            self.Ln(d, pts, (160, 115, 70), 5)
        for j in range(6):  # calima
            y = 1000 + j * 30
            self.Ln(d, [(x, y + 6 * math.sin(x / 40 + t * 5 + j)) for x in range(0, W + 40, 40)], (255, 240, 210), 2)
        self.globe(img, 830, 760, 130, t, spin=30, sea_drop=1.0, desert=1.0, glow_a=0)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name == "globo":
            m = 4000 * self.drop(t) / 0.55
            return self.pill(out, f"NIVEL DEL MAR · −{m:,.0f} m".replace(",", "."), CYAN)
        if name == "puerto":
            return self.pill(out, "LA COSTA SE ALEJA", CYAN)
        if name == "desierto":
            return self.pill(out, "SIN NUBES · SIN LLUVIA", RED)
        return out

    def sfx_events(self):
        st = self.start
        return [(self.t_drain, "rumble", 0.6), (self.t_drain + 0.3, "splash", 0.4), (st("nivel") + 0.3, "tick", 0.5),
                (st("costa") + 1.5, "splash", 0.3), (st("costa") + 3.0, "horn", 0.4), (st("fondo") + 0.5, "rumble", 0.5),
                (st("fosa") + 0.3, "boom", 0.5), (st("fosa") + 2.0, "pop", 0.5), (st("sal") + 0.4, "shimmer", 0.4),
                (self.w("oxigeno", "mitad"), "pop", 0.6), (st("clima") + 0.3, "wind", 0.5), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.5), (st("costa"), 0.6), (st("fosa"), 0.85), (st("oxigeno"), 0.7), (st("clima"), 0.9), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
