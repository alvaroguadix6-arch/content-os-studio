"""NIVEL OCULTO · Quiz del mapa de España: 5 preguntas, cuenta atrás de 5 s y la provincia se ilumina con la respuesta.

    QUIZ=monumentos python quiz.py frames --narracion dir/      → fotogramas f%05d.jpg (30 fps)
    QUIZ=monumentos python montaje.py quiz --narracion dir/ --frames frames/ --out x.mp4   → MP4 con voz, música y efectos

Contenido en quizzes/<nombre>.json (pregunta, provincia, punto [lon, lat], respuesta y detalle).
Mapa: quizzes/provincias.geojson (52 provincias).
"""
from __future__ import annotations

import json
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zona_segura as ZS  # noqa: E402

W, H, S, FPS = 1080, 1920, 2, 30
YEL = (255, 206, 60)
CYAN = (120, 225, 255)
PINK = (255, 80, 140)
FONTS = "/usr/share/fonts/opentype/inter/"
_fc = {}


def font(style, size):
    k = (style, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONTS + f"Inter-{style}.otf", int(size))
    return _fc[k]


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def back(x):
    x = min(1.0, max(0.0, x))
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


# ───── maquetación (zona segura común de Reels, TikTok y Shorts: ver zona_segura.py) ─────
# arriba: marca (268) · etiqueta y tarjeta de la pregunta (298-546) · cuenta atrás / respuesta (550-675)
# abajo: mapa entre y=690 e y=1430, sin pasar de x=862 donde están los iconos de la derecha (y > 900)
BRAND_Y, CARD_Y, CD_Y = 268, 446, 612
MAP_BOX = (118, 690, 862, 1430)  # x0, y0, x1, y1 del mapa (y su recuadro de Canarias)

# ───── mapa ─────
LON0, LAT0, K = -9.3014, 43.7924, 71.0  # proyección equirrectangular (cos 40°), ajustada a MAP_BOX
CX = math.cos(math.radians(40))
MX, MY = 118, 690
# recuadro de Canarias abajo a la izquierda (donde estaría Portugal), entero dentro de la zona segura;
# antes estaba en y=1450, debajo de la interfaz de las apps
CAN = dict(lon0=-18.17, lat0=29.42, k=56.8, x=118, y=1300, w=266, h=130)


def proj(lon, lat, can=False):
    if can:
        return (CAN["x"] + 12 + (lon - CAN["lon0"]) * CAN["k"] * math.cos(math.radians(28.5)),
                CAN["y"] + 14 + (CAN["lat0"] - lat) * CAN["k"])
    return MX + (lon - LON0) * K * CX, MY + (LAT0 - lat) * K


_QCFG = json.load(open(os.path.join(HERE, "quizzes", os.environ.get("QUIZ", "monumentos") + ".json"), encoding="utf-8"))
MAPA = _QCFG.get("mapa")  # None → España con recuadro de Canarias; si no, quizzes/mapas/<mapa>.geojson ajustado a la pantalla


def fit_country(d):
    """Ajusta la proyección para que el país llene la zona segura del mapa (MAP_BOX)."""
    global LON0, LAT0, K, CX, MX, MY
    pts = [p for f in d["features"] for poly in f["geometry"]["coordinates"] for p in poly[0]]
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    CX = math.cos(math.radians((min(lats) + max(lats)) / 2))
    w, h = (max(lons) - min(lons)) * CX, max(lats) - min(lats)
    bx0, by0, bx1, by1 = MAP_BOX
    K = min((bx1 - bx0) / w, (by1 - by0) / h)
    LON0, LAT0 = min(lons), max(lats)
    MX, MY = (bx0 + bx1) / 2 - w * K / 2, (by0 + by1) / 2 - h * K / 2


def load_map():
    if MAPA:
        d = json.load(open(os.path.join(HERE, "quizzes", "mapas", MAPA + ".geojson"), encoding="utf-8"))
        fit_country(d)
    else:
        d = json.load(open(os.path.join(HERE, "quizzes", "provincias.geojson"), encoding="utf-8"))
    provs = {}
    for f in d["features"]:
        name = f["properties"]["name"]
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        can = name in ("Las Palmas", "Santa Cruz De Tenerife")
        rings = []
        for poly in polys:
            ring = poly[0]
            if len(ring) < 4:
                continue
            rings.append([proj(lo, la, can) for lo, la in ring])
        provs[name] = rings
    return provs


PROVS = load_map()


def base_map():
    """Mapa fijo (provincias en azul con bordes cian y brillo), dibujado a 2× y reducido."""
    big = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = CAN
    if not MAPA:
        d.rounded_rectangle([c["x"] * S, c["y"] * S, (c["x"] + c["w"]) * S, (c["y"] + c["h"]) * S], 18 * S,
                            fill=(30, 26, 80, 200), outline=(110, 150, 230, 200), width=3 * S)
    for rings in PROVS.values():
        for r in rings:
            d.polygon([(x * S, y * S) for x, y in r], fill=(46, 52, 128, 255))
    lines = Image.new("RGBA", big.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lines)
    for rings in PROVS.values():
        for r in rings:
            dl.line([(x * S, y * S) for x, y in r] + [(r[0][0] * S, r[0][1] * S)], fill=CYAN + (255,), width=3 * S, joint="curve")
    glow = lines.filter(ImageFilter.GaussianBlur(7 * S))
    big.alpha_composite(glow)
    big.alpha_composite(glow)
    big.alpha_composite(lines)
    return big.resize((W, H), Image.LANCZOS)


_hl = {}


def highlight(name):
    """Capa de la provincia iluminada en amarillo (con brillo)."""
    if isinstance(name, list):
        name = tuple(name)
    if name not in _hl:
        big = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        for r in [r for n in (name if isinstance(name, tuple) else (name,)) for r in PROVS[n]]:
            pts = [(x * S, y * S) for x, y in r]
            d.polygon(pts, fill=YEL + (255,))
            d.line(pts + [pts[0]], fill=(255, 250, 220, 255), width=3 * S, joint="curve")
        glow = big.filter(ImageFilter.GaussianBlur(14 * S))
        out = Image.new("RGBA", big.size, (0, 0, 0, 0))
        out.alpha_composite(glow)
        out.alpha_composite(glow)
        out.alpha_composite(big)
        _hl[name] = out.resize((W, H), Image.LANCZOS)
    return _hl[name]


def bbox(name):
    pts = np.array([p for r in PROVS[name] for p in r])
    return pts.min(0), pts.max(0)


# ───── vídeo ─────
class Video:
    def __init__(self, nar, quiz=None):
        self.quiz = quiz or os.environ.get("QUIZ", "monumentos")
        self.Q = json.load(open(os.path.join(HERE, "quizzes", self.quiz + ".json"), encoding="utf-8"))
        L = {l["key"]: l for l in nar["lines"]}
        self.L = L
        self.duration = L["outro"]["end"] + 1.4
        self.scenes = [(0.0, "intro")] + [(L[f"q{i}"]["start"] - 0.15, f"q{i}") for i in range(1, 6)] + [(L["outro"]["start"] - 0.1, "outro")]
        self.base = None

    # audio (montaje.py)
    def music_plan(self):
        p = [(0, 0.3)]
        for i in range(1, 6):
            p += [(self.L[f"q{i}"]["end"], 0.75), (self.L[f"a{i}"]["start"] - 0.05, 0.85), (self.L[f"a{i}"]["start"] + 0.3, 0.45)]
        return p + [(self.duration, 0.3)]

    def sfx_events(self):
        ev = []
        if self.Q.get("gancho"):
            ev += [(0.08 + k * 0.22, "boom" if k == 0 else "pop", 0.55 if k == 0 else 0.45) for k in range(len(self.Q["gancho"]))]
        sabias = self.Q.get("modo") == "sabias"
        for i in range(1, 6):
            t0, t1 = self.L[f"q{i}"]["end"], self.L[f"a{i}"]["start"]
            for k in ([] if sabias else range(5)):
                ts = t0 + k * (t1 - t0) / 5
                ev.append((ts, "tick", 0.9))
                ev.append((ts, "beep", 0.12 if k < 4 else 0.22))
            ev.append((t1 - 0.05, "shimmer", 0.5))
            ev.append((t1, "pop", 0.6))
        return ev

    def bg(self, t):
        y = np.linspace(0, 1, H)[:, None]
        x = np.linspace(-1, 1, W)[None, :]
        top, bot = np.array([34, 18, 78]), np.array([60, 26, 120])
        img = top[None, None, :] * (1 - y[..., None]) + bot[None, None, :] * y[..., None]
        for k, (sp, ph, col) in enumerate([(0.35, 0.0, (120, 60, 220)), (0.25, 2.0, (40, 80, 200))]):  # haces de luz que se mueven
            cx = 0.55 * math.sin(t * sp + ph)
            beam = np.exp(-((x - cx - 0.25 * (y - 0.5)) ** 2) / 0.05) * (0.35 + 0.25 * math.sin(t * 0.7 + k))
            img = img + beam[..., None] * np.array(col)[None, None, :] * 0.5
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")

    def fondo_portada(self):
        """Fondo limpio para la portada: el mapa sin tarjetas, sin textos y sin iluminar respuestas (no hace spoiler)."""
        img = self.bg(1.0)
        img.alpha_composite(base_map())
        return img.convert("RGB")

    def current(self, t):
        cur = None
        for i in range(1, 6):
            if t >= self.L[f"q{i}"]["start"] - 0.15:
                cur = i
        if t >= self.L["outro"]["start"] - 0.1:
            return "outro"
        return cur

    def frame(self, t):
        if self.base is None:
            self.base = base_map()
        img = self.bg(t)
        cur = self.current(t)
        lay = self.base
        if isinstance(cur, int):
            lay = self.map_answer(t, cur)
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
        if cur is None:
            self.intro(img, d, t)
        elif cur == "outro":
            self.outro(img, d, t)
        else:
            self.question(img, d, t, cur)
        d.text((540, BRAND_Y), "N I V E L   O C U L T O", font=font("ExtraBold", 26), fill=(190, 170, 240), anchor="mm")
        return img.convert("RGB")

    def card(self, img, d, t0, t, label, text, size=58):
        a = back((t - t0) / 0.45)
        cy = CARD_Y - (1 - a) * 260
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([118, cy - 100 + 10, 962, cy + 100 + 14], 34, fill=(0, 0, 0, 110))
        lay = lay.filter(ImageFilter.GaussianBlur(10))
        img.alpha_composite(lay)
        d.rounded_rectangle([118, cy - 100, 962, cy + 100], 34, fill=(246, 244, 255), outline=YEL, width=7)
        lines = wrap(text, font("ExtraBold", size), 780)
        while len(lines) > 3 or (len(lines) * size * 1.18 > 180 and size > 36):
            size -= 4
            lines = wrap(text, font("ExtraBold", size), 780)
        lh = size * 1.18
        for k, ln in enumerate(lines):
            d.text((540, cy + (k - (len(lines) - 1) / 2) * lh), ln, font=font("ExtraBold", size), fill=(32, 22, 70), anchor="mm")
        f = font("ExtraBold", 32)
        w = d.textlength(label, font=f) + 60
        d.rounded_rectangle([540 - w / 2, cy - 148, 540 + w / 2, cy - 96], 26, fill=PINK)
        d.text((540, cy - 122), label, font=f, fill=(255, 255, 255), anchor="mm")

    def gancho(self, img, t):
        """Título gancho a pantalla completa: líneas que entran de golpe (las *marcadas* en amarillo)."""
        lines = self.Q["gancho"]
        dim = Image.new("RGBA", img.size, (10, 4, 30, int(150 * min(1, t / 0.2))))
        img.alpha_composite(dim)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        sizes = []
        for ln in lines:  # bajo y=900 están los iconos de la derecha: ancho máximo 644 (centrado entre 218 y 862)
            txt = ln.strip("*")
            sz = 140
            while sz > 50 and (dl.textlength(txt, font=font("Black", sz)) + 20 > 644 or sz * 1.12 * len(lines) > 720):
                sz -= 4
            sizes.append(sz)
        total = sum(s * 1.12 for s in sizes)
        y = 1060 - total / 2
        for k, (ln, sz) in enumerate(zip(lines, sizes)):
            u = (t - 0.08 - k * 0.22) / 0.32
            if u <= 0:
                y += sz * 1.12
                continue
            sc = 1 + 0.9 * (1 - back(u)) if u < 1 else 1.0
            col = YEL if ln.startswith("*") else (255, 255, 255)
            txt = ln.strip("*")
            fs = font("Black", max(8, int(sz * sc)))
            shake = 6 * math.sin(t * 60) * max(0, 1 - u) if u < 1 else 0
            dl.text((540 + shake, y + sz * 0.56), txt, font=fs, fill=col, anchor="mm", stroke_width=10, stroke_fill=(24, 10, 60))
            y += sz * 1.12
        img.alpha_composite(lay)

    def intro(self, img, d, t):
        a = back(t / 0.5)
        tema = self.Q["tema"]
        sabias = self.Q.get("modo") == "sabias"
        if self.Q.get("gancho"):
            rng = np.random.default_rng(int(t * 8))
            names = list(PROVS)
            img.alpha_composite(_alpha(highlight(names[rng.integers(len(names))]), 0.9))
            self.gancho(img, t)
            f = font("Black", int(96 * a) + 1)
            d.text((540, CD_Y - 40), "5 DATOS" if sabias else "5 PREGUNTAS", font=f, fill=YEL, anchor="mm", stroke_width=6, stroke_fill=(30, 16, 70))
            return
        self.card(img, d, 0.0, t, self.Q.get("etiqueta", "QUIZ DE " + self.Q.get("pais", "ESPAÑA")),
                  self.Q.get("titulo", f"{tema}: ¿cuántas aciertas?"), 60)
        # mapa que «late» con provincias al azar iluminándose
        rng = np.random.default_rng(int(t * 6))
        names = list(PROVS)
        nm = names[rng.integers(len(names))]
        if t > 0.6:
            h = highlight(nm)
            img.alpha_composite(_alpha(h, 0.85))
        f = font("Black", int(96 * a) + 1)
        d.text((540, CD_Y + 10), "5 DATOS" if sabias else "5 PREGUNTAS", font=f, fill=YEL, anchor="mm", stroke_width=6, stroke_fill=(30, 16, 70))

    def outro(self, img, d, t):
        t0 = self.L["outro"]["start"] - 0.1
        if self.Q.get("modo") == "sabias":
            self.card(img, d, t0, t, "¿CUÁL NO SABÍAS?", "Dímelo en los comentarios", 62)
            return
        self.card(img, d, t0, t, "¿CUÁNTAS HAS ACERTADO?", "Dímelo en los comentarios", 62)
        a = back((t - t0 - 0.3) / 0.5)
        y = CD_Y
        for k, n in enumerate("012345"):
            x = 540 + (k - 2.5) * 122
            r = 48 * a
            if r > 1:
                d.ellipse([x - r, y - r, x + r, y + r], fill=(46, 52, 128), outline=YEL, width=5)
                d.text((x, y), n, font=font("Black", max(1, int(60 * a))), fill=(255, 255, 255), anchor="mm")
        d.text((540, CD_Y + 90), "/ 5", font=font("ExtraBold", 40), fill=(220, 210, 255), anchor="mm", stroke_width=4, stroke_fill=(30, 16, 70))

    def map_answer(self, t, i):
        """Mapa con la región iluminada; en países con regiones pequeñas, zoom hacia el punto al revelar."""
        q = self.Q["preguntas"][i - 1]
        ans = self.L[f"a{i}"]["start"]
        if t < ans - 0.05:
            return self.base
        u = t - ans + 0.05
        lay = self.base.copy()
        h = highlight(q["prov"])
        a = min(1.0, u / 0.2)
        lay.alpha_composite(h if a >= 1 else _alpha(h, a))
        fl = 1 + 0.6 * max(0, 1 - u / 0.35)  # destello inicial
        if fl > 1.001:
            lay.alpha_composite(_alpha(h, (fl - 1) * 0.8))
        if not MAPA:
            return lay
        names = q["prov"] if isinstance(q["prov"], list) else [q["prov"]]
        pts = np.array([p for n in names for r in PROVS[n] for p in r])
        size = max(pts.max(0) - pts.min(0))
        Z = min(2.6, max(1.0, 260 / max(size, 1)))
        if Z < 1.05:
            return lay
        nt = self.L[f"q{i + 1}"]["start"] - 0.15 if i < 5 else self.L["outro"]["start"] - 0.1
        env = min(ease((u - 0.1) / 0.7), ease((nt - t) / 0.45))
        z = 1 + (Z - 1) * env
        if z < 1.005:
            return lay
        px, py = proj(*q["punto"])
        lay = lay.transform(lay.size, Image.AFFINE, (1 / z, 0, px - px / z, 0, 1 / z, py - py / z), resample=Image.BILINEAR)
        yy = np.arange(H)[:, None]
        m = np.clip((yy - MAP_BOX[1] + 40) / 60, 0, 1) * np.clip((MAP_BOX[3] + 10 - yy) / 60, 0, 1)  # bordes suaves
        lay.putalpha(Image.fromarray((np.asarray(lay.getchannel("A"), np.float32) * m).astype(np.uint8)))
        return lay

    def question(self, img, d, t, i):
        q = self.Q["preguntas"][i - 1]
        qs, qe = self.L[f"q{i}"]["start"] - 0.15, self.L[f"q{i}"]["end"]
        ans = self.L[f"a{i}"]["start"]
        sabias = self.Q.get("modo") == "sabias"
        self.card(img, d, qs, t, f"DATO {i}/5" if sabias else f"PREGUNTA {i}/5", q["q"], 58 if len(q["q"]) < 44 else 52 if len(q["q"]) < 70 else 46)
        # cuenta atrás
        cy = CD_Y
        if t < ans + 0.2 and not sabias:
            a = back((t - qs - 0.2) / 0.4)
            r = 56 * a
            if r > 2:
                d.ellipse([540 - r - 8, cy - r - 8, 540 + r + 8, cy + r + 8], fill=(20, 12, 50))
                d.ellipse([540 - r, cy - r, 540 + r, cy + r], outline=(70, 62, 140), width=12)
                frac = 0.0 if t < qe else min(1.0, (t - qe) / max(0.1, ans - qe))
                n = 5 if t < qe else max(1, 5 - int(frac * 5))
                col = (90, 230, 120) if n >= 4 else YEL if n >= 2 else (255, 80, 80)
                d.arc([540 - r, cy - r, 540 + r, cy + r], -90, -90 + 360 * (1 - frac), fill=col, width=12)
                ph = ((t - qe) * 5 / max(0.1, ans - qe)) % 1 if t >= qe else 0.5
                sc = 1 + 0.25 * max(0, 1 - ph * 4)
                d.text((540, cy + 2), str(n), font=font("Black", int(66 * sc * a) + 1), fill=(255, 255, 255), anchor="mm")
        # respuesta
        if t >= ans - 0.05:
            u = t - ans + 0.05
            can = not MAPA and q["prov"] in ("Las Palmas", "Santa Cruz De Tenerife")
            px, py = proj(*q["punto"], can=can)
            by = CD_Y  # la respuesta sustituye a la cuenta atrás, encima del mapa
            ln = ease((u - 0.15) / 0.4)
            if ln > 0:  # línea del punto a la caja de la respuesta (en diagonal si la provincia está en un borde)
                tx, ty = min(max(px, 400), 680), by + 62
                d.line([(px, py), (px + (tx - px) * ln, py + (ty - py) * ln)], fill=(255, 240, 190), width=5)
            pr = 15 * back(u / 0.3)
            with ZS.exento():  # el punto marca el lugar exacto del mapa (puede estar en su borde)
                d.ellipse([px - pr - 5, py - pr - 5, px + pr + 5, py + pr + 5], fill=(40, 20, 80))
                d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(255, 255, 255))
            b = back((u - 0.35) / 0.4)
            if b > 0.02:
                s1, s2 = 64, 34  # se encoge si la respuesta es larga: la caja nunca pasa de 844 px (zona segura)
                while s1 > 36 and max(d.textlength(q["respuesta"], font=font("Black", s1)), d.textlength(q["detalle"], font=font("SemiBold", s2))) + 80 > 844:
                    s1, s2 = s1 - 4, max(24, s2 - 2)
                f1 = font("Black", int(s1 * b) + 1)
                f2 = font("SemiBold", int(s2 * b) + 1)
                w = min(844, max(d.textlength(q["respuesta"], font=f1), d.textlength(q["detalle"], font=f2)) + 80)
                bh = 124 * b
                d.rounded_rectangle([540 - w / 2, by - bh / 2, 540 + w / 2, by + bh / 2], 30, fill=YEL, outline=(255, 250, 225), width=5)
                d.text((540, by - 20 * b), q["respuesta"], font=f1, fill=(30, 18, 60), anchor="mm")
                d.text((540, by + 36 * b), q["detalle"], font=f2, fill=(70, 50, 100), anchor="mm")


def _alpha(im, a):
    a = max(0.0, min(1.0, a))
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    dd = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for w in words:
        test = (cur + " " + w).strip()
        if dd.textlength(test, font=f) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


VIDEO = Video
MOOD = "alegre"
BPM = 100

_V = None


def _init(nar):
    global _V
    _V = Video(nar)


def _render(args):
    k, out = args
    _V.frame(k / FPS).save(os.path.join(out, f"f{k:05d}.jpg"), quality=92)
    return k


if __name__ == "__main__":
    out, nard = sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]
    only = [float(x) for x in os.environ.get("SOLO", "").split(",") if x]
    nar = json.load(open(os.path.join(nard, "narracion.json"), encoding="utf-8"))
    v = Video(nar)
    os.makedirs(out, exist_ok=True)
    if only:
        for ts in only:
            v.frame(ts).save(os.path.join(out, f"t{ts:05.1f}.jpg"), quality=90)
        sys.exit()
    n = int(v.duration * FPS)
    with Pool(4, _init, (nar,)) as p:
        for k in p.imap_unordered(_render, [(k, out) for k in range(n)], chunksize=8):
            if k % 300 == 0:
                print("frame", k, "/", n, flush=True)
    print("frames listos", n)
