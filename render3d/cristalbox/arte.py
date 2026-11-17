"""Ilustraciones del anuncio de Cristalbox (generadas con IA libre: LCM Dreamshaper v7, CPU).

El logotipo NO se genera: se usa el archivo original (arte/logo_cristalbox.png) sin modificarlo.

    python arte.py salida/ [nombre ...]      (usa el Python con torch + diffusers)
"""
from __future__ import annotations

import os
import sys

STYLE = ("professional automotive advertising photography, photorealistic, cinematic lighting, "
         "sharp focus, high detail, clean composition, no text, no letters, no logos")
PLATES = {
    "carretera": "driver point of view from inside a modern car looking through a clean windshield at a sunny highway "
                 "among olive groves and mountains in andalusia, part of the dashboard visible, vertical composition",
    "taller": "interior of a modern bright car glass workshop, only one clean dark grey SUV parked on the floor in the center, new windshields stored upright on racks along the wall, black walls with yellow accents, clean grey epoxy floor, bright LED ceiling lights, no car lift, nobody, wide shot, vertical composition",
    "sustitucion": "two professional auto glass technicians in black polo shirts and work gloves carefully placing a new windshield onto a silver car using suction cup handles, front three quarter view, focused expressions, detailed realistic faces, bright modern workshop, vertical composition",
    "tintado": "technician applying dark tint film on the rear side window of a dark car with a heat gun, modern workshop, vertical composition",
    "faro": "close up of a modern car headlight, crystal clear and polished, studio lighting, dark background, vertical composition",
    "adas": "modern car parked in front of a camera calibration target board with a black and white checkered pattern on a stand, "
            "technician holding a tablet, modern workshop, vertical composition",
    "camion": "a big white truck and a van parked in front of a modern industrial workshop on a sunny day, vertical composition",
    "familia": "close up of a smiling young couple sitting in the front seats of a car, the man driving with hands on the steering wheel, seen from the front through the clean windshield, sunny day, warm natural light, detailed realistic faces, upper body, vertical composition",
}


def main(out):
    import torch

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "toon"))
    from backgrounds import load

    os.makedirs(out, exist_ok=True)
    pipe = load()
    only = set(a for a in sys.argv[2:] if not a.startswith("--"))
    seeds = tuple(int(x) for x in os.environ.get("SEMILLAS", "101,202").split(","))
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
