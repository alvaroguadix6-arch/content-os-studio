"""NIVEL OCULTO · Elecciones generales del 29-N: lo que tienes que saber (24-11-2026). Vídeo informativo y neutral.

Fuentes: La Moncloa (Sánchez anuncia el 5-10-2026 la convocatoria para el 29-11; guía del 29N: campaña 13-27 nov,
reflexión el 28, votación de 9 a 20 h), BOE (Real Decreto 806/2026), LOREG art. 69.7 (prohibido publicar sondeos los
5 días anteriores a la votación), Telemadrid y Artículo 14 (candidatos: Sánchez, Feijóo, Abascal, Ada Colau al frente de
una candidatura conjunta de izquierdas, Irene Montero por Podemos), CIS de noviembre (campo 10-17 nov: PSOE 34,4 %,
PP 24,7 %, Vox 15,6 %), Infobae (media de encuestas: PP+Vox 51,5 %), resultados de 2023 (Ministerio del Interior:
PP 137, PSOE 121, Vox 33, Sumar 31, otros 28). Sin imágenes de personas reales: solo tarjetas con nombres.
"""
from __future__ import annotations

import math

from motor import CYAN, RED, WHITE, W, H, S, YEL, Video, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: F401

MOOD, BPM = "suspense", 92
PP, PSOE, VOX, SUMAR, OTROS = (40, 120, 210), (225, 45, 55), (100, 185, 70), (225, 70, 140), (150, 150, 165)
PODEMOS = (120, 70, 170)
BG = ((10, 12, 30), (24, 26, 56))


def seats(n=350, rows=12):
    """Posiciones del hemiciclo (de izquierda a derecha por ángulo)."""
    radii = [260 + i * 34 for i in range(rows)]
    tot = sum(radii)
    per = [round(n * r / tot) for r in radii]
    per[-1] += n - sum(per)
    pts = []
    for r, k in zip(radii, per):
        for j in range(k):
            a = math.pi * (1 - j / max(1, k - 1))
            pts.append((a, r))
    pts.sort(key=lambda p: (-p[0], p[1]))
    return pts


class VIDEO(Video):
    NAME = "elecciones29n"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"cinco", "días", "elecciones", "generales", "prohibido", "encuestas", "ley", "últimas", "domingo", "veintinueve", "noviembre",
                "adelantó", "octubre", "trescientos", "cincuenta", "mayoría", "absoluta", "setenta", "seis", "pp", "treinta", "siete",
                "sánchez", "feijóo", "abascal", "colau", "montero", "psoe", "vox", "podemos", "cis", "diez", "mitad", "reflexión",
                "nueve", "ocho", "votar", "respeto", "comentarios"}

    def setup(self):
        self.seat_pts = seats()
        self.cx, self.cy = 540, 1250

    def build_scenes(self):
        st = self.start
        return [(0.0, "golpe"), (st("ley") - 0.12, "ley"), (st("fecha") - 0.12, "fecha"), (st("escanos") - 0.12, "hemi"),
                (st("pasado") - 0.12, "pasado"), (st("candidatos") - 0.12, "candidatos"), (st("encuestas") - 0.12, "encuestas"),
                (st("calendario") - 0.12, "calendario"), (st("cta") - 0.1, "fin")]

    # ───── piezas ─────
    def day_tile(self, img, d, x, y, w, h, top, num, col, k=1.0):
        if k <= 0.01:
            return
        w, h = w * k, h * k
        self.R(d, x - w / 2, y - h / 2, x + w / 2, y + h / 2, WHITE, radius=18)
        self.R(d, x - w / 2, y - h / 2, x + w / 2, y - h / 2 + h * 0.28, col, radius=18)
        if k > 0.7:
            self.text(img, x, y - h / 2 + h * 0.14, top, 26, WHITE, shadow=False)
            self.text(img, x, y + h * 0.13, num, 64, (30, 30, 40), shadow=False)

    def stamp(self, img, x, y, txt, size, t, t0, col=RED, rot=-8):
        k = back_out((t - t0) / 0.3)
        if k <= 0:
            return
        from PIL import Image, ImageDraw
        from motor import font
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        f = font("ExtraBold", int(size * S * (2 - k if k < 1 else 1)))
        tw = f.getlength(txt)
        dl.rounded_rectangle([x * S - tw / 2 - 30 * S, y * S - size * S * 0.75, x * S + tw / 2 + 30 * S, y * S + size * S * 0.75], radius=int(16 * S),
                             outline=col + (255,), width=int(9 * S), fill=(0, 0, 0, 120))
        dl.text((x * S, y * S), txt, font=f, fill=col + (255,), anchor="mm")
        img.alpha_composite(lay.rotate(-rot, center=(x * S, y * S)))

    def hemicycle(self, d, n_on, colors=None, k_pulse=0.0):
        for i, (a, r) in enumerate(self.seat_pts):
            x, y = self.cx + math.cos(a) * r, self.cy - math.sin(a) * r
            if i < n_on:
                col = colors[i] if colors else (200, 205, 225)
            else:
                col = (44, 48, 78)
            self.E(d, x, y, 11, col)

    # ───── escenas ─────
    def s_golpe(self, img, d, t, lt, u):
        self.bgdyn(img, *BG)
        days = [("MAR", "24"), ("MIÉ", "25"), ("JUE", "26"), ("VIE", "27"), ("SÁB", "28"), ("DOM", "29")]
        for i, (dname, num) in enumerate(days):
            k = back_out((lt - 0.1 - i * 0.12) / 0.35)
            x = 115 + i * 170
            self.day_tile(img, d, x, 900, 150, 190, dname, num, YEL if num == "29" else (90, 90, 120), k)
            tr = self.w("intro", "prohibido") + i * 0.12
            if num != "29" and t > tr:  # tachados: días sin encuestas
                kk = clamp((t - tr) / 0.25)
                self.Ln(d, [(x - 60, 830), (x - 60 + 120 * kk, 830 + 140 * kk)], RED, 12)
        if t > self.w("intro", "elecciones"):
            self.glow(img, 115 + 5 * 170, 900, 130, (255, 214, 70), 120)
        self.pop_text(img, 540, 560, "29-N", 150, t, self.w("intro", "elecciones"), YEL)
        self.stamp(img, 540, 1260, "SIN ENCUESTAS", 74, t, self.w("intro", "encuestas"))

    def s_ley(self, img, d, t, lt, u):
        self.bgdyn(img, *BG)
        vals = [0.55, 0.8, 0.4, 0.65, 0.3]
        for i, v in enumerate(vals):  # gráfico de encuesta genérico
            k = ease_out(clamp((lt - i * 0.1) / 0.6))
            x = 250 + i * 145
            self.R(d, x, 1300 - 500 * v * k, x + 100, 1300, (90, 100, 150), radius=12)
        self.Ln(d, [(200, 1300), (930, 1300)], WHITE, 4)
        self.stamp(img, 540, 1000, "PROHIBIDO PUBLICAR", 60, t, self.start("ley") + 0.6, RED)
        self.pop_text(img, 540, 560, "LEY ELECTORAL", 84, t, self.w("ley", "ley"), WHITE)
        self.pop_text(img, 540, 670, "5 DÍAS ANTES DE VOTAR", 56, t, self.w("ley", "cinco"), YEL)
        self.pop_text(img, 540, 1460, "LAS ÚLTIMAS QUE VERÁS", 60, t, self.w("ley", "últimas"), CYAN)

    def s_fecha(self, img, d, t, lt, u):
        self.bgdyn(img, *BG)
        k = back_out((lt - 0.1) / 0.45)
        self.day_tile(img, d, 540, 900, 380, 440, "DOMINGO · NOVIEMBRE", "", RED, k)
        if k > 0.7:
            self.text(img, 540, 960, "29", 220, (30, 30, 40), shadow=False)
        kt = smooth(self.w("fecha", "adelantó") - 0.2, self.w("fecha", "octubre") + 0.6, t)
        if kt > 0:  # línea de tiempo 5 oct → 29 nov
            self.R(d, 160, 1340, 920, 1360, (50, 54, 90), radius=10)
            self.R(d, 160, 1340, 160 + 760 * kt, 1360, YEL, radius=10)
            self.E(d, 160, 1350, 18, WHITE)
            self.E(d, 920, 1350, 18, RED)
            self.text(img, 160, 1410, "5 OCT", 40, WHITE)
            self.text(img, 920, 1410, "29 NOV", 40, RED)
            self.text(img, 540, 1480, "ADELANTO ELECTORAL", 52, YEL, alpha=kt)

    def s_hemi(self, img, d, t, lt, u):
        self.bgdyn(img, *BG)
        n = int(350 * ease_out(clamp(lt / 2.2)))
        self.hemicycle(d, n)
        self.text(img, 540, self.cy + 40, f"{n}", 120, WHITE)
        self.text(img, 540, self.cy + 130, "DIPUTADOS", 44, (200, 200, 230))
        km = smooth(self.w("escanos", "mayoría") - 0.2, self.w("escanos", "mayoría") + 0.5, t)
        if km > 0:  # línea de la mayoría absoluta
            a = math.pi * (1 - 175.5 / 350)
            self.Ln(d, [(self.cx, self.cy), (self.cx + math.cos(a) * 680 * km, self.cy - math.sin(a) * 680 * km)], YEL, 8)
            self.pop_text(img, 540, 520, "MAYORÍA ABSOLUTA: 176", 70, t, self.w("escanos", "setenta"), YEL)

    def s_pasado(self, img, d, t, lt, u):
        self.bgdyn(img, *BG)
        res = [("SUMAR", 31, SUMAR), ("PSOE", 121, PSOE), ("OTROS", 28, OTROS), ("PP", 137, PP), ("VOX", 33, VOX)]
        cols = []
        for _, n, c in res:
            cols += [c] * n
        k = ease_out(clamp((lt - 0.2) / 2.0))
        self.hemicycle(d, int(350 * k), cols)
        self.pop_text(img, 540, 520, "2023", 120, t, self.start("pasado") + 0.1, WHITE)
        for i, (name, n, c) in enumerate([("PP", 137, PP), ("PSOE", 121, PSOE), ("VOX", 33, VOX), ("SUMAR", 31, SUMAR), ("OTROS", 28, OTROS)]):
            kk = back_out((lt - 0.6 - i * 0.15) / 0.35)
            if kk > 0:
                x = 130 + i * 205
                self.R(d, x - 85 * kk, 1400, x + 85 * kk, 1500, c, radius=18)
                if kk > 0.7:
                    self.text(img, x, 1430, name, 30, WHITE, shadow=False)
                    self.text(img, x, 1475, str(n), 42, WHITE, shadow=False)
        self.pop_text(img, 540, 1590, "GOBERNÓ SÁNCHEZ CON APOYOS", 50, t, self.w("pasado", "gobernó"), CYAN)

    def s_candidatos(self, img, d, t, lt, u):
        self.bgdyn(img, *BG)
        if t < self.w("candidatos", "sánchez") + 0.2:
            self.pop_text(img, 540, 900, "CANDIDATOS", 110, t, self.start("candidatos") + 0.05, YEL)
        cands = [("sánchez", "PEDRO SÁNCHEZ", "PSOE", PSOE), ("feijóo", "ALBERTO NÚÑEZ FEIJÓO", "PP", PP), ("abascal", "SANTIAGO ABASCAL", "VOX", VOX),
                 ("colau", "ADA COLAU", "CANDIDATURA CONJUNTA DE IZQUIERDAS", SUMAR), ("montero", "IRENE MONTERO", "PODEMOS", PODEMOS)]
        for i, (frag, name, party, c) in enumerate(cands):
            k = back_out((t - self.w("candidatos", frag) + 0.15) / 0.35)
            if k <= 0.01:
                continue
            y = 470 + i * 220
            x0 = 80 - (1 - min(1, k)) * 600
            self.R(d, x0, y, x0 + 920, y + 180, (20, 22, 46), radius=28, outline=c, width=6)
            self.R(d, x0, y, x0 + 28, y + 180, c, radius=12)
            self.E(d, x0 + 120, y + 70, 36, c)  # silueta genérica
            self.R(d, x0 + 70, y + 110, x0 + 170, y + 165, c, radius=28)
            self.text(img, x0 + 210, y + 70, name, 46 if len(name) < 18 else 40, WHITE, anchor="lm")
            self.text(img, x0 + 210, y + 128, party, 32 if len(party) < 20 else 26, c, anchor="lm")

    def s_encuestas(self, img, d, t, lt, u):
        self.bgdyn(img, *BG)
        tm = self.w("encuestas", "media") - 0.2
        if t < self.w("encuestas", "cis") - 0.15:
            self.pop_text(img, 540, 900, "¿QUIÉN GANA?", 110, t, self.start("encuestas") + 0.05, YEL)
            for j in range(3):
                self.qmark(img, 300 + j * 240, 1150 + 20 * math.sin(t * 4 + j), 120 * back_out((lt - 0.3 - j * 0.15) / 0.3))
            return
        if t < tm:
            self.pop_text(img, 540, 520, "CIS · NOVIEMBRE", 78, t, self.w("encuestas", "cis"), WHITE)
            for i, (name, v, c) in enumerate([("PSOE", 34.4, PSOE), ("PP", 24.7, PP), ("VOX", 15.6, VOX)]):
                if t < self.w("encuestas", "cis") - 0.1:
                    break
                k = ease_out(clamp((t - self.w("encuestas", "cis") - i * 0.2) / 1.0))
                y = 760 + i * 200
                self.text(img, 110, y, name, 54, c, anchor="lm")
                self.R(d, 300, y - 50, 300 + 15 * v * k, y + 50, c, radius=20)
                self.text(img, 300 + 15 * v * k + 20, y, f"{v * k:.1f} %".replace(".", ","), 48, WHITE, anchor="lm")
            self.text(img, 540, 1450, "campo: 10–17 de noviembre", 34, (180, 180, 210))
        else:
            k = ease_out(clamp((t - tm) / 1.2))
            self.pop_text(img, 540, 520, "MEDIA DEL RESTO", 78, t, tm, WHITE)
            self.R(d, 120, 900, 960, 1040, (40, 44, 80), radius=30)
            w1 = 840 * 0.515 * k
            self.R(d, 120, 900, 120 + w1 * 0.62, 1040, PP, radius=30)
            self.R(d, 120 + w1 * 0.62, 900, 120 + w1, 1040, VOX)
            self.Ln(d, [(540, 860), (540, 1080)], YEL, 6)
            self.text(img, 540, 830, "50 %", 40, YEL)
            self.text(img, 540, 1150, f"PP + VOX ≈ {51.5 * k:.1f} %".replace(".", ","), 72, WHITE)
            self.pop_text(img, 540, 1450, "NO SE PONEN DE ACUERDO", 60, t, tm + 0.8, YEL)

    def s_calendario(self, img, d, t, lt, u):
        self.bgdyn(img, *BG)
        items = [("viernes", "VIE 27", "FIN DE CAMPAÑA", (90, 100, 150)), ("sábado", "SÁB 28", "REFLEXIÓN", (110, 90, 150)),
                 ("domingo", "DOM 29", "VOTACIÓN", RED)]
        for i, (frag, day, lab, c) in enumerate(items):
            k = back_out((t - self.w("calendario", frag) + 0.1) / 0.35)
            x = 200 + i * 340
            self.day_tile(img, d, x, 760, 260, 300, day.split()[0], day.split()[1], c, k)
            if k > 0.7:
                self.text(img, x, 960, lab, 36, c if i == 2 else WHITE)
        kv = smooth(self.w("calendario", "vota") - 0.2, self.w("calendario", "vota") + 0.4, t)
        if kv > 0:  # urna y sobre que cae
            self.R(d, 380, 1180, 700, 1480, (230, 235, 245), radius=20)
            self.R(d, 470, 1170, 610, 1190, (40, 44, 70))
            ph = (lt * 0.8) % 1
            self.R(d, 485, 1000 + 160 * ph, 595, 1070 + 160 * ph, (250, 240, 200), radius=6)
            self.text(img, 540, 1580, "9:00 → 20:00", 76, YEL, alpha=kv)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def camera(self, t, name, lt, u):
        if name in ("hemi", "pasado"):
            return 1.0 + 0.06 * smooth(0, 4, lt), 540, 1050
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        ev = [(0.1, "riser", 0.4), (self.w("intro", "elecciones"), "boom", 0.6), (self.w("intro", "encuestas"), "boom", 0.7),
              (st("ley") + 0.6, "click", 0.6), (self.w("ley", "últimas"), "pop", 0.4), (st("fecha") + 0.1, "pop", 0.5),
              (self.w("fecha", "adelantó"), "whoosh", 0.4), (st("escanos") + 0.1, "riser", 0.4), (self.w("escanos", "setenta"), "boom", 0.5),
              (st("pasado") + 0.1, "pop", 0.5), (self.w("pasado", "gobernó"), "shimmer", 0.4), (st("encuestas") + 0.2, "whoosh", 0.4),
              (self.w("encuestas", "media"), "pop", 0.5), (st("calendario") + 0.1, "tick", 0.7), (self.w("calendario", "vota"), "drip", 0.6),
              (st("cta"), "pop", 0.6)]
        ev += [(self.w("candidatos", f), "pop", 0.45) for f in ("sánchez", "feijóo", "abascal", "colau", "montero")]
        return ev

    def music_plan(self):
        st = self.start
        return [(0, 0.8), (st("ley"), 0.6), (st("escanos"), 0.65), (st("candidatos"), 0.7), (st("encuestas"), 0.85), (st("calendario"), 0.6),
                (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
