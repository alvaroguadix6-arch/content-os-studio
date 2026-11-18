"""NIVEL OCULTO · Trucos de GTA 6: cuidado con lo que ves (comprobado el 18-11-2026).

Datos: Rockstar no ha confirmado códigos de trucos (wiki de GTA y guías, 12-11-2026); los que circulan son de
GTA V o inventados; todos los GTA principales desde GTA III han tenido trucos en el modo historia; en GTA V los
trucos desactivaban logros/trofeos en esa sesión; el modo online nunca ha tenido trucos; precarga en PS5 desde
el 10-11 (Rockstar Newswire); Rockstar ha pedido retirar vídeos falsos hechos con IA (NME, games.gg); sin fecha
oficial para PC. Recreación propia sin logotipos ni imágenes del juego.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

from gta6 import NEON, PINK, VIDEO as GTA
from motor import CYAN, RED, WHITE, W, H, S, YEL, back_out, clamp, ease_out, font, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "epico", 104


class VIDEO(GTA):
    NAME = "gta6_trucos"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"trucos", "gta", "seis", "falsos", "uno", "dos", "tres", "cuatro", "cinco", "siete", "ocho", "nueve", "diez", "rockstar",
                "confirmado", "copiados", "historia", "probable", "trofeos", "guarda", "online", "estafa", "precarga", "noviembre",
                "espacio", "enorme", "inteligencia", "artificial", "retirar", "gratis", "pc", "nivel", "oculto", "comentarios"}

    def stamp(self, img, txt, t, t_in, y=1450, col=RED, rot=-10, size=72):
        k = back_out((t - t_in) / 0.35)
        if k <= 0:
            return
        f = font("ExtraBold", size * S)
        tw = f.getlength(txt)
        lay = Image.new("RGBA", (int(tw + 80 * S), int(size * 1.9 * S)), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([6 * S, 6 * S, lay.width - 6 * S, lay.height - 6 * S], radius=18 * S, outline=col + (255,), width=int(10 * S))
        dd.text((lay.width / 2, lay.height / 2), txt, font=f, fill=col + (255,), anchor="mm")
        lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
        lay = lay.resize((max(2, int(lay.width * k)), max(2, int(lay.height * k))))
        img.alpha_composite(lay, (int(540 * S - lay.width / 2), int(y * S - lay.height / 2)))

    def pad(self, d, x, y, t, press=-1):
        """Mando genérico (sin marcas)."""
        self.R(d, x - 230, y - 90, x + 230, y + 90, (40, 40, 52), radius=90)
        self.E(d, x - 170, y + 70, 80, (40, 40, 52))
        self.E(d, x + 170, y + 70, 80, (40, 40, 52))
        for i, (dx, dy) in enumerate(((0, -38), (38, 0), (0, 38), (-38, 0))):
            on = press == i
            self.E(d, x + 140 + dx, y - 10 + dy, 22, YEL if on else (200, 205, 215))
        self.R(d, x - 175, y - 22, x - 105, y + 2, (200, 205, 215), radius=6)
        self.R(d, x - 152, y - 45, x - 128, y + 25, (200, 205, 215), radius=6)
        self.E(d, x - 60, y + 40, 30, (70, 70, 85))
        self.E(d, x + 60, y + 40, 30, (70, 70, 85))

    def card(self, img, d, x, y, txt, col, k=1.0):
        if k <= 0:
            return
        self.R(d, x - 190 * k, y - 120 * k, x + 190 * k, y + 120 * k, (30, 20, 50), radius=30 * k, outline=col, width=6)
        self.text(img, x, y, txt, 90 * k, col)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.4)
        self.pop_text(img, 540, 600, "TRUCOS GTA VI", 96, t, 0.25, WHITE)
        self.stamp(img, "¿FALSOS?", t, self.w("intro", "falsos") - 0.2, y=1520)

    def s_d1(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.9)
        self.pad(d, 540, 820, t, press=int(lt * 4) % 4)
        self.stamp(img, "NO CONFIRMADOS", t, self.w("d1", "confirmado"), y=1500, size=64)

    def s_d2(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        self.card(img, d, 300, 850, "GTA V", NEON, ease_out(lt / 0.4))
        k = ease_out((lt - 0.4) / 0.4)
        self.card(img, d, 780, 850, "GTA VI", PINK, k)
        if k > 0:
            self.Ln(d, [(500, 850), (500 + 80 * k, 850)], WHITE, 10)
            self.P(d, [(590, 850), (560, 830), (560, 870)], WHITE)
        self.stamp(img, "COPIA", t, self.w("d2", "copiados"), y=1400)

    def s_d3(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        games = ["GTA III", "VICE CITY", "SAN ANDREAS", "GTA IV", "GTA V"]
        for i, g in enumerate(games):
            y = 560 + i * 120
            k = clamp((lt - i * 0.35) / 0.3)
            if k <= 0:
                continue
            self.text(img, 520, y, g, 52, WHITE, alpha=k, anchor="rm")
            self.Ln(d, [(560, y), (585, y + 25), (635, y - 25)], (120, 230, 120), 12)
            self.text(img, 670, y, "TRUCOS", 44, (120, 230, 120), alpha=k, anchor="lm")
        kk = clamp((t - self.w("d3", "probable")) / 0.4)
        if kk > 0:
            self.text(img, 520, 1220, "GTA VI", 64, PINK, alpha=kk, anchor="rm")
            self.text(img, 560, 1220, "¿PROBABLE?", 54, YEL, alpha=kk, anchor="lm")

    def s_d4(self, img, d, t, lt, u):
        self.sunset(img, d, t, 1.0)
        cx, cy = 540, 820
        self.E(d, cx, cy - 60, 150, (250, 200, 60), ry=150)  # trofeo
        self.R(d, cx - 30, cy + 80, cx + 30, cy + 170, (250, 200, 60))
        self.R(d, cx - 110, cy + 170, cx + 110, cy + 210, (220, 170, 50), radius=10)
        for sx in (-1, 1):
            d.arc([(cx + sx * 150 - 70) * S, (cy - 140) * S, (cx + sx * 150 + 70) * S, (cy) * S], 0, 360, fill=(250, 200, 60), width=int(16 * S))
        k = clamp((t - self.w("d4", "desactivaban")) / 0.3)
        if k > 0:
            self.Ln(d, [(cx - 220, cy - 220), (cx - 220 + 440 * k, cy - 220 + 440 * k)], RED, 26)
        self.pop_text(img, 540, 1450, "GUARDA ANTES", 76, t, self.w("d4", "guarda"), YEL)

    def s_d5(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        self.globe(img, 540, 820, 260, t, spin=25, glow_col=PINK)
        self.text(img, 540, 1160, "MODO ONLINE", 64, WHITE)
        self.text(img, 540, 1260, "0 TRUCOS", 72, NEON)
        self.stamp(img, "ESTAFA", t, self.w("d5", "estafa") - 0.1, y=1500)

    def s_d6(self, img, d, t, lt, u):
        self.s_d9_base(img, d, t, lt, "PRECARGA · PS5", NEON, "DESDE EL 10 DE NOVIEMBRE", self.w("d6", "diez"))

    def s_d9_base(self, img, d, t, lt, title, col, sub, t_sub):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        k = smooth(0.3, 3.0, lt)
        self.R(d, 140, 900, 940, 990, (40, 30, 60), radius=45)
        self.R(d, 150, 910, 150 + 780 * k, 980, col, radius=35)
        self.text(img, 540, 820, title, 62, WHITE)
        self.text(img, 540, 1100, f"{int(100 * k)} %", 80, YEL)
        self.pop_text(img, 540, 1300, sub, 50, t, t_sub, CYAN)

    def s_d7(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        k = smooth(0.2, 2.5, lt)  # disco que se vacía
        self.R(d, 290, 600, 790, 1180, (40, 40, 55), radius=40)
        self.E(d, 540, 860, 170, (70, 70, 90))
        self.E(d, 540, 860, 30, (30, 30, 40))
        self.R(d, 290, 1230, 790, 1290, (40, 30, 60), radius=30)
        free = 0.15 + 0.7 * k
        self.R(d, 296, 1236, 296 + 488 * (1 - free), 1284, PINK, radius=26)
        self.text(img, 540, 1360, f"ESPACIO LIBRE · {int(free * 100)} %", 50, NEON)
        self.pop_text(img, 540, 1500, "JUEGO ENORME", 70, t, self.w("d7", "enorme"), YEL)

    def s_d8(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        self.R(d, 360, 560, 720, 1220, (25, 25, 35), radius=46)  # móvil con vídeo falso
        self.R(d, 380, 600, 700, 1180, (90, 40, 120), radius=30)
        self.P(d, [(500, 820), (500, 960), (610, 890)], WHITE)
        self.stamp(img, "FALSO · IA", t, self.w("d8", "inteligencia"), y=900, rot=-14)
        self.pop_text(img, 540, 1450, "ROCKSTAR PIDE RETIRARLOS", 50, t, self.w("d8", "retirar"), YEL)

    def s_d9(self, img, d, t, lt, u):
        self.bg(img, "night", (20, 10, 45), (60, 25, 90))
        self.stars(d, t, 0.5)
        self.R(d, 240, 600, 840, 1000, (30, 30, 40), radius=24)
        self.R(d, 260, 620, 820, 980, (50, 50, 70), radius=14)
        self.R(d, 500, 1000, 580, 1100, (30, 30, 40))
        self.R(d, 400, 1100, 680, 1130, (30, 30, 40), radius=10)
        self.text(img, 540, 800, "GTA VI GRATIS", 52, (120, 230, 120))
        self.stamp(img, "ESTAFA", t, self.w("d9", "gratis") + 0.2, y=1180, rot=-12)
        self.pop_text(img, 540, 1420, "PC: SIN FECHA OFICIAL", 60, t, self.w("d9", "fecha"), WHITE)

    def s_d10(self, img, d, t, lt, u):
        self.sunset(img, d, t, 0.7)
        self.pop_text(img, 540, 700, "NIVEL OCULTO", 120, t, self.w("d10", "nivel") - 0.1, YEL)
        k = back_out((lt - 0.4) / 0.4)
        if k > 0:  # campana de notificaciones
            sw = 12 * math.sin(t * 8)
            self.P(d, [(540 - 70 * k + sw, 960), (540 - 55 * k + sw * 0.6, 860), (540 + sw * 0.3, 830), (540 + 55 * k + sw * 0.6, 860), (540 + 70 * k + sw, 960)], WHITE)
            self.E(d, 540 + sw, 980, 18 * k, WHITE)

    def hud(self, out, t):
        name = self.scene_at(t)[0]
        if name.startswith("d"):
            return self.pill(out, f"CONSEJO {name[1:]}/10", YEL, y=1835, size=42)
        return out

    def sfx_events(self):
        ev = [(0.2, "boom", 0.5), (self.w("intro", "falsos") - 0.2, "click", 0.7)]
        for i in range(1, 11):
            ev.append((self.start(f"d{i}") + 0.05, "pop", 0.45))
        ev += [(self.w("d1", "confirmado"), "click", 0.6), (self.w("d2", "copiados"), "click", 0.6), (self.w("d4", "desactivaban"), "click", 0.5),
               (self.w("d5", "estafa") - 0.1, "click", 0.6), (self.w("d8", "inteligencia"), "click", 0.6), (self.w("d9", "gratis") + 0.2, "click", 0.6),
               (self.start("d10") + 0.3, "shimmer", 0.5), (self.start("cta"), "pop", 0.6)]
        return ev


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
