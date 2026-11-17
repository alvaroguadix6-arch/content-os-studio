"""Fondos ilustrados (estilo pintura digital de cuento) con IA de código abierto, sin coste.

Modelo: LCM Dreamshaper v7 (SimianLuo/LCM_Dreamshaper_v7, licencia MIT en su ficha; basado en
Dreamshaper / Stable Diffusion 1.5, CreativeML OpenRAIL-M, que permite uso comercial con las
restricciones de uso de esa licencia). Funciona en CPU en 4 pasos.

    python backgrounds.py salida/ [nombre ...]
"""
from __future__ import annotations

import os
import sys
import time

STYLE = ("digital painting, storybook illustration, highly detailed background art, soft volumetric light, "
         "painterly textures, cinematic composition, vertical, no people, no text")
NEGATIVE = "people, person, character, text, watermark, logo, signature, blurry, lowres, deformed"

SCENES = {
    "rayo": "empty city street at dusk under a dramatic thunderstorm, wet asphalt reflecting street lamps, tall old buildings, dark clouds",
    "siglo": "futuristic city street at night, glowing cyan neon lines on glass skyscrapers, flying lights, wet road reflections",
    "ruinas": "ruined abandoned city street overgrown with moss and trees, broken skyscrapers, golden sunset light through mist",
    "tierra": "planet earth seen from space, continents and clouds, thin blue atmosphere, stars, deep space",
    "sol": "scorched cracked desert with glowing lava cracks under a gigantic red giant sun filling the sky, red apocalyptic atmosphere",
    "espacio": "lonely deep space with countless stars and a faint purple nebula, a tiny white dwarf star far away",
}


def load(model="SimianLuo/LCM_Dreamshaper_v7"):
    import torch
    from diffusers import DiffusionPipeline

    torch.set_num_threads(os.cpu_count() or 4)
    pipe = DiffusionPipeline.from_pretrained(model, torch_dtype=torch.float32, safety_checker=None)
    pipe.to("cpu")
    pipe.set_progress_bar_config(disable=True)
    return pipe


def generate(pipe, name, out_dir, seed=7, w=512, h=896, steps=4):
    import torch
    from PIL import Image

    g = torch.Generator("cpu").manual_seed(seed)
    t = time.time()
    img = pipe(prompt=f"{SCENES[name]}, {STYLE}", width=w, height=h, num_inference_steps=steps,
               guidance_scale=8.0, generator=g).images[0]
    img = img.resize((1080, 1920), Image.LANCZOS)
    path = os.path.join(out_dir, f"fondo_{name}.png")
    img.save(path)
    print(f"[fondo] {name} en {time.time() - t:.1f} s → {path}", flush=True)
    return path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "fondos"
    names = sys.argv[2:] or list(SCENES)
    os.makedirs(out, exist_ok=True)
    pipe = load()
    for n in names:
        generate(pipe, n, out)
