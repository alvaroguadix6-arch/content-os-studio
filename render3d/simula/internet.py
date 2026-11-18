"""NIVEL OCULTO · ¿Qué pasaría si Internet desapareciera durante 30 días?"""
from __future__ import annotations

import math
import random

from motor import CYAN, RED, WHITE, City, Person, Video, W, H, S, YEL, back_out, clamp, ease_out, mix, render, schedule, shade, smooth  # noqa: F401

MOOD, BPM = "suspense", 96


class VIDEO(Video):
    NAME = "internet"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"internet", "apaga", "mundo", "treinta", "días", "cinco", "mil", "millones", "dinero", "tarjeta", "cajeros", "efectivo",
                "colas", "aeropuertos", "cancelaciones", "supermercados", "automáticos", "estanterías", "vacías", "teletrabajar",
                "empresas", "mapas", "papel", "cartas", "radio", "cables", "mar", "comentarios"}

    def setup(self):
        r = random.Random(41)
        self.city = City(seed=13)
        self.people = [Person(r, 120 + i * 170, r.uniform(195, 230), shirt=c) for i, c in
                       enumerate(((70, 130, 210), (235, 185, 60), (60, 170, 140), (220, 90, 80), (150, 100, 190), (90, 100, 115)))]
        self.wifi = [(r.uniform(80, 1000), r.uniform(450, 1150), r.uniform(0.6, 1.1)) for _ in range(9)]
        self.flights = ["MADRID", "LONDRES", "PARÍS", "ROMA", "LISBOA", "BERLÍN", "NUEVA YORK", "MÉXICO"]
        self.items = [(r.choice(((230, 80, 70), (80, 160, 220), (250, 200, 60), (120, 190, 100), (240, 240, 245))), r.uniform(0, 1)) for _ in range(60)]
        self.t_off = self.w("intro", "apaga", 0.1)
        self.shakes = [(self.t_off, 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "apagon"), (st("dia1") - 0.15, "gente"), (st("bancos") - 0.15, "cajero"), (st("aeropuertos") - 0.15, "aeropuerto"),
                (st("super") - 0.15, "super"), (st("trabajo") - 0.15, "oficina"), (st("papel") - 0.15, "papel"),
                (st("hecho") - 0.15, "cables"), (st("cta") - 0.1, "fin")]

    def wifi_icon(self, d, x, y, s, on=True):
        col = CYAN if on else (120, 120, 130)
        for i, r in enumerate((60, 40, 20)):
            d.arc([(x - r * s) * S, (y - r * s) * S, (x + r * s) * S, (y + r * s) * S], 225, 315, fill=col, width=int(8 * s * S))
        self.E(d, x, y, 7 * s, col)
        if not on:
            self.Ln(d, [(x - 50 * s, y - 60 * s), (x + 50 * s, y + 10 * s)], RED, 8 * s)

    def phone(self, d, x, y, on):
        self.R(d, x - 16, y - 28, x + 16, y + 28, (30, 30, 40), radius=6)
        self.R(d, x - 13, y - 24, x + 13, y + 22, (120, 200, 255) if on else (60, 60, 70), radius=4)

    def s_apagon(self, img, d, t, lt, u):
        off = t >= self.t_off
        self.bg(img, "night", (6, 10, 26), (24, 30, 60))
        self.stars(d, t, 0.6)
        self.city.draw(d, t, night=1.0, lights=0.0 if off else 1.0)
        for x, y, s in self.wifi:
            flick = off and (t - self.t_off) < 0.4 and int(t * 20) % 2 == 0
            self.wifi_icon(d, x, y + 10 * math.sin(t * 2 + x), s, on=(not off) or flick)
        self.pop_text(img, 540, 1600, "SIN CONEXIÓN", 100, t, self.t_off + 0.2, RED)

    def s_gente(self, img, d, t, lt, u):
        self.bg(img, "dayc", (110, 165, 225), (200, 225, 242))
        self.city.draw(d, t)
        g = self.city.ground
        for i, p in enumerate(self.people):
            x = p.x + 8 * math.sin(t + i)
            self.person(img, p, x, g, "stand", "wow" if i % 2 else "normal", "down", 0)
            self.phone(d, x + p.h * 0.18, g - p.h * 0.5, False)
            if (t * 2 + i) % 3 < 1.2:
                self.text(img, x, g - p.h - 70, "?", 60, YEL)
        self.pop_text(img, 540, 650, "+5.000 MILLONES", 90, t, self.w("dia1", "cinco"), YEL)
        self.text(img, 540, 760, "DE PERSONAS SIN CONEXIÓN", 44, WHITE, alpha=smooth(self.w("dia1", "personas"), self.w("dia1", "personas") + 0.4, t))

    def s_cajero(self, img, d, t, lt, u):
        self.bg(img, "bank", (52, 62, 84), (34, 40, 56))
        self.R(d, 0, 1500, W, H + 40, (80, 84, 96))
        # cajero automático
        self.R(d, 330, 520, 750, 1500, (150, 160, 182), radius=30)
        self.R(d, 380, 600, 700, 820, (20, 30, 45), radius=12)
        blink = int(t * 2) % 2
        self.text(img, 540, 690, "FUERA DE", 48, RED if blink else (150, 60, 60), shadow=False)
        self.text(img, 540, 750, "SERVICIO", 48, RED if blink else (150, 60, 60), shadow=False)
        self.R(d, 420, 880, 660, 900, (30, 30, 35), radius=6)
        for i in range(12):
            self.R(d, 420 + (i % 3) * 85, 950 + (i // 3) * 70, 490 + (i % 3) * 85, 1000 + (i // 3) * 70, (200, 205, 215), radius=8)
        # la cola crece
        n = 1 + int(5 * smooth(0.3, 4.5, lt))
        for i in range(min(n, len(self.people))):
            p = self.people[i]
            self.person(img, p, 860 + i * 70 - 10 * math.sin(t + i), 1500, "stand", "normal", "down", 0, scale=0.85)
        # tarjeta rechazada y billetes
        k = back_out((t - self.w("bancos", "tarjeta")) / 0.4)
        if k > 0:
            self.R(d, 120 - 90 * k, 1100 - 55 * k, 120 + 90 * k, 1100 + 55 * k, (60, 120, 200), radius=12)
            self.Ln(d, [(120 - 80 * k, 1040), (120 + 80 * k, 1160)], RED, 12)
        if t > self.w("bancos", "efectivo"):
            for i in range(6):
                ph = ((t - self.w("bancos", "efectivo")) * 0.6 + i / 6) % 1
                x = 100 + i * 160
                y = 300 + ph * 1100
                self.R(d, x - 50, y - 26, x + 50, y + 26, (120, 190, 120), radius=6)
                self.text(img, x, y, "€", 34, (60, 110, 60), shadow=False)

    def s_aeropuerto(self, img, d, t, lt, u):
        self.bg(img, "air", (30, 36, 50), (16, 20, 30))
        self.R(d, 90, 420, 990, 1250, (12, 14, 18), radius=20)
        self.text(img, 540, 480, "SALIDAS", 50, YEL, shadow=False)
        for i, city in enumerate(self.flights):
            y = 560 + i * 82
            tc = self.start("aeropuertos") + 0.6 + i * 0.35
            cancel = t > tc
            flap = 0 < t - tc < 0.18
            self.text(img, 130, y, f"{8 + i:02d}:{(i * 7) % 60:02d}", 38, WHITE, "Bold", anchor="lm", shadow=False)
            self.text(img, 300, y, city, 38, WHITE, "Bold", anchor="lm", shadow=False)
            if flap:
                self.R(d, 640, y - 26, 960, y + 26, (60, 60, 70), radius=4)
            else:
                self.text(img, 960, y, "CANCELADO" if cancel else "A HORA", 38, RED if cancel else (120, 220, 120), "ExtraBold", anchor="rm", shadow=False)
        # avión en tierra
        x = 540 + 30 * math.sin(t * 0.4)
        self.R(d, x - 260, 1440, x + 260, 1500, (235, 238, 245), radius=30)
        self.P(d, [(x - 60, 1470), (x + 90, 1470), (x - 40, 1600)], (210, 214, 225))
        self.P(d, [(x - 230, 1450), (x - 200, 1360), (x - 160, 1450)], (210, 214, 225))
        self.R(d, 0, 1560, W, H + 40, (60, 64, 74))

    def s_super(self, img, d, t, lt, u):
        self.bg(img, "shop", (44, 72, 92), (28, 46, 62))
        empty = smooth(0.3, 4.0, lt)
        for row in range(4):
            y = 640 + row * 230
            self.R(d, 80, y + 150, 1000, y + 170, (150, 120, 90))
            for j in range(15):
                col, ph = self.items[(row * 15 + j) % len(self.items)]
                if ph < 1 - empty:
                    x = 100 + j * 60
                    self.R(d, x, y + 50, x + 46, y + 150, col, radius=6)
        self.R(d, 0, 1580, W, H + 40, (70, 84, 96))
        cx = 200 + lt * 80
        self.R(d, cx - 70, 1450, cx + 70, 1540, None, outline=(210, 215, 225), width=8)
        self.E(d, cx - 45, 1560, 14, (60, 60, 70))
        self.E(d, cx + 45, 1560, 14, (60, 60, 70))
        self.pop_text(img, 540, 520, "ESTANTERÍAS VACÍAS", 70, t, self.w("super", "estanterías"), RED)

    def s_oficina(self, img, d, t, lt, u):
        self.bg(img, "office", (60, 70, 90), (30, 36, 50))
        for row in range(3):
            y = 760 + row * 300
            self.R(d, 60, y + 120, 1020, y + 140, (120, 95, 70))
            for j in range(3):
                x = 200 + j * 340
                self.R(d, x - 110, y - 20, x + 110, y + 120, (30, 32, 40), radius=10)
                self.R(d, x - 96, y - 6, x + 96, y + 106, (45, 50, 60), radius=6)
                self.wifi_icon(d, x, y + 70, 0.55, on=False)
        self.pop_text(img, 540, 560, "SIN TELETRABAJO", 74, t, self.w("trabajo", "teletrabajar"), YEL)

    def s_papel(self, img, d, t, lt, u):
        self.bg(img, "paper", (250, 235, 200), (235, 215, 175))
        k = ease_out(lt / 1.0)
        # mapa de papel que se despliega
        w_ = 700 * k
        self.R(d, 540 - w_ / 2, 560, 540 + w_ / 2, 1100, (245, 240, 225))
        for i in range(1, 4):
            x = 540 - w_ / 2 + w_ * i / 4
            self.Ln(d, [(x, 560), (x, 1100)], (210, 200, 180), 3)
        if k > 0.6:
            self.Ln(d, [(320, 1000), (420, 860), (560, 900), (700, 720), (780, 640)], (220, 70, 60), 8)
            self.E(d, 780, 640, 16, (220, 70, 60))
        # carta que vuela y radio con ondas
        ex = -100 + ((t - self.start("papel")) * 300) % 1300
        self.R(d, ex - 70, 1250, ex + 70, 1340, WHITE, radius=6)
        self.Ln(d, [(ex - 70, 1250), (ex, 1300), (ex + 70, 1250)], (180, 180, 190), 4)
        self.R(d, 380, 1450, 700, 1640, (150, 80, 50), radius=24)
        self.E(d, 470, 1545, 60, (60, 40, 30))
        self.R(d, 560, 1490, 670, 1520, (240, 220, 160), radius=6)
        for i in range(3):
            ph = (lt * 0.9 + i / 3) % 1
            r = 60 + ph * 140
            d.arc([(700 - r) * S, (1500 - r) * S, (700 + r) * S, (1500 + r) * S], -45, 45, fill=(120, 80, 50), width=int(6 * S))

    def s_cables(self, img, d, t, lt, u):
        self.bg(img, "deep", (12, 50, 90), (4, 14, 30))
        # continentes a los lados y cable por el fondo
        self.P(d, [(-40, 700), (180, 760), (260, 1500), (-40, 1500)], (110, 160, 100))
        self.P(d, [(1120, 680), (880, 740), (820, 1500), (1120, 1500)], (110, 160, 100))
        self.R(d, -40, 1500, 1120, H + 40, (70, 60, 55))
        pts = [(230, 1300), (330, 1560), (540, 1610), (750, 1560), (850, 1300)]
        self.Ln(d, pts, (40, 40, 50), 16)
        for i in range(6):  # pulsos de datos
            ph = (lt * 0.5 + i / 6) % 1
            seg = ph * (len(pts) - 1)
            j = int(seg)
            f = seg - j
            x = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f
            y = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f
            self.glow(img, x, y, 30, CYAN, 200, blur=12)
        self.text(img, 540, 1440, "DATO REAL", 46, CYAN)
        self.pop_text(img, 540, 1760, "CABLES SUBMARINOS", 74, t, self.w("hecho", "cables"), YEL)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        days = {"apagon": 1, "gente": 1, "cajero": 2, "aeropuerto": 2, "super": 5, "oficina": 10, "papel": 30}
        if name in days and (name != "apagon" or t >= self.t_off):
            return self.pill(out, f"SIN INTERNET · DÍA {days[name]}/30", RED if days[name] > 1 else CYAN)
        return out

    def sfx_events(self):
        st = self.start
        ev = [(0.2, "beep", 0.4), (self.t_off, "click", 0.8), (self.t_off + 0.05, "boom", 0.6), (self.w("dia1", "cinco"), "pop", 0.5),
              (self.w("bancos", "tarjeta"), "beep", 0.5), (self.w("bancos", "efectivo"), "shimmer", 0.3), (self.w("super", "estanterías"), "pop", 0.5),
              (self.w("trabajo", "teletrabajar"), "pop", 0.4), (st("papel") + 0.2, "whoosh", 0.5), (st("hecho") + 0.5, "drip", 0.4),
              (st("cta"), "pop", 0.6)]
        for i in range(8):
            ev.append((st("aeropuertos") + 0.6 + i * 0.35, "tick", 0.6))
        return ev

    def music_plan(self):
        st = self.start
        return [(0, 0.5), (self.t_off, 0.85), (st("bancos"), 0.7), (st("super"), 0.85), (st("papel"), 0.45), (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
