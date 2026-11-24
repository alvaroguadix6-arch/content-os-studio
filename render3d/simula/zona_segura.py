"""NIVEL OCULTO · Zona segura para Reels / TikTok / Shorts (vídeo 1080×1920).

En móviles altos (≈19,5:9) la app rellena la pantalla y RECORTA ~100 px por cada lado del vídeo.
Encima pone su interfaz: barra de estado + flecha/cámara arriba, columna de iconos a la derecha y usuario +
descripción abajo. Todo lo importante (textos, números, marcador) debe ir dentro de SAFE.

    python zona_segura.py video.mp4 salida.jpg   → vista previa «en el móvil» con las zonas tapadas marcadas
"""
from __future__ import annotations

import subprocess
import sys

from PIL import Image, ImageDraw

SIDE = 110            # recorte lateral + margen
TOP = 250             # barra de estado e iconos superiores
TOP_TEXT = 410        # los textos, por debajo del marcador (que va justo bajo TOP)
BOTTOM = 1460         # a partir de aquí: usuario, descripción, botones
RIGHT_ICONS = (870, 1000, 1600)  # x desde la que hay iconos, entre y0 e y1


def clamp_text(x, y, w, h=0):
    """Recoloca un texto centrado en (x, y) de ancho w para que quede dentro de la zona segura."""
    y = min(max(y, TOP_TEXT + h / 2), BOTTOM - h / 2)
    right = RIGHT_ICONS[0] if RIGHT_ICONS[1] - h / 2 < y < RIGHT_ICONS[2] + h / 2 else 1080 - SIDE
    x = min(max(x, SIDE + w / 2), right - w / 2)
    if w > right - SIDE:  # demasiado ancho: centrado en el hueco disponible
        x = (SIDE + right) / 2
    return x, y


def mask(im):
    im = im.convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    red = (255, 0, 60, 90)
    d.rectangle([0, 0, 1080, TOP], fill=red)
    d.rectangle([0, BOTTOM, 1080, 1920], fill=red)
    d.rectangle([RIGHT_ICONS[0], RIGHT_ICONS[1], 1080, RIGHT_ICONS[2]], fill=red)
    im.alpha_composite(lay)
    return im.crop((97, 0, 1080 - 97, 1920)).convert("RGB")


def preview_images(paths, out):
    tiles = [mask(Image.open(p)).resize((300, int(300 * 1920 / 886))) for p in paths]
    s = Image.new("RGB", (300 * len(tiles), tiles[0].height))
    for i, tl in enumerate(tiles):
        s.paste(tl, (i * 300, 0))
    s.save(out, quality=85)


def preview(video, out, times=None):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                               capture_output=True, text=True).stdout)
    times = times or [dur * k / 9 + 0.5 for k in range(9)]
    tiles = []
    for t in times:
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        im = Image.frombytes("RGB", (1080, 1920), raw).convert("RGBA")
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        red = (255, 0, 60, 90)
        d.rectangle([0, 0, 1080, TOP], fill=red)
        d.rectangle([0, BOTTOM, 1080, 1920], fill=red)
        d.rectangle([RIGHT_ICONS[0], RIGHT_ICONS[1], 1080, RIGHT_ICONS[2]], fill=red)
        im.alpha_composite(lay)
        im = im.crop((97, 0, 1080 - 97, 1920))  # lo que se ve en un iPhone
        tiles.append(im.convert("RGB").resize((300, int(300 * 1920 / 886))))
    s = Image.new("RGB", (300 * len(tiles), tiles[0].height), (0, 0, 0))
    for i, tl in enumerate(tiles):
        s.paste(tl, (i * 300, 0))
    s.save(out, quality=85)


if __name__ == "__main__":
    preview(sys.argv[1], sys.argv[2])
