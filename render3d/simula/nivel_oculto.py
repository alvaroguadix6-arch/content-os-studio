"""NIVEL OCULTO · Adaptador de paquetes (instagram-agent → motor de simulaciones).

Convierte un paquete aprobado de `paquetes/AAAA-Www/<id>.json` en un vídeo con la MISMA plantilla que el resto
de simulaciones (motor.py): ilustración plana a doble resolución, cámara siempre en movimiento, destellos en los
cortes, texto palabra a palabra con palabras clave en amarillo, marca discreta y zona segura de Reels.

Cada frase del guion es una escena (un corte). El tipo de escena sale del `visual_brief` del paquete
(mapa, simulacion, animacion, archivo, grafico, texto) y los rótulos de `on_screen_text` aparecen en su frase.

    python nivel_oculto.py guion paquetes/2026-W48/x.json voz/guion.json        # guion para la voz (números en letra)
    python ../gravedad/voz.py voz/ --guion voz/guion.json --motor kokoro --voz em_alex
    PAQUETE=paquetes/2026-W48/x.json python nivel_oculto.py plan voz/            # escena por frase
    PAQUETE=paquetes/2026-W48/x.json python nivel_oculto.py render voz/ frames/
    PAQUETE=paquetes/2026-W48/x.json python montaje.py nivel_oculto --narracion voz/ --frames frames/ --out x.mp4

Sin voz (vista previa o pruebas): `python nivel_oculto.py sintetica <paquete> <dir>` crea un narracion.json con
tiempos estimados a 170 palabras por minuto. Portada del reel: `python nivel_oculto.py portada <paquete> portada.jpg ["TÍTULO CORTO"]`.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from motor import CYAN, RED, WHITE, W, YEL, City, Video, back_out, clamp, ease_out, font, norm, render, schedule, smooth  # noqa: E402,F401
from zona_segura import BOTTOM, TOP_TEXT  # noqa: E402

WPM = 170
ALLOWED_KINDS = {"mapa", "simulacion", "animacion", "archivo", "grafico", "texto"}

# Paleta por pilar (degradado arriba/abajo) y ambiente musical de montaje.py
PALETTE = {
    "misterios": ((10, 8, 28), (58, 20, 72)),
    "ciencia": ((4, 14, 40), (12, 64, 116)),
    "historia": ((36, 22, 10), (118, 70, 32)),
    "geografia": ((4, 36, 56), (18, 106, 118)),
    "simulacion": ((2, 4, 20), (34, 30, 92)),
    "curiosidades": ((28, 10, 48), (176, 62, 92)),
}
MOODS = {"misterios": "suspense", "historia": "epico", "ciencia": "espacio", "simulacion": "espacio",
         "geografia": "epico", "curiosidades": "alegre"}

# ───────────────────────── números en letra (para que la voz los lea bien) ─────────────────────────
_U = ("cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete "
      "dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco veintiséis veintisiete "
      "veintiocho veintinueve").split()
_D = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_C = {1: "cien", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos",
      7: "setecientos", 8: "ochocientos", 9: "novecientos"}


def _apocope(s):
    return re.sub(r"veintiuno$", "veintiún", re.sub(r"(?<!veinti)uno$", "un", s))


def num_es(n: int) -> str:
    if n < 30:
        return _U[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _D[d] + (" y " + _U[u] if u else "")
    if n < 1000:
        c, r = divmod(n, 100)
        return ("ciento" if c == 1 and r else _C[c]) + (" " + num_es(r) if r else "")
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        return ("mil" if m == 1 else _apocope(num_es(m)) + " mil") + (" " + num_es(r) if r else "")
    m, r = divmod(n, 1_000_000)
    return ("un millón" if m == 1 else _apocope(num_es(m)) + " millones") + (" " + num_es(r) if r else "")


def spoken(text: str) -> str:
    """Texto para la voz: números en letra, símbolos leídos, sin caracteres que la voz pronuncie raro."""
    t = text.replace("%", " por ciento").replace("$", " dólares").replace("€", " euros")
    t = re.sub(r"\b(\d{1,3}(?:\.\d{3})+)\b", lambda m: m.group(1).replace(".", ""), t)          # 200.000 → 200000
    t = re.sub(r"\b(\d+),(\d+)\b", lambda m: f"{num_es(int(m.group(1)))} coma {' '.join(num_es(int(c)) for c in m.group(2))}", t)
    t = re.sub(r"\b\d+\b", lambda m: num_es(int(m.group(0))), t)
    t = re.sub(r"\bkm\b", "kilómetros", t)
    t = re.sub(r"\s+", " ", t).replace(" .", ".").replace(" ,", ",").strip()
    return t[:1].upper() + t[1:] if text[:1].isdigit() else t


# ───────────────────────── paquete → guion ─────────────────────────
def load_package(path):
    with open(path, encoding="utf-8") as fh:
        pkg = json.load(fh)
    script = pkg.get("script") or []
    if not script or not all(isinstance(s, str) and s.strip() for s in script):
        raise ValueError("el paquete no tiene guion")
    return pkg


def keys_for(pkg):
    return [f"b{i + 1:02d}" for i in range(len(pkg["script"]))]


def guion_for_voice(pkg):
    keys = keys_for(pkg)
    lines = [[k, spoken(s)] for k, s in zip(keys, pkg["script"])]
    pausas = {k: (0.32 if i == 0 else 0.0 if i == len(keys) - 1 else 0.18) for i, k in enumerate(keys)}
    return {"guion": lines, "pausas": pausas}


def estimated_starts(script, wpm=WPM):
    t, out = 0.0, []
    for line in script:
        out.append(t)
        t += max(0.8, len(line.split()) / wpm * 60)
    return out, t


def beat_layout(pkg):
    """Tipo de escena y rótulo de cada frase, a partir del brief visual y de on_screen_text."""
    script = pkg["script"]
    starts, total = estimated_starts(script)
    brief = pkg.get("visual_brief") or []
    bounds, acc = [], 0.0
    for sc in brief:
        bounds.append((acc, acc + float(sc.get("seconds", 0)), sc.get("kind") or "texto"))
        acc += float(sc.get("seconds", 0))
    kinds = []
    for st in starts:
        k = next((kd for a, b, kd in bounds if a <= st < b), bounds[-1][2] if bounds else "texto")
        kinds.append(k if k in ALLOWED_KINDS else "texto")
    cards = [None] * len(script)
    for card in pkg.get("on_screen_text") or []:
        at = float(card.get("at", 0))
        i = min(range(len(starts)), key=lambda j: abs(starts[j] - at))
        cards[i] = str(card.get("text", ""))[:40]
    return kinds, cards


METEOR_RE = re.compile(r"meteor|asteroid|bola de fuego|del espacio", re.I)
HOUSE_RE = re.compile(r"techo|casa|casera|sof[aá]|siesta", re.I)
IMPACT_RE = re.compile(r"atraviesa|impacto|crac|golpea|cay[oó] encima", re.I)
ROCK_RE = re.compile(r"\bkg\b|kilos|roca|piedra|trozo", re.I)


def beat_motifs(pkg):
    """Motivo visual de cada frase según el guion y el brief: «meteorito» (con o sin impacto) y «roca»."""
    text_all = " ".join(pkg["script"]) + " " + " ".join(v.get("visual", "") for v in pkg.get("visual_brief") or [])
    meteor_story = bool(re.search(r"meteor|asteroid", text_all, re.I))
    kinds, cards = beat_layout(pkg)
    out = []
    for line, kind, card in zip(pkg["script"], kinds, cards):
        txt, m = line + " " + (card or ""), None
        if meteor_story:
            if IMPACT_RE.search(txt):
                m = "impacto"
            elif kind == "mapa":
                m = None                      # los mapas (dónde ocurrió) se mantienen
            elif METEOR_RE.search(txt):
                m = "meteorito"
            elif ROCK_RE.search(txt):
                m = "roca"
            elif HOUSE_RE.search(txt) or kind in ("simulacion", "animacion", "texto"):
                m = "casa"                    # en una historia de meteorito, la casa da continuidad visual
        out.append(m)
    return out


def synthetic_narration(pkg, wpm=WPM):
    """narracion.json con tiempos estimados (sin audio): para planes, vistas previas y pruebas."""
    g = guion_for_voice(pkg)
    t, lines = 0.0, []
    for key, text in g["guion"]:
        words = text.split()
        dur = max(0.8, len(words) / wpm * 60)
        step = dur / max(1, len(words))
        lines.append({"key": key, "text": text, "start": round(t, 3), "end": round(t + dur, 3),
                      "words": [[w, round(t + i * step, 3), round(t + (i + 1) * step, 3)] for i, w in enumerate(words)]})
        t += dur + g["pausas"][key]
    return {"lines": lines, "duration": round(t, 3)}


# ───────────────────────── vídeo ─────────────────────────
def make_video(pkg):
    kinds, cards = beat_layout(pkg)
    pillar = pkg.get("pillar") or "curiosidades"
    top, bottom = PALETTE.get(pillar, PALETTE["curiosidades"])
    keys = keys_for(pkg)
    label = {"misterios": "MISTERIO", "ciencia": "CIENCIA", "historia": "HISTORIA", "geografia": "GEOGRAFÍA",
             "simulacion": "SIMULACIÓN", "curiosidades": "CURIOSIDAD"}.get(pillar, "NIVEL OCULTO")
    keywords = set()
    for c in cards:
        for w in (c or "").split():
            if len(norm(w)) > 3:
                keywords.add(norm(w))
    for s in pkg["script"]:
        for n in re.findall(r"\d[\d.,]*", s):
            keywords.update(norm(x) for x in spoken(n).split() if x not in ("y", "coma"))

    class Paquete(Video):
        NAME = pkg.get("id", "nivel-oculto")
        BRAND = "NIVEL OCULTO"
        KEYWORDS = keywords
        END_HOLD = 1.0

        def setup(self):
            self.kinds = dict(zip(keys, kinds))
            self.cards = dict(zip(keys, cards))
            self.order = {k: i for i, k in enumerate(keys)}
            self.city = City(seed=7)
            self.numbers = {k: (re.findall(r"\d[\d.,]*", s) or [None])[0] for k, s in zip(keys, pkg["script"])}
            self.motifs = dict(zip(keys, beat_motifs(pkg)))
            rr = __import__("random").Random(11)
            self.rock = [(a, 1 + rr.uniform(-0.18, 0.14)) for a in [i * 2 * math.pi / 14 for i in range(14)]]
            self.craters = [(rr.uniform(-0.45, 0.4), rr.uniform(-0.4, 0.4), rr.uniform(0.08, 0.17)) for _ in range(5)]

        def build_scenes(self):
            return [(0.0 if i == 0 else self.start(k), k) for i, k in enumerate(keys) if k in self.L]

        def __getattr__(self, name):
            if name.startswith("s_"):
                key = name[2:]
                return lambda img, d, t, lt, u: self.draw_beat(key, img, d, t, lt, u)
            raise AttributeError(name)

        # ── escenas ──
        def draw_beat(self, key, img, d, t, lt, u):
            kind = self.kinds.get(key, "texto")
            motif = self.motifs.get(key)
            if motif in ("meteorito", "impacto"):
                self.bg(img, "noche", (4, 6, 22), (24, 30, 70))
                return self.m_meteorito(key, img, d, t, lt, u, impact=motif == "impacto")
            self.bg(img, kind, top, bottom)
            if motif == "roca":
                return self.m_roca(key, img, d, t, lt, u)
            if motif == "casa":
                self.bg(img, "noche", (4, 6, 22), (24, 30, 70))
                self.stars(d, t, 0.8)
                self.R(d, -20, 1330, W + 20, 1960, (34, 44, 40))
                return self.house(d, 540, 1330, lit=1.0, crack=0.6 if "techo" in pkg["script"][self.order[key]].lower() else 0.0)
            getattr(self, "k_" + kind)(key, img, d, t, lt, u)

        def k_mapa(self, key, img, d, t, lt, u):
            self.stars(d, t, 0.5)
            R = 330 * (1 + 0.06 * smooth(0, 1, u))
            self.globe(img, 540, 930, R, t, spin=14.0, glow_col=CYAN, glow_a=80)
            self.glow(img, 560, 880, 40, YEL, alpha=170)
            self.E(d, 560, 880, 14 + 4 * math.sin(t * 6), YEL)

        def k_simulacion(self, key, img, d, t, lt, u):
            self.stars(d, t, 1.0, drift=8.0)
            self.glow(img, 540, 940, 300, CYAN, alpha=70)
            self.E(d, 540, 940, 250, (30, 60, 120), outline=CYAN, width=6)
            for i in range(3):
                a = t * (0.8 + 0.3 * i) + i * 2.1
                x, y = 540 + 330 * math.cos(a), 940 + 120 * math.sin(a)
                self.E(d, x, y, 18 - 4 * i, YEL if i == 0 else WHITE)
            y = 640 + (u ** 1.6) * 600
            self.glow(img, 540, y, 50, YEL, alpha=150)
            self.E(d, 540, y, 22, WHITE)

        def k_animacion(self, key, img, d, t, lt, u):
            self.stars(d, t, 0.35)
            self.city.draw(d, t, night=0.6, lights=0.7, dy=0.0)
            self.glow(img, 540, 820, 160, YEL, alpha=60)
            self.qmark(img, 540, 820, 260 * back_out(clamp(lt / 0.5)), YEL)

        def k_archivo(self, key, img, d, t, lt, u):
            self.R(d, 190, 560, 890, 1260, (236, 222, 190), radius=18, outline=(90, 60, 30), width=8)
            self.R(d, 240, 610, 840, 1060, (190, 170, 140), radius=8)
            for i in range(5):
                self.R(d, 240, 1100 + i * 28, 840 - (i % 3) * 120, 1112 + i * 28, (120, 96, 70), radius=4)
            self.glow(img, 540, 830, 120, (255, 230, 170), alpha=60)
            self.qmark(img, 540, 840, 180, (90, 60, 30))

        def k_grafico(self, key, img, d, t, lt, u):
            self.stars(d, t, 0.25)
            n = self.numbers.get(key)
            if not n:                       # sin cifra no hay gráfico: nada de barras sin significado
                return self.k_texto(key, img, d, t, lt, u)
            for i in range(6):
                h = 60 + 52 * i * ease_out(clamp(lt / 0.8 - i * 0.08))
                self.R(d, 230 + i * 110, 1250 - h, 300 + i * 110, 1250, CYAN if i < 5 else YEL, radius=10)
            if n and (self.cards.get(key) or "").replace(" ", "")[: len(n)] != n:
                self.pop_text(img, 540, 830, n, 190, t, self.start(key) + 0.1, col=YEL)


        def k_texto(self, key, img, d, t, lt, u):
            self.stars(d, t, 0.4)
            self.glow(img, 540, 900, 260, YEL, alpha=40)
            self.qmark(img, 540, 900, 300 * back_out(clamp(lt / 0.5)), (255, 255, 255))

        # ── motivo: meteorito sobre una casa de los años 50 ──
        def house(self, d, x, y, lit=0.8, crack=0.0):
            self.R(d, x - 230, y - 250, x + 230, y, (150, 110, 90), outline=(40, 30, 30), width=6)
            self.P(d, [(x - 270, y - 245), (x, y - 430), (x + 270, y - 245)], (110, 50, 45), outline=(40, 30, 30))
            win = (255, 215, 120) if lit > 0.5 else (60, 70, 100)
            for wx in (x - 150, x + 70):
                self.R(d, wx, y - 200, wx + 80, y - 120, win, outline=(40, 30, 30), width=5)
            self.R(d, x - 40, y - 140, x + 40, y, (80, 50, 40), outline=(40, 30, 30), width=5)
            if crack > 0:
                cx, cy = x + 20, y - 360
                for ang in (-2.4, -1.6, -0.9, -0.2, 0.6):
                    L = 120 * crack
                    self.Ln(d, [(cx, cy), (cx + L * math.cos(ang), cy + L * math.sin(ang))], (20, 15, 15), 7)
                self.E(d, cx, cy, 34 * crack, (25, 18, 18))

        def fireball(self, img, d, x, y, k=1.0, dirx=-0.55, diry=1.0):
            for i in range(9, 0, -1):
                tx, ty = x - dirx * i * 42 * k, y - diry * i * 42 * k
                self.E(d, tx, ty, (26 - i * 2) * k, (255, 170 - i * 10, 60))
            self.glow(img, x, y, 90 * k, (255, 160, 60), alpha=170)
            self.E(d, x, y, 30 * k, (255, 235, 180))

        def m_meteorito(self, key, img, d, t, lt, u, impact=False):
            self.stars(d, t, 1.0, drift=4.0)
            self.R(d, -20, 1330, W + 20, 1960, (34, 44, 40))
            hit = 0.72
            if impact:
                p = min(u / hit, 1.0)
                x, y = 900 + (560 - 900) * ease_out(p), 160 + (1000 - 160) * (p ** 1.4)
                crack = clamp((u - hit) / 0.15)
                self.house(d, 540, 1330, lit=1.0, crack=crack)
                if u < hit:
                    self.fireball(img, d, x, y, 1.0)
                else:
                    a = 1 - clamp((u - hit) / 0.25)
                    self.glow(img, 560, 1000, 260, (255, 240, 200), alpha=int(220 * a))
                    for i in range(10):
                        ang = i * 0.63 + 0.3
                        dist = 40 + 260 * clamp((u - hit) / 0.28)
                        self.E(d, 560 + dist * math.cos(ang), 1000 + dist * math.sin(ang) * 0.6, 9, (120, 100, 90))
                    if not getattr(self, "_shake_" + key, False):
                        self.shakes.append((t, 1.0))
                        setattr(self, "_shake_" + key, True)
            else:
                self.house(d, 540, 1330, lit=0.9)
                x = 980 - 520 * u
                y = 120 + 520 * u
                self.fireball(img, d, x, y, 0.8 + 0.4 * u)

        def m_roca(self, key, img, d, t, lt, u):
            self.stars(d, t, 0.35)
            k = back_out(clamp(lt / 0.6))
            R = 210 * k
            rot = t * 0.25
            cx, cy = 540, 960
            self.glow(img, cx, cy, R * 1.5, (255, 150, 60), alpha=90)
            pts = [(cx + R * r * math.cos(a + rot), cy + R * r * math.sin(a + rot)) for a, r in self.rock]
            self.P(d, pts, (96, 82, 74), outline=(30, 24, 22))
            for ox, oy, cr in self.craters:
                self.E(d, cx + R * (ox * math.cos(rot) - oy * math.sin(rot)), cy + R * (ox * math.sin(rot) + oy * math.cos(rot)),
                       R * cr, (70, 60, 55))

        # ── rótulos fijos (fuera del zoom) ──
        def overlay(self, ov, d, t, name, lt, u):
            card = self.cards.get(name)
            if not card:
                return False
            k = back_out(clamp(lt / 0.35))
            if k <= 0:
                return False
            size = 76 if len(card) <= 16 else 62
            while size > 36 and font("ExtraBold", size).getlength(card) + 80 > 844:  # zona segura: máx. 844 px
                size -= 2
            f = font("ExtraBold", size)
            tw = f.getlength(card)
            y = TOP_TEXT + 110  # bajo los subtítulos y por encima de la ilustración
            self.R(d, 540 - tw / 2 - 40, y - 62, 540 + tw / 2 + 40, y + 62, (215, 40, 50), radius=28)
            self.text(ov, 540, y, card, size * k, WHITE, alpha=clamp(lt / 0.15))
            return True

        def hud(self, out, t):
            name, _, _ = self.scene_at(t)
            i = self.order.get(name, 0)
            return self.pill(out, f"{label} · {i + 1}/{len(keys)}", col=YEL, y=BOTTOM - 80, size=44)

        # ── sonido ──
        def sfx_events(self):
            ev = [(0.0, "boom", 0.6)]
            for t0, k in self.scenes[1:]:
                ev.append((t0, "whoosh", 0.45))
                if self.cards.get(k):
                    ev.append((t0 + 0.1, "pop", 0.5))
                if self.kinds.get(k) == "grafico":
                    ev.append((t0 + 0.2, "tick", 0.35))
                if self.motifs.get(k) == "impacto":
                    t1 = next((s for s, kk in self.scenes if s > t0), self.duration)
                    ev.append((t0 + 0.72 * (t1 - t0), "boom", 0.9))
                    ev.append((t0 + 0.74 * (t1 - t0), "crack", 0.6))
                elif self.motifs.get(k) == "meteorito":
                    ev.append((t0 + 0.05, "wind", 0.4))
            return ev

        def music_plan(self):
            return [(0, 0.45), (self.duration * 0.6, 0.6), (self.duration, 0.4)]

    return Paquete


_PATH = os.environ.get("PAQUETE")
PKG = load_package(_PATH) if _PATH else None
VIDEO = make_video(PKG) if PKG else None
MOOD = MOODS.get((PKG or {}).get("pillar"), "suspense")
BPM = 84


def cover(pkg, out_path, beat=None, title=None):
    """Portada 1080×1920 para el reel: un fotograma de la propia animación (sin subtítulos), título grande en la
    zona segura, tarjeta roja con el rótulo principal y la marca. Mismo estilo que el vídeo."""
    from PIL import Image, ImageDraw, ImageFilter
    nar = synthetic_narration(pkg)
    cls = make_video(pkg)

    class Cover(cls):
        def caption(self, out, t):
            return out

        def hud(self, out, t):
            return out

        def overlay(self, ov, d, t, name, lt, u):
            return False

    v = Cover(nar)
    kinds, cards = beat_layout(pkg)
    keys = keys_for(pkg)
    if beat is None:  # primera escena «visual» (globo, simulación o gráfico), si no la primera
        beat = next((i for i, k in enumerate(kinds) if k in ("mapa", "simulacion", "grafico")), 0)
    ln = v.L[keys[beat]]
    img = v.frame(int((ln["start"] + 0.75 * (ln["end"] - ln["start"])) * 30)).convert("RGBA")
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shade).rectangle([0, 0, W, 1920], fill=(0, 0, 0, 70))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img)
    title = (title or pkg.get("title") or "").upper()
    words, lines, cur = title.split(), [], ""
    f = font("Black", 96)
    for w in words:
        test = (cur + " " + w).strip()
        if f.getlength(test) > 860 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    lines.append(cur)
    y = TOP_TEXT - 60  # por debajo de la marca y dentro de la zona segura
    for i, line in enumerate(lines[:3]):
        col = YEL if i == len(lines[:3]) - 1 else WHITE
        d.text((540 + 5, y + 6), line, font=f, fill=(0, 0, 0, 150), anchor="mt")
        d.text((540, y), line, font=f, fill=col + (255,), anchor="mt")
        y += 108
    card = next((c for c in cards if c), None)
    if card:
        fc = font("ExtraBold", 66)
        tw = fc.getlength(card)
        cy = BOTTOM - 190
        d.rounded_rectangle([540 - tw / 2 - 40, cy - 58, 540 + tw / 2 + 40, cy + 58], 28, fill=(215, 40, 50, 255))
        d.text((540, cy), card, font=fc, fill=(255, 255, 255, 255), anchor="mm")
    out = Video.brand(type("B", (), {"BRAND": "NIVEL OCULTO"})(), img.convert("RGB"))
    out.save(out_path, quality=92)
    return out_path


def main(argv):
    if len(argv) >= 4 and argv[1] == "guion":
        os.makedirs(os.path.dirname(os.path.abspath(argv[3])), exist_ok=True)
        with open(argv[3], "w", encoding="utf-8") as fh:
            json.dump(guion_for_voice(load_package(argv[2])), fh, ensure_ascii=False, indent=1)
        print("guion para la voz:", argv[3])
        return 0
    if len(argv) >= 4 and argv[1] == "sintetica":
        os.makedirs(argv[3], exist_ok=True)
        with open(os.path.join(argv[3], "narracion.json"), "w", encoding="utf-8") as fh:
            json.dump(synthetic_narration(load_package(argv[2])), fh, ensure_ascii=False)
        print("narración sintética (sin audio):", argv[3])
        return 0
    if len(argv) >= 4 and argv[1] == "portada":
        print("portada:", cover(load_package(argv[2]), argv[3], title=argv[4] if len(argv) > 4 else None))
        return 0
    if VIDEO is None:
        print("Define PAQUETE=ruta/al/paquete.json", file=sys.stderr)
        return 2
    if argv[1] == "plan":
        schedule(VIDEO, argv[2])
    elif argv[1] == "render":
        render(VIDEO, argv[2], argv[3], [int(x) for x in argv[4:]] or None)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
