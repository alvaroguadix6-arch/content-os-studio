"""NIVEL OCULTO · Casos reales en dibujos: el robo de la Mona Lisa (1911).

Fuentes: History.com, Wikipedia (Vincenzo Peruggia), History Hit, Guinness World Records: el lunes 21-8-1911 (Louvre
cerrado) Peruggia, que había trabajado allí, sale con el cuadro bajo la bata; nadie lo nota hasta el día siguiente;
detienen a Apollinaire e interrogan a Picasso (inocentes); el cuadro pasa dos años en un baúl en su habitación de
París; en diciembre de 1913 intenta venderlo en Florencia al marchante Alfredo Geri, que avisa; es detenido; el cuadro
vuelve al Louvre (enero de 1914) y el robo lo convierte en el cuadro más famoso del mundo.
Personajes genéricos de dibujos (sin parecido con personas reales).
"""
from __future__ import annotations

import math

from caso_base import CARD, GOLD, GREEN, INK, Caso, Look, Toon, back_out, clamp, ease_out, main, mix, smooth  # noqa: F401
from motor import WHITE

MOOD, BPM = "suspense", 100


class VIDEO(Caso):
    NAME = "caso_monalisa"
    FIN = ("¿QUÉ CUADRO", "TE LLEVARÍAS?")
    CARDS = {"salida": ("EL ROBO", "!"), "sospechosos": ("LOS SOSPECHOSOS", "?"), "florencia": ("LA TRAMPA", "!")}
    KEYWORDS = {"cuadro", "famoso", "dos", "años", "ladrón", "museo", "parís", "louvre", "cerrado", "peruggia", "mona", "lisa", "bata", "puerta",
                "nadie", "siguiente", "escándalo", "apollinaire", "picasso", "inocentes", "baúl", "florencia", "marchante", "policía",
                "detenido", "famoso", "planeta", "comentarios"}

    def cast(self):
        self.thief = Toon(Look(shirt=(235, 235, 240), extra={"coat": (245, 245, 250)}, hair=(40, 30, 25)), seed=2)
        self.guard = Toon(Look(shirt=(60, 70, 110), hat="police", hat_col=(40, 46, 80), skin=(240, 200, 170)), seed=5)
        self.poet = Toon(Look(shirt=(120, 90, 160), hair=(60, 40, 30), hair_style="bald", stubble=False), seed=8)
        self.painter = Toon(Look(shirt=(60, 130, 160), hair=(30, 30, 30), stubble=False), seed=9)
        self.dealer = Toon(Look(shirt=(70, 60, 60), extra={"tie": (180, 40, 50)}, hair=(160, 160, 170), stubble=False), seed=11)
        self.cop = Toon(Look(shirt=(50, 60, 90), hat="police", hat_col=(30, 36, 60), stubble=False), seed=13)
        self.host = Toon(Look(shirt=(200, 160, 110), extra={"coat": (190, 150, 100)}, hair=(50, 40, 30)), seed=15)
        self.t_det = self.w("florencia", "detenido")
        self.shakes = [(self.w("intro", "desapareció"), 0.6), (self.t_det, 0.8)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("robo") - 0.1, "robo"), (st("salida") - 0.1, "salida"), (st("nadie") - 0.1, "nadie"),
                (st("sospechosos") - 0.1, "sospechosos"), (st("baul") - 0.1, "baul"), (st("florencia") - 0.1, "florencia"),
                (st("fama") - 0.1, "fama"), (st("cta") - 0.1, "fin")]

    def hud_items(self, t):
        t0, t1 = self.start("salida"), self.t_det
        days = 0 if t < t0 else int(840 * clamp((t - t0) / max(0.1, t1 - t0)))
        sus = 0 if t < self.start("sospechosos") + 0.5 else 2
        fame = 1 + (t >= self.start("nadie")) + (t >= self.start("fama"))
        return [("DÍAS SIN CUADRO", f"{days}", WHITE), ("SOSPECHOSOS", f"{sus}", (255, 120, 120)), ("FAMA", fame, GOLD)]

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        tg = self.w("intro", "desapareció")
        gone = t > tg
        self.bg_museum(img, d, t, (120, 40, 50), [(540, 820, 360, 500, "mona", gone)])
        self.glow(img, 540, 820, 380, (255, 230, 170), 90)
        if not gone:
            self.stamp(img, 540, 470, "EL MÁS FAMOSO DEL MUNDO", 66, t, -0.3, (30, 30, 40), rot=-4)
        if gone:
            self.stamp(img, 540, 820, "DESAPARECIDA", 90, t, tg)
        tw = self.w("intro", "ladrón") - 0.2
        k = back_out((t - tw) / 0.4)
        if k > 0.02:
            self.thief.draw(img, 540, 1760, t, expr="sly", pose="point", scale=0.9 * k, look_at=(540, 800))
            self.stamp(img, 540, 1160, "TRABAJABA AQUÍ", 70, t, self.w("intro", "trabajado"), (30, 30, 40), rot=5)

    def s_robo(self, img, d, t, lt, u):
        self.bg_museum(img, d, t, (90, 40, 50), [(300, 760, 220, 280, "generic", False), (780, 760, 240, 320, "mona", False)])
        self.label(img, d, 540, 470, "PARÍS · 21-8-1911", 66, back_out((lt - 0.2) / 0.4))
        self.label(img, d, 860, 1150, "CERRADO", 44, back_out((t - self.w("robo", "cerrado")) / 0.35), CARD, WHITE)
        k = ease_out(clamp((t - self.w("robo", "peruggia") + 0.4) / 1.6))
        x = -120 + 520 * k
        self.thief.draw(img, x, 1760, t, expr="neutral", pose="idle", walk=t * 9 if k < 1 else 0, scale=0.95, look_at=(780, 760))

    def s_salida(self, img, d, t, lt, u):
        took = t > self.w("salida", "descuelga") + 0.6
        hid = t > self.w("salida", "bata")
        self.bg_museum(img, d, t, (90, 40, 50), [(300, 760, 220, 280, "generic", False), (780, 760, 240, 320, "mona", took)])
        x = 640 if not hid else 640 + 700 * ease_out(clamp((t - self.w("salida", "puerta") + 0.3) / 1.4))
        self.thief.draw(img, x, 1760, t, expr="sly", pose="hold" if took and not hid else "idle", walk=t * 9 if hid else 0, scale=0.95,
                        look_at=(100, 900) if hid else (780, 760))
        if took and not hid:
            self.painting(img, d, x, 1420, 150, 190, "mona")
        if hid:
            self.box(d, x - 60, 1180, x + 60, 1330, (245, 245, 250), 5, 10)  # bulto bajo la bata
        self.box(d, 960, 900, 1080, 1300, (90, 60, 40), 6)  # puerta

    def s_nadie(self, img, d, t, lt, u):
        te = self.w("nadie", "escándalo") - 0.2
        if t < te:
            self.bg_museum(img, d, t, (110, 50, 55), [(540, 760, 240, 320, "mona", True)])
            self.label(img, d, 540, 470, "AL DÍA SIGUIENTE", 66, back_out((lt - 0.1) / 0.4))
            self.painter.draw(img, 540, 1760, t, expr="shock" if lt > 0.8 else "neutral", pose="hands_up" if lt > 0.8 else "idle", scale=0.95,
                              look_at=(540, 760))
        else:
            self.bg_newspaper(img, d, t, ["¡ROBADA", "LA GIOCONDA!"])

    def s_sospechosos(self, img, d, t, lt, u):
        self.bg_flat(img, (60, 60, 80), (30, 30, 44))
        for i in range(6):
            y = 600 + i * 150
            self.Ln(d, [(80, y), (1000, y)], (90, 90, 110), 4)
        for i, (who, name, frag) in enumerate(((self.poet, "POETA", "apollinaire"), (self.painter, "PINTOR", "picasso"))):
            tk = self.w("sospechosos", frag) - 0.2
            k = back_out((t - tk) / 0.4)
            if k > 0.02:
                x = 300 + i * 480
                who.draw(img, x, 1700, t, expr="scared" if t < self.w("sospechosos", "inocentes") else "happy", pose="idle", scale=0.85 * k)
                self.label(img, d, x, 1080, name, 54, k)
                self.stamp(img, x, 1450, "INOCENTE", 66, t, self.w("sospechosos", "inocentes") + i * 0.2, (40, 150, 80))

    def s_baul(self, img, d, t, lt, u):
        self.bg_flat(img, (200, 170, 130), (170, 140, 110))
        self.box(d, 700, 520, 920, 760, (140, 190, 230), 6)  # ventana
        self.Ln(d, [(810, 520), (810, 760)], (100, 80, 60), 8)
        self.floor(d, 1300, (150, 110, 80), (130, 95, 70))
        ko = smooth(0.4, 1.4, lt)
        self.trunk(d, 600, 1300, 1.2, ko)
        if ko > 0.3:
            self.painting(img, d, 600, 1170 - 60 * ko, 180, 130, "mona")
        self.thief.draw(img, 230, 1760, t, expr="sly", pose="point", scale=0.85, look_at=(600, 1200))
        self.label(img, d, 540, 470, "2 AÑOS EN UN BAÚL", 70, back_out((t - self.w("baul", "baúl") + 0.3) / 0.4), GOLD, INK)

    def s_florencia(self, img, d, t, lt, u):
        self.bg_city(img, d, t, ((250, 180, 120), (255, 230, 180)), [(230, 170, 110), (240, 200, 140), (210, 140, 100)])
        self.oell(d, 860, 900, 150, 130, (200, 100, 70), 6)  # cúpula
        self.label(img, d, 540, 470, "FLORENCIA · 1913", 66, back_out((lt - 0.1) / 0.4))
        caught = t > self.t_det - 0.3
        self.thief.draw(img, 300, 1760, t, expr="shock" if caught else "grin", pose="hands_up" if caught else "hold", scale=0.85, look_at=(800, 1200))
        if not caught:
            self.painting(img, d, 300, 1440, 140, 180, "mona")
        self.dealer.draw(img, 700, 1760, t, expr="sly", pose="point" if t > self.w("florencia", "avisa") else "idle", scale=0.85, look_at=(300, 1200))
        if t > self.w("florencia", "policía") - 0.2:
            k = ease_out(clamp((t - self.w("florencia", "policía") + 0.2) / 1.0))
            self.cop.draw(img, 1250 - 330 * k, 1760, t, expr="angry", pose="run" if k < 1 else "point", walk=t * 12, scale=0.85, flip=True)
        if caught:
            self.handcuffs(d, 300, 1380, back_out((t - self.t_det) / 0.3))
        self.stamp(img, 540, 650, "DETENIDO", 100, t, self.t_det)

    def s_fama(self, img, d, t, lt, u):
        self.bg_museum(img, d, t, (120, 40, 50), [(540, 760, 280, 380, "mona", False)])
        self.glow(img, 540, 760, 420, (255, 230, 150), 140)
        for i in range(7):  # público que se agolpa
            x = 90 + i * 150
            Toon(Look(shirt=[(200, 80, 80), (80, 140, 200), (90, 170, 100), (220, 170, 60)][i % 4], stubble=False), seed=30 + i).draw(
                img, x, 1800 + 20 * (i % 2), t, expr="happy", pose="cheer" if i % 2 else "point", scale=0.55, look_at=(540, 760))
        self.pop(img, 540, 470, "EL CUADRO MÁS FAMOSO", 76, t, self.w("fama", "famoso"), GOLD)

    def camera(self, t, name, lt, u):
        if name == "intro":
            return 1.0 + 0.06 * smooth(0, 5, lt), 540, 1000
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.0, "boom", 0.6), (self.w("intro", "desapareció"), "boom", 0.8), (self.w("intro", "trabajado"), "pop", 0.6),
                (st("robo") + 0.2, "whoosh", 0.4), (self.w("robo", "cerrado"), "click", 0.6), (st("salida") - 0.1, "boom", 0.6),
                (self.w("salida", "descuelga"), "pop", 0.5), (self.w("salida", "puerta"), "whoosh", 0.6), (self.w("nadie", "escándalo"), "boom", 0.7),
                (st("sospechosos") - 0.1, "boom", 0.6), (self.w("sospechosos", "inocentes"), "pop", 0.6), (st("baul") + 0.4, "click", 0.6),
                (st("florencia") - 0.1, "boom", 0.6), (self.w("florencia", "policía"), "horn", 0.5), (self.t_det, "boom", 0.9),
                (st("fama") + 0.2, "shimmer", 0.7), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.35), (self.w("intro", "desapareció"), 0.85), (st("robo"), 0.6), (st("salida"), 0.9), (st("nadie"), 0.8),
                (st("baul"), 0.55), (st("florencia"), 0.9), (st("fama"), 0.8), (st("cta"), 0.45), (self.duration, 0.3)]


if __name__ == "__main__":
    main(VIDEO)
