"""NIVEL OCULTO · «¿A qué ritmo late su corazón?» — pixel art, 30 s, en bucle y sin voz.

Formato: plano continuo. Empieza bajo el mar con una ballena azul (≈2 latidos/min: su corazón late UNA vez en todo el
vídeo), la cámara sube a un iceberg bajo la aurora y se van apilando animales, cada uno con el corazón latiendo a su
ritmo real; la banda sonora son esos mismos latidos. Al final vuelve a la ballena: «este vídeo ha durado un latido».

Valores en reposo, aproximados (rangos habituales en fuentes veterinarias y divulgativas):
ballena azul ~2 lpm en inmersión (Goldbogen et al., PNAS 2019) · elefante ~30 · humano adulto 60-100 → 70 ·
perro mediano 60-140 → 100 · gato 120-140 → 130 · conejo 130-325 → 250 · ratón 500-700 → 600 ·
colibrí hasta ~1.200 en vuelo.

    python3 latidos.py salida.mp4
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

LW, LH, K = 270, 480, 5          # lienzo de trabajo; se recorta 216×384 y se amplía ×5 → 1080×1920
FPS, DUR = 30, 30.0
SR = 48000
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F = {s: ImageFont.truetype(MONO, s) for s in (8, 9, 10, 11, 13, 16, 20)}

SURF, GROUND, CX = 360, 340, 128   # superficie del mar, techo del iceberg, eje de la torre
WHALE = (128, 690)
CAM_UP, CAM_DOWN = 0, 430

# (clave, nombre, lpm, aparece, lado de la etiqueta, frecuencia del latido en Hz)
ANIMALS = [("elefante", "ELEFANTE", 30, 5.5, "L", 55), ("humano", "HUMANO", 70, 8.5, "R", 75),
           ("perro", "PERRO", 100, 11.5, "L", 95), ("gato", "GATO", 130, 14.5, "R", 125),
           ("conejo", "CONEJO", 250, 17.0, "L", 170), ("raton", "RATÓN", 600, 19.5, "R", 320),
           ("colibri", "COLIBRÍ", 1200, 22.0, "L", 520)]
STACK_END = 25.2                   # la cámara empieza a bajar
WHALE_BEAT = 0.3                   # único latido de la ballena (el siguiente sería en 30,3 s = el bucle)

HEART_S = [".r.r.", "rrrrr", ".rrr.", "..r.."]
HEART_B = [".rr.rr.", "rrrrrrr", "rrrrrrr", ".rrrrr.", "..rrr..", "...r..."]
RED, WHITE, YEL = (235, 40, 60), (245, 245, 245), (255, 214, 70)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def cam(t):
    if t < 3.0:
        return CAM_DOWN
    if t < 5.5:
        return CAM_DOWN + (CAM_UP - CAM_DOWN) * ease((t - 3.0) / 2.5)
    if t < STACK_END:
        return CAM_UP
    return CAM_UP + (CAM_DOWN - CAM_UP) * ease((t - STACK_END) / 2.4)


def pulse(t, bpm, t0):
    if t < t0:
        return 0.0
    ph = ((t - t0) * bpm / 60.0) % 1.0
    return math.exp(-ph * (60.0 / bpm) * 9)  # decae en ~0,1 s


# ───── capa de fondo ─────
rnd = random.Random(7)
STARS = [(rnd.randrange(LW), rnd.randrange(0, 300), rnd.random() * 6.28, rnd.choice([1, 1, 1, 2])) for _ in range(90)]
BUBBLES = [(rnd.randrange(LW), rnd.random() * 400, rnd.uniform(8, 20)) for _ in range(30)]


def sky_col(y):
    if y < SURF:
        k = max(0.0, y) / SURF
        return (int(6 + 16 * k), int(8 + 40 * k), int(26 + 55 * k))
    k = min(1.0, (y - SURF) / 520)
    return (int(16 - 13 * k), int(56 - 48 * k), int(104 - 80 * k))


def background(img, d, t, cy):
    for sy in range(LH):
        d.line([(0, sy), (LW, sy)], fill=sky_col(sy + cy))
    # estrellas
    for x, y, ph, s in STARS:
        sy = y - cy
        if 0 <= sy < LH and math.sin(t * 2 + ph) > -0.4:
            d.rectangle([x, sy, x + s - 1, sy + s - 1], fill=(220, 230, 255))
    # aurora
    lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for x in range(0, LW, 2):
        top = 60 + 14 * math.sin(x * 0.045 + t * 0.6) + 7 * math.sin(x * 0.13 - t * 1.3) - cy
        ln = 34 + 14 * math.sin(x * 0.07 + t * 0.9)
        for j in range(0, int(ln), 2):
            a = int(120 * (1 - j / ln) * (0.6 + 0.4 * math.sin(x * 0.02 + t)))
            col = (60, 230, 150, a) if j < ln * 0.6 else (120, 90, 220, a // 2)
            ld.rectangle([x, top + j, x + 1, top + j + 1], fill=col)
    # rayos de luz bajo el agua
    for i in range(5):
        x0 = 20 + i * 60 + 10 * math.sin(t * 0.5 + i)
        y0 = SURF - cy
        ld.polygon([(x0, y0), (x0 + 14, y0), (x0 - 40, y0 + 330), (x0 - 70, y0 + 330)], fill=(120, 180, 255, 18))
    img.alpha_composite(lay)


def iceberg(img, d, cy):
    lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.polygon([(52, SURF - cy), (210, SURF - cy), (228, 420 - cy), (190, 478 - cy), (96, 490 - cy), (40, 425 - cy)], fill=(110, 170, 210, 150))
    img.alpha_composite(lay)
    d.polygon([(58, SURF - cy), (74, 344 - cy), (98, GROUND - cy), (160, GROUND - cy), (186, 345 - cy), (204, SURF - cy)], fill=(222, 240, 250))
    d.polygon([(150, GROUND - cy), (160, GROUND - cy), (186, 345 - cy), (204, SURF - cy), (165, SURF - cy)], fill=(170, 205, 228))
    d.line([(98, GROUND - cy), (160, GROUND - cy)], fill=(250, 255, 255))


def sea(d, t, cy):
    for x in range(0, LW, 3):
        y = SURF - cy + round(1.5 * math.sin(x * 0.12 + t * 2.2))
        d.rectangle([x, y, x + 2, y], fill=(110, 170, 220))
        if (x // 3 + int(t * 4)) % 9 == 0:
            d.rectangle([x, y - 1, x + 1, y - 1], fill=(220, 240, 255))


def bubbles(d, t, cy):
    for x, y0, sp in BUBBLES:
        y = 880 - ((y0 + t * sp) % 480)
        sy = y - cy
        if y > SURF + 4 and 0 <= sy < LH:
            d.rectangle([x + round(2 * math.sin(t + y0)), sy, x + 1 + round(2 * math.sin(t + y0)), sy + 1], fill=(150, 200, 240))


# ───── sprites ─────
def heart(d, x, y, p, scale=1):
    pat = HEART_B if p > 0.45 else HEART_S
    w, h = len(pat[0]) * scale, len(pat) * scale
    for j, row in enumerate(pat):
        for i, c in enumerate(row):
            if c == "r":
                x0, y0 = x - w // 2 + i * scale, y - h // 2 + j * scale
                d.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=RED if p > 0.15 else (170, 30, 50))


def whale(d, t, cy):
    x, y = WHALE[0], WHALE[1] - cy
    body, belly, ol = (70, 96, 132), (128, 150, 172), (30, 40, 62)
    d.ellipse([x - 110, y - 26, x + 100, y + 24], fill=body, outline=ol)
    d.polygon([(x + 90, y - 12), (x + 135, y - 3), (x + 135, y + 3), (x + 90, y + 14)], fill=body, outline=ol)
    sw = round(4 * math.sin(t * 1.2))
    d.polygon([(x + 130, y), (x + 150, y - 16 + sw), (x + 146, y), (x + 150, y + 16 + sw)], fill=body, outline=ol)
    d.chord([x - 104, y - 6, x + 70, y + 24], 0, 180, fill=belly)
    for i in range(6):
        d.line([(x - 96 + i * 4, y + 8 + i), (x - 30 + i * 4, y + 16 + i // 2)], fill=(105, 125, 150))
    d.polygon([(x - 30, y + 14), (x - 4, y + 18), (x - 44, y + 36)], fill=body, outline=ol)
    d.rectangle([x - 86, y - 6, x - 85, y - 5], fill=(10, 12, 20))
    return x - 8, y - 4


def elephant(d, x, y):
    g, gd = (128, 128, 144), (92, 92, 108)
    for lx in (-20, -11, 4, 13):
        d.rectangle([x + lx, y - 13, x + lx + 6, y], fill=gd if lx in (-11, 13) else g)
        d.rectangle([x + lx, y - 1, x + lx + 6, y], fill=(200, 200, 205))
    d.ellipse([x - 26, y - 32, x + 22, y - 9], fill=g)
    d.ellipse([x + 12, y - 38, x + 34, y - 18], fill=g)
    d.ellipse([x + 6, y - 36, x + 20, y - 15], fill=gd)
    d.rectangle([x + 28, y - 24, x + 33, y - 6], fill=g)
    d.rectangle([x + 31, y - 7, x + 36, y - 4], fill=g)
    d.line([(x + 26, y - 19), (x + 32, y - 15)], fill=(245, 240, 225), width=2)
    d.rectangle([x + 26, y - 31, x + 27, y - 30], fill=(15, 15, 20))
    d.line([(x - 26, y - 22), (x - 31, y - 12)], fill=gd)
    return (x - 4, y - 21), y - 32


def human(d, x, y):
    skin, hair, shirt, pants = (232, 182, 142), (60, 40, 28), (220, 72, 60), (52, 72, 132)
    d.rectangle([x - 4, y - 9, x - 1, y], fill=pants)
    d.rectangle([x + 1, y - 9, x + 4, y], fill=pants)
    d.rectangle([x - 5, y - 19, x + 5, y - 9], fill=shirt)
    d.rectangle([x - 8, y - 18, x - 6, y - 10], fill=skin)
    d.rectangle([x + 6, y - 24, x + 8, y - 17], fill=skin)  # saluda
    d.rectangle([x - 4, y - 27, x + 4, y - 20], fill=skin)
    d.rectangle([x - 4, y - 28, x + 4, y - 26], fill=hair)
    d.rectangle([x + 2, y - 24, x + 2, y - 24], fill=(20, 20, 25))
    return (x - 1, y - 15), y - 28


def dog(d, x, y, t):
    c, cd = (176, 116, 64), (116, 74, 42)
    for lx in (-8, -4, 3, 7):
        d.rectangle([x + lx, y - 5, x + lx + 2, y], fill=cd)
    d.ellipse([x - 10, y - 13, x + 9, y - 4], fill=c)
    d.ellipse([x + 5, y - 18, x + 15, y - 9], fill=c)
    d.rectangle([x + 13, y - 13, x + 17, y - 10], fill=c)
    d.rectangle([x + 6, y - 17, x + 8, y - 11], fill=cd)
    d.rectangle([x + 16, y - 13, x + 17, y - 12], fill=(20, 20, 20))
    w = round(2 * math.sin(t * 14))
    d.line([(x - 10, y - 10), (x - 15, y - 15 + w)], fill=cd, width=2)
    return (x - 1, y - 8), y - 18


def cat(d, x, y, t):
    c, cd = (236, 146, 54), (184, 104, 32)
    d.ellipse([x - 6, y - 12, x + 6, y], fill=c)
    d.ellipse([x - 5, y - 19, x + 5, y - 10], fill=c)
    d.polygon([(x - 5, y - 16), (x - 4, y - 22), (x - 1, y - 18)], fill=c)
    d.polygon([(x + 5, y - 16), (x + 4, y - 22), (x + 1, y - 18)], fill=c)
    d.line([(x - 3, y - 8), (x + 3, y - 8)], fill=cd)
    d.rectangle([x - 3, y - 16, x - 2, y - 15], fill=(30, 60, 30))
    d.rectangle([x + 2, y - 16, x + 3, y - 15], fill=(30, 60, 30))
    s = round(3 * math.sin(t * 3))
    d.line([(x + 6, y - 2), (x + 11, y - 4), (x + 12 + s, y - 10)], fill=cd, width=2)
    return (x, y - 6), y - 21


def rabbit(d, x, y, t):
    w, g, pk = (240, 240, 245), (198, 198, 210), (240, 150, 172)
    d.ellipse([x - 6, y - 10, x + 6, y], fill=w)
    d.ellipse([x - 4, y - 17, x + 4, y - 9], fill=w)
    tw = 1 if math.sin(t * 5) > 0.7 else 0
    d.rectangle([x - 3, y - 25 + tw, x - 1, y - 16], fill=w)
    d.rectangle([x + 1, y - 25, x + 3, y - 16], fill=w)
    d.rectangle([x - 2, y - 23 + tw, x - 2, y - 18], fill=pk)
    d.rectangle([x + 2, y - 23, x + 2, y - 18], fill=pk)
    d.rectangle([x + 2, y - 14, x + 2, y - 13], fill=(20, 20, 25))
    d.rectangle([x - 7, y - 4, x - 6, y - 3], fill=g)
    return (x, y - 5), y - 25


def mouse(d, x, y, t):
    m, pk = (156, 156, 168), (240, 150, 172)
    d.ellipse([x - 5, y - 6, x + 5, y], fill=m)
    d.ellipse([x + 1, y - 9, x + 5, y - 5], fill=m)
    d.rectangle([x + 2, y - 8, x + 3, y - 7], fill=pk)
    d.rectangle([x + 5, y - 3, x + 6, y - 3], fill=pk)
    d.line([(x - 5, y - 2), (x - 9, y - 4), (x - 11, y - 1)], fill=pk)
    return (x - 1, y - 3), y - 9


def hummingbird(d, x, y, t):
    e, ed, r = (60, 204, 122), (30, 130, 82), (220, 40, 70)
    d.ellipse([x - 5, y - 3, x + 4, y + 2], fill=e)
    d.rectangle([x + 2, y - 4, x + 5, y - 1], fill=e)
    d.rectangle([x + 3, y - 1, x + 4, y], fill=r)
    d.line([(x + 6, y - 3), (x + 11, y - 2)], fill=(30, 30, 30))
    d.line([(x - 5, y), (x - 9, y + 3)], fill=ed, width=2)
    up = int(t * FPS) % 2 == 0
    d.polygon([(x - 1, y - 2), (x - 6, y - 10 if up else y + 6), (x + 2, y - 2)], fill=(180, 240, 210))
    return (x - 1, y), y - 4


DRAW = {"elefante": lambda d, x, y, t: elephant(d, x, y), "humano": lambda d, x, y, t: human(d, x, y), "perro": dog,
        "gato": cat, "conejo": rabbit, "raton": mouse, "colibri": hummingbird}


# ───── texto en píxeles ─────
def ptext(d, x, y, s, size, col=WHITE, anchor="mm"):
    d.fontmode = "1"
    d.text((x, y), s, font=F[size], fill=col, anchor=anchor, stroke_width=1, stroke_fill=(10, 10, 18))


def card(d, lines, y0=150):
    for i, (s, size, col) in enumerate(lines):
        ptext(d, LW // 2, y0 + sum(ln[1] + 5 for ln in lines[:i]), s, size, col)


def lpm(n):
    return f"{n:,}".replace(",", ".") + " LPM"


def frame(t):
    cy = round(cam(t))
    img = Image.new("RGBA", (LW, LH), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    background(img, d, t, cy)
    d = ImageDraw.Draw(img)
    bubbles(d, t, cy)
    hx, hy = whale(d, t, cy)
    pw = pulse(t, 2, WHALE_BEAT) if t < 10 else 0.0
    if pw > 0.02:
        r = int(6 + 40 * (1 - pw))
        d.ellipse([hx - r, hy - r, hx + r, hy + r], outline=(255, 90, 110))
    heart(d, hx, hy, pw, 3 if pw > 0.3 else 2)
    iceberg(img, d, cy)
    d = ImageDraw.Draw(img)
    sea(d, t, cy)
    # torre de animales
    y = GROUND - cy
    labels = []
    for key, name, bpm, t0, side, _ in ANIMALS:
        if t < t0:
            break
        k = (t - t0) / 0.45
        if key == "colibri":
            x = CX + 2 + round(140 * (1 - ease(k)))
            yy = y - 8 + round(2 * math.sin(t * 6))
        else:
            x = CX
            yy = y - round(150 * (1 - min(1, k)) ** 2)
        (hx, hy), top = DRAW[key](d, x, yy, t)
        heart(d, hx, hy, pulse(t, bpm, t0 + 0.4))
        labels.append((key, name, bpm, t0, side, hx, hy))
        if key != "colibri":
            y = top + (yy - y) + 1 if k < 1 else top + 1
    for key, name, bpm, t0, side, hx, hy in labels:
        if t - t0 > 0.6:
            x = hx - 34 if side == "L" else hx + 34
            ptext(d, x, hy, lpm(bpm), 9, YEL if t - t0 < 3.2 else WHITE)
    # textos
    if t < 3.4:
        card(d, [("¿A QUÉ RITMO", 16, WHITE), ("LATE SU CORAZÓN?", 16, WHITE), ("en reposo · valores aprox.", 9, (170, 190, 220))])
        if t > WHALE_BEAT + 0.2:
            ptext(d, WHALE[0] - 8, WHALE[1] - cy - 48, "BALLENA AZUL · 2 LPM", 10, YEL)
    for key, name, bpm, t0, side, _ in ANIMALS:
        if t0 + 0.4 < t < t0 + 2.8:
            card(d, [(name, 16, WHITE), (lpm(bpm), 20, YEL)])
    if t > 27.4:
        card(d, [("ESTE VÍDEO", 16, WHITE), ("HA DURADO", 16, WHITE), ("UN SOLO LATIDO", 16, YEL), ("DE BALLENA AZUL", 16, YEL)])
        ptext(d, LW // 2, 338, "NIVEL OCULTO", 10, (190, 200, 230))
    return img.convert("RGB").crop((27, 60, 243, 444)).resize((1080, 1920), Image.NEAREST)


# ───── sonido: los propios latidos ─────
def audio(path):
    n = int(DUR * SR)
    out = np.zeros(n)
    tt = np.arange(n) / SR

    def thump(t0, f, amp, dec, dub=True):
        for off, a in ((0.0, 1.0), (0.14, 0.6)) if dub else ((0.0, 1.0),):
            i0 = int((t0 + off) * SR)
            m = int(dec * 6 * SR)
            if i0 >= n:
                continue
            seg = np.arange(min(m, n - i0)) / SR
            env = np.exp(-seg / dec) * (1 - np.exp(-seg / 0.003))
            out[i0:i0 + len(seg)] += amp * a * env * np.sin(2 * np.pi * f * seg * (1 + 0.6 * np.exp(-seg / 0.02)))

    thump(WHALE_BEAT, 38, 1.0, 0.18)
    for key, name, bpm, t0, side, f in ANIMALS:
        per = 60.0 / bpm
        tb = t0 + 0.4
        while tb < STACK_END + 1.6:
            fade = min(1.0, max(0.0, (STACK_END + 1.6 - tb) / 1.6))
            dec = min(0.09, per * 0.18)
            thump(tb, f, (0.45 if bpm < 200 else 0.22) * fade, dec, dub=bpm <= 260)
            tb += per
        thump(t0 + 0.42, 900, 0.12, 0.01, dub=False)  # «pop» al aterrizar
    # ambiente: mar y un acorde suave
    noise = np.random.default_rng(1).standard_normal(n)
    sea_n = np.convolve(noise, np.ones(240) / 240, mode="same") * 0.25
    under = np.where((tt < 4.5) | (tt > 26.5), 1.0, 0.35)
    pad = sum(np.sin(2 * np.pi * fr * tt) for fr in (110, 164.8, 220)) * 0.025 * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 8))
    out += sea_n * under + pad
    out *= np.minimum(1, tt / 0.05) * np.minimum(1, (DUR - tt) / 0.05)
    out = out / max(1e-9, np.abs(out).max()) * 0.8
    st = (np.stack([out, out], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


def main(out):
    wav = out + ".wav"
    audio(wav)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
          f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS),
                          "-i", "-", "-i", wav, "-af", ln + ",aresample=48000", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for t in sys.argv[3:]:
            frame(float(t)).save(f"{sys.argv[2]}/l_{float(t):05.1f}.png")
    else:
        main(sys.argv[1])
