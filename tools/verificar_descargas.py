#!/usr/bin/env python3
"""Comprueba que los artefactos descargados de un render se abren bien (solo ffprobe y la librería estándar).

    python3 tools/verificar_descargas.py descargas/ [--resumen resumen.md]

Por cada carpeta (un artefacto = un vídeo) exige: un MP4 1080×1920 con vídeo H.264 y audio, una portada
JPG 1080×1920, descripcion.txt y hashtags.txt no vacíos. Sale con 1 si falta algo o algún archivo no se abre.
"""
import argparse
import json
import os
import subprocess
import sys


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
                       capture_output=True, text=True)
    return json.loads(r.stdout or "{}") if r.returncode == 0 else {}


def dims(info):
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    return v.get("width"), v.get("height"), v.get("codec_name")


def revisar(d):
    files = sorted(os.listdir(d))
    errs, notas = [], []
    mp4 = [f for f in files if f.endswith(".mp4")]
    if len(mp4) != 1:
        errs.append(f"se esperaba 1 MP4 y hay {len(mp4)}")
    for f in mp4:
        info = probe(os.path.join(d, f))
        w, h, c = dims(info)
        audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
        dur = float(info.get("format", {}).get("duration", 0) or 0)
        if (w, h, c) != (1080, 1920, "h264") or not audio or dur <= 0:
            errs.append(f"{f}: no se abre bien ({w}×{h} {c}, audio={audio}, {dur:.1f} s)")
        else:
            notas.append(f"MP4 {dur:.1f} s, {os.path.getsize(os.path.join(d, f)) / 1e6:.1f} MB")
    port = [f for f in files if f.endswith("-portada.jpg")]
    if not port:
        errs.append("falta la portada")
    for f in port:
        w, h, _ = dims(probe(os.path.join(d, f)))
        if (w, h) != (1080, 1920):
            errs.append(f"{f}: portada de {w}×{h}")
    for f in ("descripcion.txt", "hashtags.txt"):
        p = os.path.join(d, f)
        if not os.path.exists(p) or not open(p, encoding="utf-8").read().strip():
            errs.append(f"falta o está vacío {f}")
    for f in files:
        if f.endswith(".jpg") and f not in port:
            if probe(os.path.join(d, f)).get("streams") is None:
                errs.append(f"{f}: imagen dañada")
    return files, errs, notas


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--resumen")
    a = ap.parse_args(argv)
    dirs = sorted(x for x in os.listdir(a.dir) if os.path.isdir(os.path.join(a.dir, x))) if os.path.isdir(a.dir) else []
    md = ["## Verificación de descargas", "", "| artefacto | archivos | resultado |", "| --- | --- | --- |"]
    mal = 0
    if not dirs:
        md.append("| — | — | ❌ no se ha descargado ningún artefacto |")
        mal = 1
    for x in dirs:
        files, errs, notas = revisar(os.path.join(a.dir, x))
        mal += bool(errs)
        md.append(f"| {x} | {len(files)} | " + ("❌ " + "; ".join(errs) if errs else "✅ " + "; ".join(notas)) + " |")
    text = "\n".join(md) + "\n"
    print(text)
    if a.resumen:
        with open(a.resumen, "a", encoding="utf-8") as fh:
            fh.write(text)
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main())
