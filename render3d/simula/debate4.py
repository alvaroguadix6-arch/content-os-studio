"""NIVEL OCULTO · Actualidad: el debate a cuatro del 26-11-2026 (informativo y neutral, sin sondeos).

Fuentes (crónicas del 26-11-2026): Público, Vozpópuli, OKDiario, El Español, The Objective, Telecinco, El Folio, Infobae:
jueves 26-11 a las 22:00, Academia de la Televisión, moderado por María Casado, ~2 h, cinco bloques (vivienda,
economía, servicios públicos, corrupción, migración); atriles: Abascal (Vox), Sánchez (PSOE), Feijóo (PP), Colau
(Frente Amplio); Colau pidió a Feijóo concretar el millón de viviendas; Sánchez calificó de «bulos» la intervención
de Abascal sobre vivienda; pensiones, ingreso mínimo vital y alquiler marcaron diferencias; Sánchez preguntó a
Feijóo y Abascal si reconocerán el resultado; preguntó a Feijóo si tenía miedo a Abascal; Colau preguntó a Abascal
«qué le debe» a Netanyahu; Feijóo cerró con el minuto de oro; cada medio da un ganador distinto.
Sin imágenes de personas reales: atriles con nombre y color de partido.
"""
from __future__ import annotations

import math

from caso_base import CARD, GOLD, INK, Caso, back_out, clamp, ease_out, main, mix, smooth  # noqa: F401
from motor import H, W, WHITE

MOOD, BPM = "suspense", 100
P = {  # orden de los atriles en el plató
    "abascal": ("SANTIAGO ABASCAL", "VOX", (100, 185, 70), 195),
    "sanchez": ("PEDRO SÁNCHEZ", "PSOE", (225, 45, 55), 415),
    "feijoo": ("ALBERTO NÚÑEZ FEIJÓO", "PP", (40, 120, 210), 635),
    "colau": ("ADA COLAU", "FRENTE AMPLIO", (200, 60, 150), 855),
}
ACC = (255, 196, 40)
PODIUM_Y = 1010


class VIDEO(Caso):
    NAME = "debate4"
    FIN = ("¿QUIÉN GANÓ", "EL DEBATE?")
    CARDS = {"vivienda": ("VIVIENDA", "1"), "economia": ("ECONOMÍA", "2"), "resultado": ("EL MOMENTO", "!"), "cierre": ("EL CIERRE", "!")}
    KEYWORDS = {"cuatro", "candidatos", "dos", "horas", "cinco", "bloques", "debate", "domingo", "sánchez", "psoe", "feijóo", "pp", "abascal",
                "vox", "colau", "frente", "amplio", "casado", "vivienda", "economía", "servicios", "corrupción", "migración", "millón",
                "viviendas", "bulos", "pensiones", "ingreso", "alquiler", "comentados", "resultado", "miedo", "netanyahu", "minuto", "oro",
                "ganador", "ganó", "comentarios"}

    def cast(self):
        self.host = None

    def hud_items(self, t):
        order = ["vivienda", "economia", "resultado", "cierre"]
        n = sum(1 for k in order if t >= self.start(k) - 0.1)
        return [("CANDIDATOS", "4", WHITE), ("DURACIÓN", "2 HORAS", (120, 220, 255)), ("MOMENTO", f"{n}/4", ACC)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("quienes") - 0.1, "quienes"), (st("bloques") - 0.1, "bloques"), (st("vivienda") - 0.1, "vivienda"),
                (st("economia") - 0.1, "economia"), (st("resultado") - 0.1, "resultado"), (st("cruces") - 0.1, "cruces"),
                (st("cierre") - 0.1, "cierre"), (st("cta") - 0.1, "fin")]

    # ───── plató ─────
    def studio(self, img, d, t):
        self.bg_flat(img, (10, 14, 36), (26, 20, 56))
        for i in range(9):  # focos
            x = 60 + i * 120
            self.poly(d, [(x - 20, 0), (x + 20, 0), (x + 140 * math.sin(t * 0.4 + i), 1300), (x - 140 * math.sin(t * 0.4 + i) - 60, 1300)],
                      mix((10, 14, 36), (60, 60, 120), 0.25), 0)
        self.box(d, -10, 1440, W + 10, H + 20, (30, 26, 60), 6)

    def podium(self, img, d, key, lit=0.0, t=0.0, k=1.0):
        name, party, col, x = P[key]
        if k <= 0.02:
            return
        y = PODIUM_Y + (1 - k) * 300
        if lit > 0:
            self.glow(img, x, y - 40, 170, col, 200 * lit)
        self.poly(d, [(x - 100, y), (x + 100, y), (x + 84, y + 430), (x - 84, y + 430)], mix((40, 40, 70), col, 0.35 + 0.4 * lit), 6)
        self.box(d, x - 106, y - 22, x + 106, y + 22, col, 5, 8)
        self.oell(d, x, y + 130, 62, 62, mix((230, 230, 240), col, 0.25), 5)  # micro / emblema
        self.ot(img, x, y + 130, {'FRENTE AMPLIO': 'FA'}.get(party, party), 38, INK, 0, safe=False)
        short = name.split()[-1] if key != "feijoo" else "FEIJÓO"
        self.ot(img, x, y - 78, short, 46, WHITE if lit else (200, 200, 220), 6, safe=False)

    def arrow(self, d, a, b, col, k=1.0, y=880):
        xa, xb = P[a][3], P[b][3]
        xm = xa + (xb - xa) * k
        lift = 120 * math.sin(math.pi * k)
        pts = [(xa + (xm - xa) * f, y - 140 * math.sin(math.pi * f * k) - 0 * lift) for f in [i / 20 for i in range(21)]]
        self.Ln(d, pts, INK, 18)
        self.Ln(d, pts, col, 10)
        if k > 0.95:
            ex, ey = pts[-1]
            s = 1 if xb > xa else -1
            self.poly(d, [(ex, ey + 4), (ex - s * 34, ey - 22), (ex - s * 30, ey + 28)], col, 4)

    def all_podiums(self, img, d, t, lit=()):
        for k in P:
            self.podium(img, d, k, 1.0 if k in lit else 0.0, t)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.studio(img, d, t)
        for i, k in enumerate(P):
            self.podium(img, d, k, 0.6 * (0.5 + 0.5 * math.sin(t * 4 + i)), t, back_out((lt - 0.05 - i * 0.1) / 0.4))
        self.stamp(img, 540, 480, "DEBATE A 4", 130, t, -0.3)
        for j, (frag, txt, col) in enumerate((("cuatro", "4 CANDIDATOS", ACC), ("horas", "2 HORAS", (120, 220, 255)), ("bloques", "5 BLOQUES", (255, 120, 160)))):
            kk = back_out((t - self.w("intro", frag)) / 0.3)
            self.label(img, d, 540, 620 + j * 100, txt, 58, kk, col, INK)

    def s_quienes(self, img, d, t, lt, u):
        self.studio(img, d, t)
        lit = [k for k, frag in (("sanchez", "sánchez"), ("feijoo", "feijóo"), ("abascal", "abascal"), ("colau", "colau")) if t > self.w("quienes", frag) - 0.1]
        self.all_podiums(img, d, t, lit)
        for k in lit[-1:]:
            name, party, col, x = P[k]
            self.label(img, d, 540, 500, f"{name} · {party}", 50, back_out((t - self.w("quienes", k[:4] if k != "feijoo" else "feijóo")) / 0.3), col, WHITE)
        self.label(img, d, 540, 640, "MODERA: MARÍA CASADO", 50, back_out((t - self.w("quienes", "casado") + 0.3) / 0.35))

    def s_bloques(self, img, d, t, lt, u):
        self.studio(img, d, t)
        self.all_podiums(img, d, t)
        topics = [("vivienda", "VIVIENDA", (255, 160, 80)), ("economía", "ECONOMÍA", (120, 220, 255)), ("servicios", "SERVICIOS PÚBLICOS", (140, 230, 160)),
                  ("corrupción", "CORRUPCIÓN", (255, 110, 110)), ("migración", "MIGRACIÓN", (200, 160, 255))]
        for i, (frag, txt, col) in enumerate(topics):
            k = back_out((t - self.w("bloques", frag)) / 0.3)
            self.label(img, d, 490, 450 + i * 92, txt, 54, k, col, INK)

    def s_vivienda(self, img, d, t, lt, u):
        self.studio(img, d, t)
        t1, t2 = self.w("vivienda", "colau"), self.w("vivienda", "sánchez")
        self.all_podiums(img, d, t, ["colau", "feijoo"] if t < t2 else ["sanchez", "abascal"])
        if t < t2:
            self.arrow(d, "colau", "feijoo", P["colau"][2], ease_out(clamp((t - t1) / 0.6)))
            self.label(img, d, 540, 500, "¿CÓMO, EL MILLÓN DE VIVIENDAS?", 46, back_out((t - self.w("vivienda", "millón")) / 0.35), P["colau"][2], WHITE)
        else:
            self.arrow(d, "sanchez", "abascal", P["sanchez"][2], ease_out(clamp((t - t2) / 0.6)))
            self.stamp(img, 540, 500, "«BULOS»", 90, t, self.w("vivienda", "bulos"))

    def s_economia(self, img, d, t, lt, u):
        self.studio(img, d, t)
        self.all_podiums(img, d, t)
        for i, (frag, txt, col) in enumerate((("pensiones", "PENSIONES", ACC), ("ingreso", "INGRESO MÍNIMO VITAL", (140, 230, 160)), ("alquiler", "ALQUILER", (255, 150, 90)))):
            k = back_out((t - self.w("economia", frag)) / 0.3)
            self.label(img, d, 490, 500 + i * 120, txt, 62, k, col, INK)

    def s_resultado(self, img, d, t, lt, u):
        self.studio(img, d, t)
        self.all_podiums(img, d, t, ["sanchez", "feijoo", "abascal"])
        tq = self.w("resultado", "preguntó")
        self.arrow(d, "sanchez", "feijoo", P["sanchez"][2], ease_out(clamp((t - tq) / 0.6)), 880)
        self.arrow(d, "sanchez", "abascal", P["sanchez"][2], ease_out(clamp((t - tq - 0.3) / 0.6)), 850)
        self.stamp(img, 540, 470, "EL MÁS COMENTADO", 70, t, self.w("resultado", "comentados"))
        self.label(img, d, 490, 590, "¿RECONOCERÁN EL RESULTADO?", 48, back_out((t - self.w("resultado", "resultado")) / 0.35), P["sanchez"][2], WHITE)

    def s_cruces(self, img, d, t, lt, u):
        self.studio(img, d, t)
        tc = self.w("cruces", "colau") - 0.1
        if t < tc:
            self.all_podiums(img, d, t, ["sanchez", "feijoo"])
            self.arrow(d, "sanchez", "feijoo", P["sanchez"][2], ease_out(clamp((lt - 0.2) / 0.6)))
            self.label(img, d, 490, 520, "¿MIEDO A ABASCAL?", 60, back_out((t - self.w("cruces", "miedo")) / 0.35), P["sanchez"][2], WHITE)
        else:
            self.all_podiums(img, d, t, ["colau", "abascal"])
            self.arrow(d, "colau", "abascal", P["colau"][2], ease_out(clamp((t - tc) / 0.8)))
            self.label(img, d, 490, 520, "¿QUÉ LE DEBE A NETANYAHU?", 50, back_out((t - self.w("cruces", "netanyahu")) / 0.35), P["colau"][2], WHITE)

    def s_cierre(self, img, d, t, lt, u):
        self.studio(img, d, t)
        tg = self.w("cierre", "medio") - 0.2
        if t < tg:
            self.all_podiums(img, d, t, ["feijoo"])
            k = clamp(lt / max(0.1, tg - self.start("cierre")))
            secs = int(60 * (1 - k))
            self.label(img, d, 490, 500, f"MINUTO DE ORO  0:{secs:02d}", 64, back_out((lt - 1.4) / 0.35), ACC, INK)
        else:
            self.all_podiums(img, d, t, list(P))
            for i, k in enumerate(P):
                self.ot(img, P[k][3], 820 + 15 * math.sin(t * 5 + i), "?", 110, ACC, 6, safe=False)
            self.stamp(img, 490, 500, "CADA MEDIO, UN GANADOR", 60, t, tg + 0.1)

    def s_fin(self, img, d, t, lt, u):
        self.end_card(img, d, t, lt, None)

    def sfx_events(self):
        st = self.start
        ev = [(0.0, "boom", 0.7), (0.2, "riser", 0.4)] + [(self.w("intro", f), "pop", 0.5) for f in ("cuatro", "horas", "bloques")]
        ev += [(self.w("quienes", f), "pop", 0.45) for f in ("sánchez", "feijóo", "abascal", "colau")] + [(self.w("quienes", "casado"), "click", 0.5)]
        ev += [(self.w("bloques", f), "tick", 0.7) for f in ("vivienda", "economía", "servicios", "corrupción", "migración")]
        ev += [(st("vivienda") - 0.1, "whoosh", 0.6), (self.w("vivienda", "colau"), "whoosh", 0.4), (self.w("vivienda", "bulos"), "boom", 0.6),
               (st("economia") - 0.1, "whoosh", 0.6)] + [(self.w("economia", f), "pop", 0.45) for f in ("pensiones", "ingreso", "alquiler")]
        ev += [(st("resultado") - 0.1, "boom", 0.6), (self.w("resultado", "comentados"), "boom", 0.6), (self.w("cruces", "miedo"), "pop", 0.5),
               (self.w("cruces", "netanyahu"), "pop", 0.5), (st("cierre") - 0.1, "whoosh", 0.6), (self.w("cierre", "medio"), "shimmer", 0.5),
               (st("cta"), "pop", 0.6)]
        return ev

    def music_plan(self):
        st = self.start
        return [(0, 0.8), (st("quienes"), 0.6), (st("vivienda"), 0.8), (st("resultado"), 0.95), (st("cierre"), 0.7), (st("cta"), 0.45), (self.duration, 0.3)]


if __name__ == "__main__":
    main(VIDEO)
