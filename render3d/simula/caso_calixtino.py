"""NIVEL OCULTO · Casos reales en dibujos: el robo del Códice Calixtino (Santiago de Compostela, 2011-2012).

Fuentes: Infobae, ACI Prensa, Consumer, La Opinión, Periódico de Ibiza (EFE): manuscrito del siglo XII, guía medieval
del Camino de Santiago; desaparece del archivo de la catedral en julio de 2011 sin señales de fuerza; las sospechas
apuntan a un electricista que había trabajado durante años en la catedral; el 4-7-2012 aparece en un garaje, en una bolsa
de plástico; en los registros se halla más de un millón de euros en efectivo; vuelve a la catedral.
El sospechoso NO se nombra ni se le pone cara (silueta): es una persona privada.
"""
from __future__ import annotations

import math

from PIL import Image

from caso_base import CARD, GOLD, GREEN, INK, Caso, Look, Toon, back_out, clamp, ease_out, main, mix, smooth  # noqa: F401
from motor import H, S, W, WHITE

MOOD, BPM = "suspense", 96


class VIDEO(Caso):
    NAME = "caso_calixtino"
    FIN = ("¿CÓMO SALIÓ", "DE LA CATEDRAL?")
    CARDS = {"robo": ("EL ROBO", "!"), "sospechoso": ("EL SOSPECHOSO", "?"), "garaje": ("EL HALLAZGO", "!")}
    KEYWORDS = {"libros", "valiosos", "españa", "catedral", "santiago", "año", "garaje", "códice", "calixtino", "siglo", "doce", "camino",
                "julio", "archivo", "forzadas", "pistas", "policía", "éxito", "electricista", "plástico", "millón", "euros", "efectivo",
                "volvió", "hoy", "nadie", "comentarios"}

    def cast(self):
        self.det = Toon(Look(shirt=(40, 60, 100), hat="police", hat_col=(30, 40, 70), badge=True, stubble=False), seed=3)
        self.shadow = Toon(Look(shirt=(60, 60, 60), hair=(40, 40, 40), stubble=False), seed=5)
        self.pilgrims = [Toon(Look(shirt=c, hair=h, stubble=False), seed=20 + i) for i, (c, h) in
                         enumerate([((200, 120, 60), (60, 40, 30)), ((90, 150, 200), (180, 140, 90)), ((150, 90, 160), (30, 25, 20))])]
        self.host = Toon(Look(shirt=(200, 160, 110), extra={"coat": (190, 150, 100)}, hair=(50, 40, 30)), seed=15)
        self.shakes = [(self.w("garaje", "encuentra"), 0.6)]

    def build_scenes(self):
        st = self.start
        return [(0.0, "intro"), (st("codice") - 0.1, "codice"), (st("robo") - 0.1, "robo"), (st("busqueda") - 0.1, "busqueda"),
                (st("sospechoso") - 0.1, "sospechoso"), (st("garaje") - 0.1, "garaje"), (st("dinero") - 0.1, "dinero"),
                (st("vuelta") - 0.1, "vuelta"), (st("cta") - 0.1, "fin")]

    def hud_items(self, t):
        t0, t1 = self.start("robo"), self.w("garaje", "encuentra")
        days = 0 if t < t0 else int(365 * clamp((t - t0) / max(0.1, t1 - t0)))
        sus = 1 if t > self.w("sospechoso", "electricista") else 0
        cash = "+1 M€" if t > self.w("dinero", "millón") else "0 €"
        return [("DÍAS DESAPARECIDO", f"{days}", WHITE), ("SOSPECHOSOS", f"{sus}", (255, 120, 120)), ("EFECTIVO HALLADO", cash, GOLD)]

    def silhouette(self, img, x, y, t, scale=1.0, pose="idle"):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        self.shadow.draw(lay, x, y, t, expr="neutral", pose=pose, scale=scale)
        a = lay.getchannel("A")
        sil = Image.new("RGBA", img.size, (14, 14, 20, 255))
        sil.putalpha(a)
        self.glow(img, x, y - 400 * scale, 300 * scale, (150, 170, 210), 110)
        img.alpha_composite(sil)

    def stand(self, img, d, x, y, with_book=True, glow=True):
        self.box(d, x - 160, y, x + 160, y + 40, (110, 80, 60), 6, 8)
        self.box(d, x - 40, y + 40, x + 40, y + 300, (110, 80, 60), 6)
        if with_book:
            if glow:
                self.glow(img, x, y - 150, 220, (255, 220, 140), 140)
            self.codex(img, d, x, y - 170, 0.9)

    def shell(self, d, x, y, s=1.0):  # concha del Camino
        self.oell(d, x, y, 90 * s, 90 * s, (40, 90, 170), 6)
        for i in range(7):
            a = math.pi + i * math.pi / 6
            self.Ln(d, [(x, y + 40 * s), (x + math.cos(a) * 70 * s, y + 40 * s + math.sin(a) * 70 * s)], GOLD, 6 * s)

    # ───── escenas ─────
    def s_intro(self, img, d, t, lt, u):
        tg = self.w("intro", "garaje") - 0.2
        if t < tg:
            self.bg_cathedral(img, d, t)
            gone = t > self.w("intro", "desapareció")
            self.stand(img, d, 540, 1050, with_book=not gone)
            self.stamp(img, 540, 470, "UN TESORO DEL SIGLO XII", 64, t, -0.3, (30, 30, 40), rot=-4)
            if gone:
                self.stamp(img, 540, 850, "DESAPARECIDO", 96, t, self.w("intro", "desapareció"))
        else:
            self.bg_garage(img, d, t)
            k = back_out((t - tg) / 0.4)
            self.glow(img, 540, 1000, 300, (255, 220, 140), 160 * min(1, k))
            self.codex(img, d, 540, 1000, 1.1 * k)
            self.stamp(img, 540, 470, "...EN UN GARAJE", 90, t, tg + 0.1)

    def s_codice(self, img, d, t, lt, u):
        self.bg_flat(img, (90, 60, 50), (50, 32, 28))
        self.glow(img, 540, 950, 360, (255, 210, 130), 120)
        self.codex(img, d, 540, 950 + 15 * math.sin(t * 2), 1.5)
        self.label(img, d, 540, 470, "SIGLO XII", 90, back_out((t - self.w("codice", "siglo")) / 0.4), GOLD, INK)
        k = back_out((t - self.w("codice", "camino") + 0.2) / 0.4)
        if k > 0.02:
            self.shell(d, 200, 1550, 1.0 * k)
            for i, p in enumerate(self.pilgrims):
                p.draw(img, 460 + i * 200, 1780, t, expr="happy", pose="idle", walk=t * 8, scale=0.55 * k)
            self.label(img, d, 540, 640, "GUÍA DEL CAMINO", 60, k)

    def s_robo(self, img, d, t, lt, u):
        self.bg_cathedral(img, d, t)
        self.stand(img, d, 540, 1050, with_book=False)
        self.label(img, d, 540, 470, "JULIO 2011", 80, back_out((lt - 0.1) / 0.4))
        self.stamp(img, 300, 820, "SIN PUERTAS FORZADAS", 50, t, self.w("robo", "forzadas"), (30, 30, 40), rot=-6)
        self.stamp(img, 780, 960, "SIN PISTAS", 60, t, self.w("robo", "pistas"), CARD, rot=6)

    def s_busqueda(self, img, d, t, lt, u):
        self.bg_city(img, d, t, cols=[(220, 205, 180), (200, 190, 170), (230, 220, 200)], night=0.3)
        k = ease_out(clamp(lt / 2.5))
        self.det.draw(img, 150 + 700 * k, 1760, t, expr="sad", pose="idle", walk=t * 9, scale=0.9, look_at=(1000, 1700))
        self.magnifier(d, 150 + 700 * k + 120, 1400, 0.6)
        self.label(img, d, 540, 470, "1 AÑO BUSCANDO", 76, back_out((lt - 0.2) / 0.4))

    def s_sospechoso(self, img, d, t, lt, u):
        self.bg_flat(img, (40, 40, 60), (20, 20, 30))
        self.poly(d, [(440, 250), (640, 250), (880, 1700), (200, 1700)], (60, 60, 80), 0)
        self.silhouette(img, 540, 1740, t, 1.05)
        self.ot(img, 540, 900, "?", 200, GOLD, 8)
        self.label(img, d, 540, 470, "UN ELECTRICISTA", 76, back_out((t - self.w("sospechoso", "electricista")) / 0.4), GOLD, INK)
        self.pop(img, 540, 1600, "AÑOS TRABAJANDO EN LA CATEDRAL", 50, t, self.w("sospechoso", "catedral"), WHITE)

    def s_garaje(self, img, d, t, lt, u):
        self.bg_garage(img, d, t)
        tf = self.w("garaje", "encuentra")
        self.det.draw(img, 280, 1760, t, expr="shock" if t > tf else "neutral", pose="hands_up" if t > tf else "point", scale=0.9, look_at=(700, 1300))
        self.oell(d, 720, 1350, 170, 150, (230, 235, 240), 5)  # bolsa de plástico
        if t > tf - 0.2:
            k = back_out((t - tf + 0.2) / 0.4)
            self.glow(img, 720, 1150, 260, (255, 220, 140), 170)
            self.codex(img, d, 720, 1150 - 80 * k, 0.8 * k)
            self.stamp(img, 540, 470, "¡ENCONTRADO! JULIO 2012", 66, t, tf)

    def s_dinero(self, img, d, t, lt, u):
        self.bg_flat(img, (30, 70, 50), (14, 34, 24))
        self.money_rain(d, t, smooth(0, 1, lt))
        k = ease_out(clamp((t - self.w("dinero", "millón") + 0.4) / 1.2))
        if k > 0.01:
            self.ot(img, 540, 860, f"+{1_000_000 * k:,.0f} €".replace(",", "."), 120, GOLD)
        self.stamp(img, 540, 1080, "EN EFECTIVO", 80, t, self.w("dinero", "efectivo"))

    def s_vuelta(self, img, d, t, lt, u):
        self.bg_cathedral(img, d, t)
        self.stand(img, d, 540, 1000)
        for i, p in enumerate(self.pilgrims):
            p.draw(img, 230 + i * 310, 1800, t, expr="happy", pose="cheer", scale=0.6)
        self.label(img, d, 540, 470, "DE VUELTA EN LA CATEDRAL", 62, back_out((lt - 0.2) / 0.4), GOLD, INK)

    def camera(self, t, name, lt, u):
        if name in ("intro", "codice"):
            return 1.0 + 0.07 * smooth(0, 5, lt), 540, 1000
        return super().camera(t, name, lt, u)

    def sfx_events(self):
        st = self.start
        return [(0.0, "boom", 0.6), (self.w("intro", "desapareció"), "boom", 0.8), (self.w("intro", "garaje") - 0.2, "pop", 0.6),
                (st("codice") + 0.2, "shimmer", 0.6), (self.w("codice", "siglo"), "pop", 0.5), (st("robo") - 0.1, "boom", 0.6),
                (self.w("robo", "forzadas"), "click", 0.6), (self.w("robo", "pistas"), "click", 0.6), (st("busqueda") + 0.3, "tick", 0.6),
                (st("sospechoso") - 0.1, "boom", 0.6), (self.w("sospechoso", "electricista"), "pop", 0.6), (st("garaje") - 0.1, "boom", 0.6),
                (self.w("garaje", "encuentra"), "shimmer", 0.8), (st("dinero") + 0.2, "shimmer", 0.6), (self.w("dinero", "efectivo"), "boom", 0.6),
                (st("vuelta") + 0.2, "shimmer", 0.5), (st("cta"), "pop", 0.6)]

    def music_plan(self):
        st = self.start
        return [(0, 0.35), (self.w("intro", "desapareció"), 0.8), (st("codice"), 0.6), (st("robo"), 0.85), (st("busqueda"), 0.55),
                (st("sospechoso"), 0.85), (st("garaje"), 0.95), (st("dinero"), 0.9), (st("vuelta"), 0.6), (st("cta"), 0.45), (self.duration, 0.3)]


if __name__ == "__main__":
    main(VIDEO)
