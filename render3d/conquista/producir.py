"""TU PUEBLO CONQUISTA ESPAÑA · produce un episodio completo con un solo comando.

    python producir.py <temporada> <episodio>          p. ej.  python producir.py temporada1 2

1. Lee los votos reales de temporada/votos/ep01.csv … epNN.csv (pueblo,provincia,votos).
2. Calcula el mapa (conquistas, top 5, rivalidades, invasiones) y escribe temporada/salida/epNN_resumen.txt
   (incluye las filas que no se han reconocido: no suman hasta que se corrijan).
3. Genera el guion a partir de los datos, la voz (Kokoro, Alex), los fotogramas y el montaje con música y efectos.
Resultado: temporada/salida/epNN.mp4 (1080×1920, 30 fps).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import conquista  # noqa: E402

PY_VOZ = os.environ.get("PY_VOZ", sys.executable)      # Python con kokoro instalado
PY_MONTAJE = os.environ.get("PY_MONTAJE", sys.executable)


def main():
    temporada, ep = os.path.abspath(sys.argv[1]), int(sys.argv[2])
    out = os.path.join(temporada, "salida")
    work = os.path.join(out, f"_trabajo_ep{ep:02d}")
    os.makedirs(work, exist_ok=True)
    st = conquista.estado(temporada, ep)
    res = conquista.resumen(st)
    open(os.path.join(out, f"ep{ep:02d}_resumen.txt"), "w", encoding="utf-8").write(res + "\n")
    print(res)
    g = os.path.join(work, "guion.json")
    subprocess.run([sys.executable, os.path.join(HERE, "episodio.py"), "guion", temporada, str(ep), g], check=True)
    nar = os.path.join(work, "voz")
    subprocess.run([PY_VOZ, os.path.join(ROOT, "gravedad", "voz.py"), nar, "--motor", "kokoro", "--voz", "em_alex",
                    "--speed", "1.15", "--guion", g], check=True)
    fr = os.path.join(work, "frames")
    shutil.rmtree(fr, ignore_errors=True)
    subprocess.run([sys.executable, os.path.join(HERE, "episodio.py"), "frames", temporada, str(ep), nar, fr], check=True)
    mp4 = os.path.join(out, f"ep{ep:02d}.mp4")
    env = dict(os.environ, CONQ_TEMPORADA=temporada, CONQ_EP=str(ep), PYTHONPATH=HERE)
    subprocess.run([PY_MONTAJE, os.path.join(ROOT, "simula", "montaje.py"), "episodio", "--narracion", nar, "--frames", fr, "--out", mp4],
                   check=True, env=env)
    shutil.rmtree(fr, ignore_errors=True)
    print("✅ Episodio listo:", mp4)


if __name__ == "__main__":
    main()
