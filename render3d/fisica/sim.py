"""NIVEL OCULTO · Simulaciones de física (formato «satisfying»): fondo negro, figuras de colores, colisiones reales.

Motor 2D propio (NumPy): gravedad, choques elásticos entre figuras (impulsos + corrección de solapes) y contra las
paredes (segmentos, incluidos los bordes de la abertura), con varios subpasos por fotograma. Todo se programa a
partir de un archivo de reglas JSON, así que se pueden generar más vídeos cambiando solo las reglas:

    python sim.py reglas/mas2_por_escape.json --out video.mp4            # vídeo completo (60 fps)
    python sim.py reglas/mas2_por_escape.json --stats                    # solo simula y muestra el contador

Reglas disponibles (ver reglas/*.json): figuras_por_escape, gravedad, rebote, velocidad_inicial, acelerar_por_escape,
abertura, lado, rotacion (contenedor girando), obstaculos (círculos fijos), max_figuras, duracion, semilla, titulo.
El audio (notas en cada choque, campanita en cada escape y música suave) se sintetiza aquí mismo: sin licencias.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
import os
import subprocess
import sys
import time
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
SS = 2  # superresolución para bordes limpios
SR = 44100
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
SHAPES = ("circulo", "cuadrado", "triangulo", "hexagono", "rombo")
PENTA = [261.63, 293.66, 329.63, 392.00, 440.00]  # escala pentatónica (suena bien aunque coincidan muchas notas)


def font(style, size):
    key = (style, int(size))
    if key not in font.cache:
        font.cache[key] = ImageFont.truetype(FONT.format(style), int(size))
    return font.cache[key]


font.cache = {}


class Rules:
    defaults = dict(titulo="+2 BALLS EACH ESCAPE", figuras_por_escape=2, figuras_iniciales=2, gravedad=900.0, rebote=1.0,
                    velocidad_inicial=650.0, acelerar_por_escape=0.0, velocidad_max=1500.0, abertura=78.0, lado=780.0,
                    centro=[540.0, 1040.0], radio=13.0, rotacion=0.0, obstaculos=[], max_figuras=900, duracion=60.0,
                    fps=60, subpasos=4, semilla=7, etiqueta="BALLS", marca="NIVEL OCULTO", final="")

    def __init__(self, path=None, **over):
        d = dict(self.defaults)
        if path:
            d.update(json.load(open(path, encoding="utf-8")))
        d.update({k: v for k, v in over.items() if v is not None})
        self.__dict__.update(d)


class Sim:
    def __init__(self, R: Rules):
        self.R = R
        self.rng = np.random.default_rng(R.semilla)
        n = R.max_figuras + 200
        self.pos = np.zeros((n, 2))
        self.vel = np.zeros((n, 2))
        self.rad = np.full(n, R.radio)
        self.ang = np.zeros(n)
        self.spin = np.zeros(n)
        self.hue = np.zeros(n)
        self.shape = np.zeros(n, int)
        self.state = np.zeros(n, int)  # 0 libre, 1 dentro, 2 escapando (cae fuera)
        self.t = 0.0
        self.escapes = 0
        self.leaks = 0
        self.events = []  # (t, tipo, intensidad, nota)
        self.angle = 0.0
        self.flash = {}
        for _ in range(R.figuras_iniciales):
            self.spawn()

    # ───── geometría del contenedor ─────
    def walls(self):
        """Segmentos del cuadrado con una abertura centrada abajo (girados si hay rotación)."""
        cx, cy = self.R.centro
        h = self.R.lado / 2
        g = self.R.abertura / 2
        pts = [((-h, -h), (h, -h)), ((h, -h), (h, h)), ((-h, h), (-h, -h)), ((-h, h), (-g, h)), ((g, h), (h, h))]
        c, s = math.cos(self.angle), math.sin(self.angle)
        segs = []
        for (ax, ay), (bx, by) in pts:
            segs.append(((cx + ax * c - ay * s, cy + ax * s + ay * c), (cx + bx * c - by * s, cy + bx * s + by * c)))
        return segs

    def inside(self, p):
        cx, cy = self.R.centro
        c, s = math.cos(-self.angle), math.sin(-self.angle)
        x, y = p[..., 0] - cx, p[..., 1] - cy
        lx, ly = x * c - y * s, x * s + y * c
        h = self.R.lado / 2
        return (np.abs(lx) < h + 2) & (np.abs(ly) < h + 2)

    # ───── figuras ─────
    def spawn(self):
        free = np.where(self.state == 0)[0]
        if len(free) == 0 or (self.state == 1).sum() >= self.R.max_figuras:
            return False
        i = free[0]
        cx, cy = self.R.centro
        for _ in range(20):  # sitio libre cerca del centro
            p = np.array([cx, cy]) + self.rng.normal(0, self.R.lado * 0.12, 2)
            ins = self.state == 1
            if not ins.any() or np.min(np.hypot(*(self.pos[ins] - p).T) - self.rad[ins]) > self.R.radio * 1.1:
                break
        a = self.rng.uniform(0, 2 * math.pi)
        sp = self.R.velocidad_inicial * (1 + self.R.acelerar_por_escape * self.escapes)
        self.pos[i] = p
        self.vel[i] = (math.cos(a) * sp, math.sin(a) * sp)
        self.ang[i] = self.rng.uniform(0, 2 * math.pi)
        self.spin[i] = self.rng.uniform(-6, 6)
        self.nspawn = getattr(self, "nspawn", 0) + 1
        self.hue[i] = (0.11 + self.nspawn * 0.618034) % 1  # colores bien distintos (razón áurea)
        self.shape[i] = self.rng.integers(0, len(SHAPES))
        self.state[i] = 1
        self.flash[int(i)] = 0.25
        return True

    @property
    def count(self):
        return int((self.state == 1).sum())

    # ───── paso de física ─────
    def step(self, dt):
        R = self.R
        self.angle += R.rotacion * dt
        act = np.where(self.state > 0)[0]
        self.vel[act, 1] += R.gravedad * dt
        sp = np.hypot(self.vel[act, 0], self.vel[act, 1])
        k = np.minimum(1, R.velocidad_max / np.maximum(sp, 1e-6))
        self.vel[act] *= k[:, None]
        self.pos[act] += self.vel[act] * dt
        self.ang[act] += self.spin[act] * dt
        ins = np.where(self.state == 1)[0]
        if len(ins):
            iters = 1 if len(ins) < 150 else 3  # más pasadas cuando hay mucha densidad
            for _ in range(iters):
                self.collide_pairs(ins)
                self.collide_walls(ins)  # las paredes, al final: nada las atraviesa
            self.contain(ins)
        # escapes: las que salen por la abertura
        ins = np.where(self.state == 1)[0]
        if len(ins):
            out = ~self.inside(self.pos[ins])
            for i in ins[out]:
                cx, cy = R.centro
                c, s_ = math.cos(-self.angle), math.sin(-self.angle)
                lx = (self.pos[i, 0] - cx) * c - (self.pos[i, 1] - cy) * s_
                ly = (self.pos[i, 0] - cx) * s_ + (self.pos[i, 1] - cy) * c
                if not (abs(lx) < R.abertura / 2 + R.radio and ly > 0):
                    self.leaks += 1  # control de calidad: no debería salir nunca por una pared
                self.state[i] = 2
                self.escapes += 1
                self.events.append((self.t, "escape", 1.0, int(self.hue[i] * 5)))
                for _ in range(R.figuras_por_escape):
                    if self.spawn():
                        self.events.append((self.t, "spawn", 0.6, 0))
        # las que caen fuera de la pantalla dejan sitio
        gone = (self.state == 2) & (self.pos[:, 1] > H + 80)
        self.state[gone] = 0
        self.t += dt

    def contain(self, ins):
        """Red de seguridad: ninguna figura puede quedar fuera del cuadrado salvo por la abertura."""
        R = self.R
        cx, cy = R.centro
        c, s_ = math.cos(-self.angle), math.sin(-self.angle)
        x, y = self.pos[ins, 0] - cx, self.pos[ins, 1] - cy
        lx, ly = x * c - y * s_, x * s_ + y * c
        lim = R.lado / 2 - self.rad[ins]
        gapcol = np.abs(lx) < R.abertura / 2 - self.rad[ins] * 0.2
        nlx = np.clip(lx, -lim, lim)
        nly = np.where(gapcol, np.minimum(ly, R.lado), np.clip(ly, -lim, lim))
        bad = (nlx != lx) | (nly != ly)
        if bad.any():
            c2, s2 = math.cos(self.angle), math.sin(self.angle)
            self.pos[ins[bad], 0] = cx + nlx[bad] * c2 - nly[bad] * s2
            self.pos[ins[bad], 1] = cy + nlx[bad] * s2 + nly[bad] * c2

    def collide_walls(self, ins):
        R = self.R
        p, v, r = self.pos[ins], self.vel[ins], self.rad[ins]
        for (ax, ay), (bx, by) in self.walls():
            a = np.array([ax, ay])
            ab = np.array([bx - ax, by - ay])
            L2 = ab @ ab
            tt = np.clip(((p - a) @ ab) / L2, 0, 1)
            q = a + tt[:, None] * ab
            dvec = p - q
            dist = np.hypot(dvec[:, 0], dvec[:, 1])
            hit = dist < r
            if not hit.any():
                continue
            n = dvec[hit] / np.maximum(dist[hit], 1e-6)[:, None]
            # normal hacia el interior del contenedor (si el centro está en el segmento, usa la del segmento)
            cpos = np.array(R.centro)
            nseg = np.array([-ab[1], ab[0]]) / math.sqrt(L2)
            if (cpos - a) @ nseg < 0:
                nseg = -nseg
            mid = (tt[hit] > 0.001) & (tt[hit] < 0.999)
            n[mid] = nseg
            pen = r[hit] - dist[hit]
            p[hit] += n * pen[:, None]
            vn = np.sum(v[hit] * n, axis=1)
            approach = vn < 0
            vv = v[hit]
            vv[approach] -= ((1 + R.rebote) * vn[approach])[:, None] * n[approach]
            v[hit] = vv
            for j in np.where(approach)[0][:3]:
                self.events.append((self.t, "pared", float(min(1, -vn[j] / 900)), int(self.hue[ins[np.where(hit)[0][j]]] * 5)))
        self.pos[ins], self.vel[ins] = p, v
        for ob in R.obstaculos:  # círculos fijos
            o = np.array(ob[:2])
            orad = ob[2]
            d = self.pos[ins] - o
            dist = np.hypot(d[:, 0], d[:, 1])
            hit = dist < self.rad[ins] + orad
            if hit.any():
                idx = ins[hit]
                n = d[hit] / np.maximum(dist[hit], 1e-6)[:, None]
                self.pos[idx] = o + n * (self.rad[idx] + orad)[:, None]
                vn = np.sum(self.vel[idx] * n, axis=1)
                ap = vn < 0
                self.vel[idx[ap]] -= ((1 + R.rebote) * vn[ap])[:, None] * n[ap]
                for j in idx[ap][:2]:
                    self.events.append((self.t, "obstaculo", 0.8, int(self.hue[j] * 5)))

    def collide_pairs(self, ins):
        if len(ins) < 2:
            return
        R = self.R
        p = self.pos[ins]
        # rejilla: solo se comparan figuras cercanas (rápido aunque haya cientos)
        cell = 2 * R.radio * 1.05
        key = np.floor(p / cell).astype(int)
        order = np.lexsort((key[:, 1], key[:, 0]))
        d = p[:, None, :] - p[None, :, :] if len(ins) <= 260 else None
        if d is not None:
            dist = np.hypot(d[..., 0], d[..., 1])
            rs = self.rad[ins][:, None] + self.rad[ins][None, :]
            ii, jj = np.where(np.triu(dist < rs, 1))
        else:
            from scipy.spatial import cKDTree
            pairs = cKDTree(p).query_pairs(2 * R.radio, output_type="ndarray")
            ii, jj = (pairs[:, 0], pairs[:, 1]) if len(pairs) else (np.array([], int), np.array([], int))
        del order
        if len(ii) == 0:
            return
        a, b = ins[ii], ins[jj]
        dv = self.pos[a] - self.pos[b]
        dist = np.maximum(np.hypot(dv[:, 0], dv[:, 1]), 1e-6)
        n = dv / dist[:, None]
        pen = (self.rad[a] + self.rad[b] - dist)
        corr = n * (pen / 2)[:, None]
        np.add.at(self.pos, a, corr)
        np.add.at(self.pos, b, -corr)
        rv = np.sum((self.vel[a] - self.vel[b]) * n, axis=1)
        ap = rv < 0
        imp = (-(1 + R.rebote) * rv / 2)[ap][:, None] * n[ap]
        np.add.at(self.vel, a[ap], imp)
        np.add.at(self.vel, b[ap], -imp)
        strong = np.where(ap)[0]
        if len(strong):
            j = strong[np.argmax(-rv[strong])]
            if -rv[j] > 250:
                self.events.append((self.t, "choque", float(min(1, -rv[j] / 1200)), int(self.hue[a[j]] * 5)))


# ───── dibujo ─────
def rgb(h, s=0.85, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def shape_pts(kind, x, y, r, a):
    nsides = {"cuadrado": 4, "triangulo": 3, "hexagono": 6, "rombo": 4}[kind]
    off = math.pi / 4 if kind == "cuadrado" else 0
    rr = r * (1.25 if kind == "triangulo" else 1.12 if kind == "cuadrado" else 1.05)
    pts = []
    for i in range(nsides):
        t = a + off + i * 2 * math.pi / nsides
        k = 1.0 if kind != "rombo" else (1.2 if i % 2 == 0 else 0.8)
        pts.append((x + math.cos(t) * rr * k, y + math.sin(t) * rr * k))
    return pts


class Painter:
    def __init__(self, sim: Sim):
        self.sim = sim
        self.R = sim.R

    def frame(self, shown_count, pulse):
        R, sim = self.R, self.sim
        big = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
        d = ImageDraw.Draw(big)
        glow = Image.new("RGB", (W // 2, H // 2), (0, 0, 0))
        gd = ImageDraw.Draw(glow)
        # contenedor blanco con abertura
        for (ax, ay), (bx, by) in sim.walls():
            d.line([(ax * SS, ay * SS), (bx * SS, by * SS)], fill=(255, 255, 255), width=10 * SS)
            for (x, y) in ((ax, ay), (bx, by)):
                d.ellipse([(x - 5) * SS, (y - 5) * SS, (x + 5) * SS, (y + 5) * SS], fill=(255, 255, 255))
            gd.line([(ax / 2, ay / 2), (bx / 2, by / 2)], fill=(120, 120, 140), width=8)
        for ob in R.obstaculos:
            x, y, r = ob[:3]
            d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], outline=(255, 255, 255), width=6 * SS)
        act = np.where(sim.state > 0)[0]
        for i in act:
            x, y = sim.pos[i]
            if y > H + 40 or y < -40:
                continue
            r = sim.rad[i]
            col = rgb(sim.hue[i])
            fl = sim.flash.get(int(i), 0)
            if fl > 0:
                col = tuple(min(255, int(c + (255 - c) * fl * 3)) for c in col)
            kind = SHAPES[sim.shape[i]]
            if kind == "circulo":
                d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=col)
            else:
                d.polygon([(px * SS, py * SS) for px, py in shape_pts(kind, x, y, r, sim.ang[i])], fill=col)
            gd.ellipse([(x - r * 1.6) / 2, (y - r * 1.6) / 2, (x + r * 1.6) / 2, (y + r * 1.6) / 2], fill=col)
        img = big.reduce(SS)
        g = glow.filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
        arr = np.asarray(img, np.int16) + (np.asarray(g, np.int16) * 0.55).astype(np.int16)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        # textos: título, contador y marca
        d1 = ImageDraw.Draw(img)
        d1.text((540, 250), R.titulo, font=font("ExtraBold", 66), fill=(255, 255, 255), anchor="mm")
        s = 1 + 0.18 * pulse
        d1.text((540, 420), f"{shown_count}", font=font("ExtraBold", int(150 * s)), fill=(255, 214, 70), anchor="mm")
        d1.text((540, 530), R.etiqueta, font=font("Bold", 40), fill=(200, 200, 210), anchor="mm")
        if R.marca:
            d1.text((540, 1800), " ".join(R.marca), font=font("ExtraBold", 30), fill=(120, 120, 130), anchor="mm")
        return img


# ───── audio ─────
def synth_audio(events, dur, path, mood_seed=3):
    n = int(dur * SR) + SR
    out = np.zeros(n)
    tt = np.arange(int(0.6 * SR)) / SR
    cache = {}

    def note(freq, kind):
        key = (round(freq, 1), kind)
        if key not in cache:
            if kind == "escape":
                s = sum(np.sin(2 * np.pi * freq * m * tt) * np.exp(-tt * (5 + 2 * m)) / m for m in (1, 2, 3)) * 0.9
            elif kind == "spawn":
                s = np.sin(2 * np.pi * (freq * (1 + 0.6 * tt))[: len(tt)] * tt) * np.exp(-tt * 18) * 0.5
            else:
                s = (np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(2 * np.pi * freq * 2.01 * tt)) * np.exp(-tt * 22)
            cache[key] = s
        return cache[key]

    # como mucho unas pocas notas por cada 1/40 s (las más fuertes): suena musical, no a ruido
    events = sorted(events, key=lambda e: e[0])
    slot, bucket = -1, []

    def flush(b):
        b.sort(key=lambda e: -e[2])
        for k, (t, kind, inten, nt) in enumerate(b[:4]):
            if kind == "escape":
                f = PENTA[nt % 5] * 2
            elif kind == "spawn":
                f = 880.0
            else:
                f = PENTA[nt % 5] * (1 if kind == "pared" else 1.5)
            s = note(f, kind)
            g = (0.5 if kind == "escape" else 0.25 if kind == "spawn" else 0.18) * (0.4 + 0.6 * inten) / (1 + 0.4 * k)
            j = int(t * SR)
            m = min(len(s), n - j)
            if m > 0:
                out[j:j + m] += g * s[:m]

    for e in events:
        sl = int(e[0] * 40)
        if sl != slot:
            if bucket:
                flush(bucket)
            slot, bucket = sl, []
        bucket.append(e)
    if bucket:
        flush(bucket)
    # música suave de fondo: acordes con pulso (sintetizada)
    t = np.arange(n) / SR
    chords = [(261.63, 329.63, 392.0), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 246.94, 293.66)]
    bar = 2.0
    mus = np.zeros(n)
    for k in range(int(dur / bar) + 1):
        a = int(k * bar * SR)
        seg = np.arange(int(bar * SR)) / SR
        env = np.minimum(1, seg / 0.3) * np.minimum(1, (bar - seg) / 0.5)
        c = sum(np.sin(2 * np.pi * f / 2 * seg) + 0.3 * np.sin(2 * np.pi * f * seg) for f in chords[k % 4]) * env
        m = min(len(c), n - a)
        if m > 0:
            mus[a:a + m] += c[:m]
    beat = (np.sin(2 * np.pi * 55 * t) * np.exp(-((t % 0.5) * 18))) * 0.6
    mus = mus * 0.05 + beat * 0.10
    mus *= np.minimum(1, t / 1.5) * np.clip((dur - t) / 2.0, 0, 1)
    mix = out + mus
    mix /= max(1.0, np.abs(mix).max() / 0.9)
    pcm = (np.stack([mix, mix], 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ───── bucle principal ─────
def run(rules_path, out=None, stats=False, seconds=None):
    R = Rules(rules_path)
    if seconds:
        R.duracion = seconds
    sim = Sim(R)
    frames = int(R.duracion * R.fps)
    dt = 1 / (R.fps * R.subpasos)
    painter = Painter(sim) if out else None
    proc = None
    tmp = None
    if out:
        tmp = os.path.splitext(out)[0] + "_video.mp4"
        proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                 "-r", str(R.fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt",
                                 "yuv420p", tmp], stdin=subprocess.PIPE)
    shown = float(sim.count)
    last = sim.count
    pulse = 0.0
    t0 = time.time()
    log = []
    for f in range(frames):
        for _ in range(R.subpasos):
            sim.step(dt)
        for k in list(sim.flash):
            sim.flash[k] -= 1 / R.fps
            if sim.flash[k] <= 0:
                del sim.flash[k]
        c = sim.count
        if c != last:
            pulse = 1.0
            last = c
        pulse *= 0.85
        shown = c
        if f % R.fps == 0:
            log.append((f // R.fps, c, sim.escapes))
            if stats or f % (R.fps * 10) == 0:
                print(f"[fisica] t={f / R.fps:5.1f}s  figuras={c:4d}  escapes={sim.escapes:4d}  fugas={sim.leaks}  ({time.time() - t0:.0f}s)", flush=True)
        if proc:
            proc.stdin.write(painter.frame(int(shown), pulse).tobytes())
    if proc:
        proc.stdin.close()
        proc.wait()
        wav = os.path.splitext(out)[0] + "_audio.wav"
        synth_audio(sim.events, R.duracion, wav)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-movflags", "+faststart", "-shortest", out], check=True)
        os.remove(tmp)
        os.remove(wav)
        print("✅ Vídeo listo:", out, flush=True)
    return log, sim


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("reglas")
    ap.add_argument("--out")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--segundos", type=float)
    a = ap.parse_args()
    run(a.reglas, a.out, a.stats, a.segundos)
