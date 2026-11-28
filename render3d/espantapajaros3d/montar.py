"""Monta «El espantapájaros 3D»: fotogramas de Blender (540×960) → 1080×1920 con textos, destellos y la música.

    python montar.py fotogramas/ salida.mp4
Si faltan fotogramas (render a 15 fps), repite el anterior.
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "simula"))
import espantapajaros as E2D  # noqa: E402

FPS = 30


def main(frames, out):
    n = int(E2D.DUR * FPS)
    wav = out + ".wav"
    E2D.build_audio(wav)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
          f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS), "-i", "-",
                          "-i", wav, "-af", ln + ",aresample=48000", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    last = None
    for fi in range(n):
        path = os.path.join(frames, f"f{fi:05d}.png")
        if os.path.exists(path):
            im = Image.open(path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
            last = ImageEnhance.Color(im).enhance(1.22)
        if last is None:
            raise SystemExit(f"falta el primer fotograma ({path})")
        img = last.convert("RGBA")
        t = fi / FPS
        for a0, a1 in ((43.0, 44.2), (3.35, 3.75)):
            if a0 <= t < a1:
                c = (a0 + a1) / 2
                a = 1 - abs(t - c) / ((a1 - a0) / 2)
                img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(255 * max(0, min(1, a))))))
        E2D.texts(img, t)
        p.stdin.write(img.convert("RGB").tobytes())
    p.stdin.close()
    p.wait()
    os.remove(wav)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
