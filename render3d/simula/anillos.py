"""NIVEL OCULTO · ¿Qué pasaría si la Tierra tuviera anillos como Saturno?"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from motor import CYAN, RED, WHITE, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "espacio", 84
BANDS = [(1.45, 10, (230, 220, 200)), (1.6, 18, (245, 238, 220)), (1.78, 22, (225, 214, 192)), (1.95, 8, (200, 190, 170)),
         (2.1, 26, (240, 232, 214)), (2.32, 12, (215, 205, 185))]


class VIDEO(Video):
    NAME = "anillos"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"anillo", "anillos", "saturno", "ecuador", "finísimos", "kilómetro", "españa", "sur", "polos", "claras", "reflejarían",
                "sombra", "invierno", "frío", "satélites", "hielo", "roca", "dos", "veinticuatro", "cuatrocientos", "sesenta", "seis",
                "millones", "comentarios"}

    def setup(self):
        r = random.Random(61)
        self.houses = [(x, r.randint(90, 170), r.choice((0, 1))) for x in range(-20, 1100, 105)]
        self.hills = [(x, r.uniform(120, 260)) for x in range(-100, 1200, 180)]
        self.olives = [(r.uniform(0, W), r.uniform(1560, 1800), r.uniform(0.7, 1.2)) for _ in range(18)]
        self.particles = [(r.uniform(0, 2 * math.pi), r.uniform(1.45, 2.35), r.uniform(0, 1)) for _ in range(160)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "pueblo"), (st("plano") - 0.15, "planeta"), (st("espana") - 0.15, "sur"), (st("ecuador") - 0.15, "ecuador"),
                (st("noches") - 0.15, "noche"), (st("sombra") - 0.15, "sombra"), (st("satelites") - 0.15, "satelites"),
                (st("hecho") - 0.15, "pasado"), (st("cta") - 0.1, "fin")]

    # ───── cielo con el arco de los anillos (vista desde España, mirando al sur) ─────
    def sky_arc(self, img, t, rise=1.0, night=0.0, cx=540, base=1700):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        base = 1560  # horizonte
        for i, (rr, w_, col) in enumerate(BANDS):
            rx = 640 * rr / 1.45
            ry = 760 * rr / 1.45 * rise
            a = int((200 if night < 0.5 else 235) * (0.55 + 0.45 * (i % 2)))
            c = mix(col, (255, 245, 225), night * 0.3)
            d.arc([(cx - rx) * S, (base - ry) * S, (cx + rx) * S, (base + ry) * S], 180, 360, fill=c + (a,), width=int(w_ * 2.2 * S))
        if night > 0.4:  # la sombra de la Tierra corta el anillo en lo alto
            d.rectangle([(cx - 120) * S, 0, (cx + 120) * S, (base - 640) * S], fill=(0, 0, 0, 0))
        img.alpha_composite(lay)

    def town(self, img, d, t, night=0.0):
        for x, h_ in self.hills:
            self.E(d, x, 1560, 300, mix((160, 150, 100), (30, 34, 50), night), ry=h_)
        self.R(d, 0, 1550, W, H + 40, mix((190, 170, 120), (36, 38, 52), night))
        for x, y, k in self.olives:
            self.E(d, x, y, 40 * k, mix((110, 130, 80), (30, 40, 40), night), ry=28 * k)
        for x, h_, roof in self.houses:
            wall = mix((248, 245, 236), (70, 74, 96), night)
            self.R(d, x, 1560 - h_, x + 96, 1562, wall)
            self.P(d, [(x - 6, 1560 - h_), (x + 48, 1560 - h_ - 34), (x + 102, 1560 - h_)], mix((200, 100, 70), (90, 50, 50), night))
            self.R(d, x + 34, 1560 - h_ + 30, x + 58, 1560 - h_ + 60, (255, 210, 120) if night > 0.4 and roof else mix((80, 120, 170), (30, 30, 40), night))
        # campanario
        bx = 760
        c = mix((235, 220, 190), (80, 76, 96), night)
        self.R(d, bx - 40, 1210, bx + 40, 1562, c)
        self.P(d, [(bx - 50, 1210), (bx, 1120), (bx + 50, 1210)], mix((200, 100, 70), (90, 50, 50), night))
        self.R(d, bx - 16, 1250, bx + 16, 1300, mix((60, 50, 40), (255, 210, 120), night))

    def s_pueblo(self, img, d, t, lt, u):
        self.bgdyn(img, (120, 160, 220), (250, 200, 150))
        self.sky_arc(img, t, rise=0.75 + 0.25 * smooth(0, 3.5, lt))
        self.town(img, d, t)

    def ringed_globe(self, img, d, t, cx, cy, R, shadow=0.0, glow=True):
        lay_b = Image.new("RGBA", img.size, (0, 0, 0, 0))
        lay_f = Image.new("RGBA", img.size, (0, 0, 0, 0))
        db, df = ImageDraw.Draw(lay_b), ImageDraw.Draw(lay_f)
        for rr, w_, col in BANDS:
            rx, ry = R * rr, R * rr * 0.31
            box = [(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S]
            db.arc(box, 180, 360, fill=col + (220,), width=int(w_ * S))
            df.arc(box, 0, 180, fill=col + (235,), width=int(w_ * S))
        img.alpha_composite(lay_b)
        self.globe(img, cx, cy, R, t, spin=16, glow_a=90 if glow else 0)
        if shadow > 0:  # sombra de los anillos sobre el hemisferio de invierno
            sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).chord([(cx - R) * S, (cy - R) * S, (cx + R) * S, (cy + R) * S], 20, 160, fill=(0, 0, 20, int(150 * shadow)))
            img.alpha_composite(sh)
        img.alpha_composite(lay_f)

    def s_planeta(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        self.ringed_globe(img, d, t, 540, 980, 260)
        self.pop_text(img, 540, 1500, "SOBRE EL ECUADOR", 64, t, self.w("plano", "ecuador"), YEL)
        self.pop_text(img, 540, 1610, "SATURNO: < 1 km DE GROSOR", 50, t, self.w("plano", "saturno", 0.4) if self.w("plano", "kilómetro") else 0, CYAN)

    def s_sur(self, img, d, t, lt, u):
        self.bgdyn(img, (110, 160, 225), (230, 215, 190))
        self.sky_arc(img, t, 1.0)
        self.town(img, d, t)
        self.pop_text(img, 540, 1680, "MIRANDO AL SUR · ESPAÑA", 54, t, self.w("espana", "sur"), YEL)

    def s_ecuador(self, img, d, t, lt, u):
        polo = smooth(self.w("ecuador", "polos") - 0.4, self.w("ecuador", "polos") + 0.2, t)
        if polo < 0.5:
            self.bg(img, "trop", (90, 160, 230), (190, 225, 245))
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))  # el anillo, de canto: una línea fina sobre la cabeza
            ImageDraw.Draw(lay).rectangle([(540 - 7) * S, 0, (540 + 7) * S, 1500 * S], fill=(250, 245, 230, 230))
            img.alpha_composite(lay)
            self.R(d, 0, 1500, W, H + 40, (230, 205, 150))
            for x in (160, 900):
                self.Ln(d, [(x, 1500), (x + 30, 1200), (x + 50, 1000)], (110, 80, 50), 22)
                for i in range(6):
                    a = -math.pi / 2 + (i - 2.5) * 0.6 + 0.05 * math.sin(t * 2)
                    self.Ln(d, [(x + 50, 1000), (x + 50 + math.cos(a) * 180, 1000 + math.sin(a) * 90 + 40)], (60, 140, 70), 18)
            self.text(img, 540, 1680, "ECUADOR: UNA LÍNEA FINA", 54, YEL)
        else:
            self.bg(img, "polar", (120, 150, 190), (220, 230, 240))
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(lay).arc([-200 * S, 1350 * S, 1280 * S, 1700 * S], 180, 360, fill=(250, 245, 230, 120), width=int(8 * S))
            img.alpha_composite(lay)
            self.R(d, 0, 1500, W, H + 40, (240, 246, 252))
            for x in (250, 700):
                self.P(d, [(x - 160, 1500), (x, 1300), (x + 160, 1500)], (225, 235, 245))
            self.text(img, 540, 1680, "POLOS: APENAS SE VEN", 54, CYAN)

    def s_noche(self, img, d, t, lt, u):
        self.bg(img, "night", (6, 10, 26), (26, 34, 64))
        self.stars(d, t, 0.8)
        self.sky_arc(img, t, 1.0, night=1.0)
        self.glow(img, 540, 1400, 600, (230, 225, 210), 50)
        self.town(img, d, t, night=0.75)
        self.pop_text(img, 540, 1680, "NOCHES MÁS CLARAS", 64, t, self.w("noches", "claras"), YEL)

    def s_sombra(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        self.ringed_globe(img, d, t, 540, 980, 280, shadow=smooth(0.4, 1.4, lt))
        self.pop_text(img, 540, 1500, "SOMBRA EN INVIERNO", 66, t, self.w("sombra", "sombra"), YEL)
        self.text(img, 540, 1610, "HIPÓTESIS DE ALGUNOS CIENTÍFICOS", 40, CYAN, "Bold", alpha=smooth(self.w("sombra", "científicos") - 0.2, self.w("sombra", "científicos") + 0.4, t))

    def s_satelites(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        cx, cy, R = 540, 980, 260
        self.ringed_globe(img, d, t, cx, cy, R)
        for a0, rr, ph in self.particles:  # trozos de hielo y roca
            a = a0 + t * 0.2 / rr
            px, py = cx + math.cos(a) * R * rr, cy + math.sin(a) * R * rr * 0.31
            if math.sin(a) < 0 and (px - cx) ** 2 + (py - cy) ** 2 < R * R:
                continue  # por detrás del planeta
            self.E(d, px, py, 3 + 3 * ph, (240, 235, 220))
        for i in range(3):  # satélites que esquivan
            a = t * (0.7 + 0.2 * i) + i * 2
            x, y = cx + math.cos(a) * R * 1.25, cy + math.sin(a) * R * 1.25 * 0.9 - 40 * i
            self.R(d, x - 10, y - 10, x + 10, y + 10, (220, 220, 230))
            self.R(d, x - 42, y - 4, x - 12, y + 4, (60, 90, 160))
            self.R(d, x + 12, y - 4, x + 42, y + 4, (60, 90, 160))
            if int(t * 3 + i) % 4 == 0:
                self.star_shape(d, x + 30, y - 20, 14, YEL)
        self.pop_text(img, 540, 1550, "¡CUIDADO, SATÉLITES!", 64, t, self.w("satelites", "satélites"), RED)

    def s_pasado(self, img, d, t, lt, u):
        self.bg(img, "space", (6, 10, 28), (16, 24, 52))
        self.stars(d, t, 1.0)
        self.ringed_globe(img, d, t, 540, 940, 230)
        self.text(img, 540, 1440, "DATO REAL · ESTUDIO 2024", 46, CYAN)
        self.pop_text(img, 540, 1560, "HACE ≈ 466 M DE AÑOS", 76, t, self.w("hecho", "cuatrocientos"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def camera(self, t, name, lt, u):
        if name in ("pueblo", "sur", "noche"):  # panorámica lenta hacia arriba, hacia el arco
            return 1.08 - 0.04 * u, 540 + 20 * math.sin(t * 0.3), 1010 - 50 * smooth(0, 1, u)
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.2, "shimmer", 0.5), (0.3, "riser", 0.4), (self.w("plano", "ecuador"), "pop", 0.5), (self.w("espana", "sur"), "pop", 0.5),
                (st("ecuador") + 0.3, "whoosh", 0.4), (st("noches") + 0.4, "shimmer", 0.4), (st("sombra") + 0.5, "rumble", 0.4),
                (st("satelites") + 0.6, "click", 0.4), (st("satelites") + 1.6, "click", 0.4), (self.w("hecho", "cuatrocientos"), "pop", 0.5),
                (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.6), (st("espana"), 0.75), (st("noches"), 0.5), (st("satelites"), 0.8), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
