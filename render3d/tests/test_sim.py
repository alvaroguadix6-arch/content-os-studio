"""Pruebas de la simulación de carrera (sin Blender): python3 render3d/tests/test_sim.py"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sim import Race, RaceSpec  # noqa: E402


def test_duracion_y_fotogramas():
    r = Race()
    assert 30 <= r.duration <= 60, r.duration
    assert r.frames == round(r.duration * 30)


def test_ganador_y_cambios_de_lider():
    for winner in ("a", "b"):
        r = Race(RaceSpec(winner=winner))
        # justo después de la meta, el ganador va delante
        t = r.t_finish + 0.05
        assert r.leader(t) == winner
        leaders = [r.leader(r.t_go + k * 0.5) for k in range(2, int(r.spec.race_time * 2))]
        changes = sum(1 for x, y in zip(leaders, leaders[1:]) if x != y)
        assert changes >= 2, "debe haber adelantamientos"


def test_cruzan_la_meta_en_su_momento():
    r = Race()
    L = r.track.length
    a = r.car("a", r.t_finish)
    b = r.car("b", r.t_finish)
    assert abs((a.s + b.s) / 2 - L) < 15


def test_coches_no_se_atraviesan():
    """Huella real del coche: 4,4 m de largo y 2,0 m de ancho (+ margen)."""
    for winner in ("a", "b"):
        r = Race(RaceSpec(winner=winner))
        for k in range(r.frames):
            t = r.sim_time(k / 30)
            a, b = r.car("a", t), r.car("b", t)
            h = a.yaw
            dx, dy = b.x - a.x, b.y - a.y
            lon = dx * math.cos(h) + dy * math.sin(h)
            lat = -dx * math.sin(h) + dy * math.cos(h)
            assert not (abs(lon) < 4.8 and abs(lat) < 2.4), f"choque en t={t:.2f}: lon={lon:.2f} lat={lat:.2f}"


def test_camaras_nunca_dentro_de_un_coche():
    r = Race()
    for k in range(r.frames):
        vt = k / 30
        t = r.sim_time(vt)
        cam, _, _, _ = r.camera(vt)
        if r.shot_at(vt)["type"] == "bumper":
            continue  # cámara montada en el coche a propósito
        for w in "ab":
            c = r.car(w, t)
            dx, dy = cam[0] - c.x, cam[1] - c.y
            lon = dx * math.cos(c.yaw) + dy * math.sin(c.yaw)
            lat = -dx * math.sin(c.yaw) + dy * math.cos(c.yaw)
            assert not (abs(lon) < 2.4 and abs(lat) < 1.45 and cam[2] < 1.3), f"cámara dentro del coche {w} en t={t:.2f}"


def test_velocidades_realistas():
    r = Race()
    vmax = max(r.car("a", r.sim_time(k / 30)).speed for k in range(r.frames)) * 3.6
    assert 200 < vmax < 340, vmax


def test_camaras_cubren_todo():
    r = Race()
    for k in range(r.frames):
        assert r.shot_at(k / 30) is not None


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
