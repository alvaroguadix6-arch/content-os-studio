"""Mejora de calidad de las ilustraciones del anuncio (todo gratuito y en CPU).

1. Pase a más resolución (768×1344) con img2img: añade detalle sin cambiar la composición.
2. Repaso de caras: cada cara detectada se rehace a 512×512 y se vuelve a pegar con borde suave.
3. Reescalado ×2 con Real-ESRGAN (BSD-3) → 1536×2688, nítido a pantalla completa.

    python calidad.py entrada.png salida.png "descripción de la escena"
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "toon"))
sys.path.insert(0, HERE)


def pipelines():
    from backgrounds import load
    from diffusers import LatentConsistencyModelImg2ImgPipeline

    base = load()
    return LatentConsistencyModelImg2ImgPipeline(**base.components)


def img2img(pipe, img, prompt, strength, seed=7, steps=8):
    import torch

    g = torch.Generator("cpu").manual_seed(seed)
    return pipe(prompt=prompt, image=img, strength=strength, num_inference_steps=steps, guidance_scale=8.0, generator=g).images[0]


def detect_faces(img):
    import cv2

    a = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    cc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    faces = cc.detectMultiScale(a, scaleFactor=1.08, minNeighbors=6, minSize=(int(img.width * 0.07),) * 2)
    return [tuple(int(v) for v in f) for f in faces]


def fix_faces(pipe, img, face_prompt, strength=0.3):
    """face_prompt: una descripción por cara, separadas por «|», de izquierda a derecha."""
    out = img.copy()
    prompts = [p.strip() for p in face_prompt.split("|")]
    for i, (x, y, w, h) in enumerate(sorted(detect_faces(img))):
        fp = prompts[min(i, len(prompts) - 1)] + ", detailed realistic face, natural skin texture, sharp eyes, professional photo"
        cx, cy, s = x + w / 2, y + h / 2, max(w, h) * 1.7
        box = (int(cx - s / 2), int(cy - s / 2), int(cx + s / 2), int(cy + s / 2))
        crop = img.crop(box).resize((512, 512), Image.LANCZOS)
        new = img2img(pipe, crop, fp, strength, seed=31 + i).resize((box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
        m = Image.new("L", new.size, 0)
        pad = new.width * 0.12
        ImageDraw.Draw(m).ellipse([pad, pad, new.width - pad, new.height - pad], fill=255)
        out.paste(new, box[:2], m.filter(ImageFilter.GaussianBlur(new.width * 0.06)))
        print(f"  cara {i + 1}: {box}", flush=True)
    return out


def esrgan(img):
    import spandrel
    import torch
    from huggingface_hub import hf_hub_download

    if not hasattr(esrgan, "m"):
        esrgan.m = spandrel.ModelLoader().load_from_file(hf_hub_download("ai-forever/Real-ESRGAN", "RealESRGAN_x2.pth")).eval()
    m = esrgan.m
    a = torch.from_numpy(np.asarray(img.convert("RGB")).astype(np.float32) / 255).permute(2, 0, 1)[None]
    out = np.zeros((img.height * 2, img.width * 2, 3), np.float32)
    T, P = 384, 16  # por teselas para no agotar memoria
    with torch.no_grad():
        for y in range(0, img.height, T):
            for x in range(0, img.width, T):
                y0, x0 = max(0, y - P), max(0, x - P)
                y1, x1 = min(img.height, y + T + P), min(img.width, x + T + P)
                r = m(a[:, :, y0:y1, x0:x1])[0].permute(1, 2, 0).numpy()
                oy, ox = (y - y0) * 2, (x - x0) * 2
                hh, ww = min(T, img.height - y) * 2, min(T, img.width - x) * 2
                out[y * 2:y * 2 + hh, x * 2:x * 2 + ww] = r[oy:oy + hh, ox:ox + ww]
    return Image.fromarray((out.clip(0, 1) * 255).astype(np.uint8))


def mejorar(pipe, src, dst, prompt, faces=None, strength=0.35):
    from arte import STYLE

    img = Image.open(src).convert("RGB").resize((768, 1344), Image.LANCZOS)
    img = img2img(pipe, img, f"{prompt}, {STYLE}, highly detailed, sharp focus, 8k", strength)
    if faces:
        img = fix_faces(pipe, img, faces)
    img = esrgan(img)
    img.save(dst)
    print("[calidad]", os.path.basename(dst), img.size, flush=True)


if __name__ == "__main__":
    pipe = pipelines()
    mejorar(pipe, sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
