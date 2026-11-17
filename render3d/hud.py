"""HUD de videojuego de carreras + subtítulos sincronizados (capa transparente 1080x1920).

Se genera un PNG por fotograma con Pillow a partir de los mismos datos de la simulación,
y luego ffmpeg lo superpone sobre el render 3D.
Respeta las zonas seguras de TikTok/Reels/Shorts (arriba 7 %, abajo 20 %, derecha 14 %).
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_PLAIN = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _font(size, italic=True):
    for p in FONT_CANDIDATES if italic else FONT_PLAIN:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def word_cues(lines, max_words=3):
    """Reparte el tiempo de cada frase entre sus palabras y forma bloques de 1-3 palabras."""
    cues = []
    for ln in lines:
        words = ln["text"].split()
        weights = [len(w.strip("¡!¿?.,…:")) + 1.5 + (4 if w[-1:] in ".!?…" else 2.5 if w[-1:] in ",:;" else 0) for w in words]
        tot = sum(weights)
        t = ln["start"] + 0.05
        span = max(0.3, ln["end"] - ln["start"] - 0.1)
        timed = []
        for w, k in zip(words, weights):
            d = span * k / tot
            timed.append((w, t, t + d))
            t += d
        group = []
        for item in timed:
            group.append(item)
            if len(group) >= max_words or item[0][-1:] in ".!?…,:;":
                cues.append(group)
                group = []
        if group:
            cues.append(group)
    return [{"start": g[0][1], "end": g[-1][2], "words": g} for g in cues]


def _stroke_text(d, xy, text, font, fill, stroke=8, anchor="mm"):
    d.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 255), anchor=anchor)


def _panel(d, box, r=18, fill=(8, 10, 16, 170)):
    d.rounded_rectangle(box, r, fill=fill)


class HUD:
    def __init__(self, race, lines):
        self.race = race
        self.cues = word_cues(lines)
        self.f_big = _font(96)
        self.f_mid = _font(52)
        self.f_small = _font(36)
        self.f_tiny = _font(28, italic=False)
        self.f_sub = _font(78, italic=False)
        sp = race.spec
        self.names = {"a": sp.car_a_name.upper(), "b": sp.car_b_name.upper()}
        self.colors = {"a": (230, 30, 30, 255), "b": (255, 196, 0, 255)}

    def frame(self, f):
        race = self.race
        vt = f / race.spec.fps
        t = race.sim_time(vt)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        A, B = race.car("a", t), race.car("b", t)
        T0, TF = race.t_go, race.t_finish

        # ── Cronómetro y vuelta (arriba izquierda) ──
        if t >= T0 - 3:
            el = max(0.0, min(t, TF) - T0)
            _panel(d, (40, 150, 420, 300))
            d.text((70, 168), "VUELTA 1/1", font=self.f_small, fill=(255, 255, 255, 230))
            d.text((70, 214), f"{int(el // 60):02d}:{el % 60:05.2f}", font=self.f_mid, fill=(255, 255, 255, 255))
        # ── Clasificación (arriba derecha, sin invadir el lateral de iconos) ──
        if t >= T0:
            order = ["a", "b"] if A.s >= B.s else ["b", "a"]
            gap_m = abs(A.s - B.s)
            v_ = max(10, (A.speed + B.speed) / 2)
            _panel(d, (500, 150, 940, 300))
            for i, k in enumerate(order):
                y = 168 + i * 62
                d.rectangle((522, y + 6, 536, y + 46), fill=self.colors[k])
                d.text((552, y), f"{i + 1}  {self.names[k]}", font=self.f_small, fill=(255, 255, 255, 255))
                if i == 1 and t < TF:
                    d.text((922, y + 8), f"+{gap_m / v_:.2f}s", font=self.f_tiny, fill=(255, 220, 120, 255), anchor="ra")

        # ── Velocímetro del coche protagonista del plano ──
        sh = race.shot_at(vt)
        focus = sh.get("car") or race.leader(t)
        c = A if focus == "a" else B
        if T0 - 1 <= t <= TF + 0.5 and not race.is_slowmo(vt):
            x0, y0 = 60, 1330
            _panel(d, (x0, y0, x0 + 420, y0 + 170))
            kmh = int(c.speed * 3.6)
            d.rectangle((x0, y0 + 12, x0 + 12, y0 + 158), fill=self.colors[focus])
            d.text((x0 + 30, y0 + 14), f"{kmh:3d}", font=self.f_big, fill=(255, 255, 255, 255))
            d.text((x0 + 236, y0 + 66), "KM/H", font=self.f_tiny, fill=(200, 200, 200, 255))
            d.text((x0 + 340, y0 + 20), f"{c.gear}ª", font=self.f_mid, fill=(255, 220, 0, 255))
            # barra de revoluciones
            frac = max(0, min(1, (c.rpm - 1000) / 8500))
            for i in range(20):
                col = (80, 220, 120, 255) if i < 13 else (255, 200, 0, 255) if i < 17 else (255, 40, 40, 255)
                if i / 20 > frac:
                    col = (60, 60, 70, 200)
                d.rectangle((x0 + 36 + i * 18, y0 + 132, x0 + 50 + i * 18, y0 + 150), fill=col)
            d.text((x0 + 4, y0 - 40), self.names[focus], font=self.f_tiny, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))

        # ── Cuenta atrás / salida ──
        if T0 - 3 <= t < T0 + 1.0:
            if t < T0:
                n = 3 - int((t - (T0 - 3)) // 1)
                _stroke_text(d, (W // 2, 760), str(n), _font(220), (255, 255, 255, 255), 12)
            else:
                _stroke_text(d, (W // 2, 760), "¡YA!", _font(200), (120, 255, 120, 255), 12)
        # ── Cámara lenta / foto finish ──
        if race.is_slowmo(vt):
            _stroke_text(d, (W // 2, 420), "FOTO FINISH", _font(110), (255, 230, 0, 255), 10)
            d.text((W // 2, 520), "● CÁMARA LENTA", font=self.f_small, fill=(255, 80, 80, 255), anchor="mm")
        # ── Ganador ──
        if t > TF + 0.6:
            w = race.spec.winner
            _panel(d, (90, 380, 990, 560), 24, (8, 10, 16, 200))
            d.rectangle((90, 380, 990, 392), fill=self.colors[w])
            _stroke_text(d, (W // 2, 440), "GANADOR", self.f_mid, (255, 255, 255, 255), 0)
            _stroke_text(d, (W // 2, 505), self.names[w], _font(80), self.colors[w], 6)
        # ── Título inicial ──
        if vt < 2.6:
            a = int(255 * min(1, (2.6 - vt) / 0.4))
            _panel(d, (90, 380, 990, 540), 24, (8, 10, 16, min(200, a)))
            size = 64
            while size > 30 and d.textlength(race.spec.title.upper(), font=_font(size)) > 840:
                size -= 2
            d.text((W // 2, 460), race.spec.title.upper(), font=_font(size), fill=(255, 255, 255, a), anchor="mm")

        # ── Subtítulos ──
        for cue in self.cues:
            if cue["start"] <= vt < cue["end"] + 0.05:
                words = cue["words"]
                texts = [w[0].upper() for w in words]
                widths = [d.textlength(tx, font=self.f_sub) for tx in texts]
                space = d.textlength(" ", font=self.f_sub)
                total = sum(widths) + space * (len(widths) - 1)
                lines = [[0, len(texts)]]
                if total > W * 0.84 and len(texts) > 1:
                    lines = [[0, len(texts) // 2 + len(texts) % 2], [len(texts) // 2 + len(texts) % 2, len(texts)]]
                for li, (i0, i1) in enumerate(lines):
                    lw = sum(widths[i0:i1]) + space * (i1 - i0 - 1)
                    x = (W - lw) / 2
                    y = 1120 + li * 92 - (len(lines) - 1) * 46
                    for k in range(i0, i1):
                        active = words[k][1] <= vt < words[k][2] + 0.05
                        d.text((x, y), texts[k], font=self.f_sub, fill=(255, 212, 0, 255) if active else (255, 255, 255, 255), stroke_width=9, stroke_fill=(0, 0, 0, 255), anchor="lm")
                        x += widths[k] + space
                break
        return img


def render_hud(race, lines, out_dir, f0=0, f1=None):
    os.makedirs(out_dir, exist_ok=True)
    hud = HUD(race, lines)
    f1 = race.frames - 1 if f1 is None else f1
    for f in range(f0, f1 + 1):
        hud.frame(f).save(os.path.join(out_dir, f"h{f:05d}.png"), compress_level=1)
