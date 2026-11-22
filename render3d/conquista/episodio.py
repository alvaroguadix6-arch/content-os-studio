"""TU PUEBLO CONQUISTA ESPAÑA · vídeo de un episodio (1080×1920, 30 fps) a partir del estado de la competición.

    python episodio.py guion  <temporada> <ep> <salida.json>        → guion (texto de la voz) generado de los datos
    python episodio.py frames <temporada> <ep> <narracion/> <frames/> → fotogramas
(producir.py lo encadena todo: estado → guion → voz → fotogramas → montaje con música y efectos.)
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
import conquista  # noqa: E402
import datos  # noqa: E402
import mapa  # noqa: E402

W, H, FPS = 1080, 1920, 30
YEL = (255, 206, 40)
WHITE = (255, 255, 255)
INK = (24, 14, 52)
PINK = (255, 64, 129)
FONTS = "/usr/share/fonts/opentype/inter/"
_fc = {}


def font(style, size):
    k = (style, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONTS + f"Inter-{style}.otf", max(1, int(size)))
    return _fc[k]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def out3(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back(x):
    x = clamp(x)
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def miles(n):
    return f"{int(n):,}".replace(",", ".")


# ───── números en letra para la voz ─────
_U = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte".split()
_D = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta", 70: "setenta", 80: "ochenta", 90: "noventa"}
_C = {100: "ciento", 200: "doscientos", 300: "trescientos", 400: "cuatrocientos", 500: "quinientos", 600: "seiscientos",
      700: "setecientos", 800: "ochocientos", 900: "novecientos"}


def letras(n: int) -> str:
    n = int(n)
    if n <= 20:
        return _U[n]
    if n < 30:
        return "veinti" + ["", "uno", "dós", "trés", "cuatro", "cinco", "séis", "siete", "ocho", "nueve"][n - 20]
    if n < 100:
        d, u = divmod(n, 10)
        return _D[d * 10] + ("" if u == 0 else " y " + _U[u])
    if n == 100:
        return "cien"
    if n < 1000:
        c, r = divmod(n, 100)
        return _C[c * 100] + ("" if r == 0 else " " + letras(r))
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        head = "mil" if m == 1 else letras(m).replace("uno", "un") + " mil"
        return head + ("" if r == 0 else " " + letras(r))
    m, r = divmod(n, 1_000_000)
    head = "un millón" if m == 1 else letras(m).replace("uno", "un") + " millones"
    return head + ("" if r == 0 else " " + letras(r))


# ───── guion (se genera de los datos; nunca inventa votos) ─────
def guion(st):
    ep = st["episodio"]
    P = st["pueblos"]
    sig = ep + 1
    if st["votos_total"] == 0:  # lanzamiento (o episodio sin votos todavía)
        if ep == 1:
            return [
                ("intro", "¿Puede tu pueblo conquistar España?", ["pueblo", "España"]),
                ("vacio", "Este es el mapa de España: más de ocho mil municipios. Y ahora mismo está vacío. Nadie ha conquistado nada.", ["vacío", "nada"]),
                ("reglas", "Aquí mandas tú. Comenta el nombre de tu pueblo y tu provincia. Cada comentario es un voto.", ["comenta", "voto"]),
                ("conquista", "Con cada voto, tu pueblo conquista territorio a su alrededor.", ["conquista", "territorio"]),
                ("choque", "Y si choca con el pueblo de al lado, la frontera se la lleva el que tenga más votos.", ["choca", "más", "votos"]),
                ("top", "Cada episodio: el mapa nuevo, el top cinco y las rivalidades.", ["top", "cinco"]),
                ("cta", f"Escribe ya tu pueblo en los comentarios. En el episodio {letras(sig)}, las primeras conquistas.", ["comentarios", "conquistas"]),
            ]
        return [
            ("intro", f"Episodio {letras(ep)}. El mapa sigue vacío.", ["vacío"]),
            ("reglas", "Comenta tu pueblo y tu provincia: cada comentario es un voto y conquista territorio.", ["comenta", "voto"]),
            ("cta", f"El primer pueblo que comente, empieza ganando. Nos vemos en el episodio {letras(sig)}.", ["primer", "ganando"]),
        ]
    L = []
    nuevos = st["votos_nuevos"]
    L.append(("intro", f"Episodio {letras(ep)}. {letras(nuevos).capitalize()} votos nuevos" + (f" y {letras(len(P))} pueblos en guerra." if len(P) > 1 else "."),
              ["votos", "guerra"]))
    lid = P[0]
    if lid["puesto_antes"] == 1:
        txt = f"{lid['nombre']} sigue en cabeza: {letras(lid['votos'])} votos y {letras(lid['municipios'])} municipios conquistados."
    elif lid["nuevo"]:
        txt = f"Y el primer líder es {lid['nombre']}, con {letras(lid['votos'])} votos."
    else:
        txt = f"¡{lid['nombre']} toma el liderato! {letras(lid['votos']).capitalize()} votos y {letras(lid['municipios'])} municipios."
    if lid["domina"]:
        txt += f" Ya domina {lid['domina'][0]}."
    L.append(("lider", txt, [lid["nombre"].split("/")[0].split()[0], "cabeza", "liderato", "domina"]))
    # el gran salto: más votos ganados (que no sea el líder)
    rest = [p for p in P[1:] if p["votos"] > p["votos_antes"]]
    if rest:
        s = max(rest, key=lambda p: (p["votos"] - p["votos_antes"], -p["puesto"]))
        g = s["votos"] - s["votos_antes"]
        if s["nuevo"]:
            txt = f"Entra con fuerza {s['nombre']}: {letras(g)} votos de golpe."
        elif s["puesto_antes"] and s["puesto_antes"] > s["puesto"]:
            txt = f"{s['nombre']} sube {letras(s['puesto_antes'] - s['puesto'])} puestos con {letras(g)} votos nuevos."
        else:
            txt = f"{s['nombre']} suma {letras(g)} votos más."
        L.append(("salto", txt, [s["nombre"].split()[0], "fuerza", "sube"]))
        st["_salto"] = s["idx"]
    if st["invasiones"]:
        inv = st["invasiones"][0]
        a, d = next(p for p in P if p["idx"] == inv["atacante"]), next(p for p in P if p["idx"] == inv["defensor"])
        n = inv["municipios"]
        L.append(("invasion", f"¡Invasión! {a['nombre']} le quita {letras(n)} municipio{'s' if n > 1 else ''} a {d['nombre']}.", ["Invasión", "quita"]))
        st["_inv"] = (a["idx"], d["idx"])
    if st["rivalidades"]:
        r = st["rivalidades"][0]
        a, b = next(p for p in P if p["idx"] == r["a"]), next(p for p in P if p["idx"] == r["b"])
        if a["votos"] < b["votos"]:
            a, b = b, a
        dif = a["votos"] - b["votos"]
        txt = (f"Y ojo: {a['nombre']} contra {b['nombre']}. " + ("¡Empate total!" if dif == 0 else f"Solo les separa{'n' if dif > 1 else ''} {letras(dif)} voto{'s' if dif > 1 else ''}."))
        L.append(("rivalidad", txt, ["contra", "Empate", "separa", "separan"]))
        st["_riv"] = (a["idx"], b["idx"])
    if len(P) >= 2:
        L.append(("top", "Así queda el top cinco. ¿Está tu pueblo?", ["top", "cinco", "tu"]))
    L.append(("cta", f"Comenta tu pueblo y tu provincia para sumar votos. ¿Quién conquistará más en el episodio {letras(sig)}?", ["Comenta", "votos", "conquistará"]))
    return L


# ───── vídeo ─────
class Video:
    def __init__(self, nar, temporada=None, ep=None):
        temporada = temporada or os.environ["CONQ_TEMPORADA"]
        ep = int(ep or os.environ["CONQ_EP"])
        self.st = conquista.estado(temporada, ep)
        self.script = guion(self.st)
        self.kw = {k: kws for k, _, kws in self.script}
        self.nar = nar
        self.L = {l["key"]: l for l in nar["lines"]}
        self.duration = nar["lines"][-1]["end"] + 1.6
        self.scenes = [(0.0 if i == 0 else l["start"] - 0.12, l["key"]) for i, l in enumerate(nar["lines"])]
        munis, provs = datos.load()
        self.N = len(munis)
        self.munis = munis
        self.launch = self.st["votos_total"] == 0
        self._prep()

    # ── preparación ──
    def _prep(self):
        st, munis = self.st, self.munis
        N = self.N
        rng = np.random.default_rng(7)
        self.base = np.zeros((N + 1, 3), np.float32)
        pv = np.array([int(m["prov"]) for m in munis])
        tint = rng.uniform(-1, 1, 60)
        self.base[1:] = np.array([30, 36, 92], np.float32) + np.outer(tint[pv], [5, 6, 12]) + rng.uniform(-3, 3, (N, 1))
        self.noise = rng.uniform(0, 1, N + 1)
        g = conquista.geo()
        self.kx, self.ky = g["x"], g["y"]
        self.wxy = np.array([mapa.proj(m["lon"], m["lat"], m["prov"]) for m in munis])
        order = st["_order"]
        self.order = order
        self.tcol = np.array([conquista.PALETA[k % len(conquista.PALETA)] for k in range(max(1, len(order)))], np.float32)
        self.own_prev = np.concatenate([[-1], st["_owner_prev"]])
        self.own_cur = np.concatenate([[-1], st["_owner_cur"]])
        # momento de conquista de cada municipio (onda desde el pueblo hacia fuera)
        self.tc = np.full(N + 1, -1.0)
        if not self.launch:
            k0 = self.L.get("intro", self.nar["lines"][0])["start"] + 0.6
            dur = 4.2
            chg = np.where(self.own_cur != self.own_prev)[0]
            for m in chg:
                k = self.own_cur[m]
                if k < 0:
                    continue
                t = order[k]
                d = math.hypot(self.kx[m - 1] - self.kx[t], self.ky[m - 1] - self.ky[t])
                r = math.sqrt(max(1, self.st["pueblos"][0]["votos"]) * st["config"]["km2_por_voto"] / math.pi)
                self.tc[m] = k0 + dur * clamp(d / max(r, 1e-6)) + 0.15 * self.noise[m]
        self.camkeys = self._camera_plan()

    def P(self, idx):
        return next(p for p in self.st["pueblos"] if p["idx"] == idx)

    def town_world(self, idx):
        m = self.munis[idx]
        return mapa.proj(m["lon"], m["lat"], m["prov"])

    def territory_view(self, idxs, pad=1.35, zmax=4.2, zmin=1.0):
        """Cámara que encuadra los territorios de esos pueblos."""
        ks = [self.order.index(i) for i in idxs if i in self.order]
        mask = np.isin(self.own_cur[1:], ks)
        pts = self.wxy[mask] if mask.any() else np.array([self.town_world(i) for i in idxs])
        x0, y0 = pts.min(0)
        x1, y1 = pts.max(0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        span = max(x1 - x0, (y1 - y0) * 0.9, 40)
        z = clamp(820 / (span * pad), zmin, zmax)
        return cx, cy, z

    def _camera_plan(self):
        L = self.L
        full = (540.0, 1100.0, 1.0)
        keys = []
        if self.launch and "conquista" in L:
            dense = mapa.proj(-3.6, 41.7)
            keys += [(0.0, dense[0], dense[1], 5.5), (L["intro"]["end"] + 0.1, *full)]
            keys += [(L["vacio"]["start"], 540, 1100, 1.0), (L["reglas"]["start"], 540, 1110, 1.06), (L["reglas"]["end"], 540, 1100, 1.0)]
            self.demo = mapa.proj(-3.2, 39.25)
            keys += [(L["conquista"]["start"] + 0.6, self.demo[0] + 30, self.demo[1], 2.6), (L["choque"]["end"], self.demo[0] + 45, self.demo[1], 2.9)]
            keys += [(L["top"]["start"] + 0.8, *full), (self.duration, 540, 1100, 1.04)]
            return keys
        if self.launch:
            return [(0.0, 540, 1100, 1.25), (self.duration, 540, 1100, 1.0)]
        st = self.st
        lid = st["pueblos"][0]["idx"]
        keys.append((0.0, *full))
        keys.append((L["intro"]["end"], *full))
        lv = self.territory_view([lid])
        keys.append((L["lider"]["start"] + 0.7, *lv))
        keys.append((L["lider"]["end"] + 0.2, lv[0], lv[1], lv[2] * 1.08))
        for key, who in (("salto", [st.get("_salto")]), ("invasion", list(st.get("_inv", ()))), ("rivalidad", list(st.get("_riv", ())))):
            if key in L and all(w is not None for w in who):
                v = self.territory_view(who)
                keys.append((L[key]["start"] + 0.6, *v))
                keys.append((L[key]["end"] + 0.2, v[0], v[1], v[2] * 1.07))
        if "top" in L:
            keys.append((L["top"]["start"] + 0.6, 540, 1180, 0.82))
        keys.append((L["cta"]["start"] + 0.5, *full))
        keys.append((self.duration, 540, 1100, 1.05))
        return sorted(keys)

    def camera(self, t):
        ks = self.camkeys
        if t <= ks[0][0]:
            k = ks[0]
            return mapa.Camera(k[1], k[2], k[3])
        for a, b in zip(ks, ks[1:]):
            if a[0] <= t <= b[0]:
                u = ease((t - a[0]) / max(1e-3, b[0] - a[0]))
                z = math.exp(math.log(a[3]) * (1 - u) + math.log(b[3]) * u)
                # el centro sigue al zoom para que el movimiento sea natural
                w = (1 / a[3] - 1 / z) / (1 / a[3] - 1 / b[3]) if abs(a[3] - b[3]) > 1e-3 else u
                x = a[1] + (b[1] - a[1]) * w
                y = a[2] + (b[2] - a[2]) * w
                br = 1 + 0.012 * math.sin(t * 0.9)  # respiración: nunca está quieto
                return mapa.Camera(x + 4 * math.sin(t * 0.6), y + 3 * math.cos(t * 0.5), z * br)
        k = ks[-1]
        return mapa.Camera(k[1], k[2], k[3])

    # ── colores del mapa en el instante t ──
    def colors(self, t):
        fill = self.base.copy()
        owner = -np.ones(self.N + 1, int)
        flash = np.zeros(self.N + 1, np.float32)
        if self.launch:
            self._launch_colors(t, fill, owner)
            return fill, owner, self.tcol_launch
        if t >= 0:
            on = (self.tc >= 0) & (t >= self.tc)
            owner = np.where(on, self.own_cur, self.own_prev)
            flash = np.where(on, np.exp(-(t - self.tc) / 0.35), 0).astype(np.float32)
        m = owner >= 0
        col = self.tcol[np.clip(owner, 0, None)]
        # tono más vivo cerca del pueblo, algo más oscuro en los bordes
        shade = 0.82 + 0.18 * self.noise
        fill[m] = col[m] * shade[m, None]
        fill = fill + flash[:, None] * (255 - fill) * 0.85
        # pulso suave del territorio del líder
        if self.order:
            k = self.order.index(self.st["pueblos"][0]["idx"])
            pl = owner == k
            fill[pl] = fill[pl] * (0.92 + 0.08 * math.sin(t * 4))
        return np.clip(fill, 0, 255).astype(np.uint8), owner, self.tcol.astype(np.uint8)

    def _launch_colors(self, t, fill, owner):
        L = self.L
        rng_t = int(t * 10)
        # destellos de «cualquier pueblo puede ser» (intro) y barrido de luz (vacío/cta)
        if "conquista" in L and t < L["vacio"]["start"] + 0.6:
            k = 1 - ease((t - L["intro"]["end"] + 0.3) / 1.2)
            hit = ((self.noise * 97 + rng_t * 0.37) % 1) < 0.08 * k
            pal = np.array(conquista.PALETA, np.float32)
            fill[hit] = pal[(np.arange(self.N + 1)[hit] + rng_t) % len(pal)]
        sweep_scenes = [("vacio", 0.0), ("cta", 0.0)] if "conquista" in L else [("intro", 0.0), ("cta", 0.0)]
        for key, _ in sweep_scenes:
            if key in L:
                t0, t1 = L[key]["start"], L[key]["end"]
                if t0 <= t <= t1 + 0.5:
                    u = (t - t0) / max(0.5, t1 - t0 + 0.5)
                    line = -200 + u * 1700
                    proj_ = self.wxy[:, 0] * 0.55 + self.wxy[:, 1] * 0.85 - 900
                    gl = np.exp(-((proj_ - line) / 70) ** 2)
                    fill[1:] += gl[:, None] * np.array([90, 120, 220], np.float32)
        self.tcol_launch = np.array([(255, 196, 0), (255, 64, 129)], np.uint8)
        if "conquista" in L:  # EJEMPLO ilustrativo (no son votos reales)
            a0, a1 = L["conquista"]["start"] + 0.5, L["choque"]["end"]
            if a0 <= t <= a1 + 0.4:
                wx, wy = self.wxy[:, 0], self.wxy[:, 1]
                ax, ay = self.demo[0] - 30, self.demo[1] + 5
                bx, by = self.demo[0] + 95, self.demo[1] - 15
                c0 = L["choque"]["start"]
                va = 22 * out3((t - a0) / max(0.5, c0 - a0 - 0.3))
                vb = 34 * out3((t - c0 - 0.2) / 2.4) if t > c0 else 0
                self.demo_votes = (int(round(va)), int(round(vb)))
                ra, rb = 10.5 * math.sqrt(max(va, 0.01)), 10.5 * math.sqrt(max(vb, 0.01))
                da = np.hypot(wx - ax, wy - ay) / max(ra, 1e-3)
                db = np.hypot(wx - bx, wy - by) / max(rb, 1e-3) if vb > 0 else np.full_like(da, 9)
                A = (da <= 1) & (da <= db)
                B = (db <= 1) & (db < da)
                own = owner[1:]
                own[A] = 0
                own[B] = 1
                fill[1:][A] = np.array([255, 196, 0], np.float32) * (0.85 + 0.15 * self.noise[1:][A, None])
                fill[1:][B] = np.array([255, 64, 129], np.float32) * (0.85 + 0.15 * self.noise[1:][B, None])
                self.demo_pos = ((ax, ay), (bx, by))

    # ── fondo ──
    def bg(self, t):
        if not hasattr(self, "_grad"):
            y = np.linspace(0, 1, H)[:, None, None]
            top, bot = np.array([16, 10, 44], np.float32), np.array([44, 18, 92], np.float32)
            self._grad = (top * (1 - y) + bot * y) * np.ones((1, W, 1), np.float32)
            self._xx = np.linspace(-1, 1, W)[None, :]
            self._yy = np.linspace(0, 1, H)[:, None]
        img = self._grad.copy()
        for k, (sp, ph, col) in enumerate([(0.3, 0.0, (110, 50, 210)), (0.22, 2.1, (30, 70, 190))]):
            cx = 0.6 * math.sin(t * sp + ph)
            beam = np.exp(-((self._xx - cx - 0.3 * (self._yy - 0.5)) ** 2) / 0.06) * (0.3 + 0.2 * math.sin(t * 0.8 + k))
            img += beam[..., None] * np.array(col, np.float32) * 0.45
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")

    # ── texto ──
    def text(self, d, xy, s, size, fill=WHITE, style="Black", anchor="mm", stroke=0, stroke_fill=INK):
        d.text(xy, s, font=font(style, size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)

    def header(self, img, d, t):
        ep = self.st["episodio"]
        a = out3((t - 0.2) / 0.5) if not self.launch else out3((t - (self.L["intro"]["end"] - 0.2)) / 0.5)
        if a <= 0:
            return
        y = 92 - (1 - a) * 160
        f = font("Black", 40)
        label = "TU PUEBLO CONQUISTA ESPAÑA"
        w = d.textlength(label, font=f)
        d.rounded_rectangle([540 - w / 2 - 150, y - 38, 540 + w / 2 + 30, y + 38], 38, fill=(20, 12, 48, 235), outline=YEL, width=4)
        d.rounded_rectangle([540 - w / 2 - 146, y - 34, 540 - w / 2 - 14, y + 34], 34, fill=YEL)
        self.text(d, (540 - w / 2 - 80, y + 1), f"EP.{ep}", 34, INK, "Black")
        self.text(d, (540 + 10 - 50 + 50, y + 1), label, 40, WHITE, "Black")

    def caption(self, img, d, t):
        """Subtítulos palabra a palabra (palabras clave en amarillo)."""
        cur = None
        for l in self.nar["lines"]:
            if l["start"] - 0.05 <= t <= l["end"] + 0.35:
                cur = l
        if cur is None:
            return
        kws = [k.lower() for k in self.kw.get(cur["key"], [])]
        words = [w for w in cur["words"] if w[1] <= t + 0.02]
        if not words:
            return
        # bloques de ~5 palabras: se muestra el bloque actual
        allw = cur["words"]
        n = len(words)
        blk = (n - 1) // 6
        show = allw[blk * 6: blk * 6 + 6]
        f = font("Black", 64)
        toks = [w[0] for w in show]
        lines, curl = [], []
        for tk in toks:
            test = " ".join(curl + [tk])
            if d.textlength(test, font=f) * 1.08 > 960 and curl:
                lines.append(curl)
                curl = [tk]
            else:
                curl.append(tk)
        lines.append(curl)
        lines = [ln for ln in lines if ln]
        y0 = 1660 - (len(lines) - 1) * 40
        k = 0
        for li, ln in enumerate(lines):
            tot = sum(d.textlength(tk, font=f) for tk in ln) + d.textlength("  ", font=f) * (len(ln) - 1)
            x = 540 - tot / 2
            for tk in ln:
                wi = blk * 6 + k
                k += 1
                if wi >= n:
                    break
                age = t - allw[wi][1]
                sc = 1 + 0.08 * max(0, 1 - age / 0.12)
                clean = tk.strip("¿?¡!.,:;").lower()
                col = YEL if any(clean.startswith(kw.lower()[:5]) for kw in kws if len(kw) > 2) else WHITE
                fs = font("Black", int(64 * sc))
                d.text((x + d.textlength(tk, font=f) / 2, y0 + li * 80), tk, font=fs, fill=col, anchor="mm", stroke_width=7, stroke_fill=INK)
                x += d.textlength(tk, font=f) + d.textlength("  ", font=f)

    # ── etiquetas de pueblos ──
    def labels(self, img, d, t, cam):
        if self.launch or not self.st["pueblos"]:
            return
        if "top" in self.L and self.L["top"]["start"] + 0.2 <= t <= self.L["cta"]["start"] + 0.2:
            return
        placed = []
        for p in self.st["pueblos"][:12]:
            k = self.order.index(p["idx"])
            appear = self.tc[self.own_cur == k]
            t_on = appear.min() if len(appear) and appear.max() >= 0 else -1
            if not p["nuevo"]:
                t_on = -1
            if t < t_on:
                continue
            a = out3((t - t_on) / 0.4) if t_on >= 0 else 1.0
            wx, wy = self.town_world(p["idx"])
            sx, sy = cam.to_screen(wx, wy)
            if not (60 < sx < 1020 and 560 < sy < 1560):
                continue
            size = clamp(30 + 6 * cam.z + 3 * math.log1p(p["votos"]), 30, 66) * (0.6 + 0.4 * a)
            name = p["nombre"].split("/")[-1].upper()
            fw = d.textlength(name, font=font("Black", size))
            box = (sx - fw / 2 - 14, sy - size - 34, sx + fw / 2 + 14, sy + 30)
            if any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]) for b in placed):
                continue
            placed.append(box)
            col = tuple(conquista.PALETA[k % len(conquista.PALETA)])
            d.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=WHITE, outline=INK, width=3)
            self.text(d, (sx, sy - 26), name, size, WHITE, "Black", "ms", 6, INK)
            # votos animados (cuentan desde los del episodio anterior)
            v0, v1 = p["votos_antes"], p["votos"]
            u = out3((t - max(0.5, t_on)) / 2.5)
            v = int(round(v0 + (v1 - v0) * u))
            vs = f"{miles(v)} VOTOS"
            fv = font("Black", int(size * 0.55))
            vw = d.textlength(vs, font=fv)
            d.rounded_rectangle([sx - vw / 2 - 12, sy + 14, sx + vw / 2 + 12, sy + 14 + size * 0.7], 12, fill=col)
            d.text((sx, sy + 14 + size * 0.35), vs, font=fv, fill=INK, anchor="mm")
            if p["domina"]:
                self.crown(d, sx, sy - size - 48, size * 0.55)

    def crown(self, d, x, y, s):
        pts = [(x - s, y + s * 0.5), (x - s, y - s * 0.3), (x - s * 0.5, y + s * 0.1), (x, y - s * 0.6), (x + s * 0.5, y + s * 0.1),
               (x + s, y - s * 0.3), (x + s, y + s * 0.5)]
        d.polygon(pts, fill=YEL, outline=INK)

    # ── paneles ──
    def chips(self, img, d, t, items, t0):
        """Contadores grandes animados."""
        n = len(items)
        for i, (val, lab, col) in enumerate(items):
            a = back((t - t0 - i * 0.18) / 0.45)
            if a <= 0.01:
                continue
            cx = 540 + (i - (n - 1) / 2) * 340
            y = 470 - (1 - a) * 80
            d.rounded_rectangle([cx - 158, y - 70, cx + 158, y + 70], 26, fill=(18, 10, 44, 230), outline=col, width=4)
            self.text(d, (cx, y - 14), val, 60, col, "Black")
            self.text(d, (cx, y + 40), lab, 24, (210, 200, 240), "ExtraBold")

    def top5(self, img, d, t, t0):
        P = self.st["pueblos"][:5]
        a = out3((t - t0) / 0.5)
        x0 = 90 - (1 - a) * 1100
        y0 = 1100
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([x0, y0 - 90, x0 + 900, y0 + 5 * 92 + 20], 34, fill=(16, 9, 40, 235), outline=YEL, width=5)
        img.alpha_composite(lay)
        self.text(d, (x0 + 450, y0 - 45), "TOP 5", 54, YEL, "Black")
        for i in range(5):
            b = back((t - t0 - 0.3 - i * 0.14) / 0.4)
            if b <= 0.01:
                continue
            y = y0 + 20 + i * 92 + (1 - b) * 40
            self.text(d, (x0 + 60, y + 30), f"{i + 1}", 52, WHITE, "Black")
            if i < len(P):
                p = P[i]
                k = self.order.index(p["idx"])
                col = tuple(conquista.PALETA[k % len(conquista.PALETA)])
                d.ellipse([x0 + 110, y + 12, x0 + 146, y + 48], fill=col)
                name = p["nombre"].split("/")[-1]
                self.text(d, (x0 + 166, y + 18), name if len(name) < 22 else name[:21] + "…", 40, WHITE, "Black", "lm")
                self.text(d, (x0 + 166, y + 54), p["provincia"].split("/")[-1], 24, (190, 180, 230), "SemiBold", "lm")
                self.text(d, (x0 + 800, y + 30), miles(p["votos"]), 44, col, "Black", "rm")
                self.move_icon(d, x0 + 850, y + 30, p)
            else:
                self.text(d, (x0 + 166, y + 30), "¿TU PUEBLO?", 40, (150, 140, 200), "Black", "lm")
                self.text(d, (x0 + 800, y + 30), "0", 44, (150, 140, 200), "Black", "rm")

    def move_icon(self, d, x, y, p):
        if p["nuevo"]:
            self.text(d, (x, y), "NEW", 22, (90, 230, 120), "Black")
            return
        dlt = (p["puesto_antes"] or 99) - p["puesto"]
        if dlt > 0:
            d.polygon([(x - 16, y + 10), (x + 16, y + 10), (x, y - 14)], fill=(90, 230, 120))
        elif dlt < 0:
            d.polygon([(x - 16, y - 10), (x + 16, y - 10), (x, y + 14)], fill=(255, 80, 80))
        else:
            d.rectangle([x - 14, y - 4, x + 14, y + 4], fill=(170, 170, 200))

    # ── fotograma ──
    def frame(self, t):
        img = self.bg(t)
        cam = self.camera(t)
        fill, owner, ocol = self.colors(t)
        layer = mapa.render(cam, fill, owner, ocol)
        img.alpha_composite(layer)
        d = ImageDraw.Draw(img)
        mapa.canarias_box(cam, d)
        if self.launch:
            self.launch_overlay(img, d, t, cam)
        else:
            self.labels(img, d, t, cam)
            self.episode_overlay(img, d, t, cam)
        self.header(img, d, t)
        self.caption(img, d, t)
        self.text(d, (540, 1872), "N I V E L   O C U L T O", 28, (190, 170, 240), "ExtraBold")
        return img.convert("RGB")

    def episode_overlay(self, img, d, t, cam):
        L, st = self.L, self.st
        if t < L["intro"]["end"] + 0.3:
            self.chips(img, d, t, [(f"+{miles(st['votos_nuevos'])}", "VOTOS NUEVOS", YEL), (miles(len(st["pueblos"])), "PUEBLOS", (120, 220, 255)),
                                   (f"{st['conquistado']:.1f}%".replace(".", ","), "CONQUISTADO", PINK)], 0.4)
        for key in ("rivalidad", "invasion"):
            if key in L and L[key]["start"] - 0.1 <= t <= L[key]["end"] + 0.3:
                a = back((t - L[key]["start"]) / 0.4)
                txt = "VS" if key == "rivalidad" else "¡INVASIÓN!"
                self.text(d, (540, 520), txt, int(110 * a) + 1, YEL if key == "rivalidad" else (255, 80, 80), "Black", "mm", 8, INK)
        if "top" in L and L["top"]["start"] <= t <= L["cta"]["start"] - 0.05:
            self.top5(img, d, t, L["top"]["start"])
        if t >= L["cta"]["start"]:
            self.cta(img, d, t, L["cta"]["start"])

    def cta(self, img, d, t, t0):
        a = back((t - t0) / 0.45)
        if a <= 0.01:
            return
        y = 470
        self.text(d, (540, y), "COMENTA", int(120 * a) + 1, YEL, "Black", "mm", 9, INK)
        self.text(d, (540, y + 110), "TU PUEBLO + PROVINCIA", int(56 * a) + 1, WHITE, "Black", "mm", 7, INK)
        bob = 14 * math.sin(t * 7)
        ay = 1515 + bob
        if a > 0.5:
            d.polygon([(500, ay - 30), (580, ay - 30), (580, ay + 10), (620, ay + 10), (540, ay + 70), (460, ay + 10), (500, ay + 10)], fill=YEL, outline=INK)
        nxt = f"EPISODIO {self.st['episodio'] + 1}" + (": LAS PRIMERAS CONQUISTAS" if self.launch else "")
        b = out3((t - t0 - 0.6) / 0.4)
        if b > 0:
            f = font("Black", 36)
            w = d.textlength(nxt, font=f)
            d.rounded_rectangle([540 - w / 2 - 30, 1380 - 34, 540 + w / 2 + 30, 1380 + 34], 34, fill=PINK)
            self.text(d, (540, 1380), nxt, 36, WHITE, "Black")

    def launch_overlay(self, img, d, t, cam):
        L = self.L
        if "conquista" not in L:  # episodio sin votos (no lanzamiento)
            if t >= L["cta"]["start"]:
                self.cta(img, d, t, L["cta"]["start"])
            return
        # título de entrada
        te = L["intro"]["end"]
        if t < te + 0.5:
            a = back((t - 0.15) / 0.45)
            fade = 1 - clamp((t - te) / 0.5)
            if a > 0.01 and fade > 0:
                lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                dl = ImageDraw.Draw(lay)
                dl.text((540, 760), "TU PUEBLO", font=font("Black", int(150 * a) + 1), fill=WHITE + (int(255 * fade),), anchor="mm", stroke_width=10, stroke_fill=INK)
                dl.text((540, 920), "CONQUISTA", font=font("Black", int(120 * a) + 1), fill=YEL + (int(255 * fade),), anchor="mm", stroke_width=10, stroke_fill=INK)
                dl.text((540, 1050), "ESPAÑA", font=font("Black", int(150 * a) + 1), fill=YEL + (int(255 * fade),), anchor="mm", stroke_width=10, stroke_fill=INK)
                img.alpha_composite(lay)
        # contadores del mapa vacío
        v0, v1 = L["vacio"]["start"], L["reglas"]["start"]
        if v0 - 0.1 <= t <= v1 + 0.2:
            n = int(8131 * out3((t - v0 - 0.2) / 1.6))
            self.chips(img, d, t, [(miles(n), "MUNICIPIOS", (120, 220, 255)), ("0", "PUEBLOS", WHITE), ("0%", "CONQUISTADO", PINK)], v0 + 0.1)
            if t > v0 + 2.2:
                a = back((t - v0 - 2.2) / 0.35)
                lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                dl = ImageDraw.Draw(lay)
                dl.rounded_rectangle([540 - 270 * a, 1000 - 70 * a, 540 + 270 * a, 1000 + 70 * a], 24, fill=(255, 64, 129, 225), outline=WHITE, width=5)
                img.alpha_composite(lay.rotate(-6, center=(540, 1000)))
                lay2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ImageDraw.Draw(lay2).text((540, 1000), "MAPA VACÍO", font=font("Black", int(78 * a) + 1), fill=WHITE, anchor="mm")
                img.alpha_composite(lay2.rotate(-6, center=(540, 1000)))
        # el comentario (cómo se vota)
        r0, r1 = L["reglas"]["start"], L["conquista"]["start"]
        if r0 - 0.1 <= t <= r1 + 0.3:
            a = back((t - r0 - 0.4) / 0.45)
            out = clamp((t - r1) / 0.3)
            y = 1180 + (1 - a) * 500 + out * 600
            if a > 0.01:
                lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                dl = ImageDraw.Draw(lay)
                dl.rounded_rectangle([90, y - 110, 990, y + 110], 40, fill=(250, 248, 255, 245))
                dl.ellipse([120, y - 70, 220, y + 30], fill=(255, 196, 0))
                dl.text((170, y - 20), "TÚ", font=font("Black", 36), fill=INK, anchor="mm")
                dl.text((250, y - 62), "@tu_usuario", font=font("Bold", 30), fill=(120, 110, 150), anchor="lm")
                dl.text((250, y - 5), "Tu pueblo, tu provincia", font=font("Black", 50), fill=INK, anchor="lm")
                dl.text((250, y + 58), "Responder", font=font("SemiBold", 26), fill=(140, 130, 170), anchor="lm")
                # corazón
                hx, hy = 930, y - 10
                dl.ellipse([hx - 26, hy - 22, hx, hy + 4], fill=PINK)
                dl.ellipse([hx - 4, hy - 22, hx + 22, hy + 4], fill=PINK)
                dl.polygon([(hx - 26, hy - 6), (hx + 22, hy - 6), (hx - 2, hy + 26)], fill=PINK)
                img.alpha_composite(lay)
            b = back((t - r0 - 2.0) / 0.4)
            if b > 0.01 and out < 1:
                self.text(d, (540, 900), "1 COMENTARIO = 1 VOTO", int(70 * b) + 1, YEL, "Black", "mm", 8, INK)
                self.text(d, (540, 975), "(1 voto por cuenta y episodio)", int(34 * b) + 1, WHITE, "Bold", "mm", 5, INK)
        # demostración (EJEMPLO, no son votos reales)
        c0, c1 = L["conquista"]["start"] + 0.5, L["choque"]["end"] + 0.4
        if c0 <= t <= c1 and hasattr(self, "demo_pos"):
            badge = out3((t - c0) / 0.3)
            f = font("Black", 40)
            d.rounded_rectangle([540 - 150, 560, 540 + 150, 630], 35, fill=(255, 255, 255, int(235 * badge)))
            self.text(d, (540, 596), "EJEMPLO", 40, INK, "Black")
            (ax, ay), (bx, by) = self.demo_pos
            va, vb = getattr(self, "demo_votes", (0, 0))
            for (wx, wy), name, v, col in (((ax, ay), "TU PUEBLO", va, (255, 196, 0)), ((bx, by), "PUEBLO RIVAL", vb, (255, 64, 129))):
                if v <= 0:
                    continue
                sx, sy = cam.to_screen(wx, wy)
                self.text(d, (sx, sy - 30), name, 52, WHITE, "Black", "ms", 7, INK)
                vs = f"{v} VOTOS"
                fv = font("Black", 32)
                vw = d.textlength(vs, font=fv)
                d.rounded_rectangle([sx - vw / 2 - 14, sy - 12, sx + vw / 2 + 14, sy + 34], 14, fill=col)
                d.text((sx, sy + 11), vs, font=fv, fill=INK, anchor="mm")
            # «+1» flotando
            ch = L["choque"]["start"]
            for k in range(14):
                tk = c0 + 0.2 + k * 0.22 if k < 8 else ch + 0.3 + (k - 8) * 0.3
                age = t - tk
                if 0 <= age <= 0.8:
                    src = (ax, ay) if k < 8 else (bx, by)
                    sx, sy = cam.to_screen(*src)
                    ox = ((k * 53) % 160) - 80
                    self.text(d, (sx + ox, sy - 110 - age * 120), "+1", int(48 * back(age / 0.2)) + 1, (255, 196, 0) if k < 8 else (255, 64, 129), "Black", "mm", 6, INK)
            if t >= ch + 1.2:
                a = back((t - ch - 1.2) / 0.4)
                self.text(d, (540, 760), "VS", int(120 * a) + 1, YEL, "Black", "mm", 9, INK)
        # TOP 5 vacío
        if L["top"]["start"] <= t <= L["cta"]["start"] - 0.05:
            self.top5(img, d, t, L["top"]["start"] + 0.2)
        if t >= L["cta"]["start"]:
            self.cta(img, d, t, L["cta"]["start"])

    # ── audio (montaje.py) ──
    def music_plan(self):
        L = self.nar["lines"]
        p = [(0, 0.55)]
        for l in L:
            p.append((l["start"], 0.7 if l["key"] in ("intro", "cta", "choque", "invasion", "rivalidad") else 0.55))
        return p + [(self.duration, 0.4)]

    def sfx_events(self):
        ev = []
        L = self.L
        ev.append((0.15, "boom", 0.6))
        ev.append((0.1, "riser", 0.25))
        if self.launch and "conquista" in L:
            c0 = L["conquista"]["start"] + 0.5
            for k in range(8):
                ev.append((c0 + 0.2 + k * 0.22, "pop", 0.35))
            for k in range(6):
                ev.append((L["choque"]["start"] + 0.3 + k * 0.3, "pop", 0.35))
            ev.append((L["choque"]["start"] + 1.2, "boom", 0.45))
            ev.append((L["vacio"]["start"] + 2.2, "click", 0.5))
            ev.append((L["reglas"]["start"] + 2.0, "shimmer", 0.4))
        if not self.launch:
            ts = sorted(self.tc[self.tc >= 0])
            for k in range(0, len(ts), max(1, len(ts) // 18)):
                ev.append((ts[k], "drip", 0.18))
            for key in ("invasion", "rivalidad"):
                if key in L:
                    ev.append((L[key]["start"], "boom", 0.45))
        if "top" in L:
            for i in range(5):
                ev.append((L["top"]["start"] + 0.5 + i * 0.14, "tick", 0.8))
        ev.append((L["cta"]["start"], "shimmer", 0.5))
        return ev


VIDEO = Video
MOOD = "epico"
BPM = 112

_V = None


def _init(nar, temporada, ep):
    global _V
    _V = Video(nar, temporada, ep)


def _render(args):
    k, out = args
    _V.frame(k / FPS).save(os.path.join(out, f"f{k:05d}.jpg"), quality=92)
    return k


if __name__ == "__main__":
    cmd = sys.argv[1]
    temporada, ep = sys.argv[2], int(sys.argv[3])
    if cmd == "guion":
        st = conquista.estado(temporada, ep)
        g = guion(st)
        json.dump({"guion": [[k, txt] for k, txt, _ in g], "pausas": {k: (0.45 if k in ("intro",) else 0.3) for k, _, _ in g}},
                  open(sys.argv[4], "w"), ensure_ascii=False, indent=1)
        print("\n".join(f"[{k}] {txt}" for k, txt, _ in g))
        sys.exit()
    nard, out = sys.argv[4], sys.argv[5]
    nar = json.load(open(os.path.join(nard, "narracion.json"), encoding="utf-8"))
    os.makedirs(out, exist_ok=True)
    only = [float(x) for x in os.environ.get("SOLO", "").split(",") if x]
    mapa.raster()
    if only:
        v = Video(nar, temporada, ep)
        for ts in only:
            v.frame(ts).save(os.path.join(out, f"t{ts:05.1f}.jpg"), quality=90)
        sys.exit()
    v = Video(nar, temporada, ep)
    n = int(v.duration * FPS)
    with Pool(4, _init, (nar, temporada, ep)) as p:
        for k in p.imap_unordered(_render, [(k, out) for k in range(n)], chunksize=6):
            if k % 300 == 0:
                print("frame", k, "/", n, flush=True)
    print("frames listos", n)
