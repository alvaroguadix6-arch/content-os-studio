#!/usr/bin/env python3
"""Control de calidad técnico de un MP4 vertical (solo ffmpeg/ffprobe, gratis).

    python3 tools/qc_video.py video.mp4 [--hoja hoja.jpg] [--resumen resumen.md]

Comprueba: 1080×1920, 30 fps, H.264 + AAC, duración 7-90 s, sonoridad integrada cerca de −14 LUFS (±2),
pico real ≤ −1 dBTP, silencios largos (> 1,2 s), fotogramas congelados (> 4 s) y negros.
Genera una hoja de contactos de 8 fotogramas. Sale con 1 si falla algo crítico (formato, sin audio,
duración fuera de rango); el resto son avisos.
"""
import argparse
import json
import re
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path])
    return json.loads(r.stdout or "{}")


def filters(path, af=None, vf=None):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path]
    if af:
        cmd += ["-af", af]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-f", "null", "-"]
    return run(cmd).stderr


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--hoja")
    ap.add_argument("--resumen")
    a = ap.parse_args(argv)
    info = probe(a.video)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    au = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float(info.get("format", {}).get("duration", 0))
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den or 1)
    crit, warn, rows = [], [], []

    rows.append(("Resolución", f"{v.get('width')}×{v.get('height')}"))
    if (v.get("width"), v.get("height")) != (1080, 1920):
        crit.append("resolución distinta de 1080×1920")
    rows.append(("FPS", f"{fps:.2f}"))
    if abs(fps - 30) > 0.1:
        warn.append("fps distinto de 30")
    rows.append(("Vídeo / audio", f"{v.get('codec_name')} / {au.get('codec_name') if au else 'SIN AUDIO'}"))
    if v.get("codec_name") != "h264":
        crit.append("el vídeo no es H.264")
    if not au:
        crit.append("no hay pista de audio")
    rows.append(("Duración", f"{dur:.1f} s"))
    if not 7 <= dur <= 90:
        crit.append("duración fuera de 7-90 s")
    size = int(info.get("format", {}).get("size", 0))
    rows.append(("Tamaño", f"{size / 1e6:.1f} MB"))

    if au:
        e = filters(a.video, af="ebur128=peak=true")
        i = re.findall(r"I:\s+(-?[\d.]+) LUFS", e)
        tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)
        lufs = float(i[-1]) if i else None
        peak = float(tp[-1]) if tp else None
        rows.append(("Sonoridad integrada", f"{lufs} LUFS (objetivo −14)"))
        rows.append(("Pico real", f"{peak} dBTP"))
        if lufs is None or abs(lufs + 14) > 2:
            warn.append("sonoridad lejos de −14 LUFS")
        if peak is not None and peak > -0.9:
            warn.append("pico por encima de −1 dBTP (puede saturar)")
        s = filters(a.video, af="silencedetect=noise=-38dB:d=1.2")
        sil = [(float(x), float(y)) for x, y in zip(re.findall(r"silence_start: (-?[\d.]+)", s),
                                                     re.findall(r"silence_end: (-?[\d.]+)", s))]
        sil_mid = [x for x in sil if x[0] > 0.5 and x[1] < dur - 1.5]
        rows.append(("Silencios > 1,2 s (en medio)", ", ".join(f"{x:.1f}-{y:.1f} s" for x, y in sil_mid) or "ninguno"))
        if sil_mid:
            warn.append("hay silencios largos en mitad del vídeo")

    f = filters(a.video, vf="freezedetect=n=0.002:d=4")
    fr = re.findall(r"freeze_start: ([\d.]+)", f)
    rows.append(("Planos congelados > 4 s", ", ".join(f"{float(x):.1f} s" for x in fr) or "ninguno"))
    if fr:
        warn.append("hay planos congelados más de 4 s")
    b = filters(a.video, vf="blackdetect=d=0.3:pix_th=0.05")
    bl = re.findall(r"black_start:([\d.]+)", b)
    rows.append(("Fotogramas negros > 0,3 s", ", ".join(f"{float(x):.1f} s" for x in bl) or "ninguno"))
    if bl:
        warn.append("hay tramos en negro")

    if a.hoja and dur > 0:
        step = dur / 9
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.video, "-vf",
             f"fps=1/{step:.3f},scale=270:480,tile=4x2:padding=8:color=white", "-frames:v", "1", a.hoja])
        rows.append(("Hoja de contactos", a.hoja))

    verdict = "❌ FALLA" if crit else ("⚠️ REVISAR" if warn else "✅ OK")
    md = ["## Control de calidad del vídeo", "", f"**{verdict}**", "", "| comprobación | resultado |", "| --- | --- |"]
    md += [f"| {k} | {val} |" for k, val in rows]
    if crit or warn:
        md += [""] + [f"- ❌ {c}" for c in crit] + [f"- ⚠️ {w}" for w in warn]
    text = "\n".join(md) + "\n"
    print(text)
    if a.resumen:
        with open(a.resumen, "a", encoding="utf-8") as fh:
            fh.write(text)
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main())
