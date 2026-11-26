"""Pruebas de quiz y Conquista: lote, guion, textos, zonas seguras y portada (sin voz; tiempos sintéticos).

    python3 render3d/tests/test_formatos.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(ROOT, "simula")
CONQ = os.path.join(ROOT, "conquista")
sys.path.insert(0, SIM)
import formatos  # noqa: E402
import zona_segura as ZS  # noqa: E402

PRIVADO = ("@", "http", "token", "usuario")


def test_lote_valida_y_limita():
    j = formatos.lote("islas, castillos,islas", "2")
    assert [x["id"] for x in j] == ["quiz-islas", "quiz-castillos", "conquista-ep02"], j
    for mal in ("../etc/passwd", "noexiste", "islas;rm -rf /"):
        try:
            formatos.lote(mal)
            raise AssertionError(f"debería rechazar {mal!r}")
        except ValueError:
            pass
    try:
        formatos.lote("islas,castillos,gentilicios,comida,fiestas,monumentos")
        raise AssertionError("debería limitar a 5")
    except ValueError:
        pass
    try:
        formatos.lote("", "")
        raise AssertionError("lote vacío")
    except ValueError:
        pass


def test_quiz_json_completos():
    for t, _, _ in formatos.temas():
        q = formatos.cargar_quiz(t)
        assert len(q["preguntas"]) == 5, t
        for p in q["preguntas"]:
            assert p["q"] and p["respuesta"] and len(p["punto"]) == 2, (t, p)
        g = formatos.guion_quiz(q)
        assert [k for k, _ in g["guion"]][:3] == ["intro", "q1", "a1"] and g["guion"][-1][0] == "outro"


def test_textos_sin_datos_privados():
    for t in ("islas", "castillos", "gentilicios", "sabias_1"):
        txt, tags = formatos.texto_quiz(formatos.cargar_quiz(t))
        assert 3 <= len(tags) <= 5 and all(x.startswith("#") for x in tags)
        assert not any(p in txt.lower() for p in PRIVADO), txt
    txt, tags = formatos.texto_conquista(os.path.join(CONQ, "temporada1"), 2)
    assert "episodio 3" in txt.lower() and not any(p in txt.lower() for p in PRIVADO), txt


def _zonas_quiz(tema):
    os.environ["QUIZ"] = tema
    import importlib
    import quiz
    importlib.reload(quiz)
    nar = formatos.narracion_sintetica(formatos.guion_quiz(formatos.cargar_quiz(tema)))
    v = quiz.Video(nar, tema)
    return v, ZS.fuera_de_zona(v, paso=0.5)


def test_zonas_seguras_quiz():
    for tema in ("islas", "fiestas_peru"):  # España con Canarias y un mapa de otro país
        _, malos = _zonas_quiz(tema)
        assert not malos, (tema, malos)


def test_canarias_dentro_de_la_zona():
    os.environ["QUIZ"] = "islas"
    import importlib
    import quiz
    importlib.reload(quiz)
    c = quiz.CAN
    assert not ZS.inseguro((c["x"], c["y"], c["x"] + c["w"], c["y"] + c["h"]))
    for lon, lat in ((-18.0, 27.75), (-13.5, 29.25), (-15.6, 28.1)):  # El Hierro, La Graciosa, Gran Canaria
        x, y = quiz.proj(lon, lat, can=True)
        assert c["x"] < x < c["x"] + c["w"] and c["y"] < y < c["y"] + c["h"], (lon, lat, x, y)


def test_zonas_seguras_conquista():
    sys.path.insert(0, CONQ)
    import conquista
    import episodio
    for ep in (1, 2):
        st = conquista.estado(os.path.join(CONQ, "temporada1"), ep)
        g = {"guion": [[k, t] for k, t, _ in episodio.guion(st)], "pausas": {}}
        v = episodio.Video(formatos.narracion_sintetica(g), os.path.join(CONQ, "temporada1"), ep)
        malos = ZS.fuera_de_zona(v, paso=0.5)
        assert not malos, (ep, malos)


def test_portada():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "voz"))
        nar = formatos.narracion_sintetica(formatos.guion_quiz(formatos.cargar_quiz("castillos")))
        json.dump(nar, open(os.path.join(d, "voz", "narracion.json"), "w"))
        out = os.path.join(d, "p.jpg")
        r = subprocess.run([sys.executable, os.path.join(SIM, "formatos.py"), "portada-auto", "quiz", "castillos",
                            os.path.join(d, "voz"), out], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        from PIL import Image
        assert Image.open(out).size == (1080, 1920)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
