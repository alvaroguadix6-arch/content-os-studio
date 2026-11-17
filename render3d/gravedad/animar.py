"""Animación de «¿Qué pasaría si la gravedad desapareciera durante 10 segundos?».

Ilustraciones realistas (fondos + recortables) animadas por capas y sincronizadas con la
narración continua (narracion.json): la voz manda y las imágenes se ajustan a ella.

    python animar.py --narracion dir/ --arte arte/ --out frames/ [--only ...]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import time

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

W, H = 1080, 1920
FPS = 30
GROUND = 1700  # línea de la acera en pantalla


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else float(x >= b)
    return t * t * (3 - 2 * t)


def ease_in(x):
    x = min(1, max(0, x))
    return x * x


class Timeline:
    """Momentos clave sacados de la narración."""

    def __init__(self, nar):
        self.lines = {ln["key"]: ln for ln in nar["lines"]}
        self.duration = nar["duration"] + 0.6
        L = self.lines

        def word(key, frag, default):
            for w, a, b in L[key]["words"]:
                if frag in w.lower():
                    return a
            return default

        self.t_float = word("despegue", "despegan", L["despegue"]["start"] + 1.0)
        self.t_jump = L["salto"]["start"] + 0.4
        self.t_sky = L["salto"]["start"]
        self.t_water = L["agua"]["start"]
        self.t_grip = word("agua", "agarra", L["agua"]["start"] + 4.5)
        self.t_return = word("vuelve", "vuelve", L["vuelve"]["start"] + 3.0)
        self.t_after = L["consecuencias"]["start"]
        self.t_question = L["pregunta"]["start"]
        self.t_cta = L["cta"]["start"]


class Actor:
    def __init__(self, img, x, ground, scale, depth, kind, rnd):
        self.img, self.x0, self.ground, self.scale, self.depth, self.kind = img, x, ground, scale, depth, kind
        self.vx = {"walk": rnd.uniform(18, 35) * rnd.choice([-1, 1]), "car": rnd.uniform(-120, 120), "still": 0}[kind]
        self.rise = rnd.uniform(0.6, 1.4)  # velocidad de despegue relativa
        self.spin = rnd.uniform(-25, 25)
        self.drift = rnd.uniform(-30, 30)
        self.phase = rnd.uniform(0, 6.28)
        self.cache = {}

    def sprite(self, s, rot):
        key = (round(s, 3), int(rot))
        if key not in self.cache:
            im = self.img.resize((max(2, int(self.img.width * s)), max(2, int(self.img.height * s))), Image.BILINEAR)
            if rot:
                im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
            if len(self.cache) > 300:
                self.cache.clear()
            self.cache[key] = im
        return self.cache[key]


class Animator:
    def __init__(self, nar, arte):
        self.tl = Timeline(nar)
        self.nar = nar
        L = lambda n: Image.open(os.path.join(arte, n + ".png"))  # noqa: E731
        self.plate = {k: L(k).convert("RGB").resize((int(W * 1.18), int(H * 1.18)), Image.LANCZOS) for k in ("calle", "despues", "cielo")}
        self.sp = {k: L(k).convert("RGBA") for k in ("hombre", "mujer", "nino", "abuelo", "perro", "coche_rojo", "taxi", "furgoneta", "papelera", "bicicleta")}
        r = random.Random(5)
        self.rnd = r
        # reparto: (recortable, x, suelo, altura en px, profundidad, tipo)
        cast = [
            ("furgoneta", 800, 1400, 250, 0.55, "car"), ("taxi", 260, 1440, 190, 0.6, "car"), ("coche_rojo", 640, 1500, 220, 0.7, "car"),
            ("bicicleta", 980, 1580, 170, 0.75, "still"), ("papelera", 70, 1650, 170, 0.85, "still"),
            ("abuelo", 300, 1710, 400, 0.85, "walk"), ("mujer", 800, 1730, 430, 0.9, "walk"), ("perro", 560, 1770, 190, 0.95, "walk"),
            ("nino", 130, 1810, 320, 1.0, "walk"), ("hombre", 520, 1860, 520, 1.05, "walk"),
        ]
        self.actors = []
        for name, x, g, hpx, depth, kind in cast:
            img = self.sp[name]
            s = hpx / img.height
            if kind == "car" and r.random() < 0.5:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            self.actors.append(Actor(img, x, g, s, depth, kind, r))
        spread = [120, 330, 540, 760, 960, 230, 650, 870, 430, 540]
        for a_, sx in zip(self.actors, spread):
            a_.spread = sx
        self.hero = self.actors[-1]  # el hombre del traje: el que «sale volando» con un paso
        self.bubbles = [(r.uniform(80, 1000), r.uniform(500, 1500), r.uniform(40, 150), r.uniform(0, 6.28)) for _ in range(14)]
        self.papers = [(r.uniform(0, W), r.uniform(900, 1800), r.uniform(0, 6.28), r.uniform(0.5, 1.5)) for _ in range(40)]
        self.dust = [(r.uniform(0, W), r.uniform(0, H), r.uniform(2, 6), r.uniform(0, 6.28)) for _ in range(120)]
        self.shards = [(r.uniform(-1, 1), r.uniform(-1, -0.2), r.uniform(4, 14), r.uniform(0, 6.28)) for _ in range(60)]
        yy, xx = np.ogrid[:H, :W]
        rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vignette = (1 - 0.42 * np.clip(rr - 0.5, 0, 1) ** 1.3)[..., None]

    # ───── cámara sobre el fondo ─────
    def view(self, name, zoom, px=0.0, py=0.0):
        im = self.plate[name]
        bw, bh = im.size
        cw, ch = bw / zoom, bh / zoom
        cx = bw / 2 + px * (bw - cw) / 2
        cy = bh / 2 + py * (bh - ch) / 2
        return im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

    # ───── posición de cada personaje/objeto ─────
    def float_lift(self, a, t):
        """Altura (px) mientras flota: sube y se estabiliza a media altura, con un vaivén suave."""
        tl = self.tl
        ft = max(0.0, min(t, tl.t_return) - tl.t_float)
        if ft <= 0:
            return 0.0
        lmax = (380 + 520 * a.rise) * a.depth
        lift = lmax * (1 - math.exp(-ft / 3.5)) + 22 * math.sin(ft * 0.9 + a.phase) * min(1, ft)
        if a is self.hero and min(t, tl.t_return) > tl.t_jump:
            jt = min(t, tl.t_return) - tl.t_jump
            lift += 1500 * (1 - math.exp(-jt / 1.1))  # un paso y sale disparado hacia arriba
        return lift

    def actor_state(self, a, t):
        tl = self.tl
        tm = min(t, tl.t_float)
        x = a.x0 + (a.vx * tm if a.kind != "still" else 0)
        x = (x + 200) % (W + 400) - 200
        rot, bob = 0.0, 0.0
        if t < tl.t_float and a.kind == "walk":
            bob = abs(math.sin(t * 7 + a.phase)) * 10 * a.scale
            rot = 2.5 * math.sin(t * 7 + a.phase)
        ft = max(0.0, min(t, tl.t_return) - tl.t_float)
        rot += a.spin * ft * 0.6
        if ft > 0:  # se reparten por toda la pantalla mientras flotan
            k = 1 - math.exp(-ft / 4.0)
            x = x * (1 - k) + a.spread * k + a.drift * 0.3 * math.sin(ft * 0.5)
        lift = self.float_lift(a, t)
        if t > tl.t_return:  # vuelve la gravedad: caída acelerada (g real escalada a la pantalla)
            dt = t - tl.t_return - (0.12 if a.kind == "car" else 0.0)
            lift = max(0.0, self.float_lift(a, tl.t_return) - 0.5 * 9.8 * 140 * max(0, dt) ** 2)
        return x, lift, rot, bob

    def landed_at(self, a):
        tl = self.tl
        return tl.t_return + (0.12 if a.kind == "car" else 0.0) + math.sqrt(max(1.0, self.float_lift(a, tl.t_return)) / (0.5 * 9.8 * 140))

    # ───── fotograma ─────
    def frame(self, f):
        tl = self.tl
        t = f / FPS
        shake = (0.0, 0.0)
        # impactos: temblor cuando aterrizan las cosas grandes
        for a in self.actors:
            if a.kind == "car" or a is self.hero:
                lt = t - self.landed_at(a)
                if 0 <= lt < 0.45:
                    k = 1 - lt / 0.45
                    shake = (shake[0] + math.sin(t * 90) * 16 * k, shake[1] + math.cos(t * 70) * 22 * k)
        if t < tl.t_after:
            # cámara: empuje lento; al flotar sube; al saltar mira al cielo; al caer baja
            up = smooth(tl.t_float, tl.t_water, t) * 0.55 * (1 - smooth(tl.t_return, tl.t_return + 1.2, t))
            zoom = 1.0 + 0.06 * smooth(0, tl.t_float, t) + 0.05 * smooth(tl.t_water, tl.t_return, t)
            in_sky = tl.t_sky <= t < tl.t_water
            if in_sky:
                img = self.view("cielo", 1.0 + 0.1 * smooth(tl.t_sky, tl.t_water, t), 0, -0.4 + 0.8 * smooth(tl.t_sky, tl.t_water, t))
            else:
                img = self.view("calle", zoom, 0.0, -up)
            scene_offset = up * (self.plate["calle"].height / zoom - H) / 2 * 1.0
            img = img.convert("RGBA")
            d = ImageDraw.Draw(img, "RGBA")
            if in_sky:
                self.draw_sky_flyers(img, d, t)
            else:
                self.draw_street(img, d, t, scene_offset)
        else:
            u = (t - tl.t_after) / (tl.duration - tl.t_after)
            img = self.view("despues", 1.0 + 0.12 * u, 0.15 * math.sin(u * 2), 0.1).convert("RGBA")
            d = ImageDraw.Draw(img, "RGBA")
            self.draw_aftermath(img, d, t)
        out = img.convert("RGB")
        if shake != (0.0, 0.0):
            z = max(W / (W - 2 * abs(shake[0]) - 2), H / (H - 2 * abs(shake[1]) - 2))
            cw, ch = W / z, H / z
            out = out.resize((W, H), Image.BILINEAR, box=(W / 2 - cw / 2 - shake[0], H / 2 - ch / 2 - shake[1], W / 2 + cw / 2 - shake[0], H / 2 + ch / 2 - shake[1]))
        # destello al volver la gravedad y fundidos entre planos
        for tt, strength, dur in ((tl.t_return, 0.55, 0.35), (tl.t_sky, 0.3, 0.2), (tl.t_water, 0.3, 0.2), (tl.t_after, 0.6, 0.4)):
            if 0 <= t - tt < dur:
                out = Image.blend(out, Image.new("RGB", (W, H), (255, 255, 255)), strength * (1 - (t - tt) / dur))
        # gradación de color: ligeramente fría al flotar, cálida al principio
        arr = np.asarray(out).astype(np.float32) * self.vignette
        if tl.t_float < t < tl.t_return:
            k = min(1, (t - tl.t_float) / 1.5)
            arr = arr * (1 - 0.12 * k) + np.array([90, 120, 160]) * 0.12 * k
        out = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        out = self.hud(out, t)
        return out

    def draw_street(self, img, d, t, scene_offset):
        tl = self.tl
        # farola (la usarán para agarrarse)
        lx = 900
        if t >= tl.t_water:
            d.rectangle([lx - 12, GROUND - 900 + scene_offset, lx + 12, GROUND + 60 + scene_offset], fill=(35, 38, 45, 255))
            d.ellipse([lx - 40, GROUND - 930 + scene_offset, lx + 40, GROUND - 880 + scene_offset], fill=(255, 230, 160, 255))
        # papeles y hojas que se despegan
        if t > tl.t_float:
            ft = t - tl.t_float
            for x, y, ph, sp in self.papers:
                yy = y - ft * 60 * sp + scene_offset - (0 if t < tl.t_return else -2000 * ease_in((t - tl.t_return) / 1.0))
                xx = x + 40 * math.sin(ft * sp + ph)
                rot = ft * 80 * sp + ph * 50
                pts = [(xx + math.cos(math.radians(rot + a)) * 16, yy + math.sin(math.radians(rot + a)) * 10) for a in (0, 90, 180, 270)]
                d.polygon(pts, fill=(240, 236, 225, 220))
        # sombras y polvo (capa difuminada, más realista)
        fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fx)
        states = []
        for a in sorted(self.actors, key=lambda q: q.depth):
            x, lift, rot, bob = self.actor_state(a, t)
            g = a.ground + scene_offset * a.depth
            if a is self.actors[6] and t >= tl.t_grip and t < tl.t_return:  # agarrada a la farola
                x, lift, rot = lx - 30, 380, -78 + 6 * math.sin(t * 3)
            states.append((a, x, lift, rot, bob, g))
            sh = max(0.0, 1 - lift / 700)
            sw = a.img.width * a.scale * 0.45 * (0.5 + 0.5 * sh)
            fd.ellipse([x - sw, g - 14, x + sw, g + 14], fill=(0, 0, 0, int(120 * sh)))
            lt = t - self.landed_at(a)
            if t > tl.t_return and 0 <= lt < 1.6:
                k = lt / 1.6
                big = a.img.width * a.scale / 300
                for j in range(5):
                    r = (70 + 300 * k) * big * (0.6 + 0.15 * j)
                    cx = x + (j - 2) * 60 * big * (0.5 + k)
                    cy = g - 30 - 120 * k * big - j * 10
                    fd.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55], fill=(185, 175, 160, int(120 * (1 - k))))
        img.alpha_composite(fx.filter(ImageFilter.GaussianBlur(18)))
        for a, x, lift, rot, bob, g in states:
            s = a.sprite(a.scale, rot)
            img.alpha_composite(s, (int(x - s.width / 2), int(g - s.height - lift - bob + (s.height - a.img.height * a.scale) / 2)))
            lt = t - self.landed_at(a)
            if a.kind == "car" and t > tl.t_return and 0 <= lt < 1.2:  # cristales que saltan
                k = lt / 1.2
                for dx, dy, sz, ph in self.shards[:30]:
                    px, py = x + dx * 500 * k, g - 80 + dy * 600 * k + 900 * k * k
                    d.polygon([(px, py - sz), (px + sz * 0.6, py), (px, py + sz * 0.4)], fill=(200, 230, 255, int(230 * (1 - k))))
        # burbujas de agua flotantes
        if tl.t_water <= t:
            for i, (x, y, r, ph) in enumerate(self.bubbles):
                k = smooth(tl.t_water + i * 0.15, tl.t_water + i * 0.15 + 0.8, t)
                if k <= 0:
                    continue
                fall = 0.0
                if t > tl.t_return:
                    fall = 2600 * ease_in((t - tl.t_return) / 1.1)
                    if fall > 1500:
                        continue
                yy = y + scene_offset - (t - tl.t_water) * 25 + fall
                self.water_sphere(img, x + 15 * math.sin(t + ph), yy, r * k, t + ph, splash=fall > 0)

    def water_sphere(self, img, x, y, r, ph, splash=False):
        if r < 4:
            return
        size = int(r * 2.6)
        lay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        c = size / 2
        rx = r * (1 + 0.08 * math.sin(ph * 3))
        ry = r * (1 - 0.08 * math.sin(ph * 3))
        if splash:
            rx, ry = r * 1.3, r * 0.7
        ld.ellipse([c - rx, c - ry, c + rx, c + ry], fill=(120, 180, 230, 95), outline=(220, 240, 255, 170), width=max(2, int(r / 18)))
        ld.ellipse([c - rx * 0.75, c - ry * 0.75 + ry * 0.2, c + rx * 0.75, c + ry * 0.75 + ry * 0.2], fill=(60, 120, 200, 60))
        ld.ellipse([c - rx * 0.45, c - ry * 0.6, c - rx * 0.1, c - ry * 0.3], fill=(255, 255, 255, 190))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.2)), (int(x - c), int(y - c)))

    def draw_sky_flyers(self, img, d, t):
        """Plano mirando al cielo: el hombre que dio un paso sale volando entre los edificios."""
        tl = self.tl
        u = (t - tl.t_sky) / max(0.1, tl.t_water - tl.t_sky)
        for i, a in enumerate(self.actors[:-1]):
            if i % 2:
                continue
            s = a.sprite(a.scale * 0.35, a.spin * (t - tl.t_float))
            x = 150 + (i * 137) % 800 + 30 * math.sin(t + i)
            y = 1500 - u * 700 - i * 60
            img.alpha_composite(s, (int(x - s.width / 2), int(y)))
        h = self.hero
        s = h.sprite(h.scale * (1.4 - 0.9 * u), 25 * math.sin(t * 2) + 20 * u)
        img.alpha_composite(s, (int(W / 2 - s.width / 2 + 60 * math.sin(t)), int(1900 - 1500 * u - s.height / 2)))

    def draw_aftermath(self, img, d, t):
        tl = self.tl
        u = t - tl.t_after
        # humo y polvo
        for x, y, r, ph in self.dust:
            yy = (y - u * 40) % H
            d.ellipse([x - r, yy - r, x + r, yy + r], fill=(220, 210, 190, 90))
        smoke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(smoke)
        for k in range(8):
            ph = (u * 0.15 + k * 0.125) % 1
            x = 200 + k * 100 + 40 * math.sin(u + k)
            y = 1300 - ph * 900
            rr = 80 + ph * 220
            sd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(70, 70, 75, int(110 * (1 - ph))))
        img.alpha_composite(smoke.filter(ImageFilter.GaussianBlur(30)))
        # luces de emergencia
        k = (math.sin(t * 9) + 1) / 2
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([-300, 1100, 500, 1900], fill=(255, 40, 40, int(90 * k)))
        gd.ellipse([600, 1100, 1400, 1900], fill=(40, 90, 255, int(90 * (1 - k))))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(80)))
        # oscurecer para la pregunta final
        if t > tl.t_question:
            dk = smooth(tl.t_question, tl.t_question + 0.6, t)
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(140 * dk))))

    def hud(self, out, t):
        """Indicador de gravedad y cuenta atrás de 10 s (sincronizada con la narración)."""
        tl = self.tl
        if not (tl.t_float - 0.3 <= t < tl.t_return + 1.5):
            return out
        from overlay_font import font

        img = out.convert("RGBA")
        d = ImageDraw.Draw(img, "RGBA")
        span = tl.t_return - tl.t_float
        left = max(0.0, 10.0 * (1 - (t - tl.t_float) / span)) if t >= tl.t_float else 10.0
        zero_g = tl.t_float <= t < tl.t_return
        box = [300, 150, 780, 300]
        d.rounded_rectangle(box, 36, fill=(10, 14, 22, 170), outline=(255, 255, 255, 90), width=3)
        d.text((540, 192), "GRAVEDAD", font=font(34), fill=(200, 210, 225, 255), anchor="mm")
        if zero_g:
            d.text((540, 252), f"0 g  ·  {left:04.1f} s", font=font(58), fill=(120, 220, 255, 255), anchor="mm")
        else:
            col = (255, 90, 80, 255) if t >= tl.t_return else (255, 255, 255, 255)
            d.text((540, 252), "1 g" if t < tl.t_float else "¡1 g!", font=font(58), fill=col, anchor="mm")
        return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracion", required=True)
    ap.add_argument("--arte", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="*", type=int)
    ap.add_argument("--frames", nargs=2, type=int)
    a = ap.parse_args()
    nar = json.load(open(os.path.join(a.narracion, "narracion.json"), encoding="utf-8"))
    an = Animator(nar, a.arte)
    n = int(an.tl.duration * FPS)
    os.makedirs(a.out, exist_ok=True)
    frames = a.only or list(range(*(a.frames if a.frames else (0, n - 1))))
    if a.frames:
        frames = list(range(a.frames[0], a.frames[1] + 1))
    t0 = time.time()
    for i, f in enumerate(frames):
        an.frame(f).save(os.path.join(a.out, f"f{f:05d}.jpg"), quality=92)
        if i % 90 == 0:
            print(f"[gravedad] fotograma {f}/{n} · {time.time() - t0:.0f} s", flush=True)
    print(f"[gravedad] {len(frames)} fotogramas en {time.time() - t0:.0f} s · total del vídeo {n} fotogramas")


if __name__ == "__main__":
    main()
