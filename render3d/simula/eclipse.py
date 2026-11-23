"""NIVEL OCULTO · ¿Qué pasaría si mirases fijamente un eclipse solar?

Fuentes: NASA (seguridad en eclipses: solo es seguro mirar sin protección durante la totalidad; gafas ISO 12312-2;
las gafas de sol no sirven), American Academy of Ophthalmology (retinopatía solar: daño en la fóvea en segundos,
sin dolor porque la retina no tiene receptores de dolor; síntomas horas después: visión borrosa, mancha central;
a veces mejora en meses, a veces es permanente), IGN (eclipse total del 2-8-2027 visible desde el sur de España).
"""
from __future__ import annotations

import math

from motor import CYAN, RED, WHITE, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401
from PIL import Image, ImageDraw, ImageFilter

from motor import Video

MOOD, BPM = "suspense", 84
SUN = (255, 214, 120)
SPACE = ((6, 8, 22), (18, 16, 44))


class VIDEO(Video):
    NAME = "eclipse"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"eclipse", "mancha", "siempre", "nada", "luna", "sol", "trocito", "normal", "cristalino", "lupa", "concentra", "fóvea",
                "retina", "detalles", "segundos", "retinopatía", "dolor", "borrosa", "oscura", "gafas", "homologadas", "iso",
                "totalidad", "completo", "agosto", "veintisiete", "españa", "comentarios"}

    def setup(self):
        self.t_mancha = self.w("intro", "mancha")
        self.shakes = [(self.t_mancha, 0.5)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "golpe"), (st("sol") - 0.12, "eclipse"), (st("lupa") - 0.12, "lupa"), (st("fovea") - 0.12, "corte"),
                (st("quema") - 0.12, "celulas"), (st("dolor") - 0.12, "dolor"), (st("despues") - 0.12, "despues"),
                (st("gafas") - 0.12, "gafas"), (st("total") - 0.12, "total"), (st("cta") - 0.1, "fin")]

    # ───── piezas ─────
    def sun(self, img, d, x, y, r, t, cover=0.0, moon_dx=None, corona=0.0):
        """Sol con la Luna delante (cover 0→1 = la Luna se desplaza hasta taparlo)."""
        self.glow(img, x, y, r * 2.2, (255, 190, 90), 110 * (1 - 0.8 * corona) + 40)
        if corona > 0:
            for k in range(28):  # corona: rayos suaves
                a = k / 28 * 2 * math.pi + 0.05 * math.sin(t + k)
                L = r * (1.4 + 0.5 * ((k * 37) % 7) / 7)
                self.Ln(d, [(x + math.cos(a) * r, y + math.sin(a) * r), (x + math.cos(a) * L, y + math.sin(a) * L)], (235, 240, 255), 3)
            self.glow(img, x, y, r * 1.7, (210, 225, 255), 170 * corona)
        self.E(d, x, y, r, SUN)
        self.E(d, x, y, r * 0.82, (255, 236, 170))
        mx = x + (moon_dx if moon_dx is not None else (1 - cover) * r * 2.3)
        self.E(d, mx, y + 0.06 * r * (1 - cover), r * 1.01, (10, 10, 20))

    def eye_front(self, img, d, x, y, s, t, pupil=0.35, look=(0, 0), burn=0.0):
        """Ojo de frente (almendra, iris, pupila)."""
        pts_top = [(x + s * math.cos(a), y - s * 0.55 * math.sin(a)) for a in [i / 20 * math.pi for i in range(21)]]
        pts_bot = [(x + s * math.cos(a), y + s * 0.5 * math.sin(a)) for a in [math.pi - i / 20 * math.pi for i in range(21)]]
        self.P(d, [(x - s * 1.15, y)] + pts_top + [(x + s * 1.15, y)] + pts_bot, (250, 246, 240))
        ix, iy = x + look[0] * s * 0.2, y + look[1] * s * 0.12
        self.E(d, ix, iy, s * 0.46, (70, 130, 190))
        self.E(d, ix, iy, s * 0.34, (50, 100, 160))
        self.E(d, ix, iy, s * 0.46 * pupil * 1.6, (12, 12, 18))
        self.E(d, ix - s * 0.14, iy - s * 0.14, s * 0.08, WHITE)
        self.Ln(d, [(x - s * 1.15, y)] + pts_top + [(x + s * 1.15, y)], (60, 40, 40), max(3, s * 0.05))

    def eye_side(self, img, d, x, y, R, t, rays=1.0, focus_glow=0.0):
        """Corte lateral del ojo: córnea, cristalino, retina y fóvea (la luz entra por la izquierda)."""
        self.E(d, x, y, R, (236, 232, 228))
        self.E(d, x, y, R * 0.93, (196, 214, 226))  # humor vítreo
        # retina (arco al fondo, derecha)
        d.arc([(x - R * 0.93) * S, (y - R * 0.93) * S, (x + R * 0.93) * S, (y + R * 0.93) * S], -70, 70, fill=(220, 90, 90), width=int(10 * S))
        self.E(d, x - R * 1.0, y, R * 0.36, (210, 232, 245), ry=R * 0.46)  # córnea
        self.E(d, x - R * 0.72, y, R * 0.2, (250, 240, 205), ry=R * 0.36)  # cristalino
        fx, fy = x + R * 0.93, y
        if rays > 0:
            for k in range(-3, 4):
                y0 = y + k * R * 0.11
                a0 = (x - R * 1.9, y0)
                a1 = (x - R * 0.72, y0)
                n = clamp(rays * 2)
                self.Ln(d, [a0, (a0[0] + (a1[0] - a0[0]) * n, y0)], (255, 236, 150), 4)
                if rays > 0.5:
                    m = clamp((rays - 0.5) * 2)
                    self.Ln(d, [a1, (a1[0] + (fx - a1[0]) * m, y0 + (fy - y0) * m)], (255, 226, 120), 3)
        if focus_glow > 0:
            self.glow(img, fx, fy, 60 + 40 * focus_glow, (255, 240, 170), 230 * focus_glow)
            self.E(d, fx, fy, 10, WHITE)
        return fx, fy

    def magnifier(self, d, x, y, r, rot=-0.6):
        hx, hy = x + math.cos(rot) * r * 1.9, y - math.sin(rot) * r * 1.9
        self.Ln(d, [(x + math.cos(rot) * r, y - math.sin(rot) * r), (hx, hy)], (120, 80, 50), 26)
        self.E(d, x, y, r, (180, 220, 255), outline=(200, 205, 215), width=10)
        self.E(d, x - r * 0.35, y - r * 0.35, r * 0.18, (235, 245, 255))

    # ───── escenas ─────
    def s_golpe(self, img, d, t, lt, u):
        self.bgdyn(img, (4, 6, 16), (20, 14, 36))
        self.stars(d, t, 0.6)
        cov = 0.82 + 0.1 * smooth(0, 2.5, t)
        self.sun(img, d, 540, 520, 120, t, cover=cov)
        for k in range(-2, 3):  # luz que baja al ojo
            self.Ln(d, [(540 + k * 30, 600), (540 + k * 8, 1220)], (255, 220, 140), 3)
        self.glow(img, 540, 1230, 60, (255, 230, 160), 160)
        self.eye_front(img, d, 540, 1260, 230, t, pupil=0.3 + 0.1 * smooth(0, 1.5, t))
        k = smooth(self.t_mancha - 0.1, self.t_mancha + 0.8, t)
        if k > 0:
            self.glow(img, 540, 1260, 120 * k, (0, 0, 0), 215 * k, blur=30)
        self.pop_text(img, 540, 1660, "PARA SIEMPRE", 96, t, self.w("intro", "siempre"), RED)

    def s_eclipse(self, img, d, t, lt, u):
        self.bgdyn(img, (6, 10, 30), (24, 24, 60))
        self.stars(d, t, 0.8)
        cov = ease_out(lt / 2.6) * 0.97
        self.sun(img, d, 540, 820, 230, t, cover=cov)
        pct = int(round(cov / 0.97 * 99))
        self.text(img, 540, 1230, f"{pct}% TAPADO", 78, WHITE)
        k = smooth(self.w("sol", "trocito") - 0.2, self.w("sol", "trocito") + 0.4, t)
        if k > 0:  # el trocito que queda brilla igual
            self.glow(img, 540 + 210, 820, 90, (255, 250, 210), 230 * k)
            self.R(d, 190, 1380, 890, 1440, (40, 40, 70), radius=30)
            self.R(d, 190, 1380, 190 + 700 * k, 1440, SUN, radius=30)
            self.text(img, 540, 1505, "BRILLO DEL TROZO VISIBLE: 100%", 46, YEL, alpha=k)

    def s_lupa(self, img, d, t, lt, u):
        self.bg(img, "lupa", (20, 16, 30), (60, 40, 40))
        tw = self.w("lupa", "ojo")
        if t < tw - 0.1:  # una lupa quemando una hoja
            self.R(d, 160, 1180, 920, 1520, (236, 224, 196), radius=14)
            self.sun(img, d, 300, 470, 80, t, cover=0.0)
            self.magnifier(d, 560, 860, 130)
            for k in range(-2, 3):
                self.Ln(d, [(560 + k * 45, 860), (640, 1330)], (255, 230, 140), 4)
            heat = smooth(0.4, 2.0, lt)
            self.glow(img, 640, 1330, 40 + 50 * heat, (255, 150, 40), 255 * heat)
            self.E(d, 640, 1330, 24 * heat, (40, 25, 15))
            for i in range(6):  # humo
                ph = (t * 0.7 + i / 6) % 1
                self.E(d, 640 + 30 * math.sin(ph * 6 + i), 1310 - ph * 300, 18 + 30 * ph, (120, 120, 130), )
            self.text(img, 540, 620, "LUPA = LUZ CONCENTRADA", 58, YEL, alpha=smooth(0.2, 0.6, lt))
        else:
            k = ease_out((t - tw) / 1.0)
            self.eye_side(img, d, 600, 960, 320 * (0.6 + 0.4 * k), t, rays=clamp((t - tw) / 1.6), focus_glow=smooth(tw + 1.0, tw + 1.6, t))
            self.text(img, 540, 1460, "CRISTALINO = LUPA", 66, YEL, alpha=k)

    def s_corte(self, img, d, t, lt, u):
        self.bg(img, "corte", (14, 18, 34), (34, 30, 60))
        fx, fy = self.eye_side(img, d, 520, 960, 330, t, rays=1.0, focus_glow=0.8 + 0.2 * math.sin(t * 6))
        k = smooth(self.w("fovea", "fóvea") - 0.2, self.w("fovea", "fóvea") + 0.3, t)
        if k > 0:
            self.Ln(d, [(fx + 10, fy), (fx + 90, fy - 280)], YEL, 5)
            self.pop_text(img, fx - 20, fy - 330, "FÓVEA", 70, t, self.w("fovea", "fóvea"))

    def overlay(self, ov, d, t, name, lt, u):
        if name == "corte":
            k2 = smooth(self.w("fovea", "lees") - 0.2, self.w("fovea", "lees") + 0.3, t)
            if k2 > 0:
                self.text(ov, 540, 1560, "AQUÍ LEES Y VES DETALLES", 56, WHITE, alpha=k2)
            return k2 > 0
        if name == "despues" and t >= self.w("despues", "borrosa") - 0.15:
            for i in range(40):  # banda oscura arriba para que se lean los subtítulos
                a = int(200 * (1 - i / 40))
                d.rectangle([0, (170 + i * 5) * S, W * S, (175 + i * 5) * S], fill=(10, 12, 24, a))
            d.rectangle([0, 0, W * S, 170 * S], fill=(10, 12, 24, 200))
            return True
        return False

    def camera(self, t, name, lt, u):
        if name == "corte":  # zoom hacia la fóvea
            z = 1.0 + 0.9 * smooth(0.4, 3.0, lt)
            return z, 540 + (520 + 330 * 0.93 - 540) * smooth(0.4, 3.0, lt) * 0.85, 960
        if name == "golpe":
            return 1.0 + 0.12 * smooth(0, 3, lt), 540, 1100 - 120 * smooth(0, 3, lt)
        return super().camera(t, name, lt, u)

    def s_celulas(self, img, d, t, lt, u):
        self.bg(img, "cel", (40, 10, 20), (20, 6, 14))
        cols = 14
        burnt = smooth(0.6, 3.6, lt)
        for i in range(cols):  # conos y bastones de la fóvea
            x = 120 + i * 62
            dmg = clamp(burnt * 1.6 - abs(i - 6.5) / 8)
            col = mix((230, 120, 130), (50, 30, 30), dmg)
            self.R(d, x, 900 - 140 - 20 * math.sin(i), x + 40, 1240, col, radius=18)
            self.E(d, x + 20, 1240, 22, mix((250, 170, 170), (60, 40, 40), dmg))
        for k in range(10):  # luz cayendo
            ph = (t * 1.4 + k / 10) % 1
            x = 140 + k * 85
            self.Ln(d, [(x, 380 + ph * 380), (x, 440 + ph * 380)], (255, 236, 150), 6)
        secs = min(3.0, max(0.0, lt - 0.6))
        self.text(img, 540, 560, f"{secs:0.1f} s", 96, WHITE)
        self.pop_text(img, 540, 1450, "RETINOPATÍA SOLAR", 74, t, self.w("quema", "retinopatía"), RED)

    def s_dolor(self, img, d, t, lt, u):
        self.bg(img, "dolor", (10, 14, 30), (26, 30, 56))
        # medidor de dolor (plano) y señal nerviosa sin picos
        self.R(d, 130, 760, 950, 1100, (20, 26, 50), radius=30, outline=(80, 100, 150), width=4)
        pts = [(160 + i * 7.6, 930 + 4 * math.sin(i * 0.5 + t * 6)) for i in range(104)]
        self.Ln(d, pts, (90, 220, 140), 6)
        self.text(img, 540, 700, "SEÑAL DE DOLOR", 54, CYAN)
        k = back_out((t - self.w("dolor", "notas")) / 0.4)
        if k > 0:
            self.text(img, 540, 1270, "0", 200 * k, (90, 220, 140))
        self.pop_text(img, 540, 1480, "SIN RECEPTORES DE DOLOR", 52, t, self.w("dolor", "receptores"), YEL)

    def s_despues(self, img, d, t, lt, u):
        hrs = self.w("despues", "borrosa")
        if t < hrs - 0.15:  # reloj que avanza horas
            self.bg(img, "reloj", (12, 16, 34), (30, 30, 60))
            self.E(d, 540, 950, 260, (240, 240, 250))
            self.E(d, 540, 950, 236, (30, 36, 60))
            a = lt * 6
            self.Ln(d, [(540, 950), (540 + math.cos(a - 1.57) * 200, 950 + math.sin(a - 1.57) * 200)], WHITE, 12)
            self.Ln(d, [(540, 950), (540 + math.cos(a / 12 - 1.57) * 130, 950 + math.sin(a / 12 - 1.57) * 130)], YEL, 18)
            self.text(img, 540, 1340, "HORAS DESPUÉS...", 70, YEL)
            return
        # visión: texto que se ve borroso y con una mancha central que crece
        self.bg(img, "vision", (235, 232, 222), (210, 205, 196))
        for i, (line, sz) in enumerate([("E", 190), ("F  P", 130), ("T  O  Z", 100), ("L  P  E  D", 80), ("P  E  C  F  D", 62)]):
            self.text(img, 540, 640 + sum([190, 130, 100, 80, 62][:i]) * 1.15, line, sz, (30, 30, 40), shadow=False)  # optotipo
        k = smooth(hrs, hrs + 2.2, t)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([(540 - 260 * k) * S, (950 - 220 * k) * S, (540 + 260 * k) * S, (950 + 220 * k) * S], fill=(25, 22, 20, int(235 * k)))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(40 * S)))
        if k > 0:
            blurred = img.filter(ImageFilter.GaussianBlur(6 * S * k))
            img.paste(blurred)
        self.pop_text(img, 540, 1530, "MANCHA CENTRAL", 80, t, self.w("despues", "mancha"), RED)

    def s_gafas(self, img, d, t, lt, u):
        self.bg(img, "gafas", (12, 16, 34), (28, 30, 58))
        a = back_out(lt / 0.5)
        b = back_out((t - self.w("gafas", "homologadas")) / 0.5)

        def glasses(x, y, s, lens, frame):
            for sx in (-1, 1):
                self.R(d, x + sx * 95 * s - 80 * s, y - 55 * s, x + sx * 95 * s + 80 * s, y + 55 * s, lens, radius=36 * s, outline=frame, width=int(8 * s))
            self.Ln(d, [(x - 15 * s, y - 10 * s), (x + 15 * s, y - 10 * s)], frame, 8 * s)
        if a > 0.01:
            glasses(540, 700, a, (40, 50, 60), (30, 30, 30))
            self.text(img, 540, 830, "GAFAS DE SOL", 50, WHITE, alpha=clamp(a))
            k = smooth(self.w("gafas", "sirven") - 0.1, self.w("gafas", "sirven") + 0.3, t)
            if k > 0:
                self.Ln(d, [(360, 610), (720, 790)], RED, 22 * k)
                self.Ln(d, [(720, 610), (360, 790)], RED, 22 * k)
        if b > 0.01:
            glasses(540, 1180, b, (18, 18, 20), (240, 240, 245))
            self.text(img, 540, 1310, "GAFAS DE ECLIPSE", 50, WHITE, alpha=clamp(b))
            self.pop_text(img, 540, 1420, "ISO 12312-2", 72, t, self.w("gafas", "iso"), YEL)
            k = back_out((t - self.w("gafas", "iso") - 0.5) / 0.4)
            if k > 0:
                self.E(d, 840, 1130, 60 * k, (70, 200, 110))
                self.Ln(d, [(810, 1130), (835, 1158), (875, 1100)], WHITE, 12)

    def s_total(self, img, d, t, lt, u):
        self.bgdyn(img, (4, 6, 18), (12, 14, 34))
        self.stars(d, t, 1.0)
        tc = self.w("total", "completo")
        cover = smooth(0, tc - self.start("total"), lt)
        self.sun(img, d, 540, 760, 200, t, moon_dx=(1 - cover) * 160, corona=smooth(tc - 0.3, tc + 0.6, t))
        self.text(img, 540, 1100, "TOTALIDAD", 80, (210, 225, 255), alpha=smooth(tc - 0.2, tc + 0.3, t))
        k = back_out((t - self.w("total", "agosto")) / 0.5)
        if k > 0.01:  # calendario
            cy = 1370
            self.R(d, 540 - 190 * k, cy - 130 * k, 540 + 190 * k, cy + 140 * k, WHITE, radius=26)
            self.R(d, 540 - 190 * k, cy - 130 * k, 540 + 190 * k, cy - 60 * k, (220, 60, 90), radius=26)
            if k > 0.7:
                self.text(img, 540, cy - 95, "AGOSTO 2027", 40, WHITE, shadow=False)
                self.text(img, 540, cy + 40, "2", 150, (30, 30, 40), shadow=False)
        self.pop_text(img, 540, 1610, "SUR DE ESPAÑA", 70, t, self.w("total", "españa"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def sfx_events(self):
        st = self.start
        return [(0.1, "riser", 0.4), (self.t_mancha, "boom", 0.7), (self.w("intro", "siempre"), "pop", 0.5), (st("sol") + 0.3, "whoosh", 0.4),
                (self.w("sol", "trocito"), "shimmer", 0.4), (st("lupa") + 0.6, "crack", 0.3), (self.w("lupa", "ojo"), "whoosh", 0.4),
                (self.w("fovea", "fóvea"), "pop", 0.5), (st("quema") + 0.6, "rumble", 0.35), (self.w("quema", "retinopatía"), "boom", 0.5),
                (self.w("dolor", "notas"), "beep", 0.4), (st("despues") + 0.2, "tick", 0.6), (self.w("despues", "mancha"), "boom", 0.5),
                (self.w("gafas", "sirven"), "click", 0.6), (self.w("gafas", "iso"), "pop", 0.5), (self.w("total", "completo"), "shimmer", 0.6),
                (self.w("total", "agosto"), "pop", 0.5), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.75), (self.t_mancha, 0.95), (st("sol"), 0.55), (st("quema"), 0.85), (st("dolor"), 0.6), (st("despues"), 0.85),
                (st("gafas"), 0.5), (st("total"), 0.75), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
