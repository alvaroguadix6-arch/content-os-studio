"""NIVEL OCULTO · Zona segura para Reels / TikTok / Shorts (vídeo 1080×1920).

En móviles altos (≈19,5:9) la app rellena la pantalla y RECORTA ~100 px por cada lado del vídeo.
Encima pone su interfaz: barra de estado + flecha/cámara arriba, columna de iconos a la derecha y usuario +
descripción abajo. Todo lo importante (textos, números, marcador) debe ir dentro de la zona segura.

La zona es la UNIÓN de lo que tapan las tres apps (márgenes conservadores, vídeo 1080×1920):

| app             | arriba | abajo (usuario, texto, música) | iconos a la derecha     |
| --------------- | ------ | ------------------------------ | ----------------------- |
| Instagram Reels | ~220   | ~420 px (más si el texto es largo) | x ≥ ~950, y 1000-1600 |
| TikTok          | ~150   | ~480 px                        | x ≥ ~900, y 900-1600    |
| YouTube Shorts  | ~250   | ~440 px                        | x ≥ ~880, y 950-1600    |

→ TOP=250, BOTTOM=1440, iconos x ≥ 870 entre y=900 e y=1600, y 110 px de recorte lateral.

    python zona_segura.py video.mp4 salida.jpg   → vista previa «en el móvil» con las zonas tapadas marcadas

Comprobación automática (sin renderizar el vídeo entero): `Registro` anota la caja de cada texto, tarjeta,
círculo o polígono que se dibuja a tamaño final y `fuera_de_zona` dice cuáles quedan tapados más de 0,6 s
(las animaciones de entrada pueden pasar un instante por el borde).
"""
from __future__ import annotations

import subprocess
import sys

from PIL import Image, ImageDraw

SIDE = 110            # recorte lateral + margen
TOP = 250             # barra de estado e iconos superiores
TOP_TEXT = 410        # los textos, por debajo del marcador (que va justo bajo TOP)
BOTTOM = 1440         # a partir de aquí: usuario, descripción, botones (TikTok es la que más tapa)
RIGHT_ICONS = (870, 900, 1600)  # x desde la que hay iconos, entre y0 e y1


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


# ───── comprobación automática ─────
def inseguro(box, margen=2):
    """True si la caja (x0, y0, x1, y1) visible en pantalla toca una zona tapada en alguna de las tres apps."""
    x0, y0, x1, y1 = box
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, 1080), min(y1, 1920)
    if x1 <= x0 or y1 <= y0:
        return False  # fuera de pantalla (p. ej. entrando)
    total = max(1e-6, (box[2] - box[0]) * (box[3] - box[1]))
    if (x1 - x0) * (y1 - y0) < 0.15 * total:
        return False  # casi entero fuera de pantalla: está entrando o saliendo
    if x0 < SIDE - margen or x1 > 1080 - SIDE + margen or y0 < TOP - margen or y1 > BOTTOM + margen:
        return True
    return x1 > RIGHT_ICONS[0] + margen and y1 > RIGHT_ICONS[1] and y0 < RIGHT_ICONS[2]


_EXENTO = [0]


class exento:
    """Lo que se dibuja dentro de `with exento():` es parte del mapa o del fondo (se mueve con la cámara) y no
    cuenta como texto o rótulo para la comprobación."""

    def __enter__(self):
        _EXENTO[0] += 1

    def __exit__(self, *exc):
        _EXENTO[0] -= 1


class Registro:
    """Contexto que anota las cajas de lo que se dibuja con ImageDraw sobre lienzos de 1080×1920.

        with Registro() as r:
            v.frame(t)
        r.cajas → [(tipo, etiqueta, (x0, y0, x1, y1)), ...]
    """
    TIPOS = ("text", "rounded_rectangle", "rectangle", "ellipse", "polygon")

    def __init__(self):
        self.cajas = []
        self._orig = {}

    def __enter__(self):
        from PIL import ImageDraw as _D
        reg = self

        def wrap(name, fn):
            def inner(d, *a, **k):
                try:
                    if _EXENTO[0]:
                        return fn(d, *a, **k)
                    size = getattr(getattr(d, "_image", None), "size", None)
                    if size == (1080, 1920):
                        reg._anota(d, name, a, k)
                    elif size == (2160, 3840) and name in ("text", "rounded_rectangle"):
                        reg._anota(d, name, a, k, escala=0.5)  # lienzos dibujados a 2× (textos y tarjetas)
                except Exception:
                    pass
                return fn(d, *a, **k)
            return inner
        for n in self.TIPOS:
            self._orig[n] = getattr(_D.ImageDraw, n)
            setattr(_D.ImageDraw, n, wrap(n, self._orig[n]))
        return self

    def __exit__(self, *exc):
        from PIL import ImageDraw as _D
        for n, fn in self._orig.items():
            setattr(_D.ImageDraw, n, fn)

    def _anota(self, d, name, a, k, escala=1.0):
        pos = {"text": 2, "rounded_rectangle": 2}.get(name, 1)  # posición de `fill` en cada función
        fill = k.get("fill", a[pos] if len(a) > pos else None)
        if isinstance(fill, tuple) and len(fill) == 4 and fill[3] < 40 and not k.get("outline"):
            return  # sombras y velos casi transparentes
        if name == "text":
            xy, txt = a[0], a[1]
            if not str(txt).strip():
                return
            box = self._orig_textbbox(d, xy, txt, k)
            self.cajas.append(("texto", str(txt)[:40], tuple(v * escala for v in box)))
            return
        shape = a[0] if a else k.get("xy")
        pts = list(shape)
        if pts and not isinstance(pts[0], (tuple, list)):
            pts = [(pts[i], pts[i + 1]) for i in range(0, len(pts) - 1, 2)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        box = tuple(v * escala for v in (min(xs), min(ys), max(xs), max(ys)))
        if (box[2] - box[0]) * (box[3] - box[1]) >= 0.9 * 1080 * 1920:
            return  # fondos a pantalla completa
        self.cajas.append((name, f"{name}@{int(box[0])//40*40},{int(box[1])//40*40}", box))

    @staticmethod
    def _orig_textbbox(d, xy, txt, k):
        kw = {x: k[x] for x in ("font", "anchor", "spacing", "align", "stroke_width") if x in k}
        return d.textbbox(xy, txt, **kw)


def fuera_de_zona(video, t0=0.0, t1=None, paso=0.2, min_seguido=0.6, fps=None):
    """Recorre el vídeo cada `paso` s y devuelve [(t, tipo, etiqueta, caja)] de lo que queda en zona tapada
    durante al menos `min_seguido` s seguidos. `video` es un objeto con .frame(t) y .duration
    (con `fps`, .frame recibe el número de fotograma, como en motor.py)."""
    t1 = video.duration if t1 is None else t1
    racha, malos = {}, []
    t = t0
    while t < t1:
        with Registro() as r:
            video.frame(int(round(t * fps)) if fps else t)
        vistos = set()
        for tipo, et, box in r.cajas:
            if inseguro(box):
                key = (tipo, et)
                vistos.add(key)
                ini = racha.setdefault(key, (t, box))
                if t - ini[0] + paso >= min_seguido - 1e-6 and not any(m[1:3] == key for m in malos):
                    malos.append((round(ini[0], 2), tipo, et, tuple(round(v) for v in box)))
        for key in list(racha):
            if key not in vistos:
                del racha[key]
        t += paso
    return malos


if __name__ == "__main__":
    preview(sys.argv[1], sys.argv[2])
