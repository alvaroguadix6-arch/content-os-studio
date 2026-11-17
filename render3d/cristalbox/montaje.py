"""Montaje del anuncio de Cristalbox: voz + música moderna + efectos + subtítulos → MP4 1080×1920.

Todo el audio, salvo la voz (Kokoro-82M, Apache 2.0), se sintetiza por código: libre de derechos.

    python montaje.py --narracion dir/ --arte arte/ --frames frames/ --out anuncio.mp4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "gravedad"))
from montaje import SR, add, ass_time, env, noise, onepole, read_wav, write_wav  # noqa: E402  (gravedad/montaje.py)

BPM = 118
BEAT = 60 / BPM
CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]  # Lam · Fa · Do · Sol (MIDI)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, n, ph=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f + ph) % 1) - 1


def highpass(x, fc):
    return x - onepole(x, fc)


def sweep_lp(x, f0, f1):
    """Filtro paso bajo que se abre poco a poco (en bloques de 20 ms)."""
    out = np.zeros_like(x)
    blk = int(0.02 * SR)
    nb = max(1, len(x) // blk + 1)
    for i in range(nb):
        a, b = i * blk, min(len(x), (i + 1) * blk)
        if a >= b:
            break
        fc = f0 * (f1 / f0) ** (i / nb)
        out[a:b] = onepole(x[max(0, a - blk):b], fc)[-(b - a):]
    return out


def music(tl, n):
    out = np.zeros(n)
    drop, soft, end = tl.e2, tl.e4, tl.e5
    # pad (siempre): acordes con sierras desafinadas, filtrado
    bar = 4 * BEAT
    t = 0.0
    k = 0
    while t < tl.duration:
        m = int(bar * SR) + int(0.3 * SR)
        seg = np.zeros(m)
        for note in CHORDS[k % 4]:
            for det in (-0.006, 0.0, 0.006):
                seg += saw(hz(note) * (1 + det), m, ph=det * 10)
        fc = 700 if t < drop else (1500 if t < end else 900)
        seg = onepole(onepole(seg, fc), fc) * env(m, 0.08, 9.0) * np.minimum(1, (m - np.arange(m)) / (0.3 * SR))
        add(out, t, seg, 0.022 if t >= drop else 0.03)
        t += bar
        k += 1
    # ritmo desde el «drop» (tras el impacto y la pregunta)
    b = drop
    i = 0
    while b < end + 0.05:
        strong = b < soft or b >= end - 0.01
        nk = int(0.28 * SR)
        tt = np.arange(nk) / SR
        kick = np.sin(2 * np.pi * np.cumsum(45 + 95 * np.exp(-tt * 28)) / SR) * np.exp(-tt * 9)
        add(out, b, kick, 0.55 if strong else 0.38)
        if i % 2 == 1:  # palmada en 2 y 4
            nc = int(0.18 * SR)
            clap = highpass(onepole(noise(nc, i), 2600), 900) * env(nc, 0.002, 0.05)
            add(out, b, clap, 0.32 if strong else 0.18)
        for h in (0.0, 0.5):  # charles en corcheas
            nh = int(0.05 * SR)
            hat = highpass(noise(nh, 1000 + i * 2 + int(h * 2)), 6000) * env(nh, 0.001, 0.015)
            add(out, b + h * BEAT, hat, (0.10 if h else 0.05) * (1 if strong else 0.6))
        # bajo en corcheas con «bombeo»
        ch = CHORDS[int((b - drop) / (4 * BEAT)) % 4]
        for h in (0.0, 0.5):
            nb = int(0.24 * SR)
            bs = onepole(saw(hz(ch[0] - 24), nb), 380) * env(nb, 0.005, 0.16)
            add(out, b + h * BEAT, bs, 0.16 if h else 0.11)
        # arpegio en semicorcheas
        for q in range(4):
            note = ch[(i * 4 + q) % 3] + (12 if q % 2 else 0)
            na = int(0.16 * SR)
            pl = onepole(saw(hz(note), na) + 0.5 * np.sign(np.sin(2 * np.pi * hz(note) * np.arange(na) / SR)), 2400) * env(na, 0.002, 0.07)
            add(out, b + q * BEAT / 4, pl, 0.035 if strong else 0.025)
        b += BEAT
        i += 1
    # subida (riser) hacia el «drop»
    rl = 2.6
    nr = int(rl * SR)
    tt = np.arange(nr) / SR
    riser = sweep_lp(noise(nr, 77), 300, 7000) * (tt / rl) ** 2 + 0.3 * np.sin(2 * np.pi * np.cumsum(200 + 700 * (tt / rl) ** 2) / SR) * (tt / rl) ** 2
    add(out, drop - rl, riser, 0.18)
    # golpes de impacto en el «drop» y en el logotipo
    for th, g in ((drop, 0.55), (end + 0.15, 0.75)):
        nn = int(1.8 * SR)
        tt = np.arange(nn) / SR
        boom = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-tt * 10)) / SR) * np.exp(-tt * 2.2) + 0.4 * onepole(noise(nn, int(th * 10)), 900) * np.exp(-tt * 6)
        add(out, th, boom, g)
    # cola final: acorde largo que se apaga
    nn = int((tl.duration - end) * SR) + SR
    tt = np.arange(nn) / SR
    tail = sum(np.sin(2 * np.pi * hz(m_ + 12) * tt) for m_ in CHORDS[0]) * np.exp(-tt * 0.6)
    add(out, end + 0.15, onepole(tail, 3000), 0.04)
    fade = np.clip((tl.duration - np.arange(n) / SR) / 1.2, 0, 1)
    return out * fade


def sfx(tl, n):
    out = np.zeros(n)
    # interior del coche en marcha (rodadura y aire)
    m = int(tl.e2 * SR) + int(0.4 * SR)
    tt = np.arange(m) / SR
    road = onepole(noise(m, 3), 220) * 1.6 + 0.25 * onepole(noise(m, 4), 1800)
    road *= np.minimum(1, tt / 0.3) * np.clip((tl.e2 + 0.3 - tt) / 0.4, 0, 1)
    add(out, 0.0, road, 0.22)
    # piedra contra la luna: golpe seco + «tic» de cristal + crujido
    nn = int(0.6 * SR)
    tt = np.arange(nn) / SR
    hit = highpass(noise(nn, 5), 2500) * np.exp(-tt * 80) * 1.4
    ting = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, d in ((3150, 14), (4720, 18), (6080, 22), (2210, 11))) * 0.35
    add(out, tl.impact, hit + ting, 0.9)
    rng = np.random.default_rng(9)

    def crackle(t0, dur, dens, g):
        for _ in range(int(dur * dens)):
            tc = t0 + dur * rng.random() ** 1.6
            nc = int(0.012 * SR)
            c = highpass(noise(nc, int(rng.integers(1e6))), 3000) * env(nc, 0.0005, 0.003)
            add(out, tc, c, g * rng.uniform(0.3, 1.0))

    crackle(tl.impact + 0.02, 0.5, 70, 0.5)
    crackle(tl.L["problema"]["words"][5][1], 1.6, 40, 0.35)
    # transiciones: «whoosh» en cada corte
    for _, c, _ in tl.shots[1:]:
        nw = int(0.55 * SR)
        w = sweep_lp(noise(nw, int(c * 100)), 500, 6000) * np.sin(np.linspace(0, np.pi, nw)) ** 2
        add(out, c - 0.3, w, 0.3)
    # ventosas al colocar la luna
    nt = int(0.35 * SR)
    tt = np.arange(nt) / SR
    thunk = np.sin(2 * np.pi * (150 * np.exp(-tt * 6) + 60) * tt) * np.exp(-tt * 16) + 0.3 * highpass(noise(nt, 12), 1500) * np.exp(-tt * 60)
    add(out, tl.e3 + 0.55, thunk, 0.5)
    add(out, tl.e3 + 0.95, thunk, 0.4)
    # pistola de calor del tintado
    nh = int((tl.s_faro - tl.s_tin) * SR)
    tt = np.arange(nh) / SR
    hiss = onepole(highpass(noise(nh, 13), 900), 3500) * np.sin(np.pi * tt / (nh / SR)) ** 0.5
    add(out, tl.s_tin, hiss, 0.12)
    # pulidora del faro
    npol = int(1.2 * SR)
    tt = np.arange(npol) / SR
    pol = (np.tanh(2 * np.sin(2 * np.pi * 118 * tt)) + 0.3 * np.sin(2 * np.pi * 236 * tt) + 0.4 * onepole(noise(npol, 14), 1200)) * np.sin(np.pi * tt / 1.2)
    add(out, tl.s_faro + 0.15, onepole(pol, 2000), 0.13)
    # pitidos de calibración correcta
    nbp = int(0.09 * SR)
    beep = np.sin(2 * np.pi * 1760 * np.arange(nbp) / SR) * env(nbp, 0.003, 0.05)
    t_ok = tl.s_adas + (tl.s_cam - tl.s_adas) * 0.55
    add(out, t_ok, beep, 0.22)
    add(out, t_ok + 0.13, beep, 0.22)
    # brillo al aparecer el logotipo
    ns = int(1.6 * SR)
    tt = np.arange(ns) / SR
    shimmer = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * (2 + i)) for i, f in enumerate((1760, 2637, 3520, 4186))) * 0.25
    add(out, tl.e5 + 0.2, shimmer, 0.35)
    return out


def subtitles(tl, path):
    """Subtítulos (2-3 palabras, palabra activa en amarillo Cristalbox). El cierre ya va rotulado en pantalla."""
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter,74,&H0001D1FF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,5,2,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for key in ("problema", "solucion", "servicios", "confianza"):
        group = []
        for w in tl.L[key]["words"]:
            group.append(w)
            if len(group) == 3 or w[0][-1:] in ",.:;!?" or (len(group) == 2 and len("".join(g[0] for g in group)) > 13):
                ev.append(group)
                group = []
        if group:
            ev.append(group)
    lines = []
    for i, g in enumerate(ev):
        start, end = g[0][1], g[-1][2] + 0.05
        if i + 1 < len(ev):
            end = min(end, ev[i + 1][0][1])
        txt = "".join(f"{{\\k{max(1, int(round((b - a) * 100)))}}}{w.upper()} " for w, a, b in g).strip()
        nch = len(" ".join(w for w, _, _ in g))
        sc = min(100, int(100 * 17 / max(1, nch)))
        pop = f"{{\\pos(540,1600)\\fscx{int(sc * .85)}\\fscy{int(sc * .85)}\\t(0,110,\\fscx{int(sc * 1.03)}\\fscy{int(sc * 1.03)})\\t(110,180,\\fscx{sc}\\fscy{sc})}}"
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{pop}{txt}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracion", required=True)
    ap.add_argument("--arte", required=True)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from anuncio import FPS, V0, Timeline

    nar = json.load(open(os.path.join(a.narracion, "narracion.json"), encoding="utf-8"))
    tl = Timeline(nar)
    n = int(tl.duration * SR)
    voice = np.zeros(n)
    v = read_wav(os.path.join(a.narracion, "narracion.wav"))
    i0 = int(V0 * SR)
    voice[i0: i0 + len(v)] = v[: n - i0]
    mus = music(tl, n)
    fx = sfx(tl, n)
    venv = onepole((np.abs(voice) > 0.02).astype(float), 3)
    duck = 1 - 0.5 * np.clip(venv * 2.5, 0, 1)
    mix = 1.0 * voice + 0.75 * duck * mus + 0.8 * fx
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    work = os.path.dirname(os.path.abspath(a.out))
    wav = os.path.join(work, "mezcla.wav")
    write_wav(wav, mix)
    ass = os.path.join(work, "subtitulos.ass")
    subtitles(tl, ass)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-start_number", "0", "-i", os.path.join(a.frames, "f%05d.jpg"),
           "-i", wav, "-vf", f"subtitles={ass}:fontsdir=/usr/share/fonts/opentype/inter", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-movflags", "+faststart", "-shortest", a.out]
    subprocess.run(cmd, check=True)
    print("✅ Anuncio listo:", a.out)


if __name__ == "__main__":
    main()
