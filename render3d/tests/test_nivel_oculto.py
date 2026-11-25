"""Pruebas del adaptador de paquetes (sin voz ni vídeo): python3 render3d/tests/test_nivel_oculto.py"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "simula"))
import nivel_oculto as no  # noqa: E402

PKG = {
    "id": "2026-12-02-prueba", "brand": "nivel-oculto", "language": "es", "format": "reel", "pillar": "ciencia",
    "title": "Prueba", "script": ["38 minutos y 11 segundos.", "En 1966 un físico dijo 42.", "Pide 200.000 dólares.", "Fin."],
    "on_screen_text": [{"at": 0.0, "text": "38 MIN"}, {"at": 2.5, "text": "1966"}],
    "visual_brief": [{"scene": 1, "seconds": 2.0, "kind": "simulacion", "visual": "x"},
                     {"scene": 2, "seconds": 6.0, "kind": "grafico", "visual": "y"}],
    "caption": {"text": "x", "hashtags": ["#ciencia"]}, "sources": [{"claim": "c", "source": "s"}],
}


def test_numeros_en_letra():
    assert no.num_es(1922) == "mil novecientos veintidós"
    assert no.num_es(21000) == "veintiún mil"
    assert no.num_es(200000) == "doscientos mil"
    assert no.num_es(1_500_000) == "un millón quinientos mil"
    assert no.spoken("3,8 kilos") == "Tres coma ocho kilos"
    assert no.spoken("Pide 200.000 dólares.") == "Pide doscientos mil dólares."


def test_guion_para_voz_y_pausas():
    g = no.guion_for_voice(PKG)
    assert [k for k, _ in g["guion"]] == ["b01", "b02", "b03", "b04"]
    assert g["pausas"]["b01"] == 0.32 and g["pausas"]["b04"] == 0.0
    assert not any(ch.isdigit() for _, t in g["guion"] for ch in t)


def test_escenas_rotulos_y_fotogramas():
    kinds, cards = no.beat_layout(PKG)
    assert kinds[0] == "simulacion" and kinds[-1] == "grafico"
    assert cards[0] == "38 MIN"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "p.json")
        json.dump(PKG, open(p, "w"))
        nar = no.synthetic_narration(no.load_package(p))
        v = no.make_video(PKG)(nar)
        assert [n for _, n in v.scenes] == ["b01", "b02", "b03", "b04"]
        for f in (0, int(v.duration * 30) - 1):
            im = v.frame(f)
            assert im.size == (1080, 1920)


def test_paquete_sin_guion_falla():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "p.json")
        json.dump({"id": "x", "script": []}, open(p, "w"))
        try:
            no.load_package(p)
        except ValueError:
            return
        raise AssertionError("debería fallar")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
