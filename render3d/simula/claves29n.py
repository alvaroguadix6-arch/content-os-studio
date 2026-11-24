"""NIVEL OCULTO · Las 5 claves del 29-N (explicativo, neutral y SIN datos de sondeos: LOREG 69.7 prohíbe publicarlos
los 5 días previos a la votación).

Fuentes: Constitución art. 99 (investidura: mayoría absoluta en 1.ª votación; simple 48 h después) y art. 68.6 (el
Congreso electo se convoca en los 25 días siguientes); LOREG art. 162-163 (circunscripción provincial, mínimo de 2
diputados por provincia, 1 Ceuta y 1 Melilla, sistema D'Hondt, barrera del 3 % de votos válidos por circunscripción);
resultados 2023 (Interior): PP 137, PSOE 121, Vox 33, Sumar 31, otros 28; Madrid elige más de 30 diputados, Soria 2;
La Moncloa: votación de 9 a 20 h. El ejemplo D'Hondt es ilustrativo (partidos A-D ficticios).
"""
from __future__ import annotations

import math
import os

os.environ.setdefault("QUIZ", "monumentos")  # el mapa de provincias de quiz.py (España)
import quiz  # noqa: E402
from PIL import Image  # noqa: E402

from motor import CYAN, RED, WHITE, W, H, S, YEL, Video, back_out, clamp, ease_out, mix, render, schedule, smooth  # noqa: E402,F401

MOOD, BPM = "suspense", 90
PP, PSOE, VOX, SUMAR, OTROS = (40, 120, 210), (225, 45, 55), (100, 185, 70), (225, 70, 140), (150, 150, 165)
NAVY = ((7, 11, 26), (16, 22, 50))
ACC = (255, 196, 40)


def seats(n=350, rows=12):
    radii = [250 + i * 33 for i in range(rows)]
    tot = sum(radii)
    per = [round(n * r / tot) for r in radii]
    per[-1] += n - sum(per)
    pts = [(math.pi * (1 - j / max(1, k - 1)), r) for r, k in zip(radii, per) for j in range(k)]
    pts.sort(key=lambda p: (-p[0], p[1]))
    return pts


class VIDEO(Video):
    NAME = "claves29n"
    BRAND = "NIVEL OCULTO"
    KEYWORDS = {"ganar", "gobernar", "veintitrés", "pp", "votado", "otro", "cinco", "claves", "investidura", "presidente", "ciento", "setenta",
                "seis", "segunda", "síes", "noes", "provincia", "batalla", "madrid", "treinta", "soria", "dos", "d'hondt", "cocientes",
                "escaños", "menos", "tres", "ciento", "fuera", "bloques", "vox", "feijóo", "mayoría", "apoyos", "noche", "ocho", "urna",
                "recuento", "congreso", "veinticinco", "partida", "gobierno", "negociación", "comentarios"}
    CHAPTERS = {"mayoria": (1, "LA INVESTIDURA"), "provincias": (2, "LAS PROVINCIAS"), "dhondt": (3, "LA LEY D'HONDT"),
                "bloques": (4, "LOS BLOQUES"), "noche": (5, "LA NOCHE ELECTORAL")}

    def setup(self):
        self.pts = seats()
        self.cx, self.cy = 540, 1260
        self._map = None

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("mayoria") - 0.12, "mayoria"), (st("provincias") - 0.12, "provincias"), (st("dhondt") - 0.12, "dhondt"),
                (st("umbral") - 0.12, "umbral"), (st("bloques") - 0.12, "bloques"), (st("noche") - 0.12, "noche"),
                (st("despues") - 0.12, "despues"), (st("cta") - 0.1, "fin")]

    # ───── estética de informativo ─────
    def studio(self, img, d, t):
        self.bgdyn(img, *NAVY)
        for i in range(13):  # rejilla sutil
            x = i * 90 + (t * 6) % 90
            self.Ln(d, [(x, 0), (x, H)], (22, 30, 62), 1)
        for j in range(22):
            y = j * 90
            self.Ln(d, [(0, y), (W, y)], (22, 30, 62), 1)
        self.glow(img, 540 + 300 * math.sin(t * 0.3), 700, 520, (40, 70, 150), 60)

    def chapter(self, img, d, t, key):
        """Rótulo de capítulo al empezar cada clave (barra que barre + número)."""
        if key not in self.CHAPTERS:
            return
        n, title = self.CHAPTERS[key]
        lt = t - (self.start(key) - 0.12)
        if lt > 1.3:
            return
        a = ease_out(clamp(lt / 0.35))
        out = clamp((lt - 1.0) / 0.3)
        x1 = W * a - W * out
        self.R(d, -10, 760, x1, 1060, ACC)
        if a > 0.6 and out < 0.9:
            self.text(img, 540 - W * out, 850, f"CLAVE {n}/5", 64, (20, 16, 30), shadow=False)
            self.text(img, 540 - W * out, 960, title, 84, (20, 16, 30), shadow=False)

    def lower_third(self, img, d, t, key):
        if key not in self.CHAPTERS or t - self.start(key) < 1.2:
            return
        n, title = self.CHAPTERS[key]
        k = ease_out(clamp((t - self.start(key) - 1.2) / 0.4))
        x0 = 60 - (1 - k) * 700
        self.R(d, x0, 1600, x0 + 120, 1660, ACC, radius=10)
        self.text(img, x0 + 60, 1630, f"{n}/5", 34, (20, 16, 30), shadow=False)
        self.R(d, x0 + 130, 1600, x0 + 130 + 22 * len(title) + 60, 1660, (20, 26, 56), radius=10)
        self.text(img, x0 + 160, 1630, title, 34, WHITE, anchor="lm", shadow=False)

    def hemicycle(self, d, cols_fn, r=10):
        for i, (a, rr) in enumerate(self.pts):
            self.E(d, self.cx + math.cos(a) * rr, self.cy - math.sin(a) * rr, r, cols_fn(i))

    def spain(self, img, highlights=(), t=0.0):
        if self._map is None:
            self._map = quiz.base_map().resize((W * S, H * S), Image.LANCZOS)
        img.alpha_composite(self._map, (0, -int(40 * S)))
        for name, a in highlights:
            if a > 0:
                h = quiz.highlight(name).resize((W * S, H * S), Image.BILINEAR)
                img.alpha_composite(quiz._alpha(h, a), (0, -int(40 * S)))

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.studio(img, d, t)
        res = [(SUMAR, 31), (PSOE, 121), (OTROS, 28), (PP, 137), (VOX, 33)]
        cols = [c for c, n in res for _ in range(n)]
        k = ease_out(clamp(lt / 1.6))
        pp_on = smooth(self.w("intro", "pp") - 0.1, self.w("intro", "pp") + 0.4, t)
        self.hemicycle(d, lambda i: (cols[i] if i < 350 * k else (40, 46, 80)) if not (pp_on and cols[i] != PP) else mix(cols[i], (40, 46, 80), 0.7 * pp_on))
        self.pop_text(img, 540, 520, "GANAR ≠ GOBERNAR", 96, t, 0.25, ACC)
        kp = back_out((t - self.w("intro", "votado")) / 0.4)
        if kp > 0:
            self.R(d, 640 - 130 * kp, 1340, 640 + 130 * kp, 1440, PP, radius=20)
            self.text(img, 640, 1390, "PP 137 · 2023", 40 * min(1, kp), WHITE, shadow=False)
        self.pop_text(img, 540, 1560, "LAS 5 CLAVES DEL 29-N", 64, t, self.w("intro", "claves"), WHITE)

    def s_mayoria(self, img, d, t, lt, u):
        self.studio(img, d, t)
        k1 = smooth(self.w("mayoria", "primera") - 0.2, self.w("mayoria", "seis") + 0.3, t)
        self.text(img, 540, 560, "1.ª VOTACIÓN", 56, WHITE, alpha=clamp(k1 * 3))
        self.R(d, 120, 640, 960, 720, (30, 38, 74), radius=20)
        self.R(d, 120, 640, 120 + 840 * 176 / 350 * k1, 720, ACC, radius=20)
        xm = 120 + 840 * 176 / 350
        self.Ln(d, [(xm, 610), (xm, 750)], WHITE, 6)
        self.text(img, xm, 790, "176 DE 350", 44, ACC, alpha=clamp(k1 * 3))
        k2 = smooth(self.w("mayoria", "segunda") - 0.2, self.w("mayoria", "noes") + 0.4, t)
        if k2 > 0:
            self.text(img, 540, 960, "2.ª VOTACIÓN (48 h DESPUÉS)", 50, WHITE, alpha=clamp(k2 * 3))
            self.R(d, 160, 1040, 160 + 420 * k2, 1130, (90, 200, 120), radius=18)
            self.R(d, 160, 1160, 160 + 360 * k2, 1250, (220, 80, 80), radius=18)
            self.text(img, 620 + 0 * k2, 1085, "SÍ", 52, (90, 200, 120), anchor="lm", alpha=k2)
            self.text(img, 560, 1205, "NO", 52, (220, 80, 80), anchor="lm", alpha=k2)
            self.pop_text(img, 540, 1400, "MÁS SÍES QUE NOES", 66, t, self.w("mayoria", "noes"), ACC)
        self.chapter(img, d, t, "mayoria")
        self.lower_third(img, d, t, "mayoria")

    def s_provincias(self, img, d, t, lt, u):
        self.studio(img, d, t)
        names = sorted(quiz.PROVS)
        sweep = smooth(0.8, 3.0, lt)
        hl = [(n, 0.35) for i, n in enumerate(names) if i < len(names) * sweep and (i * 7) % 3 == 0 and t < self.w("provincias", "madrid") - 0.2]
        km = smooth(self.w("provincias", "madrid") - 0.2, self.w("provincias", "madrid") + 0.3, t)
        ks = smooth(self.w("provincias", "soria") - 0.2, self.w("provincias", "soria") + 0.3, t)
        self.spain(img, hl + [("Madrid", km), ("Soria", ks)], t)
        self.chapter(img, d, t, "provincias")

    def overlay(self, ov, d, t, name, lt, u):
        if name != "provincias":
            return False
        km = smooth(self.w("provincias", "madrid") - 0.2, self.w("provincias", "madrid") + 0.3, t)
        ks = smooth(self.w("provincias", "soria") - 0.2, self.w("provincias", "soria") + 0.3, t)
        if km > 0:
            self.R(d, 120, 1420, 500, 1530, (20, 26, 56), radius=20, outline=ACC, width=4)
            self.text(ov, 310, 1475, "MADRID: +30", 52, ACC, alpha=km)
        if ks > 0:
            self.R(d, 580, 1420, 960, 1530, (20, 26, 56), radius=20, outline=CYAN, width=4)
            self.text(ov, 770, 1475, "SORIA: 2", 52, CYAN, alpha=ks)
        if t > self.start("provincias") + 1.2:
            self.pop_text(ov, 540, 520, "52 CIRCUNSCRIPCIONES", 72, t, max(self.start("provincias") + 1.2, self.w("provincias", "provincia")), WHITE)
        self.lower_third(ov, d, t, "provincias")
        return True

    def s_dhondt(self, img, d, t, lt, u):
        self.studio(img, d, t)
        parties = [("A", 40, (90, 150, 230)), ("B", 30, (230, 120, 90)), ("C", 20, (120, 200, 140)), ("D", 10, (190, 150, 220))]
        x0, y0 = 120, 640
        self.text(img, 540, 540, "EJEMPLO · 5 ESCAÑOS", 50, ACC)
        heads = ["", "VOTOS", "ENTRE 1", "ENTRE 2", "ENTRE 3"]
        xs = [x0 + 40, x0 + 190, x0 + 380, x0 + 560, x0 + 740]
        for x, hd in zip(xs, heads):
            self.text(img, x, y0, hd, 32, (180, 190, 230))
        kd = smooth(self.w("dhondt", "dividen") - 0.3, self.w("dhondt", "dividen") + 2.2, t)
        quots = []
        for r, (nm, v, c) in enumerate(parties):
            y = y0 + 110 + r * 130
            self.R(d, x0, y - 50, x0 + 80, y + 50, c, radius=14)
            self.text(img, x0 + 40, y, nm, 50, WHITE, shadow=False)
            self.text(img, xs[1], y, f"{v}.000", 44, WHITE)
            for j in range(3):
                q = v / (j + 1)
                quots.append((q, r, j))
                if kd * 3 > j + (r * 0.15):
                    self.text(img, xs[2 + j], y, f"{q:.1f}".replace(".0", "").replace(".", ","), 44, (230, 230, 240))
        top = sorted(quots, key=lambda q: -q[0])[:5]
        kc = smooth(self.w("dhondt", "cocientes") - 0.2, self.w("dhondt", "cocientes") + 2.0, t)
        won = [0, 0, 0, 0]
        for i, (q, r, j) in enumerate(top):
            if kc * 5 > i:
                y = y0 + 110 + r * 130
                self.R(d, xs[2 + j] - 70, y - 44, xs[2 + j] + 70, y + 44, None, radius=14, outline=ACC, width=6)
                won[r] += 1
        for r in range(4):  # escaños ganados
            y = y0 + 110 + r * 130
            for s in range(won[r]):
                self.E(d, 930 + s * 0 - 0, y, 0.01, ACC)
            if kc > 0:
                self.text(img, 960, y, f"{won[r]}", 54, ACC if won[r] else (120, 120, 150), anchor="rm")
        self.pop_text(img, 540, 1360, "B: 10 PUNTOS MENOS QUE A", 52, t, self.w("dhondt", "menos"), WHITE)
        self.pop_text(img, 540, 1440, "... Y LOS MISMOS ESCAÑOS", 56, t, self.w("dhondt", "escaños", 0.2) if False else self.w("dhondt", "menos") + 0.6, ACC)
        self.chapter(img, d, t, "dhondt")
        self.lower_third(img, d, t, "dhondt")

    def s_umbral(self, img, d, t, lt, u):
        self.studio(img, d, t)
        k = ease_out(clamp(lt / 1.2))
        y_line = 1300 - 600 * 3 / 10
        for i, (v, c) in enumerate([(5.5, (90, 150, 230)), (2.9, (190, 150, 220))]):
            x = 360 + i * 360
            h = 600 * v / 10 * k
            out = v < 3 and lt > 1.4
            self.R(d, x - 90, 1300 - h, x + 90, 1300, mix(c, (70, 70, 90), 0.75) if out else c, radius=14)
            self.text(img, x, 1300 - h - 50, f"{v * k:.1f} %".replace(".", ","), 50, WHITE)
        for xx in range(120, 960, 40):
            self.Ln(d, [(xx, y_line), (xx + 22, y_line)], RED, 6)
        self.text(img, 960, y_line - 40, "3 %", 46, RED, anchor="rm")
        self.stamp_txt(img, 720, 1000, "FUERA", t, self.start("umbral") + 1.4)
        self.lower_third(img, d, t, "dhondt")

    def stamp_txt(self, img, x, y, txt, t, t0):
        k = back_out((t - t0) / 0.3)
        if k > 0:
            self.text(img, x, y, txt, 90 * min(1.6, 2 - k if k < 1 else 1), RED)

    def s_bloques(self, img, d, t, lt, u):
        self.studio(img, d, t)
        # hemiciclo neutro: el relleno del bloque oscila alrededor de 176 (sin cifras: no se pueden publicar sondeos)
        n = int(176 + 26 * math.sin(lt * 1.8)) if lt > 1.4 else int(176 * ease_out(lt / 1.4))
        self.hemicycle(d, lambda i: (PP if i >= 350 - n * 0.72 else VOX) if i >= 350 - n else (40, 46, 80))
        a = math.pi * (1 - 174 / 350)
        self.Ln(d, [(self.cx, self.cy), (self.cx + math.cos(a) * 670, self.cy - math.sin(a) * 670)], ACC, 8)
        self.text(img, self.cx + math.cos(a) * 700, self.cy - math.sin(a) * 700 - 30, "176", 56, ACC)
        self.qmark(img, 540, 1250, 130)
        ky = smooth(self.w("bloques", "suman") - 0.2, self.w("bloques", "suman") + 0.3, t)
        kn = smooth(self.w("bloques", "llegan") - 0.2, self.w("bloques", "llegan") + 0.3, t)
        if ky > 0:
            self.R(d, 80, 1390, 520, 1560, (20, 26, 56), radius=22, outline=(90, 200, 120), width=5)
            self.text(img, 300, 1440, "≥ 176", 56, (90, 200, 120), alpha=ky)
            self.text(img, 300, 1510, "MAYORÍA PP + VOX", 34, WHITE, alpha=ky)
        if kn > 0:
            self.R(d, 560, 1390, 1000, 1560, (20, 26, 56), radius=22, outline=(230, 120, 90), width=5)
            self.text(img, 780, 1440, "< 176", 56, (230, 120, 90), alpha=kn)
            self.text(img, 780, 1510, "DECIDEN OTROS GRUPOS", 34, WHITE, alpha=kn)
        self.chapter(img, d, t, "bloques")

    def s_noche(self, img, d, t, lt, u):
        self.studio(img, d, t)
        k = smooth(1.0, 3.2, lt)
        cx, cy, r = 540, 800, 220
        self.E(d, cx, cy, r + 14, (230, 232, 240))
        self.E(d, cx, cy, r, (22, 28, 56))
        for i in range(12):
            a = i / 12 * 2 * math.pi
            self.Ln(d, [(cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85), (cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95)], WHITE, 5)
        hh = 6 + 2 * k  # de las 18 a las 20 h
        am = (hh % 1) * 2 * math.pi - math.pi / 2 + k * 4 * math.pi
        ah = (hh / 12) * 2 * math.pi - math.pi / 2
        self.Ln(d, [(cx, cy), (cx + math.cos(ah) * r * 0.5, cy + math.sin(ah) * r * 0.5)], WHITE, 14)
        self.Ln(d, [(cx, cy), (cx + math.cos(am) * r * 0.78, cy + math.sin(am) * r * 0.78)], ACC, 8)
        self.text(img, 540, 1110, "20:00", 90, ACC, alpha=smooth(2.8, 3.3, lt))
        ke = smooth(self.w("noche", "recuento") - 0.2, self.end("noche") + 0.3, t)
        if ke > 0:  # barra de escrutinio
            self.R(d, 120, 1300, 960, 1380, (30, 38, 74), radius=20)
            self.R(d, 120, 1300, 120 + 840 * ke, 1380, CYAN, radius=20)
            self.text(img, 540, 1440, f"ESCRUTADO {int(100 * ke)} %", 56, WHITE)
        self.pop_text(img, 540, 1250, "SONDEOS A PIE DE URNA", 48, t, self.w("noche", "urna"), WHITE)
        self.chapter(img, d, t, "noche")

    def s_despues(self, img, d, t, lt, u):
        self.studio(img, d, t)
        k = smooth(0.4, 2.6, lt)
        for i in range(26):  # 29-N + 25 días
            x = 62 + (i % 9) * 108
            y = 620 + (i // 9) * 150
            on = i <= 25 * k
            c = ACC if i == 0 else (CYAN if i == 25 else (60, 70, 120))
            self.R(d, x, y, x + 90, y + 120, c if on else (30, 36, 66), radius=14)
            day = 29 + i if 29 + i <= 30 else 29 + i - 30
            self.text(img, x + 45, y + 60, str(day), 40, (20, 20, 30) if on and i in (0, 25) else WHITE, shadow=False)
        self.text(img, 540, 1150, "29 NOV → 24 DIC", 64, WHITE, alpha=k)
        self.pop_text(img, 540, 1290, "MÁXIMO 25 DÍAS", 72, t, self.w("despues", "veinticinco"), ACC)
        self.pop_text(img, 540, 1440, "EMPIEZA LA NEGOCIACIÓN", 56, t, self.w("despues", "partida"), CYAN)

    def s_fin(self, img, d, t, lt, u):
        self.speech_end(img, d, t, self.start("cta"))

    def camera(self, t, name, lt, u):
        if name == "provincias":
            km = smooth(self.w("provincias", "madrid") - 0.3, self.w("provincias", "madrid") + 0.8, t)
            return 1.0 + 0.35 * km, 540, 1000 + 20 * km
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        ev = [(0.15, "boom", 0.6), (self.w("intro", "votado"), "pop", 0.5), (self.w("intro", "claves"), "riser", 0.4)]
        for k in self.CHAPTERS:
            ev += [(st(k) - 0.12, "whoosh", 0.6), (st(k) + 0.2, "click", 0.5)]
        ev += [(self.w("mayoria", "seis"), "pop", 0.5), (self.w("mayoria", "noes"), "pop", 0.5), (self.w("provincias", "madrid"), "pop", 0.5),
               (self.w("provincias", "soria"), "pop", 0.5), (self.w("dhondt", "cocientes"), "tick", 0.6), (self.w("dhondt", "menos"), "boom", 0.4),
               (st("umbral") + 1.4, "boom", 0.5), (self.w("bloques", "suman"), "pop", 0.5), (self.w("bloques", "llegan"), "pop", 0.5),
               (st("noche") + 3.0, "beep", 0.6), (self.w("despues", "veinticinco"), "pop", 0.5), (st("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        st = self.start
        return [(0, 0.8), (st("mayoria"), 0.6), (st("dhondt"), 0.65), (st("bloques"), 0.85), (st("noche"), 0.75), (st("despues"), 0.6),
                (st("cta"), 0.4), (self.duration, 0.3)]


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "plan":
        schedule(VIDEO, sys.argv[2])
    else:
        render(VIDEO, sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4:]] or None)
