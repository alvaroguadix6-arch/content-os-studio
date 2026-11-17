"""Textos en pantalla de «¿Qué pasaría si fueras inmortal?»:
gancho, rótulos de época, subtítulos grandes sincronizados y pregunta final con emoji."""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hud import _font, word_cues  # noqa: E402

W, H = 1080, 1920
EMOJI_FONTS = ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "/usr/share/fonts/noto/NotoColorEmoji.ttf",
               "/System/Library/Fonts/Apple Color Emoji.ttc", "C:/Windows/Fonts/seguiemj.ttf"]
HOOK = "¿Y SI NO PUDIERAS MORIR?"


def _emoji(ch, size):
    for p in EMOJI_FONTS:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, 109)
                im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
                ImageDraw.Draw(im).text((0, 0), ch, font=f, embedded_color=True)
                return im.resize((int(size * 136 / 128), size), Image.LANCZOS)
            except Exception:
                continue
    return None


def _fit(d, text, size, maxw, plain=False):
    while size > 30 and d.textlength(text, font=_font(size, italic=not plain)) > maxw:
        size -= 2
    return _font(size, italic=not plain)


class Overlay:
    def __init__(self, story, lines):
        self.story = story
        self.cues = word_cues(lines)
        self.f_sub = _font(80, italic=False)
        final = story.spec.final_text
        self.final_txt = final.replace("👀", "").strip()
        self.eyes = _emoji("👀", 120) if "👀" in final else None

    def frame(self, f):
        st = self.story
        t = f / st.spec.fps
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Gancho (primeros 2,4 s): texto enorme
        if t < 2.4:
            a = int(255 * min(1, t / 0.15, (2.4 - t) / 0.3))
            lines = ["¿Y SI NO", "PUDIERAS MORIR?"]
            fnt = _fit(d, max(lines, key=len), 120, 940)
            for i, ln in enumerate(lines):
                d.text((W // 2, 560 + i * 130), ln, font=fnt, fill=(255, 255, 255, a), anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0, a))
            return img  # durante el gancho no se duplican los subtítulos
        # Rótulo de época
        txt, u = st.era(t)
        if txt:
            a = int(255 * min(1, u / 0.08, (1 - u) / 0.08))
            fnt = _fit(d, txt, 92, 980)
            d.text((W // 2, 360), txt, font=fnt, fill=(255, 214, 120, a), anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0, min(255, a)))
            w = d.textlength(txt, font=fnt)
            d.rectangle((W // 2 - w / 2, 425, W // 2 - w / 2 + w * min(1, u * 1.5), 433), fill=(255, 214, 120, a))
        # Pregunta final con emoji
        fin = st.duration - 3.0
        if t >= fin:
            a = int(255 * min(1, (t - fin) / 0.4))
            words = self.final_txt.split()
            lines = [" ".join(words[:1]), " ".join(words[1:])] if len(words) > 2 else [self.final_txt]
            for i, ln in enumerate(lines):
                fnt = _fit(d, ln, 120, 980)
                d.text((W // 2, 760 + i * 140), ln, font=fnt, fill=(255, 255, 255, a), anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0, a))
            if self.eyes is not None:
                e = self.eyes.copy()
                e.putalpha(e.getchannel("A").point(lambda v: v * a // 255))
                img.alpha_composite(e, (W // 2 - e.width // 2, 760 + len(lines) * 140 - 20))
            return img
        # Subtítulos grandes, palabra activa en amarillo
        for cue in self.cues:
            if cue["start"] <= t < cue["end"] + 0.05:
                words = cue["words"]
                texts = [w[0].upper() for w in words]
                widths = [d.textlength(x, font=self.f_sub) for x in texts]
                sp = d.textlength(" ", font=self.f_sub)
                total = sum(widths) + sp * (len(widths) - 1)
                rows = [(0, len(texts))]
                if total > W * 0.86 and len(texts) > 1:
                    k = (len(texts) + 1) // 2
                    rows = [(0, k), (k, len(texts))]
                for ri, (i0, i1) in enumerate(rows):
                    lw = sum(widths[i0:i1]) + sp * (i1 - i0 - 1)
                    x = (W - lw) / 2
                    y = 1180 + ri * 96 - (len(rows) - 1) * 48
                    for k in range(i0, i1):
                        on = words[k][1] <= t < words[k][2] + 0.05
                        d.text((x, y), texts[k], font=self.f_sub, fill=(255, 212, 0, 255) if on else (255, 255, 255, 255), stroke_width=10, stroke_fill=(0, 0, 0, 255), anchor="lm")
                        x += widths[k] + sp
                break
        return img


def render_overlay(story, lines, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ov = Overlay(story, lines)
    for f in range(story.frames):
        ov.frame(f).save(os.path.join(out_dir, f"h{f:05d}.png"), compress_level=1)
