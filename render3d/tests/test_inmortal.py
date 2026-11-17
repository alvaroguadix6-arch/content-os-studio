"""Pruebas del guion «¿Qué pasaría si fueras inmortal?» (sin Blender)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "inmortal"))
from story import ERAS, SCENES, Story  # noqa: E402


def test_duracion_50_60():
    s = Story()
    assert 50 <= s.duration <= 60
    assert s.frames == round(s.duration * 30)


def test_seis_escenas_en_orden_y_sin_huecos():
    names = [n for n, _, _ in SCENES]
    assert names == ["rayo", "siglo", "ruinas", "tierra", "sol", "espacio"]
    for (_, _, b), (_, a, _) in zip(SCENES, SCENES[1:]):
        assert a == b


def test_gancho_en_los_dos_primeros_segundos():
    s = Story()
    assert s.narration()[0][0] < 0.5


def test_rotulos_dentro_de_su_escena():
    s = Story()
    for a, b, _ in ERAS:
        assert s.scene(a) == s.scene(b - 0.01)


def test_camara_siempre_definida():
    s = Story()
    for f in range(s.frames):
        pos, look, lens = s.camera(f / 30)
        assert pos != look and 10 < lens < 120


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("✓", name)
            except AssertionError as e:
                fails += 1
                print("✗", name, e)
    sys.exit(1 if fails else 0)
