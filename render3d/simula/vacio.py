"""NIVEL OCULTO · ¿Qué pasaría si salieras al espacio sin traje?

Fuentes: NASA (no explotarías; consciencia ~10-15 s; no contener la respiración: rotura pulmonar; ebullición de los
fluidos —ebullismo— por debajo del límite de Armstrong, donde el agua hierve a 37 °C; hinchazón sin reventar; el vacío
apenas conduce el calor; quemaduras por UV; supervivencia con represurización hasta ~90 s según experimentos con animales),
caso Jim LeBlanc (Johnson Space Center, 1966): perdió la presión del traje en una cámara de vacío, perdió el
conocimiento a los ~14 s, recordaba la saliva burbujeando en la lengua, y se recuperó al represurizar.
"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, W, H, S, YEL, Person, Video, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "espacio", 86
SP = ((4, 6, 18), (14, 18, 44))


class VIDEO(Video):
    NAME = "vacio"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"espacio", "traje", "explotarías", "quince", "segundos", "respiración", "pulmones", "expandiría", "rompería", "soltarlo",
                "presión", "hierve", "temperatura", "cuerpo", "saliva", "burbujear", "hincharían", "piel", "elástica", "reventarías",
                "congelarías", "vacío", "calor", "ultravioleta", "quemaría", "oxígeno", "desmayas", "sesenta", "nasa", "leblanc",
                "vacío", "recuerda", "hirviendo", "recuperó", "minuto", "medio", "mortal", "astronauta", "comentarios"}

    def setup(self):
        r = random.Random(5)
        self.hero = Person(r, 540, 300, shirt=(70, 130, 210))
        self.hero.long_hair = False
        self.tech = Person(random.Random(9), 540, 280, shirt=(235, 235, 240))
        self.tech.long_hair = False
        self.t_out = self.w("intro", "explotarías") - 0.6
        self.shakes = [(self.w("aire", "rompería"), 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "fuera"), (st("aire") - 0.12, "pulmones"), (st("hervir") - 0.12, "hervir"), (st("hinchar") - 0.12, "hinchar"),
                (st("frio") - 0.12, "frio"), (st("desmayo") - 0.12, "desmayo"), (st("leblanc") - 0.12, "camara"),
                (st("rescate") - 0.12, "rescate"), (st("limite") - 0.12, "limite"), (st("cta") - 0.1, "fin")]

    # ───── piezas ─────
    def gauge(self, img, d, x, y, r, frac, label, col=CYAN):
        """Manómetro: frac 0..1."""
        self.E(d, x, y, r, (230, 232, 240))
        self.E(d, x, y, r * 0.88, (28, 32, 52))
        for i in range(11):
            a = math.radians(210 - i * 24)
            self.Ln(d, [(x + math.cos(a) * r * 0.72, y - math.sin(a) * r * 0.72), (x + math.cos(a) * r * 0.84, y - math.sin(a) * r * 0.84)], WHITE, 4)
        a = math.radians(210 - 240 * clamp(frac))
        self.Ln(d, [(x, y), (x + math.cos(a) * r * 0.7, y - math.sin(a) * r * 0.7)], mix(RED, (90, 220, 140), frac), 9)
        self.E(d, x, y, r * 0.1, WHITE)
        self.text(img, x, y + r * 0.45, label, r * 0.22, col)

    def thermometer(self, img, d, x, y, h, frac, col=RED):
        self.R(d, x - 26, y - h, x + 26, y, (230, 232, 240), radius=26)
        self.E(d, x, y + 20, 50, (230, 232, 240))
        self.R(d, x - 14, y - h * frac, x + 14, y + 10, col, radius=14)
        self.E(d, x, y + 20, 38, col)

    def station(self, d, x, y, open_k):
        self.R(d, x - 420, y - 260, x + 120, y + 260, (190, 196, 210), radius=30)
        self.R(d, x - 400, y - 240, x + 100, y + 240, (150, 156, 172), radius=24)
        door = 200 * (1 - open_k)
        self.R(d, x + 40, y - 170, x + 120, y + 170, (20, 24, 40))
        self.R(d, x + 40, y - 170, x + 40 + door * 0.4, y + 170, (210, 214, 226))
        for i in range(4):
            self.E(d, x - 300 + i * 90, y - 120, 26, (60, 120, 200))

    def body(self, img, x, y, t, scale=1.0, sx=1.0, face="scared", rot=0.0, p=None):
        p = p or self.hero
        sp, (ax, ay) = p.sprite("float", face, "up", t * 2, scale)
        if sx != 1.0:
            from PIL import Image
            sp = sp.resize((int(sp.width * sx), sp.height), Image.BICUBIC)
            ax *= sx
        if rot:
            from PIL import Image
            sp = sp.rotate(rot, resample=Image.BICUBIC, center=(ax, ay - sp.height * 0.3))
        img.alpha_composite(sp, (int(x * S - ax), int(y * S - ay)))

    def helmet(self, img, d):
        """Casco transparente sobre la cabeza del técnico (escala 1.3 → cabeza en y≈947)."""
        from PIL import Image, ImageDraw
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        cx, cy, r = 540, 940, 86
        dl.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=(200, 225, 255, 60), outline=(240, 244, 255, 255), width=int(7 * S))
        dl.arc([(cx - r * 0.7) * S, (cy - r * 0.75) * S, (cx + r * 0.2) * S, (cy + r * 0.1) * S], 190, 250, fill=(255, 255, 255, 200), width=int(6 * S))
        img.alpha_composite(lay)

    # ───── escenas ─────
    def s_fuera(self, img, d, t, lt, u):
        self.bgdyn(img, *SP)
        self.stars(d, t, 1.0, drift=-4)
        self.globe(img, 540, 2150, 900, t, spin=6)
        self.station(d, 180, 760, smooth(0, 0.8, t))
        k = smooth(self.t_out - 0.8, self.t_out + 1.4, t)
        self.body(img, 330 + 330 * k, 1000 + 40 * math.sin(t * 1.5), t, rot=-30 * k + 8 * math.sin(t))
        self.pop_text(img, 540, 1260, "NO EXPLOTARÍAS", 92, t, self.w("intro", "explotarías"), YEL)
        k2 = back_out((t - self.w("intro", "quince")) / 0.4)
        if k2 > 0:
            self.E(d, 540, 1560, 150 * k2, (20, 24, 50), outline=RED, width=10)
            d.arc([(540 - 150 * k2) * S, (1560 - 150 * k2) * S, (540 + 150 * k2) * S, (1560 + 150 * k2) * S], -90,
                  -90 + 360 * (1 - smooth(self.w("intro", "quince"), self.end("intro") + 0.3, t)), fill=YEL, width=int(14 * S))
            self.text(img, 540, 1560, "15 s", 96 * k2, WHITE)

    def s_pulmones(self, img, d, t, lt, u):
        self.bg(img, "pulm", (16, 10, 26), (40, 20, 40))
        tx = self.w("aire", "expandiría")
        k = smooth(tx - 0.3, tx + 1.2, t)
        ex = smooth(self.w("aire", "soltarlo") - 0.4, self.w("aire", "soltarlo") + 0.6, t)
        infl = 1 + 0.45 * k * (1 - ex)
        for sx in (-1, 1):  # pulmones
            cx = 540 + sx * 150
            self.E(d, cx, 980, 120 * infl, (240, 130, 150), ry=220 * infl)
            self.E(d, cx - sx * 30, 960, 80 * infl, (250, 160, 175), ry=150 * infl)
        self.R(d, 525, 640, 555, 820, (240, 140, 160), radius=14)  # tráquea
        for i in range(14):  # burbujas de aire que crecen
            a = i * 2.4
            bx, by = 540 + math.cos(a) * 170 * infl, 980 + math.sin(a) * 160 * infl
            self.E(d, bx, by, (8 + 10 * k) * (1 - ex), (255, 250, 255))
        if ex > 0:  # el aire sale
            for i in range(5):
                ph = (t * 1.5 + i / 5) % 1
                self.E(d, 540 + (i - 2) * 30, 640 - ph * 300, 20 * (1 - ph) + 6, (200, 230, 255))
        self.gauge(img, d, 860, 520, 110, 1 - smooth(0, 1.5, lt), "PRESIÓN")
        self.pop_text(img, 540, 1440, "¡NO AGUANTES EL AIRE!", 70, t, self.w("aire", "respiración"), RED)
        self.pop_text(img, 540, 1560, "SUÉLTALO", 72, t, self.w("aire", "soltarlo"), (110, 230, 150))

    def s_hervir(self, img, d, t, lt, u):
        self.bg(img, "herv", (10, 14, 32), (24, 30, 60))
        drop = smooth(0.3, 2.6, lt)
        self.gauge(img, d, 300, 760, 150, 1 - drop, "PRESIÓN")
        bp = 100 - 63 * drop  # punto de ebullición: de 100 °C a 37 °C
        self.thermometer(img, d, 780, 1000, 520, bp / 110, (255, 120, 90))
        self.text(img, 780, 400, f"HIERVE A {int(round(bp))} °C", 58, YEL)
        k = smooth(self.w("hervir", "cuerpo") - 0.3, self.w("hervir", "cuerpo") + 0.3, t)
        if k > 0:
            self.text(img, 300, 1000, "37 °C = TU CUERPO", 50, WHITE, alpha=k)
        ks = smooth(self.w("hervir", "saliva") - 0.2, self.w("hervir", "saliva") + 0.3, t)
        if ks > 0:  # lengua con burbujas
            self.E(d, 540, 1380, 230 * ks, (230, 110, 130), ry=110 * ks)
            self.Ln(d, [(540, 1300), (540, 1440)], (200, 80, 100), 6)
            for i in range(18):
                ph = (t * 1.3 + i * 0.37) % 1
                bx = 360 + (i * 61) % 360
                self.E(d, bx, 1380 - 60 * math.sin(i) - ph * 120, 6 + 10 * ph, (240, 245, 255), outline=(200, 210, 230), width=2)
            self.text(img, 540, 1580, "LA SALIVA BURBUJEA", 60, CYAN, alpha=ks)

    def s_hinchar(self, img, d, t, lt, u):
        self.bgdyn(img, *SP)
        self.stars(d, t, 0.8)
        k = smooth(0.2, 2.2, lt)
        sw = 1 + 0.35 * k + 0.03 * math.sin(t * 5) * k
        self.body(img, 540, 1250, t, scale=1.6, sx=sw)
        for sx in (-1, 1):  # flechas de hinchazón
            x = 540 + sx * (180 * sw)
            self.Ln(d, [(x, 1000), (x + sx * 70 * k, 1000)], YEL, 10)
            self.P(d, [(x + sx * (70 * k + 30), 1000), (x + sx * 70 * k, 980), (x + sx * 70 * k, 1020)], YEL)
        self.pop_text(img, 540, 660, "LA PIEL AGUANTA", 80, t, self.w("hinchar", "piel"), (110, 230, 150))
        self.pop_text(img, 540, 1560, "NO REVIENTAS", 80, t, self.w("hinchar", "reventarías"), YEL)

    def s_frio(self, img, d, t, lt, u):
        self.bgdyn(img, *SP)
        self.stars(d, t, 0.8)
        tu = self.w("frio", "sol")
        if t < tu - 0.15:  # termo: el vacío aísla
            self.R(d, 380, 640, 700, 1380, (200, 205, 215), radius=60)
            self.R(d, 410, 670, 670, 1350, (14, 18, 40), radius=48)
            self.R(d, 450, 710, 630, 1310, (255, 130, 90), radius=40)
            for i in range(6):  # calor que apenas sale
                ph = (t * 0.6 + i / 6) % 1
                self.Ln(d, [(540 + (i - 2.5) * 30, 700 - ph * 90), (540 + (i - 2.5) * 30, 680 - ph * 90)], (255, 160, 110), 6)
            self.text(img, 540, 520, "EL VACÍO AÍSLA", 80, CYAN)
            self.text(img, 540, 1520, "COMO UN TERMO", 66, WHITE, alpha=smooth(0.6, 1.2, lt))
        else:  # rayos UV del Sol
            self.glow(img, 920, 420, 200, (255, 230, 160), 200)
            self.E(d, 920, 420, 90, (255, 236, 170))
            for i in range(7):
                ph = (t * 1.2 + i / 7) % 1
                x0, y0 = 880 - ph * 500, 470 + ph * 600
                self.Ln(d, [(x0, y0), (x0 - 40, y0 + 48)], (190, 120, 255), 8)
            self.body(img, 420, 1320, t, scale=1.4, face="scared")
            k = smooth(tu, tu + 2.0, t)
            self.glow(img, 420, 1050, 120, (255, 80, 60), 110 * k)
            self.pop_text(img, 540, 1600, "QUEMADURA UV", 80, t, self.w("frio", "ultravioleta"), (190, 120, 255))

    def s_desmayo(self, img, d, t, lt, u):
        self.bg(img, "desm", (30, 8, 16), (12, 6, 20))
        o2 = 1 - smooth(0.4, self.end("desmayo") - self.start("desmayo"), lt)
        for i in range(12):  # glóbulos rojos que pierden oxígeno (rojo vivo → oscuro)
            a = i / 12 * 2 * math.pi + t * 0.4
            x, y = 540 + math.cos(a) * 290, 960 + math.sin(a) * 290
            self.E(d, x, y, 60, mix((90, 30, 50), (230, 50, 60), o2), ry=48)
            self.E(d, x, y, 30, mix((70, 20, 40), (190, 30, 45), o2), ry=22)
        self.R(d, 240, 1380, 840, 1440, (40, 30, 50), radius=30)
        self.R(d, 240, 1380, 240 + 600 * o2, 1440, (90, 200, 255), radius=30)
        self.text(img, 540, 1340, f"OXÍGENO {int(o2 * 100)}%", 52, WHITE)
        secs = 15 * (1 - o2)
        self.text(img, 540, 960, f"{secs:0.0f} s", 130, YEL)
        if o2 < 0.4:  # se apaga la vista
            from PIL import Image
            img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, int(200 * (0.4 - o2) / 0.4))))

    def s_camara(self, img, d, t, lt, u):
        self.bg(img, "cam", (16, 18, 30), (34, 36, 52))
        self.R(d, 180, 560, 900, 1420, (90, 96, 112), radius=180)
        self.R(d, 210, 590, 870, 1390, (24, 28, 44), radius=160)
        self.body(img, 540, 1260, t, scale=1.3, face="normal" if t < self.w("leblanc", "perdió") else "scared", p=self.tech)
        self.helmet(img, d)
        tp = self.w("leblanc", "perdió")
        self.gauge(img, d, 860, 480, 100, 1 - smooth(tp, tp + 1.5, t), "TRAJE")
        if t > self.w("leblanc", "saliva") - 0.2:
            for i in range(8):
                ph = (t * 1.4 + i / 8) % 1
                self.E(d, 525 + (i % 4) * 10, 975 - ph * 50, 4 + 6 * ph, WHITE)
        self.pop_text(img, 540, 450, "NASA · 1966", 70, t, self.start("leblanc") + 0.2, YEL)
        self.pop_text(img, 540, 1560, "JIM LEBLANC", 76, t, self.w("leblanc", "leblanc"), WHITE)

    def s_rescate(self, img, d, t, lt, u):
        self.bg(img, "cam", (16, 18, 30), (34, 36, 52))
        self.R(d, 180, 560, 900, 1420, (90, 96, 112), radius=180)
        self.R(d, 210, 590, 870, 1390, (24, 28, 44), radius=160)
        self.body(img, 540, 1260, t, scale=1.3, face="smile", p=self.tech)
        self.helmet(img, d)
        self.gauge(img, d, 860, 480, 100, smooth(0.1, 1.2, lt), "TRAJE")
        k = back_out((lt - 1.0) / 0.4)
        if k > 0:
            self.E(d, 540, 1560, 70 * k, (70, 200, 110))
            self.Ln(d, [(505, 1560), (532, 1590), (582, 1528)], WHITE, 14)

    def s_limite(self, img, d, t, lt, u):
        self.bgdyn(img, *SP)
        self.stars(d, t, 0.6)
        k = smooth(0.2, 2.8, lt)
        x0, x1, y = 120, 960, 1000
        self.R(d, x0, y - 22, x1, y + 22, (40, 44, 70), radius=22)
        self.R(d, x0, y - 22, x0 + (x1 - x0) * k, y + 22, mix((90, 200, 255), RED, k), radius=22)
        for sec, lab, col in ((15, "DESMAYO", YEL), (90, "LÍMITE", RED)):
            x = x0 + (x1 - x0) * sec / 120
            if k * 120 >= sec - 2:
                self.Ln(d, [(x, y - 60), (x, y + 60)], col, 8)
                self.text(img, x, y - 110, f"{sec} s", 56, col)
                self.text(img, x, y + 110, lab, 40, col)
        self.text(img, 540, 1300, f"{int(k * 120)} s", 110, WHITE)
        self.pop_text(img, 540, 620, "≈ 1 MINUTO Y MEDIO", 72, t, self.w("limite", "minuto"), RED)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def camera(self, t, name, lt, u):
        if name == "fuera":
            return 1.0 + 0.1 * smooth(0, 3, lt), 540, 1060
        if name == "hinchar":
            return 1.0 + 0.25 * smooth(0, 3, lt), 540, 1050
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.1, "whoosh", 0.5), (0.6, "wind", 0.3), (self.w("intro", "explotarías"), "boom", 0.6), (self.w("intro", "quince"), "beep", 0.5),
                (self.w("aire", "rompería"), "crack", 0.5), (self.w("aire", "soltarlo"), "whoosh", 0.5), (st("hervir") + 0.3, "riser", 0.3),
                (self.w("hervir", "saliva"), "drip", 0.6), (self.w("hinchar", "reventarías"), "pop", 0.5), (self.w("frio", "ultravioleta"), "shimmer", 0.4),
                (st("desmayo") + 0.4, "rumble", 0.4), (self.w("leblanc", "perdió"), "horn", 0.35), (self.w("leblanc", "saliva"), "drip", 0.5),
                (st("rescate") + 1.0, "shimmer", 0.5), (self.w("limite", "minuto"), "boom", 0.5), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.7), (st("aire"), 0.85), (st("hervir"), 0.6), (st("desmayo"), 0.9), (st("leblanc"), 0.7), (st("rescate"), 0.5),
                (st("limite"), 0.8), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
