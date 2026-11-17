"""Banda sonora de la carrera: todo generado por el programa (libre de derechos).

- Narración en español con Piper (modelo es_ES-davefx-medium, licencia MIT).
- Motores V12 sintetizados a partir de las revoluciones simuladas de cada coche,
  con volumen, panorama estéreo y efecto Doppler según la cámara activa.
- Música electrónica procedural, pitidos del semáforo, público y golpes de cámara lenta.
"""
from __future__ import annotations

import math
import os
import wave

import numpy as np

SR = 44100


def _env(n, a=0.005, r=0.1):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e


def _noise(n, seed=0):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _onepole(x, cutoff):
    """Paso bajo de un polo con scipy si está disponible; si no, versión numpy simple."""
    try:
        from scipy.signal import lfilter

        a = math.exp(-2 * math.pi * cutoff / SR)
        return lfilter([1 - a], [1, -a], x)
    except Exception:
        k = max(1, int(SR / cutoff / 2))
        return np.convolve(x, np.ones(k) / k, mode="same")


# ─────────────────────────── voz ───────────────────────────

def synth_voice(text, model_path, speed=1.05):
    from piper import PiperVoice

    voice = PiperVoice.load(model_path)
    try:
        from piper import SynthesisConfig

        cfg = SynthesisConfig(length_scale=1 / speed)
        chunks = list(voice.synthesize(text, syn_config=cfg))
    except Exception:
        chunks = list(voice.synthesize(text))
    data = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float64)
    rate = chunks[0].sample_rate
    # remuestreo lineal a 44,1 kHz
    n = int(len(data) * SR / rate)
    data = np.interp(np.linspace(0, len(data) - 1, n), np.arange(len(data)), data)
    # recorte de silencios
    idx = np.where(np.abs(data) > 0.01)[0]
    if len(idx):
        data = data[max(0, idx[0] - 2000): idx[-1] + 3000]
    return data / max(1e-6, np.abs(data).max()) * 0.95


def narration_lines(race):
    sp = race.spec
    if sp.narration:
        return [(float(t), str(txt)) for t, txt in sp.narration]
    T0, TF, R = race.t_go, race.t_finish, sp.race_time
    v = race.video_time_of_sim
    A, B = "el rojo", "el amarillo"
    win, lose = (A, B) if sp.winner == "a" else (B, A)
    return [
        (0.2, "Dos superdeportivos. Solo uno puede ganar."),
        (v(T0 - 0.6), "¡Arrancan!"),
        (v(T0 + 2.4), f"{B.capitalize()} sale mejor y se coloca primero."),
        (v(T0 + 0.24 * R), f"Pero {A} no se rinde: va pegado a su rebufo."),
        (v(T0 + 0.47 * R), "¡Se tira por el interior… y adelanta!"),
        (v(T0 + 0.70 * R), f"{B.capitalize()} contraataca en la recta."),
        (v(T0 + 0.86 * R), "Última curva. Rueda con rueda."),
        (v(TF - 0.7), "¡Foto finish!"),
        (v(TF + 0.5), f"¡Gana {win} por medio coche!"),
        (v(TF + 0.5) + 2.3, "¿Tú por quién ibas?"),
    ]


def build_narration(race, model_path, total_n):
    """Devuelve (pista de voz, lista de líneas con tiempos reales)."""
    track = np.zeros(total_n)
    lines = []
    cursor = 0.0
    for t, text in narration_lines(race):
        audio = synth_voice(text, model_path)
        start = max(t, cursor + 0.15)
        i0 = int(start * SR)
        i1 = min(total_n, i0 + len(audio))
        if i0 >= total_n:
            break
        track[i0:i1] += audio[: i1 - i0]
        dur = (i1 - i0) / SR
        lines.append({"start": start, "end": start + dur, "text": text})
        cursor = start + dur
    return track, lines


# ─────────────────────────── motores ───────────────────────────

def engine_track(rows, which, fps, total_n, seed):
    """Motor sintetizado con revoluciones, distancia a cámara, Doppler y panorama."""
    ft = np.array([r["vt"] for r in rows])
    rpm = np.array([r[which]["rpm"] for r in rows])
    car = np.array([[r[which]["x"], r[which]["y"], 0.6] for r in rows])
    cam = np.array([r["cam"] for r in rows])
    slow = np.array([1.0 if r["slowmo"] else 0.0 for r in rows])
    rel = car - cam
    dist = np.linalg.norm(rel, axis=1) + 0.5
    vr = np.gradient(dist) * fps  # velocidad radial (m/s de vídeo)
    doppler = 343.0 / np.clip(343.0 + vr, 150, 600)
    # panorama: dirección de la cámara aproximada como la dirección hacia el punto medio de los coches
    pan = np.clip(np.gradient(rel[:, 0]) * 0, -1, 1)
    gain = 1.0 / (1.0 + (dist / 9.0) ** 1.4)
    accel = np.clip(np.gradient(rpm) * fps / 4000, -1, 1)
    t = np.arange(total_n) / SR
    rpm_s = np.interp(t, ft, rpm)
    dop_s = np.interp(t, ft, doppler)
    gain_s = np.interp(t, ft, gain)
    slow_s = np.interp(t, ft, slow)
    acc_s = np.interp(t, ft, accel)
    pitch = 1 - 0.55 * slow_s
    f0 = rpm_s / 60.0 * 6.0 * dop_s * pitch  # V12: 6 explosiones por vuelta
    phase = 2 * np.pi * np.cumsum(f0) / SR
    rng = np.random.default_rng(seed)
    jitter = np.interp(t, np.linspace(0, t[-1], 4000), rng.normal(0, 0.06, 4000))
    sig = (
        1.0 * np.sin(phase + jitter)
        + 0.55 * np.sin(2 * phase)
        + 0.35 * np.sin(3 * phase + 0.3)
        + 0.25 * np.sin(0.5 * phase)
        + 0.18 * np.sin(4 * phase)
    )
    throttle = 0.65 + 0.35 * np.clip(acc_s, 0, 1)
    sig = np.tanh(sig * (1.2 + 1.4 * throttle)) * throttle
    sig += 0.12 * _noise(total_n, seed) * gain_s  # rugido/aire
    # los coches lejanos suenan más apagados
    far = _onepole(sig, 900)
    near_w = np.clip(gain_s * 3, 0, 1)
    sig = near_w * sig + (1 - near_w) * far
    out = sig * gain_s * 0.55
    _ = pan
    return out


# ─────────────────────────── música y efectos ───────────────────────────

def music_track(race, total_n, bpm=126):
    t = np.arange(total_n) / SR
    out = np.zeros(total_n)
    beat = 60 / bpm
    start = race.video_time_of_sim(race.t_go)
    a, _ = race._warp
    slow_end = race.video_time_of_sim(race._warp[1])
    notes = [45, 45, 48, 43]  # La, La, Do, Sol (graves)

    def tone(freq, dur, kind="saw"):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        if kind == "saw":
            w = 2 * (tt * freq % 1) - 1
        elif kind == "sq":
            w = np.sign(np.sin(2 * np.pi * freq * tt))
        else:
            w = np.sin(2 * np.pi * freq * tt)
        return w

    # Intro: pad tenso + subida
    pad_n = int(start * SR)
    if pad_n > 0:
        tt = t[:pad_n]
        pad = 0.12 * (np.sin(2 * np.pi * 110 * tt) + np.sin(2 * np.pi * 164.8 * tt) + 0.5 * np.sin(2 * np.pi * 220 * tt * (1 + tt / 30)))
        pad *= np.minimum(1, tt / 1.5)
        out[:pad_n] += pad
    k = 0
    tb = start
    while tb < race.duration:
        in_slow = a <= tb < slow_end
        i0 = int(tb * SR)
        bar_note = notes[(k // 16) % 4]
        if not in_slow:
            # bombo
            n = int(0.25 * SR)
            kt = np.arange(n) / SR
            kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 9)
            seg = out[i0:i0 + n]
            seg += 0.5 * kick[: len(seg)]
            # bajo (corcheas)
            for half in (0, 0.5):
                j0 = int((tb + half * beat) * SR)
                n2 = int(beat * 0.45 * SR)
                f = 440 * 2 ** ((bar_note - 69) / 12)
                b = tone(f, beat * 0.45) * _env(n2, 0.003, 0.12)
                b = _onepole(b, 700)
                seg2 = out[j0:j0 + n2]
                seg2 += 0.22 * b[: len(seg2)]
            # palmada en 2 y 4
            if k % 2 == 1:
                n3 = int(0.18 * SR)
                cl = _onepole(_noise(n3, k), 3000) * _env(n3, 0.001, 0.05)
                seg3 = out[i0:i0 + n3]
                seg3 += 0.35 * cl[: len(seg3)]
            # arpegio
            for q in range(4):
                j0 = int((tb + q * beat / 4) * SR)
                n4 = int(beat / 4 * SR)
                f = 440 * 2 ** ((bar_note + 24 + [0, 7, 12, 15][q] - 69) / 12)
                ar = tone(f, beat / 4, "sq") * _env(n4, 0.002, 0.05)
                seg4 = out[j0:j0 + n4]
                seg4 += 0.045 * ar[: len(seg4)]
        tb += beat
        k += 1
    return out


def sfx_track(race, total_n, cuts):
    out = np.zeros(total_n)
    v = race.video_time_of_sim
    T0 = race.t_go
    # pitidos del semáforo
    for i in range(5):
        tt = v(T0 - 3.0 + i * 0.5)
        n = int(0.16 * SR)
        s = np.sin(2 * np.pi * 523 * np.arange(n) / SR) * _env(n, 0.002, 0.08)
        i0 = int(tt * SR)
        out[i0:i0 + n] += 0.35 * s[: len(out[i0:i0 + n])]
    n = int(0.7 * SR)
    go = np.sin(2 * np.pi * 1046 * np.arange(n) / SR) * _env(n, 0.002, 0.3)
    i0 = int(v(T0) * SR)
    out[i0:i0 + n] += 0.4 * go[: len(out[i0:i0 + n])]
    # golpes de transición en cada cambio de cámara
    for c in cuts:
        n = int(0.5 * SR)
        w = _onepole(_noise(n, int(c * 100)), 1500) * np.sin(np.linspace(0, np.pi, n)) ** 2
        i0 = max(0, int((c - 0.25) * SR))
        seg = out[i0:i0 + n]
        seg += 0.18 * w[: len(seg)]
    # cámara lenta: impacto grave + latidos
    a, b = race._warp
    sa = a
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (35 + 60 * np.exp(-tt * 6)) * tt) * np.exp(-tt * 2.2)
    i0 = int(sa * SR)
    out[i0:i0 + n] += 0.7 * boom[: len(out[i0:i0 + n])]
    sb = race.video_time_of_sim(b)
    hb = sa + 0.8
    while hb < sb - 0.2:
        m = int(0.25 * SR)
        k = np.sin(2 * np.pi * 55 * np.arange(m) / SR) * _env(m, 0.003, 0.07)
        j = int(hb * SR)
        out[j:j + m] += 0.45 * k[: len(out[j:j + m])]
        hb += 0.75
    # público al final
    tf = race.video_time_of_sim(race.t_finish)
    n = total_n - int(tf * SR)
    if n > 0:
        crowd = _onepole(_noise(n, 99), 2200) - _onepole(_noise(n, 99), 300)
        env = np.minimum(1, np.arange(n) / SR / 0.8)
        out[int(tf * SR):] += 0.35 * crowd * env
    return out


def write_wav(path, stereo):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build_audio(race, out_wav, model_path):
    rows = race.timeline()
    total_n = int(race.duration * SR) + SR // 2
    voice, lines = build_narration(race, model_path, total_n)
    cuts = [sh["start"] for sh in race.shots[1:]]
    eng_a = engine_track(rows, "a", race.spec.fps, total_n, 1)
    eng_b = engine_track(rows, "b", race.spec.fps, total_n, 2)
    music = music_track(race, total_n)
    sfx = sfx_track(race, total_n, cuts)
    # Ducking: la música y los motores bajan cuando habla el narrador
    venv = _onepole((np.abs(voice) > 0.02).astype(float), 4)
    duck = 1 - 0.55 * np.clip(venv * 3, 0, 1)
    left = 0.95 * voice + duck * (0.55 * music + 0.75 * eng_a + 0.6 * eng_b) + 0.8 * sfx
    right = 0.95 * voice + duck * (0.55 * music + 0.6 * eng_a + 0.75 * eng_b) + 0.8 * sfx
    st = np.stack([left, right], axis=1)
    st /= max(1.0, np.abs(st).max() / 0.95)
    write_wav(out_wav, st)
    return lines


if __name__ == "__main__":
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sim import Race

    lines = build_audio(Race(), sys.argv[1] if len(sys.argv) > 1 else "audio.wav", sys.argv[2] if len(sys.argv) > 2 else "es_ES-davefx-medium.onnx")
    for ln in lines:
        print(f"{ln['start']:6.2f}-{ln['end']:6.2f}  {ln['text']}")
