#!/usr/bin/env python3
"""Control de calidad de TODOS los MP4 de una carpeta (un artefacto por subcarpeta), en una sola tabla.

    python3 tools/qc_lote.py descargas/ [--resumen resumen.md]

Usa las mismas comprobaciones que tools/qc_video.py. Sale con 1 si algún vídeo tiene un fallo crítico.
"""
import argparse
import glob
import io
import os
import re
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qc_video  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--resumen")
    a = ap.parse_args(argv)
    filas, peor = [], 0
    for mp4 in sorted(glob.glob(os.path.join(a.dir, "**", "*.mp4"), recursive=True)):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = qc_video.main([mp4])
        txt = buf.getvalue()
        peor = max(peor, rc)
        def campo(nombre):
            m = re.search(r"\| " + re.escape(nombre) + r" \| ([^|]+) \|", txt)
            return m.group(1).strip() if m else "—"
        veredicto = "❌ FALLA" if "FALLA" in txt else "⚠️ REVISAR" if "REVISAR" in txt else "✅ OK"
        avisos = "; ".join(x[4:] for x in txt.splitlines() if x.startswith("- ⚠️") or x.startswith("- ❌"))
        filas.append(f"| {os.path.basename(mp4)[:-4]} | {campo('Duración')} | {campo('Sonoridad integrada').split(' (')[0]} | "
                     f"{campo('Pico real')} | {veredicto}{' · ' + avisos if avisos else ''} |")
    md = ["## Control de calidad del lote", "", "| vídeo | duración | sonoridad | pico real | resultado |",
          "| --- | --- | --- | --- | --- |"] + (filas or ["| — | — | — | — | ❌ no hay vídeos |"])
    text = "\n".join(md) + "\n"
    print(text)
    if a.resumen:
        with open(a.resumen, "a", encoding="utf-8") as fh:
            fh.write(text)
    return 1 if peor or not filas else 0


if __name__ == "__main__":
    sys.exit(main())
