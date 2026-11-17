"""Ilustraciones para «¿Qué pasaría si la gravedad desapareciera durante 10 segundos?».

Fondos (calle antes y después) y «recortables» (personas, coches, objetos) generados con IA libre
(LCM Dreamshaper v7, CPU). Los recortables se piden sobre fondo blanco y se recortan solos.

    python arte.py salida/            (usa el Python con torch + diffusers)
"""
from __future__ import annotations

import os
import sys

STYLE = "highly detailed digital painting, realistic illustration, soft cinematic lighting, sharp focus"
PLATES = {
    "calle": ("sunny wide avenue in a spanish city at morning, elegant old buildings with balconies and cream facades, "
              "a plaza with a big stone fountain in the middle distance, palm trees, clear blue sky with a few clouds, "
              "warm golden sunlight, empty sidewalk in the foreground, no people, no cars, vertical composition", 896, 512, 41),
    "despues": ("the same sunny spanish city avenue after a disaster, crashed cars piled on top of each other, broken glass, "
                "flooded pavement, scattered debris, smoke and dust in the air, no people, vertical composition", 896, 512, 42),
    "cielo": ("looking straight up between elegant old spanish buildings with balconies and palm trees into a bright blue "
              "sky with white clouds, sunny, vertical composition", 896, 512, 43),
}
SPRITES = {
    "hombre": ("a businessman in a grey suit walking, full body, side view", 704, 384, 21),
    "mujer": ("a young woman in a red coat with a handbag walking, full body", 704, 384, 22),
    "nino": ("a little boy with a yellow raincoat, full body, standing", 640, 384, 23),
    "abuelo": ("an elderly man with a cane and a hat, full body, standing", 704, 384, 24),
    "perro": ("a golden retriever dog, full body, side view", 448, 512, 25),
    "coche_rojo": ("a red compact car, side view", 384, 640, 26),
    "taxi": ("a yellow taxi car, side view", 384, 640, 27),
    "furgoneta": ("a white delivery van, side view", 448, 640, 28),
    "papelera": ("a metal street trash bin", 512, 384, 29),
    "bicicleta": ("a city bicycle, side view", 384, 640, 30),
}


def cutout(img):
    """Quita el fondo blanco (relleno desde los bordes) y suaviza el borde."""
    import numpy as np
    from PIL import Image, ImageFilter
    from scipy import ndimage

    a = np.asarray(img.convert("RGB")).astype(np.int16)
    white = (a.min(axis=2) > 222) & ((a.max(axis=2) - a.min(axis=2)) < 28)
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    mask = ~bg
    mask = ndimage.binary_opening(mask, iterations=2)
    lab2, n = ndimage.label(mask)
    if n > 1:  # quedarse con la pieza principal
        sizes = ndimage.sum(mask, lab2, range(1, n + 1))
        mask = lab2 == (1 + int(np.argmax(sizes)))
    alpha = Image.fromarray((mask * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.2))
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out.crop(out.getbbox())


def main(out):
    import torch
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "toon"))
    from backgrounds import load

    os.makedirs(out, exist_ok=True)
    pipe = load()
    only = set(sys.argv[2:])
    for name, (prompt, h, w, seed) in {**PLATES, **SPRITES}.items():
        if only and name not in only:
            continue
        sprite = name in SPRITES
        full = f"{prompt}, {STYLE}" + (", isolated on a plain pure white background, centered, no shadow" if sprite else "")
        g = torch.Generator("cpu").manual_seed(seed)
        img = pipe(prompt=full, width=w, height=h, num_inference_steps=6, guidance_scale=8.0, generator=g).images[0]
        if sprite:
            img = cutout(img)
            img.save(os.path.join(out, f"{name}.png"))
        else:
            img.save(os.path.join(out, f"{name}.png"))
        print("[arte]", name, flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "arte")
