"""Narración continua para «¿Qué pasaría si la gravedad desapareciera durante 10 segundos?».

Se sintetiza todo el guion de una vez y se encadenan las frases con pausas cortas y naturales
(sin silencios largos). Devuelve el audio y los tiempos de cada frase y palabra, que el
animador usa para sincronizar las imágenes con lo que se va contando.

Motores gratuitos con licencia comercial:
  - kokoro  (Kokoro-82M, Apache 2.0; voces em_alex, em_santa, ef_dora; pronunciación de España)
  - piper   (Piper, MIT; voz es_ES-davefx-medium)

    python voz.py salida/ --motor kokoro --voz em_alex
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import types
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100

GUION = [
    ("intro", "¿Qué pasaría si la gravedad desapareciera durante solo diez segundos?"),
    ("ciudad", "Imagina una mañana cualquiera en la ciudad: gente que camina deprisa, coches que esperan en el semáforo."),
    ("despegue", "Y de repente, tus pies se despegan del suelo."),
    ("flotan", "La Tierra sigue girando, y todo lo que no está anclado empieza a separarse poco a poco: personas, coches, papeleras, perros."),
    ("salto", "Un simple paso basta para salir volando."),
    ("agua", "El agua de las fuentes se rompe en enormes burbujas temblorosas que flotan entre los edificios, y la gente se agarra desesperada a farolas, barandillas y ventanas."),
    ("vuelve", "Y entonces, justo cuando se cumplen los diez segundos, la gravedad vuelve de golpe."),
    ("caida", "Todo lo que flotaba cae a la vez: coches que aplastan coches, cristales que estallan, toneladas de agua que lo empapan todo."),
    ("consecuencias", "En solo diez segundos habría miles de accidentes, caídas y destrozos en todo el planeta."),
    ("pregunta", "¿Crees que sobrevivirías?"),
    ("cta", "¿Qué otra situación quieres que simulemos? ¡Déjalo en comentarios!"),
]

# pausa tras cada frase (s): corta y natural; algo más larga tras las preguntas y antes del clímax
PAUSAS = {"intro": 0.32, "ciudad": 0.18, "despegue": 0.22, "flotan": 0.2, "salto": 0.22, "agua": 0.28,
          "vuelve": 0.12, "caida": 0.3, "consecuencias": 0.3, "pregunta": 0.25, "cta": 0.0}


def resample(x, sr_in, sr_out=SR):
    n = int(len(x) * sr_out / sr_in)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def trim(x, thr=0.008):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(0, idx[0] - 600): idx[-1] + 1200] if len(idx) else x


def shorten_pauses(x, sr=SR, max_pause=0.22, keep=0.14, thr=0.01):
    """Acorta silencios internos largos (comas, puntos) sin cortar la respiración natural."""
    w = int(sr * 0.01)
    env = np.convolve(np.abs(x), np.ones(w) / w, mode="same")
    quiet = env < thr
    out, i, n = [], 0, len(x)
    while i < n:
        j = i
        q = quiet[i]
        while j < n and quiet[j] == q:
            j += 1
        seg = x[i:j]
        if q and (j - i) / sr > max_pause and 0 < i and j < n:
            k = int(keep * sr / 2)
            fade = np.linspace(1, 0, k) ** 2
            seg = np.concatenate([seg[:k] * fade, seg[-k:] * fade[::-1]])
        out.append(seg)
        i = j
    return np.concatenate(out)


def synth_kokoro(text, voice, speed):
    sys.modules.setdefault("spacy", types.ModuleType("spacy"))
    from kokoro import KPipeline

    if not hasattr(synth_kokoro, "p"):
        synth_kokoro.p = KPipeline(lang_code="e")
    a = np.concatenate([au.numpy() for _, _, au in synth_kokoro.p(text, voice=voice, speed=speed)])
    return resample(a.astype(np.float64), 24000)


def synth_piper(text, model, speed):
    sys.path.insert(0, os.path.dirname(HERE))
    from audio import synth_voice

    return synth_voice(text, model, speed=speed, lively=True)


def syllables(word):
    w = re.sub(r"[^a-záéíóúüñ]", "", word.lower())
    return max(1, len(re.findall(r"[aeiouáéíóúü]+", w)))


def word_times(text, start, end):
    """Reparte el tiempo de la frase por sílabas (y pausas en signos de puntuación)."""
    words = text.split()
    wts = [syllables(w) + (1.2 if w[-1:] in ",:;" else 0) + (1.6 if w[-1:] in ".!?" else 0) for w in words]
    tot = sum(wts)
    t, out = start, []
    for w, k in zip(words, wts):
        d = (end - start) * k / tot
        out.append((w, t, t + d))
        t += d
    return out


def build(out_dir, motor="kokoro", voz="em_alex", speed=1.12, model=None):
    os.makedirs(out_dir, exist_ok=True)
    parts, lines, t = [], [], 0.25
    parts.append(np.zeros(int(0.25 * SR)))
    for key, text in GUION:
        a = synth_kokoro(text, voz, speed) if motor == "kokoro" else synth_piper(text, model, speed)
        a = shorten_pauses(trim(a))
        a = a / max(1e-6, np.abs(a).max()) * 0.92
        dur = len(a) / SR
        lines.append({"key": key, "text": text, "start": t, "end": t + dur, "words": word_times(text, t + 0.03, t + dur - 0.05)})
        parts.append(a)
        gap = PAUSAS.get(key, 0.2)
        parts.append(np.zeros(int(gap * SR)))
        t += dur + gap
    voice = np.concatenate(parts)
    pcm = (np.clip(voice, -1, 1) * 32767).astype("<i2")
    with wave.open(os.path.join(out_dir, "narracion.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    info = {"motor": motor, "voz": voz, "speed": speed, "duration": len(voice) / SR, "lines": lines}
    with open(os.path.join(out_dir, "narracion.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--motor", default="kokoro", choices=["kokoro", "piper"])
    ap.add_argument("--voz", default="em_alex")
    ap.add_argument("--speed", type=float, default=1.12)
    ap.add_argument("--modelo", default=os.path.join(os.path.dirname(HERE), "assets", "voices", "es_ES-davefx-medium.onnx"))
    a = ap.parse_args()
    info = build(a.out, a.motor, a.voz, a.speed, a.modelo)
    for ln in info["lines"]:
        print(f"{ln['start']:5.2f}-{ln['end']:5.2f}  {ln['text'][:70]}")
    print(f"Duración total: {info['duration']:.1f} s")
