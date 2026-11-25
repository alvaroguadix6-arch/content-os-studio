#!/usr/bin/env python3
"""Valida que los paquetes públicos (paquetes/**/*.json) solo contienen campos de producción y ningún dato privado.

Se ejecuta antes de cada render y en las pruebas. Sale con 1 si algo no cumple.
    python3 tools/check_paquetes.py [archivos...]
"""
import glob
import json
import re
import sys

ALLOWED = {"id", "brand", "language", "format", "pillar", "title", "script", "on_screen_text", "visual_brief",
           "slides", "sources", "caption", "exported_from"}
CAPTION = {"text", "hashtags", "alt_text"}
PRIVATE = re.compile(r"EAA[A-Za-z0-9]{20,}|IGAA[A-Za-z0-9]{20,}|access_token|[\w.+-]+@[\w-]+\.[\w.]{2,}"
                     r"|\b\d{15,}\b|(?<![\w/])@[A-Za-z0-9_.]{2,30}", re.I)
ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$")


def check(path):
    errs = []
    try:
        d = json.load(open(path, encoding="utf-8"))
    except ValueError as e:
        return [f"JSON inválido: {e}"]
    if not isinstance(d, dict):
        return ["no es un objeto"]
    errs += [f"campo no permitido: {k}" for k in d if k not in ALLOWED]
    errs += [f"caption.{k} no permitido" for k in (d.get("caption") or {}) if k not in CAPTION]
    if not ID_RE.match(str(d.get("id", ""))):
        errs.append("id inválido")
    if d.get("brand") != "nivel-oculto":
        errs.append("brand debe ser nivel-oculto")
    sc = d.get("script")
    if not isinstance(sc, list) or not sc or not all(isinstance(x, str) and 0 < len(x) <= 400 for x in sc) or len(sc) > 40:
        errs.append("script inválido (lista de 1-40 frases de hasta 400 caracteres)")
    text = re.sub(r"https?://\S+?(?=[\"\s])", "", json.dumps(d, ensure_ascii=False))
    m = PRIVATE.search(text)
    if m:
        errs.append(f"posible dato privado: «{m.group(0)[:6]}…»")
    if len(text) > 60_000:
        errs.append("paquete demasiado grande")
    return errs


def main(argv):
    files = argv[1:] or sorted(glob.glob("paquetes/**/*.json", recursive=True))
    bad = 0
    for f in files:
        errs = check(f)
        for e in errs:
            print(f"FAIL {f}: {e}")
        bad += bool(errs)
    print(f"{len(files)} paquete(s) revisados, {bad} con problemas")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
