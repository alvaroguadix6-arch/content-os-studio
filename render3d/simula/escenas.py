"""NIVEL OCULTO · Escenas con datos reales para los paquetes (historias, misterios, ciencia, curiosidades).

Sustituyen a las escenas genéricas (globo con un punto, signo de interrogación…) cuando el `visual_brief` del
paquete trae un campo `escena`. Cada escena dibuja SU dato: el lugar real en el mapa, la cifra que cuenta, la
comparación, la fecha… Todo dentro de la zona segura común de Reels/TikTok/Shorts (zona_segura.py).

    {"scene": 2, "seconds": 6, "kind": "mapa", "visual": "Bélmez (Jaén)",
     "escena": {"tipo": "mapa_espana", "punto": [-3.38, 37.73], "etiqueta": "BÉLMEZ", "resaltar": ["Jaén"]}}

Tipos (TIPOS): mapa_espana · mapa_mundo · contador · comparacion · linea_tiempo · personas · reloj · documento ·
figura (galeon, monedas, iglesia, suelo_cara, salto, frontera). Si falta un dato o el tipo no existe, el paquete
vuelve a la escena genérica de su `kind` (nunca falla el render por una escena).
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from motor import CYAN, WHITE, W, H, YEL, back_out, clamp, ease_out, font, smooth  # noqa: F401
from plano import S
from zona_segura import clamp_text

HERE = os.path.dirname(os.path.abspath(__file__))
TIPOS = {"mapa_espana", "mapa_mundo", "contador", "comparacion", "linea_tiempo", "personas", "reloj", "documento", "figura"}
FIGURAS = {"galeon", "monedas", "iglesia", "suelo_cara", "salto", "frontera"}
CAJA = (130, 640, 850, 1250)   # zona de la ilustración: bajo subtítulos y rótulo, encima de la píldora inferior
CANARIAS = ("Las Palmas", "Santa Cruz De Tenerife")
LAND = (46, 52, 128)
INK = (24, 16, 52)


def valida(spec):
    """True si la escena se puede dibujar (tipo conocido y datos mínimos)."""
    if not isinstance(spec, dict) or spec.get("tipo") not in TIPOS:
        return False
    t = spec["tipo"]
    need = {"mapa_espana": ["punto"], "mapa_mundo": ["punto"], "contador": ["valor"], "comparacion": ["items"],
            "linea_tiempo": ["hitos"], "personas": ["resaltar"], "documento": ["titular"], "reloj": ["horas"],
            "figura": ["figura"]}[t]
    if any(spec.get(k) in (None, "", []) for k in need):
        return False
    return t != "figura" or spec["figura"] in FIGURAS


def foco(spec):
    """Punto de la pantalla hacia el que se acerca la cámara (fase 2): el lugar en el mapa de España. None si no hay."""
    if not valida(spec) or spec["tipo"] != "mapa_espana":
        return None
    lon, lat = spec["punto"]
    proj, _ = _proyeccion(lon < -13 and lat < 30)
    return proj(lon, lat)


def num_es(x, dec=0):
    s = f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def _label(v, img, x, y, txt, size=48, col=YEL, fg=INK, alpha=1.0):
    """Etiqueta en píldora, recolocada dentro de la zona segura."""
    f = font("ExtraBold", size)
    w = f.getlength(txt) + 56
    x, y = clamp_text(x, y, w, size + 30)
    v.R(ImageDraw.Draw(img), x - w / 2, y - size / 2 - 16, x + w / 2, y + size / 2 + 14, col, radius=(size + 30) / 2)
    v.text(img, x, y, txt, size, fg, alpha=alpha, shadow=False)


def _fit_text(txt, size, maxw, style="ExtraBold"):
    while size > 26 and font(style, size).getlength(txt) > maxw:
        size -= 2
    return size


def _wrap(txt, size, maxw, style="ExtraBold"):
    f, lines, cur = font(style, size), [], ""
    for w in txt.split():
        nxt = (cur + " " + w).strip()
        if f.getlength(nxt) <= maxw or not cur:
            cur = nxt
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


# ───── mapa de España (provincias reales) ─────
_GEO, _MAPAS = {}, {}


def _provincias():
    if not _GEO:
        d = json.load(open(os.path.join(HERE, "quizzes", "provincias.geojson"), encoding="utf-8"))
        for f in d["features"]:
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            _GEO[f["properties"]["name"]] = [p[0] for p in polys if len(p[0]) >= 4]
    return _GEO


def _proyeccion(canarias):
    """Proyección equirrectangular ajustada a CAJA (Península y Baleares, o solo Canarias)."""
    geo = _provincias()
    names = [n for n in geo if (n in CANARIAS) == canarias and n not in ("Ceuta", "Melilla")]
    pts = [p for n in names for ring in geo[n] for p in ring]
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    cx = math.cos(math.radians((min(lats) + max(lats)) / 2))
    w, h = (max(lons) - min(lons)) * cx, max(lats) - min(lats)
    x0, y0, x1, y1 = CAJA
    k = min((x1 - x0) / w, (y1 - y0) / h)
    ox, oy = (x0 + x1) / 2 - w * k / 2, (y0 + y1) / 2 - h * k / 2
    lon0, lat0 = min(lons), max(lats)

    def proj(lon, lat):
        return ox + (lon - lon0) * k * cx, oy + (lat0 - lat) * k
    return proj, names


def _capa_mapa(canarias, resaltar):
    key = (canarias, tuple(resaltar))
    if key not in _MAPAS:
        proj, names = _proyeccion(canarias)
        geo = _provincias()
        big = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        lines = Image.new("RGBA", big.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lines)
        for n in names:
            col = YEL + (255,) if n in resaltar else LAND + (255,)
            for ring in geo[n]:
                pts = [(x * S, y * S) for x, y in (proj(lo, la) for lo, la in ring)]
                d.polygon(pts, fill=col)
                dl.line(pts + [pts[0]], fill=CYAN + (255,), width=2 * S, joint="curve")
        glow = lines.filter(ImageFilter.GaussianBlur(6 * S))
        big.alpha_composite(glow)
        big.alpha_composite(lines)
        _MAPAS[key] = big
    return _MAPAS[key]


def mapa_espana(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.3)
    lon, lat = spec["punto"]
    can = lon < -13 and lat < 30
    capa = _capa_mapa(can, [p for p in spec.get("resaltar") or [] if p in _provincias()])
    a = clamp(0.7 + lt / 0.2)          # fase 2: el mapa se ve desde el primer fotograma (nada de pantalla vacía)
    if a < 1:
        capa = capa.copy()
        capa.putalpha(capa.getchannel("A").point(lambda x: int(x * a)))
    img.alpha_composite(capa)
    proj, _ = _proyeccion(can)
    x, y = proj(lon, lat)
    k = back_out(clamp((lt - 0.1) / 0.3))
    if k > 0:
        pulse = 1 + 0.25 * math.sin(t * 6)
        v.glow(img, x, y, 70 * pulse, YEL, alpha=160)
        v.E(d, x, y, 34 * pulse * k, (255, 80, 90), outline=WHITE, width=5)
        v.E(d, x, y, 12 * k, WHITE)
    if spec.get("etiqueta") and lt > 0.3:
        # la etiqueta se aparta del punto hacia el centro para no tapar la zona resaltada
        _label(v, img, 0.4 * x + 0.6 * 540, y - 120 if y > 800 else y + 140, spec["etiqueta"].upper(), 46,
               alpha=clamp((lt - 0.3) / 0.15))


# ───── globo girado hasta el lugar real ─────
def _globo_xy(lat, dlon, tilt=math.radians(18)):
    ph, dl = math.radians(lat), math.radians(dlon)
    nx = math.cos(ph) * math.sin(dl)
    z2 = math.cos(ph) * math.cos(dl)
    ny = -math.sin(ph) * math.cos(tilt) + z2 * math.sin(tilt)
    nz = math.sin(ph) * math.sin(tilt) + z2 * math.cos(tilt)
    return nx, ny, nz


def mapa_mundo(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.6)
    lon, lat = spec["punto"]
    spin = 3.0
    girar = 30 * (1 - ease_out(clamp(lt / 0.6)))      # llega girando y se para en el lugar (rápido: retención)
    centro = lon + girar
    R = 300 * (1 + 0.08 * smooth(0, 1, u))
    cx, cy = 540, 960
    v.globe(img, cx, cy, R, 0.0, spin=spin, rot0=centro + 180, glow_col=CYAN, glow_a=80)
    nx, ny, nz = _globo_xy(lat, lon - centro)
    if nz > 0.05:
        x, y = cx + nx * R, cy + ny * R
        k = back_out(clamp((lt - 0.45) / 0.3))
        if k > 0:
            v.glow(img, x, y, 60, YEL, alpha=170)
            v.E(d, x, y, 24 * k * (1 + 0.2 * math.sin(t * 6)), (255, 80, 90), outline=WHITE, width=4)
        if spec.get("etiqueta") and lt > 0.6:
            _label(v, img, x, y - 90, spec["etiqueta"].upper(), 44, alpha=clamp((lt - 0.6) / 0.15))


# ───── cifra que cuenta ─────
def contador(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.25)
    val, desde = float(spec["valor"]), float(spec.get("desde", 0))
    dec = int(spec.get("decimales", 0))
    p = ease_out(clamp(lt / max(0.6, float(spec.get("duracion", 1.6)))))
    cur = desde + (val - desde) * p
    cx, cy, r = 540, 930, 250
    v.glow(img, cx, cy, r + 40, YEL, alpha=50)
    v.E(d, cx, cy, r, (30, 26, 70), outline=(70, 70, 130), width=18)
    # anillo de progreso
    n = int(90 * p)
    for i in range(n):
        a = -math.pi / 2 + i / 90 * 2 * math.pi
        v.E(d, cx + r * math.cos(a), cy + r * math.sin(a), 11, YEL)
    txt = (spec.get("prefijo", "") + num_es(cur, dec) + spec.get("sufijo", ""))
    v.text(img, cx, cy - 10, txt, _fit_text(txt, 150, 2 * r - 60), WHITE)
    if spec.get("unidad"):
        v.text(img, cx, cy + 105, spec["unidad"].upper(), _fit_text(spec["unidad"].upper(), 50, 2 * r - 80), YEL)


# ───── comparación en barras ─────
def comparacion(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.25)
    items = spec["items"][:5]
    mx = max(float(i["valor"]) for i in items) or 1
    n = len(items)
    h = min(150, (CAJA[3] - CAJA[1] - 40) / n)
    y0 = (CAJA[1] + CAJA[3]) / 2 - n * h / 2
    for k, it in enumerate(items):
        p = ease_out(clamp((lt - 0.15 * k) / 0.9))
        y = y0 + k * h
        col = YEL if it.get("destacar") else CYAN
        v.text(img, 140, y + 26, str(it["etiqueta"]).upper(), _fit_text(str(it["etiqueta"]).upper(), 40, 420), WHITE, anchor="lm")
        wbar = (840 - 140) * float(it["valor"]) / mx * p
        v.R(d, 140, y + 56, 140 + max(20, wbar), y + h - 22, col, radius=14)
        val = num_es(float(it["valor"]) * p, int(spec.get("decimales", 0))) + (" " + spec["unidad"] if spec.get("unidad") else "")
        if p > 0.2:
            v.text(img, 840, y + 26, val, _fit_text(val, 38, 260), col, anchor="rm")


# ───── línea de tiempo ─────
def linea_tiempo(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.25)
    hitos = spec["hitos"][:5]
    n = len(hitos)
    top, bot = CAJA[1] + 30, CAJA[3] - 30
    v.R(d, 222, top, 234, bot, (70, 70, 130), radius=6)
    prog = clamp(lt / max(0.8, 0.45 * n))
    v.R(d, 222, top, 234, top + (bot - top) * prog, YEL, radius=6)
    for k, hito in enumerate(hitos):
        y = top + (bot - top) * (k + 0.5) / n
        a = clamp((prog - (k + 0.2) / n) * n * 2)
        if a <= 0:
            continue
        v.E(d, 228, y, 22 * back_out(a), YEL, outline=WHITE, width=4)
        v.text(img, 280, y - 26, str(hito["fecha"]), _fit_text(str(hito["fecha"]), 50, 560), YEL, anchor="lm", alpha=a)
        txt = str(hito.get("texto", ""))
        if txt:
            v.text(img, 280, y + 24, txt, _fit_text(txt, 36, 570, "SemiBold"), WHITE, style="SemiBold", anchor="lm", alpha=a)


# ───── 100 personas ─────
def personas(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.25)
    total = int(spec.get("total", 100))
    cols = 10
    rows = math.ceil(total / cols)
    res = int(spec["resaltar"])
    cw, ch = 70, min(60, (CAJA[3] - CAJA[1] - 120) / rows)
    x0 = 540 - cols * cw / 2 + cw / 2
    y0 = CAJA[1] + 20
    p = clamp(lt / 1.4)
    on = int(res * ease_out(p))
    for i in range(total):
        r, c = divmod(i, cols)
        x, y = x0 + c * cw, y0 + r * ch
        col = YEL if i < on else (90, 96, 150)
        v.E(d, x, y + 8, 11, col)
        v.P(d, [(x - 15, y + 46), (x - 10, y + 22), (x + 10, y + 22), (x + 15, y + 46)], col)
    lab = spec.get("etiqueta")
    if lab:
        txt = f"{on} DE {total} · {lab.upper()}"
        v.text(img, 540, y0 + rows * ch + 50, txt, _fit_text(txt, 52, 600), YEL)


# ───── relojes ─────
def reloj(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.25)
    horas = spec["horas"][:2]
    n = len(horas)
    for k, (lab, hhmm) in enumerate(horas):
        cx = 540 if n == 1 else (330 if k == 0 else 690)
        cy, r = 920, 160 if n == 2 else 230
        hh, mm = (int(x) for x in str(hhmm).split(":"))
        p = ease_out(clamp((lt - 0.2 * k) / 1.2))
        mins = (hh % 12) * 60 + mm
        cur = mins * p
        v.glow(img, cx, cy, r + 20, YEL if k else CYAN, alpha=60)
        v.E(d, cx, cy, r, (245, 240, 230), outline=INK, width=10)
        for i in range(12):
            a = i / 12 * 2 * math.pi
            v.E(d, cx + (r - 24) * math.sin(a), cy - (r - 24) * math.cos(a), 6, INK)
        ah = cur / 720 * 2 * math.pi
        am = (cur % 60) / 60 * 2 * math.pi
        v.Ln(d, [(cx, cy), (cx + r * 0.5 * math.sin(ah), cy - r * 0.5 * math.cos(ah))], INK, 14)
        v.Ln(d, [(cx, cy), (cx + r * 0.8 * math.sin(am), cy - r * 0.8 * math.cos(am))], (220, 60, 60), 8)
        v.E(d, cx, cy, 12, INK)
        v.text(img, cx, cy + r + 50, str(lab).upper(), _fit_text(str(lab).upper(), 44, 330), YEL if k else CYAN)
        v.text(img, cx, cy - r - 50, str(hhmm), 54, WHITE, alpha=clamp((lt - 0.8) / 0.3))


# ───── portada de periódico / documento ─────
def documento(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.2)
    k = back_out(clamp(lt / 0.5))
    x0, x1, y0, y1 = 150, 850, 640, 1240
    cy = (y0 + y1) / 2
    hh = (y1 - y0) / 2 * k
    v.R(d, x0, cy - hh, x1, cy + hh, (242, 236, 222), radius=14, outline=(60, 50, 40), width=6)
    if k < 0.9:
        return
    v.text(img, 500, y0 + 60, spec.get("cabecera", "EL DIARIO").upper(), 44, INK, style="Black", shadow=False)
    v.R(d, x0 + 30, y0 + 100, x1 - 30, y0 + 106, INK)
    if spec.get("fecha"):
        v.text(img, 500, y0 + 135, str(spec["fecha"]), 30, (90, 80, 70), style="SemiBold", shadow=False)
    size, hueco = 60, (y1 - 150) - (y0 + 180)        # el titular nunca pisa las líneas de texto de abajo
    lines = _wrap(spec["titular"].upper(), size, 620, "Black")
    while len(lines) * (size + 14) > hueco and size > 32:
        size -= 4
        lines = _wrap(spec["titular"].upper(), size, 620, "Black")
    for i, ln in enumerate(lines):
        v.text(img, 500, y0 + 215 + i * (size + 14), ln, size, INK, style="Black", shadow=False, alpha=clamp((lt - 0.4 - 0.12 * i) / 0.2))
    for i in range(4):
        yy = y1 - 150 + i * 30
        v.R(d, x0 + 40, yy, x1 - 40 - (i % 2) * 140, yy + 12, (190, 180, 165), radius=4)


# ───── figuras ─────
def figura(v, spec, img, d, t, lt, u):
    globals()["f_" + spec["figura"]](v, spec, img, d, t, lt, u)


def f_galeon(v, spec, img, d, t, lt, u):
    v.bgdyn(img, (8, 20, 50), (10, 40, 80))
    v.stars(d, t, 0.4)
    hundir = spec.get("hundir")
    sink = ease_out(clamp((u - 0.25) / 0.7)) if hundir else 0.0
    cx, cy = 520, 1000 + 260 * sink
    rot = 0.08 * math.sin(t * 1.3) + 0.35 * sink

    def rp(px, py):
        return cx + px * math.cos(rot) - py * math.sin(rot), cy + px * math.sin(rot) + py * math.cos(rot)
    for mx_, h in ((-120, 330), (40, 380), (180, 280)):
        v.Ln(d, [rp(mx_, 0), rp(mx_, -h)], (70, 45, 30), 12)
        v.P(d, [rp(mx_ - 90, -h + 40), rp(mx_ + 90, -h + 40), rp(mx_ + 80, -h + 170), rp(mx_ - 80, -h + 170)], (240, 230, 205))
        v.P(d, [rp(mx_ - 70, -h + 200), rp(mx_ + 70, -h + 200), rp(mx_ + 62, -h + 300), rp(mx_ - 62, -h + 300)], (235, 222, 195))
    v.P(d, [rp(-300, -40), rp(300, -60), rp(250, 60), rp(-250, 60)], (120, 70, 40), outline=(50, 30, 20))
    v.R(d, cx - 230, cy - 25, cx + 230, cy - 12, (200, 160, 60))
    for i in range(14):   # olas por delante
        x = 110 + i * 60
        y = 1085 + 14 * math.sin(t * 2 + i)
        v.E(d, x, y, 46, (20, 70, 130))
    v.R(d, 60, 1095, 1020, 1400, (16, 58, 110))
    if sink > 0.3:
        for i in range(8):
            bx = cx - 100 + i * 30
            by = 1080 - ((t * 120 + i * 47) % 200)
            v.E(d, bx, by, 7, (180, 220, 255))


def f_monedas(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.3)
    n = int(26 * ease_out(clamp(lt / 1.4)))
    for i in range(n):
        col, row = i % 7, i // 7
        x = 540 + (col - 3) * 95 + (row % 2) * 40
        y = 1180 - row * 70 - (col % 3) * 10
        v.E(d, x, y, 46, (210, 160, 40), outline=(120, 80, 10), width=5, ry=24)
        v.E(d, x, y - 6, 38, (255, 210, 80), ry=18)
    v.glow(img, 540, 1030, 260, (255, 200, 80), alpha=70)
    if spec.get("texto"):
        v.text(img, 540, 760, spec["texto"].upper(), _fit_text(spec["texto"].upper(), 80, 700), YEL)


def f_iglesia(v, spec, img, d, t, lt, u):
    v.bgdyn(img, (40, 20, 30), (120, 60, 40))
    x, y = 540, 1240
    v.R(d, x - 230, y - 330, x + 150, y, (225, 210, 180), outline=(80, 60, 40), width=6)
    v.P(d, [(x - 250, y - 325), (x - 40, y - 460), (x + 170, y - 325)], (170, 90, 60), outline=(80, 60, 40))
    v.R(d, x + 150, y - 520, x + 280, y, (215, 200, 170), outline=(80, 60, 40), width=6)
    v.P(d, [(x + 135, y - 515), (x + 215, y - 610), (x + 295, y - 515)], (170, 90, 60), outline=(80, 60, 40))
    v.E(d, x + 215, y - 440, 26, (60, 40, 30))
    v.R(d, x - 80, y - 160, x, y, (80, 50, 35))
    v.R(d, x - 190, y - 250, x - 130, y - 170, (60, 40, 30), radius=30)
    for i in range(9):   # sacos terreros
        v.E(d, 170 + i * 82, y + 10, 46, (170, 150, 110), outline=(90, 75, 55), width=4, ry=26)
    for k in range(4):   # disparos del asedio
        ph = (t * 1.7 + k * 0.37) % 1
        if ph < 0.12:
            px = 160 + k * 200
            v.glow(img, px, 700 + (k % 2) * 60, 40, (255, 220, 120), alpha=200)


def f_suelo_cara(v, spec, img, d, t, lt, u):
    v.bgdyn(img, (12, 10, 18), (40, 34, 40))
    for r in range(9):
        for c in range(9):
            x, y = 150 + c * 80, 700 + r * 62
            g = 70 + ((r + c) % 2) * 12
            v.R(d, x, y, x + 76, y + 58, (g, g - 4, g - 10))
    a = clamp((lt - 0.4) / 2.0) * (0.85 + 0.15 * math.sin(t * 3))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    col = (20, 14, 12, int(210 * a))
    for ex in (450, 630):
        dl.ellipse([(ex - 45) * S, 900 * S, (ex + 45) * S, 960 * S], fill=col)
    dl.polygon([(540 * S, 960 * S), (510 * S, 1060 * S), (570 * S, 1060 * S)], fill=col)
    dl.ellipse([450 * S, 1100 * S, 630 * S, 1160 * S], fill=col)
    dl.ellipse([380 * S, 820 * S, 700 * S, 1230 * S], outline=(30, 20, 16, int(160 * a)), width=10 * S)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(5 * S)))
    v.glow(img, 540, 1000, 300, (200, 200, 255), alpha=int(25 * a))


def f_salto(v, spec, img, d, t, lt, u):
    v.stars(d, t, 0.5)
    v.globe(img, 540, 1680, 640, t, spin=2.0, rot0=176, glow_col=CYAN, glow_a=60)
    hop = abs(math.sin(t * 3.2))
    for i in range(9):
        x = 170 + i * 85
        y = 1040 - 120 * hop - 8 * (i % 3)
        col = YEL if i == 4 else (235, 235, 255)
        v.E(d, x, y - 70, 20, col)
        v.Ln(d, [(x, y - 50), (x, y + 10)], col, 12)
        v.Ln(d, [(x - 30, y - 60 - 20 * hop), (x, y - 35), (x + 30, y - 60 - 20 * hop)], col, 8)
        v.Ln(d, [(x - 22, y + 55), (x, y + 10), (x + 22, y + 55)], col, 9)
    if spec.get("texto"):
        v.text(img, 540, 760, spec["texto"].upper(), _fit_text(spec["texto"].upper(), 70, 700), YEL)


def f_frontera(v, spec, img, d, t, lt, u):
    v.bgdyn(img, (20, 60, 110), (10, 40, 80))
    v.stars(d, t, 0.2)
    v.P(d, [(110, 1300), (110, 860), (300, 820), (470, 900), (470, 1300)], (190, 160, 110))      # costa (país A)
    v.P(d, [(560, 1300), (560, 780), (700, 700), (820, 760), (860, 1300)], (150, 140, 120))     # peñón (país B)
    v.R(d, 470, 1120, 560, 1300, (210, 190, 140))                                              # istmo de arena
    p = ease_out(clamp((lt - 0.3) / 0.8))
    for i in range(int(8 * p)):
        y = 1120 + i * 22
        v.R(d, 508, y, 522, y + 12, (255, 80, 90))
    a, b = spec.get("lados", ["", ""])[:2] if spec.get("lados") else ("", "")
    if a:
        v.text(img, 290, 960, a.upper(), _fit_text(a.upper(), 44, 300), INK, shadow=False)
    if b:
        v.text(img, 700, 860, b.upper(), _fit_text(b.upper(), 40, 260), INK, shadow=False)
    if spec.get("texto") and lt > 0.9:
        _label(v, img, 515, 1060, spec["texto"].upper(), 50, alpha=clamp((lt - 0.9) / 0.2))


def dibujar(v, spec, img, d, t, lt, u):
    globals()[spec["tipo"]](v, spec, img, d, t, lt, u)
