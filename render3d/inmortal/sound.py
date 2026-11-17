"""Sonido de «¿Qué pasaría si fueras inmortal?»: narración + música de suspense + efectos.
Todo generado por código (libre de derechos), salvo la voz Piper (licencia MIT)."""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audio import SR, _env, _noise, _onepole, synth_voice, write_wav  # noqa: E402
from story import ERAS, LIGHTNING_T  # noqa: E402


def narration(story, model, total_n, lively=True):
    """Narración continua: cada frase empieza en su momento y, si no cabe antes de la
    siguiente, se acelera un poco (hasta 1,4x) para no dejar huecos ni solaparse."""
    track = np.zeros(total_n)
    lines, cursor = [], 0.0
    items = list(story.narration())
    base = 1.15 if lively else 1.0
    for idx, (t, text) in enumerate(items):
        nxt = items[idx + 1][0] if idx + 1 < len(items) else story.duration - 0.3
        start = max(t, cursor + 0.08)
        window = max(0.8, nxt - start - 0.1)
        a = synth_voice(text, model, speed=base, lively=lively)
        if len(a) / SR > window:
            a = synth_voice(text, model, speed=min(1.4, base * (len(a) / SR) / window), lively=lively)
        i0 = int(start * SR)
        i1 = min(total_n, i0 + len(a))
        if i0 >= total_n:
            break
        track[i0:i1] += a[: i1 - i0]
        lines.append({"start": start, "end": i1 / SR, "text": text})
        cursor = i1 / SR
    return track, lines


def _tone(freq, n, kind="sin", phase=0.0):
    t = np.arange(n) / SR
    if kind == "saw":
        return 2 * ((t * freq + phase) % 1) - 1
    return np.sin(2 * np.pi * freq * t + phase)


def music(story, total_n):
    """Suspense: dron grave, pulso tipo latido, cuerdas que suben y un clímax con la gigante roja."""
    t = np.arange(total_n) / SR
    out = np.zeros(total_n)
    sh = {s["type"]: (s["start"], s["end"]) for s in story.shots}
    # Dron (Re menor) con batido lento
    drone = 0.5 * np.sin(2 * np.pi * 36.7 * t) + 0.35 * np.sin(2 * np.pi * 73.4 * t * (1 + 0.0008 * np.sin(t)))
    drone += 0.2 * np.sin(2 * np.pi * 110.0 * t + 0.4 * np.sin(2 * np.pi * 0.1 * t))
    intensity = np.interp(t, [0, 2, sh["siglo"][0], sh["ruinas"][0], sh["tierra"][0], sh["sol"][0], sh["sol"][0] + 6.5, sh["espacio"][0], story.duration],
                          [0.6, 0.35, 0.45, 0.55, 0.6, 0.75, 1.0, 0.3, 0.15])
    out += 0.16 * drone * intensity
    # Cuerdas (sierra filtrada) que cambian de acorde por escena
    chords = {"rayo": [146.8, 174.6, 220.0], "siglo": [130.8, 164.8, 196.0], "ruinas": [116.5, 146.8, 174.6],
              "tierra": [110.0, 138.6, 164.8], "sol": [98.0, 116.5, 146.8], "espacio": [73.4, 110.0, 146.8]}
    for name, (a, b) in sh.items():
        i0, i1 = int(a * SR), min(total_n, int(b * SR) + int(0.8 * SR))
        n = i1 - i0
        seg = np.zeros(n)
        for f in chords[name]:
            for det in (-0.004, 0.004):
                seg += _tone(f * (1 + det), n, "saw")
        seg = _onepole(seg, 700 if name != "sol" else 1400)
        env = np.minimum(1, np.arange(n) / SR / 1.2) * np.minimum(1, (n - np.arange(n)) / SR / 0.8)
        out[i0:i1] += 0.018 * seg * env
    # Latido (pulso) que acelera hasta la gigante roja
    bt = sh["siglo"][0]
    while bt < sh["espacio"][0]:
        bpm = np.interp(bt, [sh["siglo"][0], sh["sol"][0] + 6], [62, 110])
        for off, amp in ((0.0, 1.0), (0.22, 0.6)):
            m = int(0.28 * SR)
            k = np.sin(2 * np.pi * 48 * np.arange(m) / SR) * _env(m, 0.004, 0.09)
            j = int((bt + off) * SR)
            out[j:j + m] += 0.35 * amp * k[: len(out[j:j + m])]
        bt += 60 / bpm
    return out


def sfx(story, total_n):
    out = np.zeros(total_n)
    # Gancho: impacto + trueno del rayo
    n = int(2.5 * SR)
    tt = np.arange(n) / SR
    crack = _noise(n, 7) * np.exp(-tt * 9)
    rumble = _onepole(_noise(n, 8), 120) * np.exp(-tt * 1.2) * 6
    i0 = int(LIGHTNING_T * SR)
    out[i0:i0 + n] += (0.8 * crack + 0.9 * rumble)[: len(out[i0:i0 + n])]
    m = int(1.2 * SR)
    hit = np.sin(2 * np.pi * (30 + 80 * np.exp(-np.arange(m) / SR * 7)) * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 2.5)
    out[:m] += 0.6 * hit
    # Transiciones: whoosh antes de cada corte
    for s in story.shots[1:]:
        n = int(0.9 * SR)
        w = _onepole(_noise(n, int(s["start"] * 10)), 2500) * np.sin(np.linspace(0, np.pi, n)) ** 3
        j = max(0, int((s["start"] - 0.6) * SR))
        out[j:j + n] += 0.35 * w[: len(out[j:j + n])]
    # Rótulo de época: "braam" grave
    for a, _, _ in ERAS:
        n = int(2.2 * SR)
        tt = np.arange(n) / SR
        br = np.tanh(3 * (_tone(43.6, n, "saw") + 0.5 * _tone(87.3, n, "saw"))) * np.exp(-tt * 1.4)
        br = _onepole(br, 400)
        j = int(a * SR)
        out[j:j + n] += 0.32 * br[: len(out[j:j + n])]
    # Colapso del Sol: estallido
    sol0 = next(s["start"] for s in story.shots if s["type"] == "sol")
    n = int(3.0 * SR)
    tt = np.arange(n) / SR
    boom = _onepole(_noise(n, 11), 300) * np.exp(-tt * 1.5) * 4 + np.sin(2 * np.pi * 28 * tt) * np.exp(-tt * 1.2)
    j = int((sol0 + 7.0) * SR)
    out[j:j + n] += 0.6 * boom[: len(out[j:j + n])]
    # Final: silencio y un golpe suave al aparecer la pregunta
    fin = story.duration - 3.0
    n = int(2.5 * SR)
    tt = np.arange(n) / SR
    bell = (np.sin(2 * np.pi * 220 * tt) + 0.5 * np.sin(2 * np.pi * 330 * tt)) * np.exp(-tt * 1.3)
    j = int(fin * SR)
    out[j:j + n] += 0.25 * bell[: len(out[j:j + n])]
    return out


def _beat(kind, seed=0):
    """Efectos tipo dibujos animados, sintetizados."""
    rng = np.random.default_rng(seed)
    if kind == "bonk":
        n = int(0.45 * SR)
        tt = np.arange(n) / SR
        return 0.9 * np.sin(2 * np.pi * (620 * np.exp(-tt * 6) + 180) * tt) * np.exp(-tt * 9) + 0.5 * _onepole(rng.uniform(-1, 1, n), 1800) * np.exp(-tt * 30)
    if kind == "boing":
        n = int(0.6 * SR)
        tt = np.arange(n) / SR
        return 0.6 * np.sin(2 * np.pi * (220 + 160 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 3)) * tt) * np.exp(-tt * 4)
    if kind == "pop":
        n = int(0.12 * SR)
        tt = np.arange(n) / SR
        return 0.6 * np.sin(2 * np.pi * (900 - 600 * tt / 0.12) * tt) * np.exp(-tt * 40)
    if kind == "fall":
        n = int(0.6 * SR)
        tt = np.arange(n) / SR
        return 0.35 * np.sin(2 * np.pi * np.cumsum(1400 - 1000 * tt / 0.6) / SR) * np.minimum(1, tt * 20)
    if kind == "crash":
        n = int(0.9 * SR)
        tt = np.arange(n) / SR
        return 0.8 * rng.uniform(-1, 1, n) * np.exp(-tt * 6) + 0.6 * np.sin(2 * np.pi * 60 * tt) * np.exp(-tt * 5)
    if kind == "car":
        n = int(0.6 * SR)
        tt = np.arange(n) / SR
        return 0.45 * np.tanh(3 * np.sin(2 * np.pi * np.cumsum(90 + 120 * tt) / SR)) * np.sin(np.pi * tt / 0.6) + 0.3 * np.sin(2 * np.pi * 700 * tt) * (tt > 0.3) * np.exp(-(tt - 0.3) * 8)
    if kind == "fly":
        n = int(0.8 * SR)
        tt = np.arange(n) / SR
        return 0.45 * _onepole(rng.uniform(-1, 1, n), 1500) * np.sin(np.pi * tt / 0.8) ** 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 12 * tt))
    if kind == "thump":
        n = int(0.3 * SR)
        tt = np.arange(n) / SR
        return 0.7 * np.sin(2 * np.pi * (90 * np.exp(-tt * 8) + 40) * tt) * np.exp(-tt * 14)
    if kind in ("sparkle", "cling"):
        n = int(0.7 * SR)
        tt = np.arange(n) / SR
        notes = (1568, 2093, 2637) if kind == "sparkle" else (2637, 3520)
        out = np.zeros(n)
        for i, f in enumerate(notes):
            d0 = int(i * 0.07 * SR)
            out[d0:] += 0.25 * np.sin(2 * np.pi * f * tt[: n - d0]) * np.exp(-tt[: n - d0] * 7)
        return out
    if kind == "whoosh":
        n = int(0.7 * SR)
        return 0.4 * _onepole(rng.uniform(-1, 1, n), 2500) * np.sin(np.linspace(0, np.pi, n)) ** 3
    if kind == "zap":
        n = int(0.5 * SR)
        tt = np.arange(n) / SR
        return 0.5 * np.sign(np.sin(2 * np.pi * 70 * tt)) * rng.uniform(0.3, 1, n) * np.exp(-tt * 7)
    return np.zeros(1)


def beats_track(total_n):
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "toon"))
        from director import BEATS
    except Exception:
        return np.zeros(total_n)
    out = np.zeros(total_n)
    for i, (t, kind) in enumerate(BEATS):
        a = _beat(kind, i)
        j = int(t * SR)
        out[j:j + len(a)] += a[: len(out[j:j + len(a)])]
    return out


def build_audio(story, out_wav, model):
    total_n = int(story.duration * SR) + SR // 2
    voice, lines = narration(story, model, total_n, lively=getattr(story.spec, "style", "") in ("toon", "popart"))
    mus = music(story, total_n)
    fx = sfx(story, total_n)
    if getattr(story.spec, "style", "") in ("toon", "popart"):
        fx = fx + 0.9 * beats_track(total_n)
    venv = _onepole((np.abs(voice) > 0.02).astype(float), 4)
    duck = 1 - 0.5 * np.clip(venv * 3, 0, 1)
    mono = 1.0 * voice + duck * (0.9 * mus) + 0.8 * fx
    # estéreo con un poco de anchura en la música
    width = _onepole(mus, 300) * 0.08
    st = np.stack([mono + width, mono - width], axis=1)
    st /= max(1.0, np.abs(st).max() / 0.95)
    write_wav(out_wav, st)
    return lines
