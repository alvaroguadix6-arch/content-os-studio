"""Montaje final: narración + música de suspense + efectos + subtítulos → MP4 1080×1920.

    python montaje.py --narracion dir/ --arte arte/ --frames frames/ --out video.mp4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SR = 44100


def onepole(x, fc):
    from scipy.signal import lfilter

    a = math.exp(-2 * math.pi * fc / SR)
    return lfilter([1 - a], [1, -a], x)


def noise(n, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def env(n, a, r):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))


def add(track, t, sig, gain=1.0):
    i = int(t * SR)
    if i >= len(track) or i + len(sig) <= 0:
        return
    j = min(len(track), i + len(sig))
    track[max(0, i):j] += gain * sig[max(0, -i): j - i]


def music(tl, n):
    t = np.arange(n) / SR
    out = np.zeros(n)
    # dron de suspense en Re menor con batido
    drone = 0.5 * np.sin(2 * np.pi * 36.7 * t) + 0.35 * np.sin(2 * np.pi * 55.0 * t + 0.3 * np.sin(0.2 * t)) + 0.15 * np.sin(2 * np.pi * 73.4 * t)
    level = np.interp(t, [0, tl.t_float, tl.t_return - 0.5, tl.t_return - 0.05, tl.t_return + 0.6, tl.t_after, tl.duration],
                      [0.45, 0.55, 0.95, 0.0, 0.0, 0.55, 0.4])
    out += 0.18 * drone * level
    # cuerdas: acordes que suben medio tono durante la ingravidez
    for k, (a, b) in enumerate(((0, tl.t_float), (tl.t_float, tl.t_return - 0.05), (tl.t_return + 0.6, tl.duration))):
        i0, i1 = int(a * SR), int(b * SR)
        tt = np.arange(i1 - i0) / SR
        bend = 1 + (0.06 * tt / max(0.1, b - a) if k == 1 else 0)
        seg = np.zeros(i1 - i0)
        for f in ((146.8, 174.6, 220.0), (155.6, 185.0, 233.1), (110.0, 130.8, 164.8))[k]:
            ph = 2 * np.pi * np.cumsum(f * bend) / SR
            seg += np.sign(np.sin(ph)) * 0.3 + np.sin(ph)
        seg = onepole(seg, 900)
        fade = np.minimum(1, tt / 1.0) * np.minimum(1, (tt[-1] - tt) / 0.3 + 1e-3)
        out[i0:i1] += 0.02 * seg * fade
    # pulso (latido) que acelera antes de que vuelva la gravedad
    bt = tl.t_float
    while bt < tl.t_return - 0.1:
        bpm = np.interp(bt, [tl.t_float, tl.t_return], [70, 130])
        m = int(0.25 * SR)
        kick = np.sin(2 * np.pi * 52 * np.arange(m) / SR) * env(m, 0.004, 0.08)
        add(out, bt, kick, 0.5)
        add(out, bt + 0.18, kick, 0.3)
        bt += 60 / bpm
    return out


def sfx(tl, an, n):
    out = np.zeros(n)
    # ambiente de ciudad (tráfico lejano) hasta que flotan
    city = onepole(noise(int(tl.t_float * SR), 1), 500) * 0.25
    city *= np.minimum(1, np.arange(len(city)) / SR / 1.0)
    add(out, 0, city)
    for th in (1.6, 6.8):  # bocinas
        m = int(0.35 * SR)
        hn = np.sign(np.sin(2 * np.pi * 415 * np.arange(m) / SR)) * env(m, 0.01, 0.25) * 0.08
        add(out, th, onepole(hn, 1800))
    # despegue: «whoosh» ascendente y viento suave mientras flotan
    m = int(1.6 * SR)
    add(out, tl.t_float - 0.3, onepole(noise(m, 2), 2500) * np.sin(np.linspace(0, np.pi, m)) ** 2 * 0.4)
    m = int((tl.t_return - tl.t_float) * SR)
    wind = onepole(noise(m, 3), 700) * (0.5 + 0.5 * np.sin(np.arange(m) / SR * 0.8)) * 0.18
    add(out, tl.t_float, wind * np.minimum(1, np.arange(m) / SR / 1.5))
    # salto: «fiuuu»
    m = int(1.0 * SR)
    tt = np.arange(m) / SR
    add(out, tl.t_jump, np.sin(2 * np.pi * np.cumsum(500 + 900 * tt) / SR) * env(m, 0.05, 0.5) * 0.15)
    # burbujas de agua
    for k in range(10):
        m = int(0.25 * SR)
        tt = np.arange(m) / SR
        blob = np.sin(2 * np.pi * (300 + 500 * tt / 0.25 + k * 30) * tt) * env(m, 0.005, 0.07) * 0.18
        add(out, tl.t_water + 0.3 + k * 0.55, blob)
    # silencio tenso + latido fuerte justo antes de que vuelva
    m = int(0.3 * SR)
    add(out, tl.t_return - 0.8, np.sin(2 * np.pi * 45 * np.arange(m) / SR) * env(m, 0.004, 0.1) * 0.7)
    # impactos: coches (golpe metálico + cristales), personas (golpe sordo), agua (salpicadura)
    for a in an.actors:
        ti = an.landed_at(a)
        if a.kind == "car":
            m = int(1.4 * SR)
            tt = np.arange(m) / SR
            crash = noise(m, int(ti * 100)) * np.exp(-tt * 5) * 0.9 + np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 4) * 0.8
            metal = sum(np.sin(2 * np.pi * f * tt) for f in (523, 1176, 2093)) * np.exp(-tt * 6) * 0.1
            glass = onepole(noise(m, 9), 9000) - onepole(noise(m, 9), 3000)
            add(out, ti, crash + metal + glass * np.exp(-tt * 3) * 0.6)
        else:
            m = int(0.4 * SR)
            tt = np.arange(m) / SR
            add(out, ti, np.sin(2 * np.pi * (90 * np.exp(-tt * 8) + 40) * tt) * np.exp(-tt * 12) * 0.6)
    m = int(1.6 * SR)
    tt = np.arange(m) / SR
    splash = onepole(noise(m, 21), 3500) * np.exp(-tt * 2.5) * 0.5
    add(out, tl.t_return + 0.9, splash)
    # sirenas lejanas en las consecuencias
    m = int((tl.duration - tl.t_after) * SR)
    tt = np.arange(m) / SR
    siren = np.sin(2 * np.pi * np.cumsum(np.where((tt % 1.4) < 0.7, 740, 587)) / SR)
    add(out, tl.t_after, onepole(siren, 1500) * 0.06 * np.minimum(1, tt / 1.5))
    return out


def write_wav(path, x):
    st = np.stack([x, x], axis=1)
    pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def read_wav(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32767
        return x if w.getnchannels() == 1 else x.reshape(-1, w.getnchannels()).mean(axis=1)


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def subtitles(nar, path):
    """Subtítulos ASS: bloques de 2-3 palabras, palabra activa en amarillo (karaoke) y rebote."""
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,84,&H0000D4FF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for ln in nar["lines"]:
        words = ln["words"]
        group = []
        for w in words:
            group.append(w)
            if len(group) == 3 or w[0][-1:] in ",.:;!?" or (len(group) == 2 and len("".join(g[0] for g in group)) > 13):
                ev.append(group)
                group = []
        if group:
            ev.append(group)
    lines = []
    for i, g in enumerate(ev):
        start = g[0][1]
        end = g[-1][2] + 0.05
        if i + 1 < len(ev):
            end = min(end, ev[i + 1][0][1])
        txt = "".join(f"{{\\k{max(1, int(round((b - a) * 100)))}}}{w.upper()} " for w, a, b in g).strip()
        nch = len(" ".join(w for w, _, _ in g))
        sc = min(100, int(100 * 15.5 / max(1, nch)))  # que nunca se salga del ancho (≈15 car. a 84 px)
        pop = f"{{\\pos(540,1240)\\fscx{int(sc*.8)}\\fscy{int(sc*.8)}\\t(0,120,\\fscx{int(sc*1.04)}\\fscy{int(sc*1.04)})\\t(120,200,\\fscx{sc}\\fscy{sc})}}"
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{pop}{txt}")
    # texto final
    tq = nar["lines"][-2]["start"]
    end = nar["duration"] + 0.6
    lines.append(f"Dialogue: 1,{ass_time(tq)},{ass_time(end)},Sub,,0,0,0,,{{\\pos(540,620)\\fs96\\c&H00FFFFFF&\\fad(250,0)}}¿SOBREVIVIRÍAS?")
    lines.append(f"Dialogue: 1,{ass_time(nar['lines'][-1]['start'] + 1.2)},{ass_time(end)},Sub,,0,0,0,,{{\\pos(540,760)\\fs60\\c&H0000D4FF&\\fad(250,0)}}¡DÉJALO EN COMENTARIOS!")
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracion", required=True)
    ap.add_argument("--arte", required=True)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--estilo", default="realista", choices=["realista", "plano"],
                    help="plano: ilustración plana con el texto ya dibujado arriba (sin subtítulos ASS)")
    a = ap.parse_args()
    if a.estilo == "plano":
        from plano import Animator
    else:
        from animar import Animator

    nar = json.load(open(os.path.join(a.narracion, "narracion.json"), encoding="utf-8"))
    an = Animator(nar, a.arte)
    tl = an.tl
    n = int(tl.duration * SR)
    voice = np.zeros(n)
    v = read_wav(os.path.join(a.narracion, "narracion.wav"))
    voice[: min(n, len(v))] = v[:n]
    mus = music(tl, n)
    fx = sfx(tl, an, n)
    # la música baja cuando habla el narrador (y mucho más que antes: la voz manda)
    venv = onepole((np.abs(voice) > 0.02).astype(float), 3)
    duck = 1 - 0.6 * np.clip(venv * 2.5, 0, 1)
    mix = 1.0 * voice + 0.55 * duck * mus + 0.7 * (1 - 0.35 * np.clip(venv * 2.5, 0, 1)) * fx
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    work = os.path.dirname(os.path.abspath(a.out))
    wav = os.path.join(work, "mezcla.wav")
    write_wav(wav, mix)
    ass = os.path.join(work, "subtitulos.ass")
    subtitles(nar, ass)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-start_number", "0", "-i", os.path.join(a.frames, "f%05d.jpg"),
           "-i", wav, *([] if a.estilo == "plano" else ["-vf", f"subtitles={ass}:fontsdir=/usr/share/fonts"]), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-movflags", "+faststart", "-shortest", a.out]
    subprocess.run(cmd, check=True)
    # también un .srt por si la red social lo pide aparte
    def ts(x):
        ms = int(x * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    with open(os.path.splitext(a.out)[0] + ".srt", "w", encoding="utf-8") as f:
        for i, ln in enumerate(nar["lines"], 1):
            f.write(f"{i}\n{ts(ln['start'])} --> {ts(ln['end'])}\n{ln['text']}\n\n")
    print("✅ Vídeo listo:", a.out)


if __name__ == "__main__":
    main()
