"""10 cosas interesantes sobre GTA 6 — solo datos confirmados por Rockstar (comprobados el 17-11-2026).

Fuentes: Rockstar Newswire (fecha 19-11-2026, retrasos, precarga 10-11), Rockstar vía The Hollywood Reporter
(475 M de visualizaciones del tráiler 2 en 24 h, todas las plataformas), prensa especializada (tráiler 1: más de
90 M en YouTube en 24 h). Sin logotipos ni imágenes del juego: recreación propia en el estilo de la serie.
"""
from __future__ import annotations

import math
import os
import random

import numpy as np
from PIL import Image, ImageFilter

from motor import CYAN, RED, WHITE, HERE, Person, Video, W, H, S, YEL, back_out, clamp, draw_car, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "epico", 100
PINK, NEON = (255, 80, 170), (90, 230, 255)


class VIDEO(Video):
    NAME = "gta6"
    KEYWORDS = {"diez", "gta", "seis", "confirmadas", "uno", "dos", "tres", "cuatro", "cinco", "siete", "ocho", "nueve", "diecinueve",
                "noviembre", "veintiséis", "retrasado", "veinticinco", "mayo", "leonida", "florida", "vice", "city", "miami", "jason",
                "lucía", "noventa", "millones", "cuatrocientos", "setenta", "filtración", "confirmó", "precarga", "diez", "pc", "rumor",
                "comentarios"}

    def setup(self):
        r = random.Random(6)
        m = np.unpackbits(np.load(os.path.join(HERE, "florida_mask.npy")))[: 1500 * 1080].reshape(1500, 1080)
        a = Image.fromarray((m * 255).astype(np.uint8)).resize((W * S, int(1500 * S)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
        a = a.point(lambda v: 255 if v > 127 else 0)
        self.fl = Image.new("RGBA", a.size, (255, 120, 190, 255))
        self.fl.putalpha(a)
        self.palms = [(x, r.uniform(0.8, 1.2)) for x in (60, 230, 860, 1010)]
        self.bld = [(x, r.randint(300, 760), r.randint(90, 150)) for x in range(-40, 1100, 120)]
        self.jason = Person(r, 380, 330, shirt=(60, 70, 90))
        self.lucia = Person(r, 700, 315, shirt=(230, 90, 150))
        self.lucia.long_hair = True
        self.files = [(r.uniform(-1, 1), r.uniform(-1, -0.2), r.uniform(0, 6)) for _ in range(14)]

    def build_scenes(self):
        sc = [(0.0, "intro")]
        for i in range(1, 11):
            sc.append((self.start(f"d{i}") - 0.15, f"d{i}"))
        sc.append((self.start("cta") - 0.1, "fin"))
        return sc

    # ───── decorado «Vice City» (recreación propia, estilo plano) ─────
    def sunset(self, img, d, t, night=0.0):
        top = mix((255, 110, 140), (20, 10, 45), night)
        bot = mix((255, 190, 110), (90, 30, 110), night)
        self.bg(img, "sunset%d" % int(night * 4), top, bot)
        if night > 0.3:
            self.stars(d, t, night)
        sy = 900 + 120 * night
        self.glow(img, 540, sy, 300, (255, 150, 80), 120 * (1 - night * 0.6))
        self.E(d, 540, sy, 230, mix((255, 210, 90), (255, 90, 140), 0.3 + night * 0.4))
        for i in range(6):  # franjas del sol
            y = sy + 40 + i * 32
            self.R(d, 300, y, 780, y + 8 + i * 2, mix((255, 110, 140), (90, 30, 110), night))
        for x, h_, w_ in self.bld:
            col = mix((70, 40, 90), (25, 15, 45), night)
            self.R(d, x, 1200 - h_, x + w_, 1210, col)
            for wy in range(1200 - h_ + 30, 1180, 50):
                for wx in range(x + 14, x + w_ - 20, 34):
                    if (wx * 3 + wy) % 7 < 3:
                        self.R(d, wx, wy, wx + 14, wy + 22, PINK if (wx + wy) % 3 == 0 else NEON)
        self.R(d, 0, 1200, W, 1380, mix((40, 120, 170), (20, 40, 80), night))
        for j in range(5):
            y = 1220 + j * 32
            self.Ln(d, [(x, y + 5 * math.sin(x / 60 + t * 2 + j)) for x in range(0, W + 40, 40)], (255, 170, 160), 3)
        self.R(d, 0, 1380, W, H + 40, mix((60, 50, 80), (25, 20, 40), night))
        for i, (x, k) in enumerate(self.palms):
            self.palm(d, x, 1400, k, t + i)

    def palm(self, d, x, y, k, t):
        sw = 8 * math.sin(t * 1.2)
        top = (x + 30 * k + sw, y - 520 * k)
        self.Ln(d, [(x, y), (x + 20 * k, y - 260 * k), top], (40, 25, 50), 26 * k)
        for i in range(7):
            a = -math.pi / 2 + (i - 3) * 0.55 + 0.03 * sw
            L = 230 * k
            self.Ln(d, [top, (top[0] + math.cos(a) * L * 0.6, top[1] + math.sin(a) * L * 0.3 - 30 * k),
                        (top[0] + math.cos(a) * L, top[1] + math.sin(a) * L * 0.5 + 60 * k)], (40, 25, 50), 22 * k)

    def screen(self, d, x, y, w, h):
        self.R(d, x - w / 2, y - h / 2, x + w / 2, y + h / 2, (25, 25, 35), radius=28)
        self.R(d, x - w / 2 + 14, y - h / 2 + 14, x + w / 2 - 14, y + h / 2 - 14, (60, 30, 90), radius=18)
        self.P(d, [(x - 40, y - 50), (x - 40, y + 50), (x + 55, y)], WHITE)

    def counter(self, img, t, t0, t1, n, y, size=96, col=YEL, suffix=""):
        k = ease_out(clamp((t - t0) / max(0.1, t1 - t0)))
        self.text(img, 540, y, f"{n * k:,.0f}".replace(",", ".") + suffix, size, col)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.15)
        x = (lt * 260) % (W + 400) - 200  # coche por el paseo marítimo
        car = getattr(self, "_car", None) or draw_car((255, 80, 170), 300, "car")
        self._car = car
        self.paste(img, car, x, 1560)
        self.pop_text(img, 540, 620, "GTA VI", 170, t, 0.3, WHITE)
        self.pop_text(img, 540, 760, "10 DATOS CONFIRMADOS", 50, t, self.w("intro", "confirmadas"), YEL)

    def s_d1(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.6)
        k = back_out(lt / 0.5)
        self.R(d, 540 - 260 * k, 560, 540 + 260 * k, 1080, WHITE, radius=30)
        self.R(d, 540 - 260 * k, 560, 540 + 260 * k, 690, (220, 60, 90), radius=30)
        if k > 0.6:
            self.text(img, 540, 625, "NOVIEMBRE", 52, WHITE, shadow=False)
            self.text(img, 540, 880, "19", 230, (40, 40, 50), shadow=False)
            self.text(img, 540, 1030, "2026", 56, (120, 120, 130), shadow=False)
        self.pop_text(img, 330, 1560, "PS5", 70, t, self.w("d1", "playstation"), NEON)
        self.pop_text(img, 760, 1560, "XBOX SERIES", 58, t, self.w("d1", "xbox"), (120, 230, 120))

    def s_d2(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.8)
        items = [("OTOÑO 2025", self.w("d2", "otoño")), ("26 MAYO 2026", self.w("d2", "mayo")), ("19 NOV 2026", self.end("d2") - 0.6)]
        for i, (txt, ti) in enumerate(items):
            y = 640 + i * 260
            k = clamp((t - ti + 0.3) / 0.3)
            if k <= 0:
                continue
            col = WHITE if i < 2 else YEL
            self.R(d, 170, y - 80, 910, y + 80, (30, 20, 50), radius=40)
            self.text(img, 540, y, txt, 70, col, alpha=k)
            if i < 2:
                s = clamp((t - ti - 0.5) / 0.35)
                if s > 0:
                    self.Ln(d, [(190, y + 10), (190 + 700 * s, y - 10)], RED, 12)
        self.pop_text(img, 540, 1500, "2 RETRASOS", 72, t, self.w("d2", "retrasado"), RED)

    def s_d3(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.6)
        k = ease_out(lt / 1.2)
        fl = self.fl if k >= 1 else self.fl.resize((self.fl.width, self.fl.height))
        a = np.asarray(fl.getchannel("A")).astype(np.float32) * k
        lay = fl.copy()
        lay.putalpha(Image.fromarray(a.astype(np.uint8)))
        self.glow(img, 700, 1100, 420, PINK, 70 * k)
        img.alpha_composite(lay, (0, int(260 * S)))
        self.pop_text(img, 560, 1150, "LEONIDA", 110, t, self.w("d3", "leonida"), WHITE)
        self.text(img, 560, 1270, "≈ FLORIDA", 56, NEON, alpha=smooth(self.w("d3", "florida") - 0.2, self.w("d3", "florida") + 0.3, t))

    def s_d4(self, img, d, t, lt, u):
        self.sunset(img, d, t, 1.0)
        self.pop_text(img, 540, 650, "VICE CITY", 140, t, self.w("d4", "vice") - 0.1, PINK)
        self.text(img, 540, 800, "≈ MIAMI", 64, NEON, alpha=smooth(self.w("d4", "miami") - 0.2, self.w("d4", "miami") + 0.3, t))

    def s_d5(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.9)
        self.person(img, self.jason, 380 + 6 * math.sin(t), 1560, "stand", "normal", "down", 0, scale=1.0)
        self.person(img, self.lucia, 700 + 6 * math.sin(t + 1), 1560, "stand", "smile", "down", 0, scale=1.0)
        self.pop_text(img, 380, 1640, "JASON", 56, t, self.w("d5", "jason"), NEON)
        self.pop_text(img, 700, 1640, "LUCÍA", 56, t, self.w("d5", "lucía"), PINK)

    def s_d6(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        self.screen(d, 540, 820, 760, 440)
        self.counter(img, t, self.start("d6") + 0.3, self.w("d6", "visualizaciones"), 90_000_000, 1260, 92, YEL, "+")
        self.text(img, 540, 1380, "VISUALIZACIONES EN 24 h · TRÁILER 1", 38, WHITE, "Bold", alpha=smooth(0.6, 1.2, lt))

    def s_d7(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        for i, (x, y, w_, h_) in enumerate(((300, 720, 380, 230), (780, 700, 300, 200), (540, 980, 460, 260))):
            k = back_out((lt - i * 0.2) / 0.4)
            if k > 0:
                self.screen(d, x, y, w_ * k, h_ * k)
        self.counter(img, t, self.start("d7") + 0.3, self.w("d7", "cuatrocientos") + 1.6, 475_000_000, 1330, 92, YEL)
        self.text(img, 540, 1450, "EN 24 h · TODAS LAS PLATAFORMAS (ROCKSTAR)", 34, WHITE, "Bold", alpha=smooth(0.6, 1.2, lt))

    def s_d8(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        # portátil del que salen vídeos del desarrollo
        self.R(d, 300, 1000, 780, 1290, (40, 40, 55), radius=18)
        self.R(d, 320, 1020, 760, 1270, (30, 60, 110), radius=10)
        self.P(d, [(240, 1300), (840, 1300), (880, 1340), (200, 1340)], (70, 70, 85))
        for i, (dx, dy, ph) in enumerate(self.files):
            k = ((lt * 0.45 + i / len(self.files)) % 1)
            x, y = 540 + dx * 420 * k, 1100 + dy * 600 * k
            self.R(d, x - 40, y - 28, x + 40, y + 28, (230, 230, 240), radius=6)
            self.P(d, [(x - 10, y - 14), (x - 10, y + 14), (x + 14, y)], (200, 60, 90))
        self.pop_text(img, 540, 620, "FILTRACIÓN 2022", 80, t, self.w("d8", "filtración"), RED)
        self.pop_text(img, 540, 1530, "CONFIRMADA POR ROCKSTAR", 50, t, self.w("d8", "confirmó"), YEL)

    def s_d9(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        k = smooth(0.3, 3.0, lt)
        self.R(d, 140, 900, 940, 990, (40, 30, 60), radius=45)
        self.R(d, 150, 910, 150 + 780 * k, 980, NEON, radius=35)
        self.text(img, 540, 820, "PRECARGA · PS5", 62, WHITE)
        self.text(img, 540, 1100, f"{int(100 * k)} %", 80, YEL)
        self.pop_text(img, 540, 1300, "DESDE EL 10 DE NOVIEMBRE", 52, t, self.w("d9", "diez"), CYAN)

    def s_d10(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        self.R(d, 240, 640, 840, 1040, (30, 30, 40), radius=24)
        self.R(d, 260, 660, 820, 1020, (50, 50, 70), radius=14)
        self.R(d, 500, 1040, 580, 1140, (30, 30, 40))
        self.R(d, 400, 1140, 680, 1170, (30, 30, 40), radius=10)
        self.qmark(img, 540, 850, 220 * back_out(lt / 0.5))
        self.text(img, 540, 1290, "PC: SIN FECHA OFICIAL", 62, WHITE)
        k = back_out((t - self.w("d10", "rumor")) / 0.35)
        if k > 0:
            lay = Image.new("RGBA", (int(620 * S), int(170 * S)), (0, 0, 0, 0))
            from PIL import ImageDraw
            dd = ImageDraw.Draw(lay)
            dd.rounded_rectangle([6 * S, 6 * S, 614 * S, 164 * S], radius=20 * S, outline=RED + (255,), width=int(12 * S))
            from motor import font
            dd.text((310 * S, 85 * S), "¿FECHA? = RUMOR", font=font("ExtraBold", 66 * S), fill=RED + (255,), anchor="mm")
            lay = lay.rotate(-12, expand=True, resample=Image.BICUBIC)
            lay = lay.resize((max(2, int(lay.width * k)), max(2, int(lay.height * k))))
            img.alpha_composite(lay, (int(540 * S - lay.width / 2), int(1480 * S - lay.height / 2)))

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name.startswith("d"):
            return self.pill(out, f"DATO {name[1:]}/10", YEL, y=1835, size=42)
        return out

    def sfx_events(self):
        ev = [(0.25, "boom", 0.5), (0.3, "shimmer", 0.4)]
        for i in range(1, 11):
            ev.append((self.start(f"d{i}") + 0.05, "pop", 0.45))
        ev += [(self.w("d2", "otoño") + 0.5, "click", 0.4), (self.w("d2", "mayo") + 0.5, "click", 0.4),
               (self.start("d6") + 0.3, "riser", 0.4), (self.start("d7") + 0.3, "riser", 0.4), (self.w("d8", "filtración"), "boom", 0.4),
               (self.w("d10", "rumor"), "click", 0.6), (self.start("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        return [(0, 0.8), (self.start("d5"), 0.7), (self.start("d8"), 0.85), (self.start("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
