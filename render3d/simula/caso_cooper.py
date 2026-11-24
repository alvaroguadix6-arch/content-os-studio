"""NIVEL OCULTO · Casos reales en dibujos: D. B. Cooper (1971).

Fuentes: FBI, Britannica, History.com: el 24-11-1971 un hombre que se hizo llamar Dan Cooper compró un billete de
Portland a Seattle (vuelo 305 de Northwest Orient), pasó una nota a una azafata diciendo que llevaba una bomba, pidió
200.000 $ y cuatro paracaídas; en Seattle recibió el dinero y liberó a los pasajeros; el avión despegó rumbo a México
y en plena noche saltó por la escalera trasera; nunca se le identificó; en 1980 un niño encontró parte de los billetes
en la orilla del río Columbia; en 2016 el FBI dejó de investigar activamente el caso.
"""
from __future__ import annotations

import math

from caso_base import CARD, GOLD, GREEN, INK, Caso, Look, Toon, back_out, clamp, ease_out, main, mix, smooth  # noqa: F401
from motor import H, W, WHITE

MOOD, BPM = "suspense", 96


class VIDEO(Caso):
    NAME = "caso_cooper"
    FIN = ("¿SOBREVIVIÓ", "AL SALTO?")
    CARDS = {"nota": ("EL SECUESTRO", "!"), "salto": ("EL SALTO", "↓"), "fbi": ("SIN RESOLVER", "?")}
    KEYWORDS = {"avión", "doscientos", "mil", "dólares", "paracaídas", "noche", "nunca", "setenta", "cooper", "portland", "seattle", "nota",
                "azafata", "bomba", "cuatro", "dinero", "pasajeros", "méxico", "escalera", "salta", "encontraron", "niño", "billetes", "río",
                "fbi", "dieciséis", "resolver", "sobrevivió", "comentarios"}

    def cast(self):
        self.cooper = Toon(Look(shirt=(40, 40, 50), extra={"tie": (20, 20, 24), "sunglasses": True}, hair=(30, 25, 25), stubble=False), seed=4)
        self.attendant = Toon(Look(shirt=(60, 110, 170), hat="police", hat_col=(60, 110, 170), hair=(200, 160, 90), stubble=False), seed=7)
        self.kid = Toon(Look(shirt=(230, 120, 60), hair=(150, 90, 40), stubble=False), seed=9)
        self.pax = [Toon(Look(shirt=c, stubble=False, hair=h), seed=20 + i) for i, (c, h) in
                    enumerate([((200, 80, 80), (40, 30, 20)), ((80, 150, 90), (160, 110, 60)), ((90, 110, 200), (20, 20, 20)), ((220, 170, 60), (90, 60, 40))])]
        self.agent = Toon(Look(shirt=(50, 50, 60), extra={"tie": (40, 60, 120)}, hair=(50, 40, 30), stubble=False), seed=31)
        self.host = self.cooper
        self.t_jump = self.w("salto", "salta")
        self.shakes = [(self.w("nota", "bomba"), 0.6), (self.t_jump, 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("billete") - 0.1, "billete"), (st("nota") - 0.1, "cabina"), (st("pide") - 0.1, "pide"),
                (st("seattle") - 0.1, "seattle"), (st("salto") - 0.1, "salto"), (st("dinero") - 0.1, "rio"), (st("fbi") - 0.1, "fbi"),
                (st("cta") - 0.1, "fin")]

    def hud_items(self, t):
        res = 0 if t < self.start("seattle") else 200_000
        par = 0 if t < self.start("seattle") else (4 if t < self.t_jump else 3)
        return [("RESCATE", f"{res:,} $".replace(",", "."), GOLD), ("PARACAÍDAS", f"{par}", WHITE), ("PARADERO", "?" if t > self.t_jump else "A BORDO", (255, 120, 120))]

    def falling(self, img, d, x, y, t, s=1.0, chute=True):
        if chute:
            self.parachute(d, x, y - 220 * s, s, (230, 90, 70))
        self.cooper.draw(img, x, y + 120 * s, t, expr="sly", pose="cheer", scale=0.42 * s, bounce=False)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        self.bg_night_sky(img, d, t)
        self.plane(img, d, 1250 - 600 * ease_out(clamp(lt / 3)), 600, 0.9, t, night=True)
        if lt > 0.8:
            k = ease_out(clamp((lt - 0.8) / 3))
            self.falling(img, d, 540 + 40 * math.sin(t), 820 + 500 * k, t, 1.0)
        self.stamp(img, 540, 470, "200.000 $ Y UN SALTO", 70, t, -0.3)
        self.stamp(img, 540, 1550, "NUNCA MÁS SE SUPO DE ÉL", 64, t, self.w("intro", "nunca"), (30, 30, 40), rot=4)

    def s_billete(self, img, d, t, lt, u):
        self.bg_flat(img, (180, 200, 220), (140, 160, 180))
        self.box(d, 520, 1250, 1060, 1420, (90, 110, 150), 6, 10)  # mostrador
        self.label(img, d, 540, 470, "24-11-1971", 76, back_out((lt - 0.1) / 0.4))
        self.label(img, d, 540, 600, "PORTLAND → SEATTLE", 56, back_out((t - self.w("billete", "portland")) / 0.4), (90, 110, 150), WHITE)
        k = ease_out(clamp((lt - 0.3) / 1.6))
        self.cooper.draw(img, -100 + 450 * k, 1760, t, expr="neutral", pose="idle", walk=t * 9 if k < 1 else 0, scale=0.9)
        self.briefcase(d, -100 + 450 * k + 120, 1640, 0.7)
        kt = back_out((t - self.w("billete", "cooper")) / 0.4)
        if kt > 0.02:
            self.box(d, 640 - 200 * kt, 920 - 90 * kt, 640 + 200 * kt, 920 + 90 * kt, (250, 245, 230), 6, 10)
            self.ot(img, 640, 890, "BILLETE", 40 * kt, (120, 110, 100), 0)
            self.ot(img, 640, 950, "«DAN COOPER»", 54 * kt, INK, 0)

    def cabin(self, img, d):
        self.bg_flat(img, (200, 200, 210), (170, 170, 180))
        for i in range(3):  # ventanillas
            self.box(d, 100 + i * 330, 560, 220 + i * 330, 720, (20, 24, 60), 6, 50)
        self.floor(d, 1350, (90, 100, 130))
        for i in range(3):  # asientos
            x = 140 + i * 330
            self.box(d, x, 1100, x + 200, 1450, (60, 90, 150), 6, 20)

    def s_cabina(self, img, d, t, lt, u):
        self.cabin(img, d)
        tb = self.w("nota", "bomba")
        self.cooper.draw(img, 300, 1760, t, expr="sly", pose="point", scale=0.85, look_at=(800, 1100))
        self.attendant.draw(img, 800, 1760, t, expr="shock" if t > tb - 0.2 else "happy", pose="hands_up" if t > tb else "idle", scale=0.85,
                            look_at=(300, 1100))
        kn = back_out((t - self.w("nota", "nota")) / 0.35)
        if kn > 0.02:
            self.box(d, 540 - 150 * kn, 860 - 110 * kn, 540 + 150 * kn, 860 + 110 * kn, (250, 245, 220), 6, 6)
            self.ot(img, 540, 820, "NOTA", 50 * kn, INK, 0)
            for j in range(3):
                self.Ln(d, [(450, 870 + j * 30), (630 - j * 20, 870 + j * 30)], (120, 110, 100), 5)
        self.stamp(img, 540, 470, "«LLEVO UNA BOMBA»", 70, t, tb)

    def s_pide(self, img, d, t, lt, u):
        self.bg_flat(img, (40, 30, 50), (20, 16, 26))
        self.money_rain(d, t, 0.4)
        k = back_out((t - self.w("pide", "doscientos")) / 0.4)
        self.ot(img, 540, 760, "200.000 $", 150 * max(0.05, k), GOLD)
        kp = smooth(self.w("pide", "cuatro") - 0.2, self.w("pide", "cuatro") + 0.8, t)
        for i in range(4):
            if kp * 4 > i:
                self.parachute(d, 180 + i * 240, 1250, 0.6, [(230, 90, 70), (240, 200, 60), (90, 160, 230), (120, 200, 110)][i])
        self.pop(img, 540, 1550, "+ 4 PARACAÍDAS", 80, t, self.w("pide", "paracaídas"), WHITE)

    def s_seattle(self, img, d, t, lt, u):
        self.bg_flat(img, (90, 100, 140), (150, 150, 170))
        self.box(d, -10, 1250, W + 10, H + 20, (70, 70, 80), 6)
        for i in range(6):
            x = (i * 220) % (W + 220) - 110
            d.rectangle([x * 2, 1600 * 2, (x + 120) * 2, 1618 * 2], fill=(240, 240, 240))
        self.plane(img, d, 760, 1000, 1.2, t)
        self.label(img, d, 540, 470, "SEATTLE", 80, back_out((lt - 0.1) / 0.4))
        self.briefcase(d, 260, 1500, 1.1, smooth(0.5, 1.2, lt))
        k = ease_out(clamp((t - self.w("seattle", "pasajeros") + 0.4) / 1.6))
        for i, p in enumerate(self.pax):
            p.draw(img, 560 + i * 120 + 300 * k, 1780, t, expr="happy", pose="cheer" if k > 0.6 else "idle", walk=t * 9 if 0 < k < 1 else 0, scale=0.55)

    def s_salto(self, img, d, t, lt, u):
        self.bg_night_sky(img, d, t)
        self.label(img, d, 540, 470, "RUMBO A MÉXICO", 70, back_out((t - self.w("salto", "méxico")) / 0.4), (90, 110, 150), WHITE)
        px = 540 + 260 * math.sin(lt * 0.4)
        self.plane(img, d, px, 760, 1.1, t, night=True)
        ks = smooth(self.w("salto", "escalera") - 0.2, self.w("salto", "escalera") + 0.4, t)
        if ks > 0:  # escalera trasera
            self.poly(d, [(px - 230, 780), (px - 180, 790), (px - 300, 780 + 160 * ks), (px - 340, 770 + 150 * ks)], (150, 150, 160), 5)
        if t > self.t_jump:
            k = ease_out(clamp((t - self.t_jump) / 2.0))
            self.falling(img, d, px - 300 - 80 * k, 960 + 600 * k, t, 0.8, chute=k > 0.4)
            self.stamp(img, 540, 1600, "¡SALTA!", 100, t, self.t_jump)

    def s_rio(self, img, d, t, lt, u):
        self.bg_forest(img, d, t, night=0.0)
        self.label(img, d, 540, 470, "1980", 90, back_out((t - self.w("dinero", "ochenta") + 0.2) / 0.4))
        tk = self.w("dinero", "niño") - 0.3
        if t > tk:
            k = back_out((t - tk) / 0.4)
            self.kid.draw(img, 360, 1490, t, expr="shock" if t > self.w("dinero", "billetes") else "happy", pose="hands_up" if t > self.w("dinero", "billetes") else "idle",
                          scale=0.5 * k)
            for i in range(5):
                bx = 600 + i * 70
                self.poly(d, [(bx, 1450), (bx + 90, 1440), (bx + 95, 1480), (bx + 5, 1490)], (120, 190, 140), 4)
        self.stamp(img, 540, 650, "NUNCA LO ENCONTRARON", 64, t, self.start("dinero") + 0.2, (30, 30, 40))

    def s_fbi(self, img, d, t, lt, u):
        self.bg_flat(img, (60, 50, 44), (30, 26, 24))
        self.box(d, 120, 600, 960, 1450, (210, 180, 120), 8, 10)  # carpeta
        self.box(d, 120, 540, 420, 620, (210, 180, 120), 8, 10)
        self.ot(img, 540, 760, "EXPEDIENTE", 70, (90, 70, 40), 0)
        self.ot(img, 540, 880, "«D. B. COOPER»", 90, INK, 0)
        self.stamp(img, 540, 1100, "2016: SE DEJA DE INVESTIGAR", 52, t, self.w("fbi", "dieciséis"))
        self.stamp(img, 540, 1300, "SIN RESOLVER", 90, t, self.w("fbi", "resolver"), (30, 30, 40), rot=6)

    def camera(self, t, name, lt, u):
        if name == "intro":
            return 1.0 + 0.08 * smooth(0, 5, lt), 540, 1000
        if name == "salto":
            return 1.0 + 0.12 * smooth(self.t_jump - self.start("salto"), self.t_jump - self.start("salto") + 2, lt), 480, 1100
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.0, "boom", 0.6), (0.3, "wind", 0.5), (self.w("intro", "nunca"), "boom", 0.7), (st("billete") + 0.2, "click", 0.5),
                (self.w("billete", "cooper"), "pop", 0.5), (st("nota") - 0.1, "boom", 0.6), (self.w("nota", "nota"), "pop", 0.4),
                (self.w("nota", "bomba"), "boom", 0.8), (self.w("pide", "doscientos"), "shimmer", 0.6), (self.w("pide", "cuatro"), "pop", 0.5),
                (st("seattle") + 0.3, "click", 0.6), (self.w("seattle", "pasajeros"), "pop", 0.4), (st("salto") - 0.1, "boom", 0.6),
                (self.w("salto", "escalera"), "wind", 0.6), (self.t_jump, "whoosh", 0.9), (st("dinero") + 0.2, "boom", 0.5),
                (self.w("dinero", "billetes"), "shimmer", 0.5), (st("fbi") - 0.1, "boom", 0.6), (self.w("fbi", "resolver"), "boom", 0.7), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.35), (self.w("intro", "nunca"), 0.85), (st("billete"), 0.55), (st("nota"), 0.95), (st("seattle"), 0.7), (st("salto"), 1.0),
                (st("dinero"), 0.6), (st("fbi"), 0.75), (st("cta"), 0.45), (self.duration, 0.3)]


if __name__ == "__main__":
    main(VIDEO)
