"""Ilustraciones del anuncio de Cristalbox (generadas con IA libre: LCM Dreamshaper v7, CPU).

El logotipo NO se genera: se usa el archivo original (arte/logo_cristalbox.png) sin modificarlo.

    python arte.py salida/ [nombre ...]      (usa el Python con torch + diffusers)
"""
from __future__ import annotations

import os
import sys

STYLE = ("professional automotive advertising, realistic digital painting, cinematic lighting, "
         "sharp focus, high detail, clean composition, no text, no letters, no logos")
PLATES = {
    "carretera": "driver point of view from inside a modern car looking through a clean windshield at a sunny highway "
                 "among olive groves and mountains in andalusia, part of the dashboard visible, vertical composition",
    "taller": "modern bright car glass repair workshop interior, a clean silver car inside, black walls with yellow accents, "
              "organized tools, polished floor, professional, vertical composition",
    "sustitucion": "two technicians in black work uniforms installing a new windshield on a car using suction cup lifters, "
                   "modern workshop, vertical composition",
    "tintado": "technician applying dark tint film on the rear side window of a dark car with a heat gun, modern workshop, vertical composition",
    "faro": "close up of a modern car headlight, crystal clear and polished, studio lighting, dark background, vertical composition",
    "adas": "modern car parked in front of a camera calibration target board with a black and white checkered pattern on a stand, "
            "technician holding a tablet, modern workshop, vertical composition",
    "camion": "a big white truck and a van parked in front of a modern industrial workshop on a sunny day, vertical composition",
    "familia": "happy family inside a car driving on a sunny mountain road in andalusia, seen from the front through a clean windshield, "
               "smiling, vertical composition",
}


def main(out):
    import torch

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "toon"))
    from backgrounds import load

    os.makedirs(out, exist_ok=True)
    pipe = load()
    only = set(a for a in sys.argv[2:] if not a.startswith("--"))
    seeds = (101, 202)
    for name, prompt in PLATES.items():
        if only and name not in only:
            continue
        for seed in seeds:
            g = torch.Generator("cpu").manual_seed(seed + sum(map(ord, name)))
            img = pipe(prompt=f"{prompt}, {STYLE}", width=512, height=896, num_inference_steps=6, guidance_scale=8.0, generator=g).images[0]
            img.save(os.path.join(out, f"{name}_{seed}.png"))
            print("[arte]", name, seed, flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "arte")
