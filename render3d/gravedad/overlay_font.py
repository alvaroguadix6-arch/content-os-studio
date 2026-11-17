"""Tipografías del vídeo (con caché)."""
import os

from PIL import ImageFont

CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
_cache = {}


def font(size):
    size = max(8, int(size))
    if size not in _cache:
        path = next((p for p in CANDIDATES if os.path.exists(p)), None)
        _cache[size] = ImageFont.truetype(path, size) if path else ImageFont.load_default(size)
    return _cache[size]
