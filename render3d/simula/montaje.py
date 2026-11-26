"""Montaje común: narración + música ambiental + efectos → MP4 1080×1920 listo para redes (~20 MB).

    python montaje.py <video> --narracion dir/ --frames frames/ --out salida.mp4
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(HERE), "gravedad"))
_spec = importlib.util.spec_from_file_location("grav_montaje", os.path.join(os.path.dirname(HERE), "gravedad", "montaje.py"))
base = importlib.util.module_from_spec(_spec)  # utilidades de audio del vídeo de la gravedad
_spec.loader.exec_module(base)

SR, add, env, noise, onepole, read_wav, write_wav = base.SR, base.add, base.env, base.noise, base.onepole, base.read_wav, base.write_wav

MOODS = {  # acordes (Hz) por estado de ánimo
    "suspense": [(146.8, 174.6, 220.0), (130.8, 155.6, 196.0), (116.5, 146.8, 174.6), (110.0, 130.8, 164.8)],
    "epico": [(110.0, 138.6, 164.8), (130.8, 164.8, 196.0), (146.8, 185.0, 220.0), (123.5, 155.6, 185.0)],
    "espacio": [(98.0, 123.5, 146.8), (87.3, 110.0, 130.8), (110.0, 130.8, 164.8), (98.0, 116.5, 146.8)],
    "alegre": [(130.8, 164.8, 196.0), (174.6, 220.0, 261.6), (146.8, 174.6, 220.0), (196.0, 246.9, 293.7)],
}


def saw(f, n, ph=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f + ph) % 1) - 1


def music(v, n, mood="suspense", bpm=84):
    t = np.arange(n) / SR
    out = np.zeros(n)
    plan = v.music_plan()
    level = np.interp(t, [p[0] for p in plan], [p[1] for p in plan])
    root = MOODS[mood][0][0] / 4
    drone = 0.5 * np.sin(2 * np.pi * root * t) + 0.35 * np.sin(2 * np.pi * root * 1.5 * t + 0.3 * np.sin(0.2 * t)) + 0.15 * np.sin(2 * np.pi * root * 2 * t)
    out += 0.16 * drone * (0.4 + 0.6 * level)
    # pad que cambia de acorde en cada escena
    cuts = [s[0] for s in v.scenes] + [v.duration]
    for k in range(len(cuts) - 1):
        a, b = cuts[k], cuts[k + 1]
        m = int((b - a + 0.8) * SR)
        seg = np.zeros(m)
        for f in MOODS[mood][k % 4]:
            for det in (-0.004, 0.0, 0.004):
                seg += saw(f * (1 + det), m, det * 7)
        seg = onepole(onepole(seg, 900), 900)
        e = np.minimum(1, np.arange(m) / SR / 0.6) * np.minimum(1, (m - np.arange(m)) / SR / 0.8)
        add(out, a, seg * e, 0.016)
    # pulso suave (bombo + charles) que sigue la intensidad
    beat = 60 / bpm
    bt = 0.0
    i = 0
    while bt < v.duration - 0.5:
        lv = float(np.interp(bt, [p[0] for p in plan], [p[1] for p in plan]))
        if lv > 0.25:
            nk = int(0.3 * SR)
            tt = np.arange(nk) / SR
            kick = np.sin(2 * np.pi * np.cumsum(42 + 70 * np.exp(-tt * 25)) / SR) * np.exp(-tt * 8)
            add(out, bt, kick, 0.32 * lv)
            nh = int(0.04 * SR)
            hat = (noise(nh, i) - onepole(noise(nh, i), 5000)) * env(nh, 0.001, 0.012)
            add(out, bt + beat / 2, hat, 0.06 * lv)
        bt += beat
        i += 1
    fade = np.clip((v.duration - t) / 1.5, 0, 1) * np.clip(t / 0.4, 0, 1)
    return out * fade


def sfx_sound(kind, seed=0):
    rng = np.random.default_rng(seed)
    if kind == "whoosh":
        m = int(0.6 * SR)
        x = rng.uniform(-1, 1, m)
        return (onepole(x, 3000) - onepole(x, 400)) * np.sin(np.linspace(0, np.pi, m)) ** 2 * 1.4
    if kind == "boom":
        m = int(2.0 * SR)
        tt = np.arange(m) / SR
        return np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-tt * 8)) / SR) * np.exp(-tt * 2.2) + 0.5 * onepole(rng.uniform(-1, 1, m), 600) * np.exp(-tt * 4)
    if kind == "pop":
        m = int(0.18 * SR)
        tt = np.arange(m) / SR
        return 0.7 * np.sin(2 * np.pi * (500 + 900 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 22)
    if kind == "tick":
        m = int(0.03 * SR)
        x = rng.uniform(-1, 1, m)
        return (x - onepole(x, 4000)) * env(m, 0.0005, 0.006) * 0.8
    if kind == "wind":
        m = int(3.0 * SR)
        x = onepole(rng.uniform(-1, 1, m), 700) * 3
        return x * np.sin(np.linspace(0, np.pi, m)) * (0.7 + 0.3 * np.sin(np.arange(m) / SR * 2.1))
    if kind == "rumble":
        m = int(2.5 * SR)
        return onepole(rng.uniform(-1, 1, m), 120) * 5 * np.sin(np.linspace(0, np.pi, m)) ** 0.5
    if kind == "splash":
        m = int(1.4 * SR)
        x = rng.uniform(-1, 1, m)
        return (onepole(x, 5000) - onepole(x, 600)) * np.exp(-np.arange(m) / SR * 3) * 1.2
    if kind == "crack":
        m = int(0.9 * SR)
        out = np.zeros(m)
        for _ in range(26):
            j = int(rng.uniform(0, 0.85) * m)
            k = int(0.012 * SR)
            c = rng.uniform(-1, 1, k)
            out[j:j + k] += (c - onepole(c, 2500)) * np.exp(-np.arange(k) / SR * 400) * rng.uniform(0.3, 1)
        return out
    if kind == "click":
        m = int(0.5 * SR)
        tt = np.arange(m) / SR
        return 0.8 * np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 14) + 0.4 * rng.uniform(-1, 1, m) * np.exp(-tt * 80)
    if kind == "shimmer":
        m = int(1.6 * SR)
        tt = np.arange(m) / SR
        return sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * (2 + i)) for i, f in enumerate((1318.5, 1760, 2637, 3520))) * 0.3
    if kind == "beep":
        m = int(0.1 * SR)
        return np.sin(2 * np.pi * 1760 * np.arange(m) / SR) * env(m, 0.003, 0.05)
    if kind == "riser":
        m = int(1.8 * SR)
        tt = np.arange(m) / SR
        return 0.4 * np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt / 1.8) ** 2) / SR) * (tt / 1.8) ** 2 + 0.3 * onepole(rng.uniform(-1, 1, m), 3000) * (tt / 1.8) ** 3
    if kind == "drip":
        m = int(0.25 * SR)
        tt = np.arange(m) / SR
        return 0.5 * np.sin(2 * np.pi * (900 + 1500 * tt) * tt) * np.exp(-tt * 25)
    if kind == "horn":
        m = int(0.7 * SR)
        tt = np.arange(m) / SR
        return 0.25 * np.tanh(3 * (np.sin(2 * np.pi * 330 * tt) + np.sin(2 * np.pi * 415 * tt))) * np.minimum(1, tt * 30) * np.minimum(1, (0.7 - tt) * 20)
    return np.zeros(1)


def sfx(v, n):
    out = np.zeros(n)
    for i, (ts, _) in enumerate(v.scenes[1:]):
        add(out, ts - 0.32, sfx_sound("whoosh", 100 + i), 0.28)
    for i, (ts, kind, g) in enumerate(v.sfx_events()):
        add(out, ts, sfx_sound(kind, i), g)
    return out


# Audio final: −14 LUFS (lo que usan las apps) y pico real ≤ −1 dBTP.
#  1) un limitador suave recorta los transitorios («tic», «pop») para que quepa la ganancia;
#  2) loudnorm en DOS pasadas (mide y aplica una ganancia lineal exacta: el volumen sale en −14);
#  3) un limitador final a −2 dBFS deja margen para el AAC.
PRE = "aresample=48000,alimiter=limit=0.56:level=0:attack=3:release=80"
POST = "aresample=48000,alimiter=limit=0.79:level=0:attack=2:release=60"


def audio_final(wav):
    import re as _re
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af",
                        PRE + ",loudnorm=I=-14:TP=-2:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = _re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr)
    if not m:  # sin medida: normalización de una pasada (también deja el pico controlado)
        return PRE + ",loudnorm=I=-14:TP=-2:LRA=11," + POST
    j = json.loads(m.group(0))
    return (PRE + f",loudnorm=I=-14:TP=-2:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}"
            f":measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}"
            ":linear=true," + POST)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--narracion", required=True)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    mod = importlib.import_module(a.video)
    nar = json.load(open(os.path.join(a.narracion, "narracion.json"), encoding="utf-8"))
    v = mod.VIDEO(nar)
    n = int(v.duration * SR)
    voice = np.zeros(n)
    vv = read_wav(os.path.join(a.narracion, "narracion.wav"))
    voice[: min(n, len(vv))] = vv[:n]
    mus = music(v, n, getattr(mod, "MOOD", "suspense"), getattr(mod, "BPM", 84))
    fx = sfx(v, n)
    venv = onepole((np.abs(voice) > 0.02).astype(float), 3)
    duck = 1 - 0.6 * np.clip(venv * 2.5, 0, 1)
    mix = voice + 0.6 * duck * mus + 0.65 * (1 - 0.35 * np.clip(venv * 2.5, 0, 1)) * fx
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    work = os.path.dirname(os.path.abspath(a.out))
    wav = os.path.join(work, "mezcla.wav")
    write_wav(wav, mix)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-start_number", "0", "-i", os.path.join(a.frames, "f%05d.jpg"),
           "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-af", audio_final(wav), "-ar", "48000", "-movflags", "+faststart", "-shortest", a.out]
    subprocess.run(cmd, check=True)
    print("✅ Vídeo listo:", a.out)


if __name__ == "__main__":
    main()
