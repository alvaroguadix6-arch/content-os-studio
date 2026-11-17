"""Anuncio de Cristalbox (Granada · Guadix · Baza) — 9:16, 1080×1920, ~31 s.

La narración continua (narracion.json, voz Kokoro em_alex) marca el ritmo: cada plano y cada
rótulo entra con la palabra que lo nombra. Las ilustraciones se animan con los «fondos vivos» del
vídeo de la gravedad (parallax con mapa de profundidad, luz, nubes) y efectos propios: conducción,
impacto y grieta en la luna, pulido de faro antes/después, escaneo de calibración ADAS.

El logotipo se usa tal cual (arte/logo_cristalbox.png): solo se escala y se anima su entrada.

    python anuncio.py --narracion dir/ --arte arte/ --out frames/ [--only 10 200 ...]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "gravedad"))
from fondo_vivo import LivingPlate  # noqa: E402

W, H, FPS = 1080, 1920, 30
YELLOW = (255, 209, 1)
INK = (14, 14, 14)
V0 = 1.3        # la voz empieza tras el impacto en la luna
END_HOLD = 4.4  # segundos de cierre con el logotipo tras la última palabra
FONTS = "/usr/share/fonts/opentype/inter/"


def font(name, size):
    key = (name, size)
    if key not in font.cache:
        font.cache[key] = ImageFont.truetype(os.path.join(FONTS, f"Inter-{name}.otf"), max(8, int(size)))
    return font.cache[key]


font.cache = {}


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(a, b, x):
    k = clamp((x - a) / (b - a)) if b != a else float(x >= b)
    return k * k * (3 - 2 * k)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back_out(x, s=1.4):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


class Timeline:
    def __init__(self, nar):
        L = {}
        for ln in nar["lines"]:
            L[ln["key"]] = dict(ln, start=ln["start"] + V0, end=ln["end"] + V0,
                                words=[(w, a + V0, b + V0) for w, a, b in ln["words"]])
        self.L = L

        def w(key, frag):
            for word, a, _ in L[key]["words"]:
                if frag.lower() in word.lower():
                    return a
            raise KeyError(frag)

        self.impact = 0.6
        self.e2 = L["solucion"]["start"] - 0.3
        self.v_rap, self.v_pro, self.v_mar = w("solucion", "rapidez"), w("solucion", "profesionalidad"), w("solucion", "primeras")
        self.e3 = L["servicios"]["start"] - 0.25
        self.s_tin = w("servicios", "realizamos") - 0.08
        self.s_faro = w("servicios", "pulimos") - 0.08
        self.s_adas = w("servicios", "calibramos") - 0.08
        self.s_cam = w("servicios", "cuando") - 0.05
        self.e4 = L["confianza"]["start"] - 0.25
        self.e5 = L["cierre"]["start"] - 0.45
        self.t_ciudades = w("cierre", "granada")
        self.duration = L["cierre"]["end"] + END_HOLD
        self.shots = [("carretera", 0.0, self.e2), ("taller", self.e2, self.e3), ("sustitucion", self.e3, self.s_tin),
                      ("tintado", self.s_tin, self.s_faro), ("faro", self.s_faro, self.s_adas), ("adas", self.s_adas, self.s_cam),
                      ("camion", self.s_cam, self.e4), ("familia", self.e4, self.e5), ("cierre", self.e5, self.duration)]

    def shot(self, t):
        for s in self.shots:
            if s[1] <= t < s[2]:
                return s
        return self.shots[-1]


LABELS = {
    "sustitucion": "REPARACIÓN Y SUSTITUCIÓN\nDE LUNAS",
    "tintado": "TINTADO HOMOLOGADO",
    "faro": "PULIDO DE FAROS",
    "adas": "CALIBRACIÓN DE SISTEMAS ADAS",
    "camion": "TURISMOS · CAMIONES\nVEHÍCULOS INDUSTRIALES",
}


class Anuncio:
    def __init__(self, nar, arte):
        self.tl = Timeline(nar)
        self.arte = arte
        self.plates = {}
        cfg = {"camion": dict(clouds=0.4, cloud_speed=12),
               "familia": dict(clouds=0.35, cloud_speed=10, rays=0.8)}
        for name in ("carretera", "taller", "sustitucion", "tintado", "faro", "adas", "camion", "familia"):
            img = Image.open(os.path.join(arte, name + ".png")).convert("RGB").resize((int(W * 1.18), int(H * 1.18)), Image.LANCZOS)
            dp = os.path.join(arte, name + "_depth.png")
            c = dict(clouds=0.0, cloud_speed=0.0)
            c.update(cfg.get(name, {}))
            self.plates[name] = LivingPlate(img, Image.open(dp) if os.path.exists(dp) else None, seed=len(name), **c)
        self.logo = Image.open(os.path.join(arte, "logo_cristalbox.png")).convert("RGBA")
        self.logo_big = self.logo.resize((540, 540), Image.LANCZOS)
        self.logo_bug = self.logo.resize((104, 104), Image.LANCZOS)
        r = random.Random(7)
        # grieta: rayos que salen del punto de impacto, con quiebros
        self.crack_pt = (610, 700)
        self.cracks = []
        for i in range(11):
            ang = i / 11 * 2 * math.pi + r.uniform(-0.25, 0.25)
            length = r.uniform(140, 470)
            pts, x, y, a = [(0.0, 0.0)], 0.0, 0.0, ang
            for k in range(9):
                a += r.uniform(-0.35, 0.35)
                step = length / 9
                x, y = x + math.cos(a) * step, y + math.sin(a) * step
                pts.append((x, y))
            self.cracks.append((pts, r.uniform(0.6, 1.0)))
        self.grain = [np.random.default_rng(s).normal(0, 5.5, (H // 2, W // 2)).astype(np.float32) for s in range(6)]
        yy, xx = np.ogrid[:H, :W]
        rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vignette = (1 - 0.38 * np.clip(rr - 0.55, 0, 1) ** 1.4)[..., None].astype(np.float32)
        self.lines_bg = [(r.uniform(-400, W), r.uniform(0, H), r.uniform(0.3, 1.0)) for _ in range(14)]

    @staticmethod
    def par(t, k=1.0):
        return (k * (30 * math.sin(0.5 * t + 0.4) + 8 * math.sin(1.3 * t)), k * (12 * math.sin(0.37 * t) + 5 * math.sin(0.9 * t + 1)))

    # ───────── utilidades de dibujo ─────────
    def text_fit(self, text, style, size, maxw):
        f = font(style, size)
        while max(f.getbbox(line)[2] for line in text.split("\n")) > maxw and size > 20:
            size -= 2
            f = font(style, size)
        return f

    def label(self, img, text, t_in, t, y=250):
        """Rótulo de servicio: barra amarilla que se despliega con texto negro."""
        k = ease_out((t - t_in) / 0.45)
        if k <= 0:
            return
        f = self.text_fit(text, "ExtraBold", 58, 880)
        lines = text.split("\n")
        lh = f.size * 1.18
        bw = max(f.getbbox(line)[2] for line in lines) + 80
        bh = int(lh * len(lines) + 44)
        x0 = (W - bw) // 2
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.rectangle([x0 + 8, y + 10, x0 + bw + 8, y + bh + 10], fill=(0, 0, 0, 90))
        d.rectangle([x0, y, x0 + bw, y + bh], fill=YELLOW + (255,))
        d.rectangle([x0, y, x0 + 14, y + bh], fill=INK + (255,))
        for i, line in enumerate(lines):
            d.text((W / 2 + 7, y + 22 + lh * (i + 0.5)), line, font=f, fill=INK + (255,), anchor="mm")
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).rectangle([x0 - 10, 0, x0 - 10 + (bw + 30) * k, H], fill=255)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel("A")), np.asarray(mask))))
        img.alpha_composite(lay)

    def chip(self, img, text, icon, t_in, t, y):
        k = ease_out((t - t_in) / 0.4)
        if k <= 0:
            return
        f = font("Bold", 48)
        tw = f.getbbox(text)[2]
        bw, bh = tw + 150, 96
        x0 = int((W - bw) / 2 - (1 - k) * 160)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle([x0, y, x0 + bw, y + bh], 48, fill=(12, 12, 12, 215), outline=YELLOW + (255,), width=3)
        cx, cy = x0 + 50, y + bh / 2
        d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=YELLOW + (255,))
        if icon == "rayo":
            d.polygon([(cx + 4, cy - 20), (cx - 12, cy + 3), (cx - 1, cy + 3), (cx - 5, cy + 20), (cx + 12, cy - 4), (cx + 1, cy - 4)], fill=INK + (255,))
        elif icon == "check":
            d.line([(cx - 14, cy + 1), (cx - 4, cy + 12), (cx + 15, cy - 11)], fill=INK + (255,), width=7, joint="curve")
        else:  # estrella
            pts = []
            for i in range(10):
                rr = 19 if i % 2 == 0 else 8
                a = -math.pi / 2 + i * math.pi / 5
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
            d.polygon(pts, fill=INK + (255,))
        d.text((x0 + 100, cy), text, font=f, fill=(255, 255, 255, 255), anchor="lm")
        a = np.asarray(lay.getchannel("A")).astype(np.float32) * clamp(k * 1.4)
        lay.putalpha(Image.fromarray(a.astype(np.uint8)))
        img.alpha_composite(lay)

    def light_sweep(self, img, u, alpha=55, width=260):
        """Reflejo de luz que cruza el plano en diagonal (como en los anuncios de coches)."""
        if not 0 < u < 1:
            return
        lay = Image.new("L", (W // 4, H // 4), 0)
        d = ImageDraw.Draw(lay)
        x = -W // 4 + u * (W // 2 + W // 4)
        w4 = width / 4
        d.polygon([(x, 0), (x + w4, 0), (x + w4 - H // 8, H // 4), (x - H // 8, H // 4)], fill=alpha)
        lay = lay.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
        img.alpha_composite(Image.merge("RGBA", (Image.new("L", (W, H), 255),) * 3 + (lay,)))

    # ───────── planos ─────────
    def s_carretera(self, t, lt, u):
        tl = self.tl
        p = self.plates["carretera"]
        shake = (0.0, 0.0)
        if tl.impact <= t < tl.impact + 0.35:
            k = 1 - (t - tl.impact) / 0.35
            shake = (math.sin(t * 95) * 14 * k, math.cos(t * 80) * 10 * k)
        rumble = (1.5 * math.sin(t * 23), 1.8 * math.sin(t * 31 + 1))
        base = p.render(W, H, 1.0, 0, 0, t, (shake[0] + rumble[0], shake[1] + rumble[1]))
        # avance: el paisaje se acerca (zoom al punto de fuga) con desenfoque de movimiento
        z = 1.0 + 0.32 * (lt / max(1.0, tl.e2)) ** 0.9
        far = p.render(W, H, z, 0, -0.05, t, (shake[0], shake[1]))
        f2 = far.resize((W, H), Image.BILINEAR, box=(W * 0.012, H * 0.012, W * 0.988, H * 0.988))
        far = Image.blend(far, f2, 0.3)
        if not hasattr(self, "_dash"):
            d = np.asarray(Image.fromarray(p.depth).resize((W, H), Image.BILINEAR, box=(p.P + p.size[0] * 0.0327, p.P + p.size[1] * 0.0327,
                                                                                          p.P + p.size[0] * 0.9673, p.P + p.size[1] * 0.9673)))
            m = ((d > 0.62) & (np.arange(H)[:, None] > H * 0.55)).astype(np.uint8) * 255
            self._dash = Image.fromarray(m).filter(ImageFilter.GaussianBlur(5))
        img = Image.composite(base, far, self._dash).convert("RGBA")
        d = ImageDraw.Draw(img, "RGBA")
        cx, cy = self.crack_pt
        if 0.12 <= t < tl.impact:  # la piedra que viene de frente
            k = (t - 0.12) / (tl.impact - 0.12)
            sx, sy = 540 + (cx - 540) * k, 780 + (cy - 780) * k
            r = 2 + 16 * k ** 2
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(70, 66, 60, 255))
        if t >= tl.impact:
            self.crack(img, t)
        if tl.impact <= t < tl.impact + 0.18:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(150 * (1 - (t - tl.impact) / 0.18)))))
        return img

    def crack(self, img, t):
        tl = self.tl
        g = ease_out((t - tl.impact) / 0.35) * (0.5 + 0.5 * smooth(tl.L["problema"]["words"][5][1], tl.e2 - 0.2, t))
        cx, cy = self.crack_pt
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d, ds = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
        for pts, wgt in self.cracks:
            n = max(2, int(len(pts) * g * wgt + 0.999))
            seg = [(cx + x * g, cy + y * g) for x, y in pts[:n]]
            ds.line(seg, fill=(0, 0, 0, 110), width=6)
            d.line(seg, fill=(240, 248, 255, 225), width=3)
        # «ojo de buey» del impacto
        r = 34 * min(1.0, g * 2)
        d.ellipse([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85], outline=(235, 245, 255, 170), width=3)
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(255, 255, 255, 235))
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(70, 80, 90, 255))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0.7)))
        # destello del sol en la grieta
        tw = 0.5 + 0.5 * math.sin(t * 5)
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(gl).ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=(255, 250, 230, int(70 + 50 * tw)))
        img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(25)))

    def s_taller(self, t, lt, u):
        tl = self.tl
        img = self.plates["taller"].render(W, H, 1.0 + 0.14 * ease_out(u), 0.0, -0.05, t, self.par(t, 1.3)).convert("RGBA")
        self.light_sweep(img, (lt - 0.3) / 1.6)
        for i, (txt, ic, tin) in enumerate((("RAPIDEZ", "rayo", tl.v_rap), ("PROFESIONALIDAD", "check", tl.v_pro), ("PRIMERAS MARCAS", "estrella", tl.v_mar))):
            self.chip(img, txt, ic, tin - 0.1, t, 330 + i * 125)
        return img

    def s_service(self, name, t, lt, u, t0, zoom=(1.02, 1.16), pan=(0.0, 0.0)):
        z = zoom[0] + (zoom[1] - zoom[0]) * ease_out(u)
        img = self.plates[name].render(W, H, z, pan[0] * (u - 0.5), pan[1], t, self.par(t, 1.5)).convert("RGBA")
        return img

    def s_sustitucion(self, t, lt, u):
        img = self.s_service("sustitucion", t, lt, u, self.tl.e3, pan=(0.25, 0.0))
        self.light_sweep(img, (lt - 0.2) / 1.2, alpha=45)
        self.label(img, LABELS["sustitucion"], self.tl.e3 + 0.1, t, y=1230)
        return img

    def s_tintado(self, t, lt, u):
        img = self.s_service("tintado", t, lt, u, self.tl.s_tin, zoom=(1.12, 1.02), pan=(-0.2, 0.0))
        self.label(img, LABELS["tintado"], self.tl.s_tin + 0.05, t)
        return img

    def s_faro(self, t, lt, u):
        img = self.s_service("faro", t, lt, u, self.tl.s_faro, zoom=(1.04, 1.12))
        after = img.convert("RGB")
        a = np.asarray(after).astype(np.float32)
        before = a * 0.62 + np.array([150, 125, 70], np.float32) * 0.38
        before = Image.fromarray(before.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))
        xw = int(W * ease_out((lt - 0.2) / 1.0))
        out = before.copy()
        if xw > 0:
            out.paste(after.crop((0, 0, xw, H)), (0, 0))
        img = out.convert("RGBA")
        d = ImageDraw.Draw(img, "RGBA")
        if 0 < xw < W:
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(glow).rectangle([xw - 10, 0, xw + 10, H], fill=(255, 255, 255, 200))
            img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
            d.rectangle([xw - 2, 0, xw + 2, H], fill=(255, 255, 255, 255))
        f = font("Bold", 40)
        if xw > 260:
            d.rounded_rectangle([60, 1250, 330, 1330], 40, fill=(12, 12, 12, 210))
            d.text((195, 1290), "DESPUÉS", font=f, fill=YELLOW + (255,), anchor="mm")
        if xw < W - 260:
            d.rounded_rectangle([W - 300, 1250, W - 60, 1330], 40, fill=(12, 12, 12, 210))
            d.text((W - 180, 1290), "ANTES", font=f, fill=(255, 255, 255, 255), anchor="mm")
        self.label(img, LABELS["faro"], self.tl.s_faro + 0.05, t)
        return img

    def s_adas(self, t, lt, u):
        img = self.s_service("adas", t, lt, u, self.tl.s_adas, zoom=(1.0, 1.1))
        d = ImageDraw.Draw(img, "RGBA")
        # visor de calibración: esquinas, línea de escaneo y confirmación
        x0, y0, x1, y1 = 110, 1180, 970, 1800
        L = 70
        for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=YELLOW + (255,), width=7)
        sy = y0 + (y1 - y0) * (0.5 + 0.5 * math.sin(lt * 3.2 - 1.57))
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rectangle([x0, sy - 10, x1, sy + 10], fill=YELLOW + (170,))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
        d.line([(x0, sy), (x1, sy)], fill=(255, 240, 160, 255), width=3)
        dur = self.tl.s_cam - self.tl.s_adas
        if lt > dur * 0.55:
            k = ease_out((lt - dur * 0.55) / 0.3)
            cx, cy = W / 2, y0 - 90
            d.rounded_rectangle([cx - 150, cy - 44, cx + 150, cy + 44], 44, fill=(12, 12, 12, int(220 * k)), outline=YELLOW + (int(255 * k),), width=3)
            d.line([(cx - 95, cy), (cx - 80, cy + 16), (cx - 50, cy - 16)], fill=YELLOW + (int(255 * k),), width=7)
            d.text((cx + 20, cy), "OK", font=font("ExtraBold", 46), fill=(255, 255, 255, int(255 * k)), anchor="mm")
        self.label(img, LABELS["adas"], self.tl.s_adas + 0.05, t)
        return img

    def s_camion(self, t, lt, u):
        img = self.s_service("camion", t, lt, u, self.tl.s_cam, zoom=(1.1, 1.0))
        self.label(img, LABELS["camion"], self.tl.s_cam + 0.05, t)
        return img

    def s_familia(self, t, lt, u):
        img = self.plates["familia"].render(W, H, 1.03 + 0.12 * ease_out(u), 0.0, 0.0, t, self.par(t, 1.2)).convert("RGBA")
        self.light_sweep(img, (lt - 0.6) / 2.2, alpha=40, width=380)
        return img

    def s_cierre(self, t, lt, u):
        tl = self.tl
        img = Image.new("RGBA", (W, H), (10, 10, 10, 255))
        d = ImageDraw.Draw(img, "RGBA")
        # líneas diagonales sutiles en movimiento (eco de las líneas del logotipo)
        for x, y, s in self.lines_bg:
            xx = (x + lt * 60 * s) % (W + 800) - 400
            d.line([(xx, y), (xx + 500, y - 260)], fill=YELLOW + (int(22 * s),), width=3)
        # logotipo original: entra con escala y aparece (no se altera)
        k = back_out((lt - 0.15) / 0.6)
        a = clamp((lt - 0.15) / 0.35)
        if a > 0:
            s = int(540 * (0.82 + 0.18 * k))
            lg = self.logo_big.resize((s, s), Image.LANCZOS)
            if a < 1:
                lg.putalpha(Image.fromarray((np.asarray(lg.getchannel("A")) * a).astype(np.uint8)))
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).rectangle([540 - s / 2 + 14, 700 - s / 2 + 18, 540 + s / 2 + 14, 700 + s / 2 + 18], fill=(0, 0, 0, int(160 * a)))
            img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))
            img.alpha_composite(lg, (int(540 - s / 2), int(700 - s / 2)))
        # nombre de la marca con espaciado que se cierra
        ka = clamp((lt - 0.55) / 0.5)
        if ka > 0:
            sp = 34 - 22 * ease_out(ka)
            self.spaced(img, "CRISTALBOX", font("ExtraBold", 112), 1100, sp, (255, 255, 255, int(255 * ka)))
        kc = clamp((t - tl.t_ciudades + 0.1) / 0.4)
        if kc > 0:
            d.text((540, 1225), "GRANADA · GUADIX · BAZA", font=font("Bold", 52), fill=YELLOW + (int(255 * kc),), anchor="mm")
            wl = 360 * ease_out(kc)
            d.rectangle([540 - wl, 1290, 540 + wl, 1294], fill=YELLOW + (int(200 * kc),))
        ks = clamp((t - tl.L["cierre"]["end"] - 0.1) / 0.5)
        if ks > 0:
            d.text((540, 1375), "«Tu vehículo, en las mejores manos.»", font=font("SemiBoldItalic", 54), fill=(255, 255, 255, int(255 * ks)), anchor="mm")
        return img

    def spaced(self, img, text, f, y, sp, fill):
        widths = [f.getbbox(c)[2] for c in text]
        total = sum(widths) + sp * (len(text) - 1)
        x = (W - total) / 2
        d = ImageDraw.Draw(img, "RGBA")
        for c, w in zip(text, widths):
            d.text((x, y), c, font=f, fill=fill, anchor="lm")
            x += w + sp

    # ───────── fotograma ─────────
    def frame(self, f):
        tl = self.tl
        t = f / FPS
        name, t0, t1 = tl.shot(t)
        lt = t - t0
        u = clamp(lt / max(0.01, t1 - t0))
        img = getattr(self, "s_" + name)(t, lt, u)
        # cortina amarilla de marca entre planos (entra al final de uno, sale al principio del siguiente)
        cut_names = [s[1] for s in tl.shots[1:]]
        for c in cut_names:
            dt = t - c
            if -0.16 <= dt < 0.2:
                k = (dt + 0.16) / 0.36
                xl = -W * 0.6 + k * (W * 2.3)
                d = ImageDraw.Draw(img, "RGBA")
                d.polygon([(xl - 520, H), (xl, H), (xl + 520, 0), (xl, 0)], fill=YELLOW + (255,))
                d.polygon([(xl - 620, H), (xl - 540, H), (xl - 20, 0), (xl - 100, 0)], fill=INK + (255,))
        # logotipo pequeño (original) en la esquina durante el anuncio
        if tl.e2 <= t < tl.e5 - 0.2:
            a = smooth(tl.e2, tl.e2 + 0.4, t)
            bug = self.logo_bug.copy()
            bug.putalpha(Image.fromarray((np.asarray(bug.getchannel("A")) * a).astype(np.uint8)))
            img.alpha_composite(bug, (W - 104 - 48, 60))
        out = np.asarray(img.convert("RGB")).astype(np.float32)
        if name != "cierre":
            out = out * self.vignette
            # gradación: contraste suave y tono cálido de anuncio
            out = 255 * (0.5 + (out / 255 - 0.5) * 1.06)
            out = out * np.array([1.03, 1.0, 0.96], np.float32)
        g = self.grain[f % len(self.grain)]
        out = out + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
        return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracion", required=True)
    ap.add_argument("--arte", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="*", type=int)
    a = ap.parse_args()
    nar = json.load(open(os.path.join(a.narracion, "narracion.json"), encoding="utf-8"))
    an = Anuncio(nar, a.arte)
    n = int(an.tl.duration * FPS)
    os.makedirs(a.out, exist_ok=True)
    frames = a.only or list(range(n))
    t0 = time.time()
    for i, f in enumerate(frames):
        an.frame(f).save(os.path.join(a.out, f"f{f:05d}.jpg"), quality=93)
        if i % 90 == 0:
            print(f"[cristalbox] fotograma {f}/{n} · {time.time() - t0:.0f} s", flush=True)
    print(f"[cristalbox] {len(frames)} fotogramas en {time.time() - t0:.0f} s · vídeo {n / FPS:.1f} s")


if __name__ == "__main__":
    main()
