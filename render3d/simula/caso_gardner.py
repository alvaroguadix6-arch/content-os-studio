"""NIVEL OCULTO · Casos reales en dibujos: el robo del museo Isabella Stewart Gardner (Boston, 1990).

Fuentes: FBI (robo del 18-3-1990, 13 obras, más de 500 M$), Isabella Stewart Gardner Museum (recompensa de 10 M$ por
la recuperación de las 13 obras; marcos vacíos expuestos), PBS, History.com: dos hombres vestidos de policía, el
vigilante les abrió, los guardias acabaron atados en el sótano; entre las obras, «El concierto» de Vermeer y «La
tormenta en el mar de Galilea», la única marina de Rembrandt; sin resolver, nadie condenado.
"""
from __future__ import annotations

import math

from caso_base import CARD, GOLD, GREEN, INK, Caso, Look, Toon, back_out, clamp, ease_out, main, mix, smooth  # noqa: F401
from motor import WHITE

MOOD, BPM = "suspense", 98
WALL = (60, 90, 80)


class VIDEO(Caso):
    NAME = "caso_gardner"
    FIN = ("¿DÓNDE ESTÁN", "LOS CUADROS?")
    CARDS = {"dentro": ("EL ENGAÑO", "!"), "obras": ("EL BOTÍN", "$"), "pistas": ("SIN RESOLVER", "?")}
    KEYWORDS = {"cuadros", "diez", "millones", "dólares", "desaparecidos", "noventa", "boston", "madrugada", "policía", "museo", "gardner",
                "aviso", "vigilante", "atados", "sótano", "hora", "trece", "vermeer", "rembrandt", "marina", "quinientos", "mayor", "robo",
                "arte", "marcos", "vacíos", "pared", "treinta", "ninguna", "nadie", "condenado", "comentarios"}

    def cast(self):
        fake = dict(shirt=(40, 60, 110), hat="police", hat_col=(25, 40, 80), badge=True, stubble=False)
        self.t1 = Toon(Look(**fake, extra={"mustache": True}, hair=(50, 35, 25)), seed=3)
        self.t2 = Toon(Look(**fake, extra={"mustache": True, "mustache_col": (90, 60, 40)}, skin=(230, 185, 150)), seed=6)
        self.guard = Toon(Look(shirt=(120, 120, 130), badge=True, hair=(160, 100, 50), stubble=False), seed=9)
        self.guard2 = Toon(Look(shirt=(120, 120, 130), badge=True, hair=(30, 25, 25), skin=(190, 135, 100), stubble=False), seed=12)
        self.visitor = Toon(Look(shirt=(200, 90, 120), hair=(90, 60, 40), stubble=False), seed=14)
        self.host = Toon(Look(shirt=(200, 160, 110), extra={"coat": (190, 150, 100)}, hair=(50, 40, 30)), seed=15)
        self.shakes = [(self.w("dentro", "atados"), 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("policia") - 0.1, "puerta"), (st("dentro") - 0.1, "dentro"), (st("obras") - 0.1, "obras"),
                (st("valor") - 0.1, "valor"), (st("marcos") - 0.1, "marcos"), (st("pistas") - 0.1, "pistas"), (st("cta") - 0.1, "fin")]

    def hud_items(self, t):
        n = 0 if t < self.start("obras") else int(13 * clamp((t - self.start("obras")) / max(0.1, self.end("obras") - self.start("obras"))))
        val = "?" if t < self.start("valor") else "+500 M$"
        return [("OBRAS ROBADAS", f"{n}/13", WHITE), ("VALOR", val, GOLD), ("RECOMPENSA", "10 M$", GREEN)]

    def frames_wall(self, img, d, t, gone=0, spot=False):
        fr = [(220, 760, 240, 300, "concert"), (540, 740, 260, 340, "storm"), (860, 760, 220, 280, "generic")]
        self.bg_museum(img, d, t, WALL, [(x, y, w, h, k, i < gone) for i, (x, y, w, h, k) in enumerate(fr)], (130, 100, 70))
        if spot:
            self.glow(img, 540, 760, 500, (255, 240, 200), 70)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.frames_wall(img, d, t, gone=3, spot=True)
        self.money_rain(d, t, 0.6)
        self.stamp(img, 540, 470, "RECOMPENSA: 10.000.000 $", 70, t, -0.3, (30, 120, 60), rot=-4)
        self.stamp(img, 540, 1120, "DESAPARECIDOS DESDE 1990", 60, t, self.w("intro", "desaparecidos"))

    def s_puerta(self, img, d, t, lt, u):
        self.bg_city(img, d, t, night=1.0)
        self.box(d, 380, 900, 700, 1300, (90, 60, 40), 7, 10)  # puerta del museo
        self.label(img, d, 540, 840, "MUSEO", 50, 1.0)
        self.label(img, d, 540, 470, "BOSTON · DE MADRUGADA", 64, back_out((lt - 0.1) / 0.4))
        k = ease_out(clamp((lt - 0.4) / 2.2))
        for i, tn in enumerate((self.t1, self.t2)):
            tn.draw(img, -150 + 560 * k + i * 190, 1760, t, expr="sly", pose="idle", walk=t * 9 if k < 1 else 0, scale=0.85, look_at=(540, 1000))
        if t > self.w("policia", "policía"):
            self.stamp(img, 540, 650, "¿POLICÍAS?", 80, t, self.w("policia", "policía"), (30, 30, 40))

    def s_dentro(self, img, d, t, lt, u):
        ta = self.w("dentro", "atados") - 0.3
        if t < ta:
            self.bg_flat(img, (80, 70, 60), (50, 44, 40))
            self.box(d, 520, 1350, 1000, 1500, (110, 80, 60), 6, 8)  # mostrador
            self.guard.draw(img, 760, 1760, t, expr="neutral" if t < self.w("dentro", "abre") else "happy", pose="wave" if t > self.w("dentro", "abre") else "idle", scale=0.85)
            self.t1.draw(img, 250, 1760, t, expr="sly", pose="point", scale=0.85, look_at=(760, 1100))
            self.label(img, d, 540, 470, "«VENIMOS POR UN AVISO»", 62, back_out((lt - 0.2) / 0.4))
        else:
            self.bg_flat(img, (70, 70, 80), (40, 40, 48))
            self.label(img, d, 540, 470, "EL SÓTANO", 70, back_out((t - ta) / 0.4))
            for i, g in enumerate((self.guard, self.guard2)):
                x = 320 + i * 440
                g.draw(img, x, 1760, t, expr="scared", pose="idle", scale=0.85, bounce=False)
                for j in range(3):  # cinta adhesiva
                    y = 1350 + j * 60
                    self.box(d, x - 130, y, x + 130, y + 30, (170, 170, 175), 4, 6)
            self.stamp(img, 540, 1110, "ATADOS", 90, t, self.w("dentro", "atados"))

    def s_obras(self, img, d, t, lt, u):
        dur = self.end("obras") - self.start("obras")
        gone = int(3 * clamp(lt / max(0.1, dur * 0.7)))
        self.frames_wall(img, d, t, gone)
        self.t1.draw(img, 260, 1760, t, expr="grin", pose="hold", scale=0.8, walk=t * 7)
        self.painting(img, d, 260, 1500, 140, 160, "concert")
        self.t2.draw(img, 820, 1760, t, expr="sly", pose="hold", scale=0.8)
        self.painting(img, d, 820, 1500, 160, 120, "storm")
        self.pop(img, 260, 1560, "VERMEER", 54, t, self.w("obras", "vermeer"), GOLD)
        self.pop(img, 820, 1560, "REMBRANDT", 54, t, self.w("obras", "rembrandt"), GOLD)

    def s_valor(self, img, d, t, lt, u):
        self.bg_flat(img, (30, 70, 50), (14, 34, 24))
        self.money_rain(d, t, smooth(0, 1, lt))
        k = ease_out(clamp((lt - 0.2) / 1.5))
        self.ot(img, 540, 860, f"{500 * k:,.0f}".replace(",", ".") + " M$", 140, GOLD)
        self.stamp(img, 540, 1100, "EL MAYOR ROBO DE ARTE", 70, t, self.w("valor", "mayor"))

    def s_marcos(self, img, d, t, lt, u):
        self.frames_wall(img, d, t, gone=3, spot=True)
        self.visitor.draw(img, 540, 1760, t, expr="sad", pose="idle", scale=0.85, look_at=(540, 740))
        self.pop(img, 540, 470, "MARCOS VACÍOS", 90, t, self.w("marcos", "marcos"), WHITE)

    def s_pistas(self, img, d, t, lt, u):
        self.bg_flat(img, (120, 85, 60), (90, 62, 44))
        self.box(d, 90, 500, 990, 1250, (190, 150, 100), 8, 10)  # tablero de corcho
        pts = [(230, 640), (800, 620), (520, 900), (250, 1120), (830, 1100)]
        for a, b in ((0, 2), (1, 2), (2, 3), (2, 4), (0, 1)):
            self.Ln(d, [pts[a], pts[b]], CARD, 5)
        for i, (x, y) in enumerate(pts):
            self.box(d, x - 70, y - 80, x + 70, y + 80, (245, 240, 225), 5, 4)
            self.ot(img, x, y, "?", 90, GOLD if i == 2 else (120, 110, 100), 4)
            self.E(d, x, y - 80, 12, CARD)
        self.host.draw(img, 540, 1760, t, expr="sad", pose="shrug", scale=0.8)
        self.stamp(img, 540, 450, "NADIE CONDENADO", 80, t, self.w("pistas", "nadie"))

    def camera(self, t, name, lt, u):
        if name in ("intro", "marcos"):
            return 1.0 + 0.07 * smooth(0, 5, lt), 540, 1000
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.0, "boom", 0.7), (0.2, "shimmer", 0.5), (self.w("intro", "desaparecidos"), "boom", 0.6), (st("policia") + 0.3, "wind", 0.4),
                (self.w("policia", "policía"), "pop", 0.6), (st("dentro") - 0.1, "boom", 0.6), (self.w("dentro", "abre"), "click", 0.6),
                (self.w("dentro", "atados"), "boom", 0.8), (st("obras") - 0.1, "boom", 0.6), (self.w("obras", "vermeer"), "pop", 0.5),
                (self.w("obras", "rembrandt"), "pop", 0.5), (st("valor") + 0.2, "shimmer", 0.6), (self.w("valor", "mayor"), "boom", 0.7),
                (st("marcos") + 0.3, "wind", 0.3), (st("pistas") - 0.1, "boom", 0.6), (self.w("pistas", "nadie"), "boom", 0.6), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.35), (self.w("intro", "desaparecidos"), 0.8), (st("policia"), 0.6), (st("dentro"), 0.85), (st("obras"), 0.9),
                (st("valor"), 0.95), (st("marcos"), 0.5), (st("pistas"), 0.75), (st("cta"), 0.45), (self.duration, 0.3)]


if __name__ == "__main__":
    main(VIDEO)
