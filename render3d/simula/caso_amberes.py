"""NIVEL OCULTO · Casos reales en dibujos: el robo de diamantes de Amberes (2003).

Fuentes: Wikipedia, National Geographic, Guinness World Records (más de 100 M$, el mayor robo de diamantes), Wired
(cámara del Antwerp Diamond Centre con sensores de calor, movimiento, luz… y puerta de unas 3 toneladas; Leonardo
Notarbartolo alquiló una oficina en el edificio): febrero de 2003, vaciaron más de cien cajas de seguridad; al huir
tiraron una bolsa de basura junto a una carretera (E19) con papeles y un bocadillo de salami a medio comer, que llevó a
la policía hasta la banda; Notarbartolo fue condenado a 10 años; la mayoría de los diamantes nunca apareció.
"""
from __future__ import annotations

import math

from caso_base import CARD, GOLD, GREEN, INK, Caso, Look, Toon, back_out, clamp, ease_out, main, mix, smooth  # noqa: F401
from motor import H, W, WHITE

MOOD, BPM = "suspense", 102


class VIDEO(Caso):
    NAME = "caso_amberes"
    FIN = ("¿UN BOCADILLO?", "¡EN SERIO!")
    CARDS = {"golpe": ("EL GOLPE", "!"), "error": ("EL ERROR", "?"), "diamantes": ("EL MISTERIO", "?")}
    KEYWORDS = {"cien", "millones", "diamantes", "seguras", "mundo", "bocadillo", "amberes", "bélgica", "dos", "mil", "tres", "calor",
                "movimiento", "luz", "toneladas", "notarbartolo", "meses", "oficina", "edificio", "sensores", "cajas", "fuertes", "oro", "joyas",
                "basura", "carretera", "salami", "papeles", "policía", "diez", "años", "nunca", "apareció", "delatara", "comentarios"}

    def cast(self):
        self.boss = Toon(Look(shirt=(60, 60, 70), extra={"tie": (160, 40, 50)}, hair=(120, 110, 100), stubble=True), seed=4)
        self.crew = [Toon(Look(shirt=(30, 30, 36), hair=h, skin=sk, stubble=False), seed=10 + i) for i, (h, sk) in
                     enumerate([((30, 25, 20), (230, 185, 150)), ((150, 100, 50), (250, 210, 180))])]
        self.local = Toon(Look(shirt=(90, 140, 90), hair=(90, 70, 50), stubble=True), seed=20)
        self.cop = Toon(Look(shirt=(40, 60, 100), hat="police", hat_col=(30, 40, 70), badge=True, stubble=False), seed=22)
        self.host = self.boss
        self.shakes = [(self.w("error", "salami"), 0.5), (self.w("pista", "detenido"), 0.7)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("centro") - 0.1, "camara"), (st("plan") - 0.1, "plan"), (st("golpe") - 0.1, "golpe"),
                (st("botin") - 0.1, "botin"), (st("error") - 0.1, "error"), (st("pista") - 0.1, "pista"), (st("diamantes") - 0.1, "misterio"),
                (st("cta") - 0.1, "fin")]

    def hud_items(self, t):
        g0, g1 = self.start("golpe"), self.end("golpe")
        n = 0 if t < g0 else int(123 * clamp((t - g0) / max(0.1, g1 - g0)))
        bot = "0" if t < self.start("botin") else "+100 M$"
        st = (t > self.start("error")) + (t > self.w("error", "salami")) + (t > self.w("pista", "detenido"))
        return [("CAJAS ABIERTAS", f"{n}", WHITE), ("BOTÍN", bot, GOLD), ("PISTAS", st, (255, 120, 120))]

    def diamonds_pile(self, d, x, y, t, n=12, s=0.8):
        for i in range(n):
            f = s / 0.8
            self.diamond(d, x + (((i * 47) % 260) - 130) * f, y - ((i // 4) * 40 + ((i * 13) % 20)) * f, s, t + i)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.bg_flat(img, (30, 40, 70), (12, 16, 30))
        self.diamonds_pile(d, 540, 1200, t, 16, 1.7)
        self.glow(img, 540, 1050, 300, (150, 220, 255), 100)
        self.stamp(img, 540, 470, "+100 MILLONES EN DIAMANTES", 62, t, -0.3)
        tb = self.w("intro", "bocadillo") - 0.2
        if t > tb:
            self.sandwich(d, 540, 1600, 1.6 * back_out((t - tb) / 0.4))
            self.stamp(img, 540, 760, "¿Y LOS PILLÓ UN BOCADILLO?", 56, t, tb + 0.1, (30, 30, 40), rot=5)

    def s_camara(self, img, d, t, lt, u):
        self.bg_vault(img, d, t, 0)
        self.label(img, d, 540, 470, "AMBERES · 2003", 76, back_out((lt - 0.1) / 0.4))
        for i, (frag, lab, col) in enumerate((("calor", "CALOR", (255, 120, 80)), ("movimiento", "MOVIMIENTO", (120, 220, 255)), ("luz", "LUZ", GOLD))):
            k = back_out((t - self.w("centro", frag)) / 0.3)
            if k > 0.02:
                self.label(img, d, 200 + i * 340, 640, "SENSOR: " + lab if i < 1 else lab, 44, k, col, INK)
        k = back_out((t - self.w("centro", "toneladas") + 0.4) / 0.4)
        if k > 0.02:  # la puerta de la cámara
            self.oell(d, 540, 1100, 330 * k, 330 * k, (150, 155, 170), 10)
            self.oell(d, 540, 1100, 240 * k, 240 * k, (120, 125, 140), 6)
            for a in range(6):
                ang = a * math.pi / 3 + t * 0.3
                self.Ln(d, [(540, 1100), (540 + math.cos(ang) * 200 * k, 1100 + math.sin(ang) * 200 * k)], (90, 90, 100), 14)
            self.label(img, d, 540, 1600, "PUERTA DE 3 TONELADAS", 56, k, CARD, WHITE)

    def s_plan(self, img, d, t, lt, u):
        self.bg_city(img, d, t, cols=[(200, 200, 210), (180, 180, 190), (210, 205, 200)])
        self.box(d, 300, 700, 780, 1250, (120, 130, 150), 7)  # edificio del centro del diamante
        self.label(img, d, 540, 760, "CENTRO DEL DIAMANTE", 44, 1.0, (60, 70, 100), WHITE)
        ko = back_out((t - self.w("plan", "oficina")) / 0.4)
        if ko > 0.02:
            self.box(d, 440 - 80 * ko, 950 - 60 * ko, 440 + 80 * ko, 950 + 60 * ko, (255, 230, 140), 5, 6)
            self.ot(img, 440, 950, "SU OFICINA", 30 * ko, INK, 0)
        self.boss.draw(img, 300, 1760, t, expr="sly", pose="point", scale=0.9, look_at=(440, 950))
        for i, c in enumerate(self.crew):
            c.draw(img, 700 + i * 200, 1760, t, expr="sly", pose="idle", scale=0.75)
        self.pop(img, 540, 470, "LEONARDO NOTARBARTOLO", 60, t, self.w("plan", "notarbartolo"), GOLD)

    def s_golpe(self, img, d, t, lt, u):
        dur = self.end("golpe") - self.start("golpe")
        n = int(63 * clamp((lt - 0.3) / max(0.1, dur * 0.85)))
        self.bg_vault(img, d, t, n)
        for i, c in enumerate([self.boss] + self.crew):
            c.draw(img, 230 + i * 310, 1780, t, expr="grin", pose="hold" if i % 2 else "cheer", scale=0.7, walk=t * 4)
        self.diamonds_pile(d, 540, 1450, t, min(12, n // 4), 0.7)

    def s_botin(self, img, d, t, lt, u):
        self.bg_flat(img, (30, 40, 70), (12, 16, 30))
        self.diamonds_pile(d, 540, 1300, t, 20, 1.2)
        for i in range(5):  # lingotes
            self.poly(d, [(250 + i * 120, 1500), (340 + i * 120, 1500), (320 + i * 120, 1450), (270 + i * 120, 1450)], GOLD, 5)
        k = ease_out(clamp((lt - 0.2) / 1.6))
        self.ot(img, 540, 650, f"+{100 * k:.0f} MILLONES $", 110, GOLD)
        self.pop(img, 540, 800, "VALOR ESTIMADO", 50, t, self.start("botin") + 0.4, WHITE)

    def s_error(self, img, d, t, lt, u):
        self.bg_road(img, d, t, night=0.5)
        tb = self.w("error", "basura")
        k = ease_out(clamp((t - tb + 0.3) / 1.0))
        bx, by = 540 - 300 * (1 - k), 1380 - 400 * math.sin(math.pi * k) * (k < 1)
        self.oell(d, bx, by, 120, 140, (40, 40, 44), 6)  # bolsa de basura
        self.poly(d, [(bx - 30, by - 140), (bx + 30, by - 140), (bx, by - 190)], (40, 40, 44), 5)
        ks = back_out((t - self.w("error", "salami")) / 0.4)
        if ks > 0.02:
            self.sandwich(d, 780, 1300, 1.1 * ks)
            for j in range(3):  # papeles
                self.poly(d, [(250 + j * 50, 1230 + j * 20), (340 + j * 50, 1220 + j * 20), (350 + j * 50, 1300 + j * 20), (260 + j * 50, 1310 + j * 20)], (245, 240, 225), 4)
            self.stamp(img, 540, 650, "UN BOCADILLO A MEDIO COMER", 56, t, self.w("error", "salami"))

    def s_pista(self, img, d, t, lt, u):
        self.bg_police(img, d, t)
        self.sandwich(d, 540, 900, 0.9)
        self.magnifier(d, 470 + 30 * math.sin(t * 2), 860, 0.9)
        td = self.w("pista", "detenido")
        caught = t > td - 0.2
        self.boss.draw(img, 330, 1760, t, expr="shock" if caught else "sly", pose="hands_up" if caught else "idle", scale=0.85)
        self.cop.draw(img, 780, 1760, t, expr="angry", pose="point", scale=0.85, look_at=(330, 1100), flip=True)
        if caught:
            self.handcuffs(d, 330, 1380, back_out((t - td) / 0.3))
        self.stamp(img, 540, 470, "CONDENADO: 10 AÑOS", 72, t, self.w("pista", "diez"))

    def s_misterio(self, img, d, t, lt, u):
        self.bg_vault(img, d, t, 63)
        for i in range(6):
            self.ot(img, 170 + i * 150, 900 + 60 * math.sin(t * 2 + i), "?", 110, GOLD, 6)
        self.stamp(img, 540, 1150, "NUNCA APARECIERON", 80, t, self.w("diamantes", "nunca"))

    def camera(self, t, name, lt, u):
        if name in ("intro", "botin"):
            return 1.0 + 0.08 * smooth(0, 5, lt), 540, 1050
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.0, "boom", 0.7), (0.2, "shimmer", 0.6), (self.w("intro", "bocadillo"), "pop", 0.7), (st("centro") + 0.2, "click", 0.5),
                (self.w("centro", "calor"), "beep", 0.4), (self.w("centro", "movimiento"), "beep", 0.4), (self.w("centro", "luz"), "beep", 0.4),
                (self.w("centro", "toneladas"), "boom", 0.6), (self.w("plan", "notarbartolo"), "pop", 0.5), (self.w("plan", "oficina"), "click", 0.5),
                (st("golpe") - 0.1, "boom", 0.6)] + [(st("golpe") + 0.3 + i * 0.25, "click", 0.35) for i in range(10)] + [
                (st("botin") + 0.2, "shimmer", 0.7), (st("error") - 0.1, "boom", 0.6), (self.w("error", "basura"), "whoosh", 0.5),
                (self.w("error", "salami"), "pop", 0.7), (st("pista") + 0.2, "horn", 0.4), (self.w("pista", "detenido"), "boom", 0.8),
                (st("diamantes") - 0.1, "boom", 0.6), (self.w("diamantes", "nunca"), "boom", 0.6), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.35), (self.w("intro", "bocadillo"), 0.8), (st("centro"), 0.6), (st("golpe"), 0.95), (st("botin"), 0.9),
                (st("error"), 0.75), (st("pista"), 0.9), (st("diamantes"), 0.6), (st("cta"), 0.45), (self.duration, 0.3)]


if __name__ == "__main__":
    main(VIDEO)
