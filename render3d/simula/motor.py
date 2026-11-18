"""Plantilla común de las «simulaciones» (mismo estilo que el vídeo de la gravedad).

- Ilustración plana dibujada por código a doble resolución (bordes limpios).
- Cámara siempre en movimiento (empuje lento + deriva), temblores y destellos en los cortes.
- Texto arriba palabra a palabra, palabras clave en amarillo subrayadas (como la gravedad).
- Indicador inferior tipo «píldora» (contador, temperatura, dato 3/10...).
- Globo terráqueo con los continentes reales (máscara tierra/mar), noche, hielo, mares que bajan,
  luces de ciudades y alertas.

Cada vídeo es una subclase de Video con su guion (guion.json), sus escenas (métodos s_<nombre>)
y sus efectos de sonido. La narración (voz.py de gravedad) marca todos los tiempos.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "gravedad"))
from plano import (S, YEL, Person, back_out, clamp, draw_car, ease_out, font, mix, shade,  # noqa: E402,F401
                   smooth, vgrad)

W, H, FPS = 1080, 1920, 30
CYAN = (130, 215, 255)
RED = (255, 95, 80)
WHITE = (255, 255, 255)


def norm(w):
    return w.lower().strip("¿¡,.:;!?«»\"'…")


class Video:
    NAME = "video"
    BRAND = None  # p. ej. "NIVEL OCULTO": marca discreta arriba y en el cierre
    KEYWORDS: set = set()
    END_HOLD = 0.8

    def __init__(self, nar):
        self.nar = nar
        self.L = {ln["key"]: ln for ln in nar["lines"]}
        self.duration = nar["duration"] + self.END_HOLD
        self.rnd = random.Random(3)
        self._grad = {}
        self.stars_xy = [(self.rnd.uniform(0, W), self.rnd.uniform(0, H), self.rnd.uniform(0.8, 2.8), self.rnd.uniform(0, 6.3)) for _ in range(220)]
        self.shakes = []  # (t, fuerza)
        self.setup()
        self.scenes = sorted(self.build_scenes())  # [(t0, nombre)]

    # ───── tiempos ─────
    def start(self, key):
        return self.L[key]["start"]

    def end(self, key):
        return self.L[key]["end"]

    def w(self, key, frag, offset=0.0):
        for word, a, _ in self.L[key]["words"]:
            if frag.lower() in word.lower():
                return a + offset
        return self.L[key]["start"] + offset

    def setup(self):
        pass

    def build_scenes(self):
        return [(0.0, "intro")]

    def scene_at(self, t):
        cur = self.scenes[0]
        for i, sc in enumerate(self.scenes):
            if t >= sc[0]:
                cur = sc
                nxt = self.scenes[i + 1][0] if i + 1 < len(self.scenes) else self.duration
        t0, name = cur
        t1 = next((s[0] for s in self.scenes if s[0] > t0), self.duration)
        return name, t0, t1

    # ───── utilidades de dibujo (coordenadas a 1x; se multiplican por S) ─────
    def grad(self, key, top, bottom):
        if key not in self._grad:
            self._grad[key] = vgrad(W * S, H * S, top, bottom)
        return self._grad[key]

    def bg(self, img, key, top, bottom):
        img.paste(self.grad(key, top, bottom))

    @staticmethod
    def bgdyn(img, top, bottom):
        """Degradado que cambia en cada fotograma (sin caché)."""
        col = np.linspace(0, 1, 256, dtype=np.float32)[:, None]
        g = np.array(top, np.float32) * (1 - col) + np.array(bottom, np.float32) * col
        img.paste(Image.fromarray(g[:, None, :].astype(np.uint8)).resize((W * S, H * S), Image.BILINEAR))

    def stars(self, d, t, alpha=1.0, drift=0.0):
        for x, y, r, ph in self.stars_xy:
            tw = 0.55 + 0.45 * math.sin(t * 2 + ph)
            c = int(220 * tw * alpha)
            xx = (x + drift * t * r) % W
            d.ellipse([(xx - r) * S, (y - r) * S, (xx + r) * S, (y + r) * S], fill=(c, c, min(255, c + 25)))

    @staticmethod
    def E(d, x, y, r, fill, outline=None, width=0, ry=None):
        ry = r if ry is None else ry
        d.ellipse([(x - r) * S, (y - ry) * S, (x + r) * S, (y + ry) * S], fill=fill, outline=outline, width=int(width * S))

    @staticmethod
    def R(d, x0, y0, x1, y1, fill, radius=0, outline=None, width=0):
        if radius:
            d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=radius * S, fill=fill, outline=outline, width=int(width * S))
        else:
            d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=fill, outline=outline, width=int(width * S))

    @staticmethod
    def P(d, pts, fill, outline=None):
        d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=outline)

    @staticmethod
    def Ln(d, pts, fill, width):
        d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint="curve")

    def text(self, img, x, y, txt, size, col=WHITE, style="ExtraBold", alpha=1.0, anchor="mm", shadow=True):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        f = font(style, size * S)
        if shadow:
            d.text((x * S + 4 * S, y * S + 5 * S), txt, font=f, fill=(0, 0, 0, int(90 * alpha)), anchor=anchor)
        d.text((x * S, y * S), txt, font=f, fill=tuple(col[:3]) + (int(255 * alpha),), anchor=anchor)
        img.alpha_composite(lay)

    def pop_text(self, img, x, y, txt, size, t, t_in, col=YEL, style="ExtraBold"):
        k = back_out((t - t_in) / 0.35)
        if k <= 0:
            return
        self.text(img, x, y, txt, max(8, size * k), col, style, alpha=clamp((t - t_in) / 0.15))

    def glow(self, img, x, y, r, col, alpha=120, blur=None):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=tuple(col[:3]) + (int(alpha),))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur((blur or r * 0.45) * S)))

    def star_shape(self, d, x, y, r, col, rot=0.0):
        pts = []
        for i in range(10):
            rr = r if i % 2 == 0 else r * 0.45
            a = -math.pi / 2 + i * math.pi / 5 + rot
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        self.P(d, pts, col)

    def qmark(self, img, x, y, size, col=YEL):
        if size > 4:
            self.text(img, x, y, "?", size, col)

    def person(self, img, p, x, y, pose="stand", face="normal", arms="down", walk=0.0, rot=0.0, scale=1.0):
        sp, (ax, ay) = p.sprite(pose, face, arms, walk, scale)
        if rot:
            sp = sp.rotate(rot, resample=Image.BICUBIC, center=(ax, ay))
        img.alpha_composite(sp, (int(x * S - ax), int(y * S - ay)))

    def paste(self, img, sp, x, y, rot=0.0, anchor=(0.5, 1.0)):
        if rot:
            sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
            anchor = (0.5, 0.5)
        img.alpha_composite(sp, (int(x * S - sp.width * anchor[0]), int(y * S - sp.height * anchor[1])))

    def cloud(self, d, x, y, k=1.0, col=(250, 252, 255)):
        for dx, dy, rr in ((0, 0, 60), (55, 10, 48), (-55, 12, 44), (25, -28, 42)):
            rr *= k
            d.ellipse([(x + dx * k - rr) * S, (y + dy * k - rr) * S, (x + dx * k + rr) * S, (y + dy * k + rr * 0.8) * S], fill=col)

    def speech_end(self, img, d, t, t0):
        """Final común: bocadillo amarillo con puntos que botan (como la gravedad)."""
        self.bg(img, "end", (28, 48, 82), (14, 24, 44))
        k = back_out((t - t0) / 0.5)
        cx, cy = 540, 980 + 16 * math.sin(t * 3)
        w_, h_ = 320 * k, 230 * k
        if k <= 0.01:
            return
        self.R(d, cx - w_, cy - h_, cx + w_, cy + h_, YEL, radius=80 * k)
        self.P(d, [(cx - 120 * k, cy + h_ - 4), (cx - 190 * k, cy + h_ + 110 * k), (cx - 20 * k, cy + h_ - 4)], YEL)
        for j in range(3):
            b = abs(math.sin(t * 5 - j * 0.6)) * 26 * k
            self.E(d, cx + (j - 1) * 150 * k, cy - b, 38 * k, (28, 40, 70))
        if self.BRAND:
            self.text(img, 540, 1450, self.BRAND, 70 * k, YEL, alpha=clamp((t - t0 - 0.3) / 0.4))

    # ───── globo terráqueo ─────
    def _globe_geo(self, R):
        key = ("geo", R)
        if key not in self._grad:
            n = int(2 * R * S)
            yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
            nx, ny = (xx - n / 2) / (n / 2), (yy - n / 2) / (n / 2)
            rr = nx ** 2 + ny ** 2
            inside = rr <= 1
            nz = np.sqrt(np.clip(1 - rr, 0, 1))
            tilt = math.radians(18)
            y2 = ny * math.cos(tilt) - nz * math.sin(tilt)
            z2 = ny * math.sin(tilt) + nz * math.cos(tilt)
            lat = np.degrees(np.arcsin(np.clip(-y2, -1, 1)))
            lon0 = np.degrees(np.arctan2(nx, z2))
            light = np.clip(0.25 + 0.75 * (nz * 0.75 - nx * 0.45 - ny * 0.25), 0.18, 1.0)
            self._grad[key] = (inside, lat, lon0, light, n)
        return self._grad[key]

    @staticmethod
    def land_mask():
        if not hasattr(Video, "_land"):
            m = np.unpackbits(np.load(os.path.join(os.path.dirname(HERE), "gravedad", "tierra_mask.npy")))[: 360 * 720].reshape(360, 720).astype(bool)
            Video._land = m
            # «profundidad» aproximada del mar: distancia a la costa (las plataformas aparecen primero)
            dist = np.zeros(m.shape, np.float32)
            cur = m.copy()
            for k in range(1, 70):
                grown = cur | np.roll(cur, 1, 0) | np.roll(cur, -1, 0) | np.roll(cur, 1, 1) | np.roll(cur, -1, 1)
                dist[grown & ~cur] = k
                cur = grown
            dist[~cur] = 70
            # suavizado + variación para que el fondo marino aparezca con formas orgánicas
            dist = np.sqrt(dist / 70.0)
            for _ in range(10):
                dist = (dist + np.roll(dist, 1, 0) + np.roll(dist, -1, 0) + np.roll(dist, 1, 1) + np.roll(dist, -1, 1)) / 5
            from PIL import Image as _I
            r0 = np.random.default_rng(9)
            nz = np.zeros(m.shape, np.float32)
            for sc_, amp in ((8, 0.10), (24, 0.05), (72, 0.025)):
                small = r0.random((max(2, 360 // sc_), max(2, 720 // sc_))).astype(np.float32)
                nz += amp * (np.asarray(_I.fromarray((small * 255).astype(np.uint8)).resize((720, 360), _I.BICUBIC), np.float32) / 255 - 0.5)
            dist = np.where(m, 0, np.clip(dist + nz, 0.01, 1))
            Video._depth = dist
            r = np.random.default_rng(5)
            Video._lights = (r.random(m.shape) < 0.08) & m
        return Video._land, Video._depth, Video._lights

    def globe(self, img, cx, cy, R, t, spin=22.0, rot0=20.0, night=0.0, ice=0.0, sea_drop=0.0, lights=0.0,
              desert=0.0, dark_ocean=0.0, glow_col=(90, 160, 255), glow_a=90):
        land, depth, lts = self.land_mask()
        inside, lat, lon0, light, n = self._globe_geo(R)
        lon = (lon0 + t * spin + rot0) % 360 - 180
        li = np.clip(((90 - lat) / 180 * 360).astype(int), 0, 359)
        lj = np.clip(((lon + 180) / 360 * 720).astype(int), 0, 719)
        L = land[li, lj]
        dp = depth[li, lj]
        ocean = np.array([45, 115, 200], np.float32) * (1 - dark_ocean) + np.array([20, 40, 70], np.float32) * dark_ocean
        green = np.array([105, 180, 95], np.float32) * (1 - desert) + np.array([205, 165, 105], np.float32) * desert
        seabed = np.array([150, 120, 90], np.float32)
        col = np.where(L[..., None], green, ocean)
        if sea_drop > 0:
            dry = (~L) & (dp < sea_drop)
            col = np.where(dry[..., None], seabed * (0.85 + 0.3 * dp[..., None]), col)
        if ice > 0:
            pol = np.abs(lat) > (90 - 90 * ice)
            col = np.where(pol[..., None], np.array([235, 242, 250], np.float32), col)
        lit = light[..., None] * (1 - 0.82 * night)
        col = col * lit
        if lights > 0:
            on = lts[li, lj] & (light < 0.55 + 0.45 * night)
            col = np.where(on[..., None], np.array([255, 210, 120], np.float32) * lights + col * (1 - lights), col)
        a = np.zeros((n, n, 4), np.uint8)
        a[..., :3] = col.clip(0, 255).astype(np.uint8)
        a[..., 3] = (inside * 255).astype(np.uint8)
        if glow_a:
            self.glow(img, cx, cy, R + 34, glow_col, glow_a, blur=30)
        img.alpha_composite(Image.fromarray(a), (int((cx - R) * S), int((cy - R) * S)))

    # ───── texto arriba (palabra a palabra, mismo estilo que la gravedad) ─────
    def chunks(self):
        if hasattr(self, "_chunks"):
            return self._chunks
        out = []
        for ln in self.nar["lines"]:
            cur = []
            for w in ln["words"]:
                cur.append(w)
                if len(cur) >= 7 or (w[0][-1:] in ",.:;!?" and len(cur) >= 3):
                    out.append(cur)
                    cur = []
            if cur:
                if out and len(cur) <= 2 and out[-1][-1][0][-1:] not in ".?!" and out[-1][0][1] >= ln["start"] - 0.01:
                    out[-1].extend(cur)
                else:
                    out.append(cur)
        self._chunks = out
        return out

    def is_key(self, w):
        return norm(w) in self.KEYWORDS

    def caption(self, out, t):
        ch = self.chunks()
        cur = None
        for i, c in enumerate(ch):
            end = ch[i + 1][0][1] if i + 1 < len(ch) else self.duration
            if c[0][1] - 0.05 <= t < end:
                cur = c
        if not cur:
            return out
        img = out.convert("RGBA")
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        size = 56
        fr, fb = font("SemiBold", size), font("ExtraBold", size)
        sp = fr.getlength(" ")
        lines, line, lw = [], [], 0.0
        for w in cur:
            ww = fb.getlength(w[0])
            if line and lw + sp + ww > 900:
                lines.append(line)
                line, lw = [], 0.0
            line.append(w)
            lw += (sp if len(line) > 1 else 0) + ww
        lines.append(line)
        y = 250
        for line in lines:
            widths = [(fb if self.is_key(w) or (a <= t < b + 0.15) else fr).getlength(w) for w, a, b in line]
            total = sum(widths) + sp * (len(line) - 1)
            x = (W - total) / 2
            for (w, a, b), ww in zip(line, widths):
                if t >= a - 0.04:
                    k = clamp((t - a + 0.04) / 0.12)
                    key = self.is_key(w)
                    f = fb if key or (a <= t < b + 0.15) else fr
                    col = YEL if key else WHITE
                    d.text((x, y), w, font=f, fill=col + (int(255 * k),), anchor="ls")
                    if key:
                        ul = ww * ease_out((t - a) / 0.3)
                        d.rounded_rectangle([x, y + 10, x + ul, y + 16], radius=3, fill=YEL + (int(255 * k),))
                x += ww + sp
            y += size * 1.25
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(lay.getchannel("A").point(lambda v: int(v * 0.55)).filter(ImageFilter.GaussianBlur(7)))
        img.alpha_composite(sh)
        img.alpha_composite(lay)
        return img.convert("RGB")

    # ───── indicador inferior ─────
    def pill(self, out, text, col=CYAN, alpha=1.0, y=1755, size=54):
        if alpha <= 0:
            return out
        img = out.convert("RGBA")
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        f = font("ExtraBold", size)
        tw = f.getlength(text)
        bw = max(420, tw + 90)
        d.rounded_rectangle([540 - bw / 2, y - 55, 540 + bw / 2, y + 55], 55, fill=(20, 30, 50, int(200 * alpha)))
        d.text((540, y), text, font=f, fill=tuple(col) + (int(255 * alpha),), anchor="mm")
        img.alpha_composite(lay)
        return img.convert("RGB")

    def hud(self, out, t):
        return out

    def overlay(self, ov, d, t, name, lt, u):
        """Rótulos fijos en pantalla (no les afecta el zoom de la cámara). Devuelve True si dibuja algo."""
        return False

    def camera(self, t, name, lt, u):
        """Cámara por defecto: empuje lento y deriva suave, para que nunca haya un plano quieto."""
        z = 1.02 + 0.06 * smooth(0, 1, u)
        return z, W / 2 + 14 * math.sin(t * 0.37), H / 2 + 10 * math.sin(t * 0.29)

    def grade(self, out, t, name):
        return out

    # ───── fotograma ─────
    def frame(self, f):
        t = f / FPS
        name, t0, t1 = self.scene_at(t)
        lt = t - t0
        u = clamp(lt / max(0.01, t1 - t0))
        img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)
        getattr(self, "s_" + name)(img, d, t, lt, u)
        z, cx, cy = self.camera(t, name, lt, u)
        for ts, k in self.shakes:
            if 0 <= t - ts < 0.6:
                a = (1 - (t - ts) / 0.6) * k
                z = max(z, 1.04)
                cx += math.sin(t * 83) * 16 * a
                cy += math.cos(t * 67) * 20 * a
        cw, ch = W / z, H / z
        cx = min(max(cx, cw / 2), W - cw / 2)
        cy = min(max(cy, ch / 2), H - ch / 2)
        out = img.convert("RGB").resize((W, H), Image.LANCZOS, box=((cx - cw / 2) * S, (cy - ch / 2) * S, (cx + cw / 2) * S, (cy + ch / 2) * S))
        for ts, _ in self.scenes[1:]:
            if 0 <= t - ts < 0.22:
                out = Image.blend(out, Image.new("RGB", (W, H), WHITE), 0.32 * (1 - (t - ts) / 0.22))
        ov = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        if self.overlay(ov, ImageDraw.Draw(ov), t, name, lt, u):
            out = out.convert("RGBA")
            out.alpha_composite(ov.resize((W, H), Image.LANCZOS))
            out = out.convert("RGB")
        out = self.grade(out, t, name)
        out = self.hud(out, t)
        out = self.caption(out, t)
        return self.brand(out) if self.BRAND else out

    def brand(self, out):
        img = out.convert("RGBA")
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        f = font("ExtraBold", 28)
        txt = " ".join(self.BRAND)
        tw = f.getlength(txt)
        d.rounded_rectangle([540 - tw / 2 - 22, 118, 540 + tw / 2 + 22, 162], 22, fill=(10, 14, 24, 120))
        d.text((540, 141), txt, font=f, fill=(255, 255, 255, 215), anchor="mm")
        d.rectangle([540 - 18, 158, 540 + 18, 162], fill=YEL + (230,))
        img.alpha_composite(lay)
        return img.convert("RGB")

    # ───── sonido: eventos (t, tipo, ganancia) ─────
    def sfx_events(self):
        return []

    def music_plan(self):
        """[(t, intensidad 0-1)] para la música ambiental."""
        return [(0, 0.5), (self.duration, 0.4)]


def render(video_cls, nar_dir, out_dir, only=None):
    nar = json.load(open(os.path.join(nar_dir, "narracion.json"), encoding="utf-8"))
    v = video_cls(nar)
    n = int(v.duration * FPS)
    os.makedirs(out_dir, exist_ok=True)
    frames = only or list(range(n))
    t0 = time.time()
    for i, f in enumerate(frames):
        v.frame(f).save(os.path.join(out_dir, f"f{f:05d}.jpg"), quality=93)
        if i % 150 == 0:
            print(f"[{v.NAME}] fotograma {f}/{n} · {time.time() - t0:.0f} s", flush=True)
    print(f"[{v.NAME}] {len(frames)} fotogramas en {time.time() - t0:.0f} s · vídeo {v.duration:.1f} s")
    return v


def schedule(video_cls, nar_dir):
    """Comprobación previa: qué escena se ve con cada frase de la narración."""
    nar = json.load(open(os.path.join(nar_dir, "narracion.json"), encoding="utf-8"))
    v = video_cls(nar)
    print(f"== {v.NAME}: {v.duration:.1f} s ==")
    for ln in nar["lines"]:
        names = sorted({v.scene_at(x)[0] for x in np.arange(ln["start"], ln["end"], 0.1)}, key=lambda s: [n for _, n in v.scenes].index(s))
        print(f"{ln['start']:5.1f}-{ln['end']:5.1f} [{ln['key']:>10}] escenas: {', '.join(names):28s} | {ln['text'][:60]}")
    return v


class City:
    """Ciudad plana reutilizable (como la de la gravedad): edificios de colores con ventanas."""

    PALETTE = [(226, 128, 96), (232, 190, 92), (110, 140, 200), (205, 90, 95), (140, 180, 120), (220, 150, 120), (120, 120, 170)]

    def __init__(self, seed=4, palette=None, ground=1460):
        r = random.Random(seed)
        pal = palette or self.PALETTE
        self.ground = ground
        self.back, self.front = [], []
        x = -200
        while x < W + 200:
            bw = r.randint(150, 230)
            self.back.append((x, bw, r.randint(500, 900), r.choice(pal)))
            x += bw + r.randint(-20, 10)
        x = -120
        while x < W + 150:
            bw = r.randint(200, 290)
            self.front.append((x, bw, r.randint(560, 980), r.choice(pal), [[r.random() < 0.5 for _ in range(6)] for _ in range(30)]))
            x += bw + r.randint(0, 14)

    def draw(self, d, t, night=0.0, frost=0.0, lights=0.0, haze=(170, 190, 215), dy=0.0, neon=False):
        s, g = S, self.ground + dy
        for x, bw, hgt, col in self.back:
            c = mix(mix(col, haze, 0.55), (25, 30, 50), night * 0.8)
            top = g - 140 - hgt
            d.rectangle([x * s, top * s, (x + bw) * s, g * s], fill=c)
            for wy in range(int(top + 40), int(g - 200), 70):
                for wx in range(x + 22, x + bw - 30, 48):
                    on = ((wx * 7 + wy * 3) % 5 == 0) and lights > 0.2
                    d.rectangle([wx * s, wy * s, (wx + 22) * s, (wy + 30) * s], fill=(255, 214, 120) if on else shade(c, 0.88))
            if frost > 0:
                d.rectangle([x * s, top * s, (x + bw) * s, (top + 14 * frost) * s], fill=(235, 242, 250))
        for x, bw, hgt, col, lit in self.front:
            c = mix(col, (30, 34, 55), night * 0.75)
            top, bot = g - hgt, g
            d.rectangle([x * s, top * s, (x + bw) * s, bot * s], fill=c)
            d.rectangle([x * s, top * s, (x + bw) * s, (top + 16) * s], fill=shade(c, 0.82))
            nx = max(2, (bw - 40) // 58)
            gap = (bw - 40 - nx * 34) / max(1, nx - 1)
            for row, wy in enumerate(range(int(top + 50), int(bot - 150), 84)):
                for cc in range(nx):
                    wx = x + 20 + cc * (34 + gap)
                    on = lit[row % 30][cc % 6]
                    day = (255, 214, 120) if on else (70, 82, 104)
                    nightc = (255, 205, 110) if (on and lights > 0) else (22, 26, 40)
                    wc = mix(day, nightc, night) if not neon else ((255, 90, 200) if on and (row + cc) % 3 == 0 else (90, 230, 255) if on else (40, 30, 70))
                    d.rectangle([wx * s, wy * s, (wx + 34) * s, (wy + 46) * s], fill=wc)
                    if frost > 0.3:
                        d.rectangle([wx * s, (wy + 40) * s, (wx + 34) * s, (wy + 46) * s], fill=(235, 242, 250))
            d.rectangle([(x + bw * 0.3) * s, (bot - 120) * s, (x + bw * 0.7) * s, bot * s], fill=shade(c, 0.65))
            if frost > 0:
                d.rounded_rectangle([(x - 4) * s, (top - 18 * frost) * s, (x + bw + 4) * s, (top + 6) * s], radius=10 * s, fill=(240, 246, 252))
        # acera y calzada
        side = mix(mix((200, 200, 204), (60, 62, 75), night), (240, 245, 250), frost)
        road = mix(mix((96, 100, 112), (35, 38, 48), night), (225, 232, 240), frost * 0.9)
        d.rectangle([0, g * s, W * s, (g + 150) * s], fill=side)
        d.rectangle([0, (g + 150) * s, W * s, (g + 168) * s], fill=shade(side, 0.8))
        d.rectangle([0, (g + 168) * s, W * s, (H + 50) * s], fill=road)
        for k in range(-1, 8):
            xx = k * 180 + 40
            d.rectangle([xx * s, (g + 300) * s, (xx + 90) * s, (g + 312) * s], fill=mix((235, 235, 235), road, frost * 0.7))
