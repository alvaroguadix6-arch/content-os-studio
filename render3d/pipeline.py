"""Orquestador de producción 3D de Content-OS.

Pasos:
  1) render   → fotogramas 3D con Blender (se puede repartir en trozos/máquinas)
  2) finish   → narración + motores + música + HUD + subtítulos → MP4 1080x1920

Ejemplos:
  python pipeline.py render --out trabajo/frames --frames 0 99
  python pipeline.py finish --frames trabajo/frames --out trabajo/carrera.mp4
  python pipeline.py all --out trabajo         (todo en una máquina; tarda horas sin GPU)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from sim import Race, RaceSpec  # noqa: E402

VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx"
CAR_URL = "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/CarConcept/glTF-Binary/CarConcept.glb"

CREDITS = """Créditos del vídeo
- Modelo 3D «Car Concept»: Eric Chadwick / Darmstadt Graphics Group, licencia CC BY 4.0
  (https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CarConcept),
  basado en un modelo de dominio público (CC0) de «Unity Fan». Pintura y alerón modificados.
- Voz: Piper TTS, voz es_ES-davefx-medium (https://github.com/rhasspy/piper).
- Circuito, ciudad, música y efectos: generados por Content-OS (sin material de terceros).
- Carrera ficticia. Coches genéricos sin marca; cualquier parecido es estético.
"""


def ensure_file(path, url):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"Descargando {url} …", flush=True)
        urllib.request.urlretrieve(url, path)
    return path


def load_spec(path):
    return RaceSpec.from_json(path) if path else RaceSpec()


def template_of(path):
    if not path:
        return "carrera"
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("template", "carrera")


INM_DIR = os.path.join(HERE, "inmortal")


def style_of(path):
    if not path:
        return ""
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("style", "toon" if json.load(open(path, encoding="utf-8")).get("template") == "inmortal" else "")


def get_story(path):
    """Devuelve el objeto de guion de la plantilla (frames, duración, fps…)."""
    if template_of(path) == "inmortal":
        sys.path.insert(0, INM_DIR)
        from story import Story, StorySpec

        return Story(StorySpec.from_json(path) if path else StorySpec())
    return Race(load_spec(path))


CREDITS_TOON = """Créditos del vídeo
- Personaje: diseño original de Content-OS (dibujado por código).
- Fondos ilustrados: generados con el modelo libre LCM Dreamshaper v7 (SimianLuo/LCM_Dreamshaper_v7, licencia MIT;
  basado en Stable Diffusion 1.5, licencia CreativeML OpenRAIL-M). Imágenes generadas con IA.
- Voz: Piper TTS, voz es_ES-davefx-medium (https://github.com/rhasspy/piper).
- Música y efectos: generados por Content-OS (sin material de terceros).
- Simulación hipotética con fines divulgativos; las cifras temporales son estimaciones científicas aproximadas.
"""

CREDITS_INMORTAL = """Créditos del vídeo
- Personaje, ciudad, Tierra, Sol, espacio, música y efectos: generados por Content-OS con Blender (sin material de terceros).
- Coches del time-lapse: modelo «Car Concept» de Eric Chadwick / Darmstadt Graphics Group, licencia CC BY 4.0
  (https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CarConcept).
- Voz: Piper TTS, voz es_ES-davefx-medium (https://github.com/rhasspy/piper).
- Simulación hipotética con fines divulgativos; las cifras temporales son estimaciones científicas aproximadas.
"""


def cmd_render(a):
    ensure_file(os.path.join(HERE, "assets", "CarConcept.glb"), CAR_URL)
    script = os.path.join(INM_DIR, "scene.py") if template_of(a.spec) == "inmortal" else os.path.join(HERE, "scene_race.py")
    if template_of(a.spec) == "inmortal" and style_of(a.spec) == "toon":
        script = os.path.join(HERE, "toon", "director.py")  # estilo dibujos animados: animación 2D con gags
    args = [sys.executable, script, "--out", a.out, "--samples", str(a.samples), "--scale", str(a.scale), "--every", str(a.every)]
    if a.frames:
        args += ["--frames", str(a.frames[0]), str(a.frames[1])]
    if a.spec:
        args += ["--spec", a.spec]
    subprocess.run(args, check=True)


def cmd_finish(a):
    inm = template_of(a.spec) == "inmortal"
    if inm:
        sys.path.insert(0, INM_DIR)
        from overlay import render_overlay as render_hud
        from sound import build_audio
    else:
        from audio import build_audio
        from hud import render_hud

    race = get_story(a.spec)
    spec = race.spec
    work = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(work, exist_ok=True)
    frames = sorted(glob.glob(os.path.join(a.frames, "f*.jpg")))
    have = {int(os.path.basename(p)[1:6]) for p in frames}
    missing = [f for f in range(race.frames) if f not in have]
    if missing and not a.allow_missing:
        sys.exit(f"Faltan {len(missing)} fotogramas (p. ej. {missing[:5]}). Renderízalos antes o usa --allow-missing.")
    if missing:
        # Rellenar huecos con el fotograma anterior (solo para vistas previas)
        import shutil

        prev = frames[0]
        for f in range(race.frames):
            p = os.path.join(a.frames, f"f{f:05d}.jpg")
            if os.path.exists(p):
                prev = p
            else:
                shutil.copy(prev, p)
    voice = ensure_file(a.voice, VOICE_URL)
    ensure_file(a.voice + ".json", VOICE_URL + ".json")
    wav = os.path.join(work, "audio.wav")
    print("Generando audio (narración, motores, música, efectos)…", flush=True)
    lines = build_audio(race, wav, voice)
    hud_dir = os.path.join(work, "hud")
    print("Generando HUD y subtítulos…", flush=True)
    render_hud(race, lines, hud_dir)
    print("Montando MP4…", flush=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(spec.fps), "-start_number", "0", "-i", os.path.join(a.frames, "f%05d.jpg"),
        "-framerate", str(spec.fps), "-start_number", "0", "-i", os.path.join(hud_dir, "h%05d.png"),
        "-i", wav,
        "-filter_complex", "[0:v]scale=1080:1920:flags=lanczos[bg];[bg][1:v]overlay=0:0,format=yuv420p[v]",
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-preset", a.preset, "-crf", "21" if style_of(a.spec) == "toon" else "18", "-profile:v", "high", "-r", str(spec.fps),
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", a.out,
    ]
    subprocess.run(cmd, check=True)
    # Subtítulos aparte (.srt) y créditos
    from hud import word_cues

    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    with open(os.path.splitext(a.out)[0] + ".srt", "w", encoding="utf-8") as f:
        for i, c in enumerate(word_cues(lines), 1):
            f.write(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{' '.join(w[0] for w in c['words'])}\n\n")
    with open(os.path.splitext(a.out)[0] + "-creditos.txt", "w", encoding="utf-8") as f:
        f.write((CREDITS_TOON if style_of(a.spec) == "toon" else CREDITS_INMORTAL) if inm else CREDITS)
    info = {"duration": race.duration, "frames": race.frames, "fps": spec.fps, "title": spec.title, "missing_frames_filled": len(missing), "narration": lines}
    with open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"✅ Vídeo listo: {a.out}")


def missing_ranges(n, have, size):
    """Agrupa los fotogramas que faltan en tramos contiguos de como máximo `size`."""
    out = []
    f = 0
    while f < n:
        if f in have:
            f += 1
            continue
        start = f
        while f < n and f not in have and f - start < size:
            f += 1
        out.append([start, f - 1])
    return out


def cmd_plan(a):
    race = get_story(a.spec)
    n = race.frames
    have = set()
    if a.have_dir and os.path.isdir(a.have_dir):
        for p in glob.glob(os.path.join(a.have_dir, "**", "f*.jpg"), recursive=True):
            try:
                have.add(int(os.path.basename(p)[1:6]))
            except ValueError:
                pass
    if a.chunk_frames:
        chunks = missing_ranges(n, have, a.chunk_frames)
    else:
        k = a.chunks
        size = -(-n // k)
        chunks = [[i * size, min(n - 1, (i + 1) * size - 1)] for i in range(k) if i * size < n]
    print(json.dumps({"frames": n, "duration": round(race.duration, 2), "already": len(have), "chunks": chunks}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--out", required=True)
    r.add_argument("--frames", nargs=2, type=int)
    r.add_argument("--samples", type=int, default=20)
    r.add_argument("--scale", type=int, default=100)
    r.add_argument("--every", type=int, default=1)
    r.add_argument("--spec")
    f = sub.add_parser("finish")
    f.add_argument("--frames", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--spec")
    f.add_argument("--voice", default=os.path.join(HERE, "assets", "voices", "es_ES-davefx-medium.onnx"))
    f.add_argument("--preset", default="medium")
    f.add_argument("--allow-missing", action="store_true")
    p = sub.add_parser("plan")
    p.add_argument("--chunks", type=int, default=20)
    p.add_argument("--chunk-frames", type=int, default=0, help="tamaño de tramo en fotogramas (reanudación)")
    p.add_argument("--have-dir", default=None, help="carpeta con fotogramas ya renderizados (se omiten)")
    p.add_argument("--spec")
    al = sub.add_parser("all")
    al.add_argument("--out", required=True)
    al.add_argument("--samples", type=int, default=20)
    al.add_argument("--scale", type=int, default=100)
    al.add_argument("--spec")
    a = ap.parse_args()
    if a.cmd == "render":
        cmd_render(a)
    elif a.cmd == "finish":
        cmd_finish(a)
    elif a.cmd == "plan":
        cmd_plan(a)
    else:
        frames = os.path.join(a.out, "frames")
        cmd_render(argparse.Namespace(out=frames, frames=None, samples=a.samples, scale=a.scale, every=1, spec=a.spec))
        cmd_finish(argparse.Namespace(frames=frames, out=os.path.join(a.out, "video.mp4"), spec=a.spec,
                                      voice=os.path.join(HERE, "assets", "voices", "es_ES-davefx-medium.onnx"), preset="medium", allow_missing=False))


if __name__ == "__main__":
    main()
