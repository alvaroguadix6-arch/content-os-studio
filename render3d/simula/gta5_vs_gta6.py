"""NIVEL OCULTO · 5 diferencias entre GTA 5 y GTA 6 (pantalla partida, como los comparativos virales).

Solo diferencias confirmadas (18-11-2026): ciudad (Los Santos/Los Ángeles vs Vice City/Miami), protagonistas
(Michael, Franklin y Trevor vs Jason y Lucía), mapa (Los Santos y Blaine vs Leonida con 6 regiones confirmadas;
tamaño oficial sin confirmar), consolas (2013 PS3/X360 vs PS5/Series, sin fecha PC) y expectación (GTA V +200 M de
copias; tráiler 1 de GTA VI récord en YouTube). Recreación propia, sin logotipos ni imágenes de los juegos.
"""
from __future__ import annotations

import math

from gta6 import NEON, PINK, VIDEO as GTA
from motor import CYAN, RED, WHITE, Person, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "epico", 100
TOP = (360, 985)
BOT = (1015, 1700)
WARM = (255, 170, 90)
REGIONES = ["VICE CITY", "LEONIDA KEYS", "GRASSRIVERS", "PORT GELLHORN", "AMBROSIA", "MOUNT KALAGA"]


class VIDEO(GTA):
    NAME = "gta5_vs_gta6"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"trece", "años", "gta", "cinco", "seis", "diferencias", "uno", "ciudad", "santos", "ángeles", "vice", "city", "miami",
                "dos", "protagonistas", "tres", "michael", "franklin", "trevor", "jason", "lucía", "mapa", "blaine", "leonida",
                "regiones", "tamaño", "cuatro", "consolas", "trece", "playstation", "xbox", "pc", "expectación", "doscientos",
                "millones", "récords", "quedas", "comentarios"}

    def setup(self):
        super().setup()
        import random
        r = random.Random(77)
        self.trio = [Person(r, 0, 190, shirt=c) for c in ((60, 70, 90), (90, 160, 90), (200, 190, 170))]
        self.duo = [self.jason, self.lucia]
        self.la_bld = [(x, r.randint(120, 330), r.randint(60, 110)) for x in range(-20, 1100, 95)]

    def build_scenes(self):
        sc = [(0.0, "intro")]
        for i in range(1, 6):
            sc.append((self.start(f"d{i}") - 0.15, f"d{i}"))
        sc.append((self.start("cta") - 0.1, "fin"))
        return sc

    # ───── mitades ─────
    def band(self, d, y0, y1, top, bot, steps=40):
        for i in range(steps):
            a = y0 + (y1 - y0) * i / steps
            self.R(d, 0, a, W, a + (y1 - y0) / steps + 1, mix(top, bot, i / steps))

    def half_v(self, img, d, t, dim=0.0):
        """Mitad de arriba: «Los Santos» (tonos cálidos de California, recreación propia)."""
        y0, y1 = TOP
        self.band(d, y0, y1, mix((255, 190, 120), (90, 70, 60), dim), mix((255, 225, 170), (110, 90, 70), dim))
        self.glow(img, 820, y0 + 150, 120, (255, 230, 170), 120 * (1 - dim))
        self.E(d, 820, y0 + 150, 60, mix((255, 240, 190), (150, 130, 110), dim))
        for i, x in enumerate((-60, 300, 700)):
            self.E(d, x + 200, y1 - 120, 320, mix((170, 130, 90), (80, 65, 55), dim), ry=110 + 30 * (i % 2))
        for x, h_, w_ in self.la_bld:
            c = mix((210, 200, 185), (90, 85, 80), dim)
            self.R(d, x, y1 - 80 - h_, x + w_, y1 - 60, c)
            for wy in range(y1 - 60 - h_ + 14, y1 - 80, 30):
                self.R(d, x + 10, wy, x + w_ - 10, wy + 10, mix((120, 170, 210), (60, 70, 80), dim))
        self.R(d, 0, y1 - 62, W, y1, mix((120, 110, 100), (60, 55, 50), dim))
        for i, x in enumerate((60, 980)):
            self.palm(d, x, y1 - 60, 0.45, t + i)
        self.chip(img, d, 110, y0 + 50, "GTA V", WARM)

    def half_vi(self, img, d, t, dim=0.0):
        """Mitad de abajo: «Vice City» (neón, recreación propia)."""
        y0, y1 = BOT
        self.band(d, y0, y1, mix((255, 100, 150), (40, 20, 50), dim), mix((90, 30, 110), (20, 10, 30), dim))
        self.E(d, 540, y0 + 330, 170, mix((255, 170, 90), (90, 50, 60), dim))
        for i in range(5):
            self.R(d, 370, y0 + 360 + i * 22, 710, y0 + 366 + i * 24, mix((255, 100, 150), (40, 20, 50), dim))
        for j, (x, h_, w_) in enumerate(self.bld):
            self.R(d, x, y1 - 160 - h_ * 0.55, x + w_, y1 - 150, mix((60, 30, 85), (25, 15, 40), dim))
            for wy in range(int(y1 - 160 - h_ * 0.55 + 20), y1 - 170, 36):
                for wx in range(x + 14, x + w_ - 20, 30):
                    if (wx * 3 + wy + j) % 5 < 2:
                        self.R(d, wx, wy, wx + 12, wy + 16, PINK if (wx + wy) % 3 == 0 else NEON)
        self.R(d, 0, y1 - 150, W, y1 - 60, (40, 110, 170))
        for k in range(3):
            y = y1 - 140 + k * 26
            self.Ln(d, [(x, y + 4 * math.sin(x / 50 + t * 2 + k)) for x in range(0, W + 40, 40)], (255, 170, 160), 3)
        self.R(d, 0, y1 - 62, W, y1, (40, 30, 60))
        for i, x in enumerate((70, 1000)):
            self.palm(d, x, y1 - 60, 0.5, t + i + 1)
        self.chip(img, d, 120, y0 + 50, "GTA VI", PINK)

    def chip(self, img, d, x, y, txt, col):
        self.R(d, x - 85, y - 32, x + 85, y + 32, (15, 12, 25), radius=32, outline=col, width=4)
        self.text(img, x, y, txt, 38, col, shadow=False)

    def vs(self, img, d, t):
        y = (TOP[1] + BOT[0]) / 2
        self.R(d, 0, TOP[1], W, BOT[0], (10, 8, 18))
        pul = 1 + 0.06 * math.sin(t * 6)
        self.E(d, 540, y, 62 * pul, YEL)
        self.text(img, 540, y, "VS", 54, (20, 16, 30), shadow=False)

    def base(self, img, d, t, dim=0.0):
        self.bg(img, "dark", (14, 10, 26), (8, 6, 16))
        self.half_v(img, d, t, dim)
        self.half_vi(img, d, t, dim)
        self.vs(img, d, t)

    def label(self, img, d, y, txt, col, t, t_in, size=52):
        k = back_out((t - t_in) / 0.35)
        if k <= 0:
            return
        f_w = len(txt) * size * 0.62 * k
        self.R(d, 540 - f_w / 2 - 30, y - size * 0.75 * k, 540 + f_w / 2 + 30, y + size * 0.75 * k, (15, 12, 25), radius=24, outline=col, width=4)
        self.text(img, 540, y, txt, size * k, col, shadow=False)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.base(img, d, t)
        self.label(img, d, TOP[0] + 300, "2013", WARM, t, 0.4, 90)
        self.label(img, d, BOT[0] + 280, "2026", PINK, t, 0.9, 90)
        self.pop_text(img, 540, (TOP[1] + BOT[0]) / 2 - 140, "13 AÑOS", 90, t, self.w("intro", "trece"), YEL)

    def s_d1(self, img, d, t, lt, u):
        self.base(img, d, t)
        self.label(img, d, TOP[0] + 270, "LOS SANTOS ≈ LOS ÁNGELES", WARM, t, self.w("d1", "santos"), 46)
        self.label(img, d, BOT[0] + 250, "VICE CITY ≈ MIAMI", PINK, t, self.w("d1", "vice"), 52)

    def s_d2(self, img, d, t, lt, u):
        self.base(img, d, t, dim=0.55)
        for i, (p, name) in enumerate(zip(self.trio, ("MICHAEL", "FRANKLIN", "TREVOR"))):
            x = 280 + i * 260
            k = clamp((t - self.w("d2", name.lower()) + 0.2) / 0.3)
            if k > 0:
                self.person(img, p, x, TOP[1] - 110, "stand", "normal", "down", 0, scale=0.95)
                self.text(img, x, TOP[1] - 70, name, 34, WARM, alpha=k)
        for i, (p, name) in enumerate(zip(self.duo, ("JASON", "LUCÍA"))):
            x = 400 + i * 280
            k = clamp((t - self.w("d2", name.lower()) + 0.2) / 0.3)
            if k > 0:
                self.person(img, p, x, BOT[1] - 110, "stand", "smile" if i else "normal", "down", 0, scale=0.62)
                self.text(img, x, BOT[1] - 70, name, 38, NEON if i == 0 else PINK, alpha=k)
        self.pop_text(img, 940, TOP[0] + 120, "3", 110, t, self.w("d2", "tres"), WARM)
        self.pop_text(img, 940, BOT[0] + 120, "2", 110, t, self.w("d2", "jason", -0.5), PINK)

    def s_d3(self, img, d, t, lt, u):
        self.base(img, d, t, dim=0.7)
        # arriba: mapa genérico de una isla con dos zonas (recreación propia)
        k = ease_out(lt / 0.8)
        cx, cy = 540, (TOP[0] + TOP[1]) / 2 + 20
        pts = [(cx + math.cos(a) * 260 * k * (1 + 0.12 * math.sin(3 * a)), cy + math.sin(a) * 230 * k * (1 + 0.1 * math.cos(2 * a)))
               for a in [i / 24 * 2 * math.pi for i in range(24)]]
        self.P(d, pts, (190, 170, 120))
        self.P(d, [p for p in pts if p[1] > cy - 10] + [(cx - 250 * k, cy)], (150, 150, 160))
        if k > 0.8:
            self.text(img, cx, cy - 90, "BLAINE", 40, (80, 60, 40), shadow=False)
            self.text(img, cx, cy + 120, "LOS SANTOS", 40, (40, 40, 60), shadow=False)
        # abajo: Leonida (contorno real de Florida) y sus 6 regiones confirmadas
        fl = self.fl.resize((int(self.fl.width * 0.42), int(self.fl.height * 0.42)))
        img.alpha_composite(fl, (int(560 * S), int((BOT[0] + 20) * S)))
        self.text(img, 290, BOT[0] + 130, "LEONIDA", 64, PINK)
        for i, reg in enumerate(REGIONES):
            kk = clamp((t - self.w("d3", "seis") - i * 0.18) / 0.25)
            if kk > 0:
                y = BOT[0] + 220 + i * 66
                self.R(d, 60, y - 26, 520, y + 26, (15, 12, 25), radius=26, outline=NEON, width=3)
                self.text(img, 290, y, reg, 32, NEON, alpha=kk, shadow=False)
        self.pop_text(img, 540, BOT[1] - 30, "TAMAÑO OFICIAL: SIN CONFIRMAR", 40, t, self.w("d3", "tamaño"), YEL)

    def s_d4(self, img, d, t, lt, u):
        self.base(img, d, t, dim=0.7)
        self.label(img, d, TOP[0] + 150, "2013", WARM, t, self.w("d4", "dos"), 80)
        self.label(img, d, TOP[0] + 300, "PS3 · XBOX 360", WARM, t, self.w("d4", "playstation"), 56)
        self.label(img, d, TOP[0] + 440, "+ PS4 · XBOX ONE · PC · PS5", WHITE, t, self.w("d4", "playstation") + 0.8, 38)
        self.label(img, d, BOT[0] + 150, "2026", PINK, t, self.w("d4", "sale"), 80)
        self.label(img, d, BOT[0] + 300, "PS5 · XBOX SERIES", PINK, t, self.w("d4", "solo"), 56)
        self.label(img, d, BOT[0] + 450, "PC: SIN FECHA", RED, t, self.w("d4", "pc"), 50)

    def s_d5(self, img, d, t, lt, u):
        self.base(img, d, t, dim=0.75)
        k1 = ease_out(clamp((t - self.w("d5", "doscientos") + 0.3) / 1.2))
        if k1 > 0:
            self.text(img, 540, TOP[0] + 260, f"+{200 * k1:,.0f} MILLONES".replace(",", "."), 80, WARM)
            self.text(img, 540, TOP[0] + 360, "DE COPIAS VENDIDAS", 44, WHITE)
        k2 = back_out((t - self.w("d5", "récords")) / 0.4)
        if k2 > 0:
            self.screen(d, 540, BOT[0] + 230, 420 * k2, 240 * k2)
            self.text(img, 540, BOT[0] + 450, "TRÁILER 1 · RÉCORD", 60, PINK)
            self.text(img, 540, BOT[0] + 530, "+90 M EN 24 h", 46, WHITE)

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name.startswith("d"):
            return self.pill(out, f"DIFERENCIA {name[1:]}/5", YEL, y=1835, size=42)
        return out

    def camera(self, t, name, lt, u):
        return 1.0 + 0.02 * smooth(0, 1, u), 540, 960

    def sfx_events(self):
        ev = [(0.2, "boom", 0.5), (0.4, "pop", 0.5), (0.9, "pop", 0.5), (self.w("intro", "trece"), "shimmer", 0.4)]
        for i in range(1, 6):
            ev.append((self.start(f"d{i}") + 0.05, "whoosh", 0.5))
        for frag in ("santos", "vice"):
            ev.append((self.w("d1", frag), "pop", 0.4))
        for frag in ("michael", "franklin", "trevor", "jason", "lucía"):
            ev.append((self.w("d2", frag), "pop", 0.35))
        ev += [(self.w("d3", "seis") + i * 0.18, "tick", 0.5) for i in range(6)]
        ev += [(self.w("d4", "pc"), "click", 0.5), (self.w("d5", "doscientos"), "riser", 0.4), (self.w("d5", "récords"), "boom", 0.4),
               (self.start("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        return [(0, 0.8), (self.start("d3"), 0.7), (self.start("d5"), 0.9), (self.start("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
