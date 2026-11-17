"""Simulación de la carrera (sin Blender).

Calcula, para cada fotograma del vídeo, dónde está cada coche, a qué velocidad va,
qué cámara está activa y dónde está. La usan a la vez:
  - la escena 3D de Blender (para animar coches y cámaras),
  - el audio (sonido de motores sincronizado, efecto Doppler),
  - el HUD y los subtítulos.
Así todo queda perfectamente sincronizado.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

# ─────────────────────────── utilidades ───────────────────────────


def smoothstep(a: float, b: float, x: float) -> float:
    if b == a:
        return 1.0 if x >= b else 0.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def interp_keys(keys: list[tuple[float, float]], t: float) -> float:
    """Interpolación suave entre (tiempo, valor)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * smoothstep(t0, t1, t)
    return keys[-1][1]


def catmull_rom_closed(points, samples_per_seg=60):
    n = len(points)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = points[(i - 1) % n], points[i], points[(i + 1) % n], points[(i + 2) % n]
        for k in range(samples_per_seg):
            t = k / samples_per_seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


# ─────────────────────────── circuito ───────────────────────────

# Circuito cerrado ficticio (metros). La recta de meta va en dirección +X por y≈-160.
TRACK_POINTS = [
    (-120, -160), (160, -160), (330, -150), (410, -70), (400, 40), (300, 110),
    (170, 80), (80, 150), (-60, 190), (-250, 160), (-370, 60), (-380, -70), (-290, -150),
]
ROAD_WIDTH = 16.0


class Track:
    def __init__(self, points=TRACK_POINTS, samples_per_seg=80):
        pts = catmull_rom_closed(points, samples_per_seg)
        # Rotamos para que el punto 0 sea la línea de salida/meta (en la recta, x≈0)
        start = min(range(len(pts)), key=lambda i: (pts[i][0]) ** 2 + (pts[i][1] + 160) ** 2)
        pts = pts[start:] + pts[:start]
        self.pts = pts
        self.cum = [0.0]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            self.cum.append(self.cum[-1] + math.dist(a, b))
        self.length = self.cum[-1]

    def _seg(self, s):
        s = s % self.length
        lo, hi = 0, len(self.pts)
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if self.cum[mid] <= s:
                lo = mid
            else:
                hi = mid
        return lo, (s - self.cum[lo]) / max(1e-9, self.cum[lo + 1] - self.cum[lo])

    def point(self, s):
        i, f = self._seg(s)
        a, b = self.pts[i], self.pts[(i + 1) % len(self.pts)]
        return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

    def heading(self, s, ds=2.0):
        a, b = self.point(s - ds), self.point(s + ds)
        return math.atan2(b[1] - a[1], b[0] - a[0])

    def curvature(self, s, ds=6.0):
        h1, h0 = self.heading(s + ds), self.heading(s - ds)
        d = (h1 - h0 + math.pi) % (2 * math.pi) - math.pi
        return d / (2 * ds)

    def frame(self, s, lateral=0.0):
        """Posición con desplazamiento lateral (+ = izquierda en el sentido de marcha)."""
        x, y = self.point(s)
        h = self.heading(s)
        return (x - math.sin(h) * lateral, y + math.cos(h) * lateral, h)


# ─────────────────────────── guion de la carrera ───────────────────────────


@dataclass
class RaceSpec:
    title: str = "Carrera: Rosso contra Giallo"
    car_a_name: str = "Rosso"  # superdeportivo rojo (inspirado en un Ferrari, sin marca)
    car_b_name: str = "Giallo"  # superdeportivo amarillo (inspirado en un Lamborghini, sin marca)
    car_a_color: tuple = (0.55, 0.0, 0.0)
    car_b_color: tuple = (0.9, 0.55, 0.0)
    winner: str = "a"
    fps: int = 30
    intro: float = 4.0  # parrilla y semáforo
    race_time: float = 36.0  # tiempo de carrera (simulado) hasta la meta
    outro: float = 5.0
    slowmo: float = 0.3  # velocidad de la cámara lenta en la meta
    slowmo_window: float = 0.9  # segundos simulados alrededor de la meta a cámara lenta
    narration: list = field(default_factory=list)

    @classmethod
    def from_json(cls, path):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        spec = cls()
        for k, v in d.items():
            if hasattr(spec, k):
                setattr(spec, k, tuple(v) if isinstance(getattr(spec, k), tuple) else v)
        return spec


@dataclass
class CarState:
    s: float
    x: float
    y: float
    yaw: float
    speed: float  # m/s
    lateral: float
    steer: float
    drift: float
    rpm: float
    gear: int


class Race:
    """Toda la coreografía: velocidades, adelantamientos, cámaras y cámara lenta."""

    def __init__(self, spec: RaceSpec | None = None):
        self.spec = spec or RaceSpec()
        self.track = Track()
        sp = self.spec
        self.t_go = sp.intro
        self.t_finish = sp.intro + sp.race_time
        self.t_end_sim = self.t_finish + sp.outro * 0.9
        # Velocidad media "base": arranque, velocidad de crucero ~ 70 m/s (252 km/h) y frenadas en curva
        dt = 1 / 200
        self._tbl_t, self._tbl_s, self._tbl_v = [], [], []
        s, v, t = 0.0, 0.0, 0.0
        raw = []
        while t <= self.t_end_sim + 1:
            if t < self.t_go:
                v = 0.0
            else:
                k = abs(self.track.curvature(s + 40))
                target = 78 - min(40, k * 2600)  # frena antes de las curvas
                if t > self.t_finish:
                    target = 30
                acc = 9.0 if target > v else -14.0
                v = max(0.0, min(target if acc < 0 else 1e9, v + acc * dt)) if acc < 0 else min(target, v + acc * dt * (1.2 - v / 95))
            raw.append((t, s, v))
            s += v * dt
            t += dt
        # Escalamos para que el coche medio cruce la meta (1 vuelta) justo en t_finish
        s_at_finish = next(ss for tt, ss, vv in raw if tt >= self.t_finish)
        k = self.track.length / s_at_finish
        for tt, ss, vv in raw:
            self._tbl_t.append(tt)
            self._tbl_s.append(ss * k)
            self._tbl_v.append(vv * k)
        self._dt = dt
        win = 1 if sp.winner == "a" else -1
        T0, TF = self.t_go, self.t_finish
        R = sp.race_time
        # Ventaja de A sobre B (metros). Guion: B sale mejor, A presiona, adelanta en curva,
        # B contraataca con rebufo, y final de foto: gana por medio coche.
        self.gap_keys = [
            (0, 0), (T0, 0), (T0 + 0.10 * R, -7), (T0 + 0.30 * R, -9), (T0 + 0.45 * R, -3.5),
            (T0 + 0.58 * R, 4.5), (T0 + 0.72 * R, 3.0), (T0 + 0.86 * R, -2.0), (T0 + 0.95 * R, -0.6),
            (TF, 0.9 * win), (TF + 3, 6 * win),
        ]
        # Trazada común (desplazamiento lateral compartido, m): pequeñas variaciones de línea de carrera
        self.line_keys = [(0, 0), (T0 + 0.15 * R, 0.6), (T0 + 0.35 * R, -0.5), (T0 + 0.55 * R, 0.4), (T0 + 0.75 * R, -0.4), (TF, 0)]
        self._build_timewarp()
        self.shots = self._build_shots()

    # ── tiempo de vídeo → tiempo simulado (cámara lenta en la meta) ──
    def _build_timewarp(self):
        sp = self.spec
        a = self.t_finish - sp.slowmo_window * 0.6
        b = self.t_finish + sp.slowmo_window * 0.4
        self._warp = (a, b)
        video_len = a + (b - a) / sp.slowmo + (self.t_end_sim - b)
        self.duration = video_len
        self.frames = int(round(video_len * sp.fps))

    def sim_time(self, video_t: float) -> float:
        a, b = self._warp
        sm = self.spec.slowmo
        if video_t <= a:
            return video_t
        if video_t <= a + (b - a) / sm:
            return a + (video_t - a) * sm
        return b + (video_t - a - (b - a) / sm)

    def is_slowmo(self, video_t):
        a, b = self._warp
        return a < video_t <= a + (b - a) / self.spec.slowmo

    def video_time_of_sim(self, t):
        a, b = self._warp
        if t <= a:
            return t
        if t <= b:
            return a + (t - a) / self.spec.slowmo
        return a + (b - a) / self.spec.slowmo + (t - b)

    # ── coches ──
    def _base(self, t):
        i = min(len(self._tbl_t) - 1, max(0, int(t / self._dt)))
        return self._tbl_s[i], self._tbl_v[i]

    SEP_CLOSE = 4.2  # separación lateral entre centros cuando van rueda con rueda (m)

    def lateral(self, which, t):
        """Separación automática: si están cerca en longitudinal, cada uno en su carril (A izquierda, B derecha)."""
        g = abs(interp_keys(self.gap_keys, t))
        sep = self.SEP_CLOSE * (1 - smoothstep(6.0, 9.5, g))
        base = interp_keys(self.line_keys, t)
        return base + (sep / 2 if which == "a" else -sep / 2)

    def car(self, which: str, t: float) -> CarState:
        s, v = self._base(t)
        gap = interp_keys(self.gap_keys, t)
        dgap = (interp_keys(self.gap_keys, t + 0.05) - interp_keys(self.gap_keys, t - 0.05)) / 0.1
        if which == "a":
            s += gap / 2
            v += dgap / 2
            lat = self.lateral("a", t)
            # posición de salida: A ligeramente por detrás en la parrilla
            s += -6 if t < self.t_go else -6 * (1 - smoothstep(self.t_go, self.t_go + 6, t))
        else:
            s -= gap / 2
            v -= dgap / 2
            lat = self.lateral("b", t)
            s += -6 if t < self.t_go else -6 * (1 - smoothstep(self.t_go, self.t_go + 6, t))
        x, y, h = self.track.frame(s, lat)
        k = self.track.curvature(s)
        # Derrape controlado en curva rápida (estética de videojuego)
        drift = max(-0.22, min(0.22, k * v * v * 0.0011)) if v > 25 else 0.0
        dlat = (self.lateral(which, t + 0.1) - lat) / 0.1
        lat_yaw = math.atan2(dlat, max(5, v))
        steer = max(-0.45, min(0.45, k * 4.4 + lat_yaw * 1.5))
        # Cambio de marchas simulado para el sonido y el HUD
        kmh = v * 3.6
        gears = [0, 70, 120, 165, 210, 255, 400]
        gear = next(g for g in range(1, 7) if kmh < gears[g])
        lo, hi = gears[gear - 1], gears[gear]
        rpm = 3000 + 5500 * (kmh - lo) / max(1, hi - lo)
        if v < 0.5:
            rpm, gear = 1200 + (1800 if t > self.t_go - 2 else 0), 1
        return CarState(s, x, y, h + drift + lat_yaw, v, lat, steer, drift, rpm, gear)

    def leader(self, t):
        return "a" if self.car("a", t).s >= self.car("b", t).s else "b"

    # ── cámaras ──
    def _build_shots(self):
        T0, TF, R = self.t_go, self.t_finish, self.spec.race_time
        v = self.video_time_of_sim
        a, b = self._warp
        shots = [
            ("drone_grid", 0, v(T0 - 1.2), {}),
            ("start_low", v(T0 - 1.2), v(T0 + 2.6), {}),
            ("chase", v(T0 + 2.6), v(T0 + 0.18 * R), {"car": "b", "dist": 10, "h": 2.6}),
            ("trackside", v(T0 + 0.18 * R), v(T0 + 0.27 * R), {"at": 0.27}),
            ("bumper", v(T0 + 0.27 * R), v(T0 + 0.40 * R), {"car": "b", "look": "a"}),
            ("heli", v(T0 + 0.40 * R), v(T0 + 0.50 * R), {"car": "a"}),
            ("side", v(T0 + 0.50 * R), v(T0 + 0.63 * R), {"side": 1}),
            ("chase", v(T0 + 0.63 * R), v(T0 + 0.75 * R), {"car": "a", "dist": 8, "h": 1.6}),
            ("front", v(T0 + 0.75 * R), v(T0 + 0.86 * R), {}),
            ("side", v(T0 + 0.86 * R), a, {"side": -1}),
            ("finish_low", a, v(b) + 0.4, {}),
            ("orbit_end", v(b) + 0.4, self.duration + 0.01, {}),
        ]
        return [{"type": s[0], "start": s[1], "end": s[2], **s[3]} for s in shots]

    def shot_at(self, video_t):
        for sh in self.shots:
            if sh["start"] <= video_t < sh["end"]:
                return sh
        return self.shots[-1]

    def camera(self, video_t):
        """Devuelve (posición, punto al que mira, focal en mm, roll) de la cámara activa."""
        sh = self.shot_at(video_t)
        t = self.sim_time(video_t)
        A, B = self.car("a", t), self.car("b", t)
        mid = ((A.x + B.x) / 2, (A.y + B.y) / 2)
        u = (video_t - sh["start"]) / max(0.01, sh["end"] - sh["start"])
        typ = sh["type"]
        tr = self.track
        if typ == "drone_grid":
            ang = -1.9 + u * 1.3
            r = 34 - 12 * u
            return (mid[0] + math.cos(ang) * r, mid[1] + math.sin(ang) * r, 22 - 15 * u), (mid[0], mid[1], 0.6), 30, 0
        if typ == "start_low":
            # cámara a ras de suelo entre los dos carriles: los coches pasan uno a cada lado
            x, y, h = tr.frame(28, interp_keys(self.line_keys, t))
            return (x, y, 0.45), (mid[0], mid[1], 0.9), 24, 0
        if typ in ("chase", "heli"):
            c = A if sh.get("car", "a") == "a" else B
            if typ == "heli":
                lag = 18
                x, y, h = tr.frame(c.s - lag, c.lateral * 0.5)
                return (x, y, 26), (c.x + math.cos(c.yaw) * 10, c.y + math.sin(c.yaw) * 10, 0), 32, 0
            d = sh.get("dist", 9)
            other = B if c is A else A
            hcam = sh.get("h", 2.2)
            # si el otro coche está entre la cámara y el objetivo, subimos y alejamos la cámara
            if c.s - d - 3 < other.s < c.s:
                d, hcam = d + 6, hcam + 3.5
            x, y, h = tr.frame(c.s - d, c.lateral * 0.7)
            fwd = tr.frame(c.s + 25, c.lateral * 0.4)
            shake = 0.04 * math.sin(video_t * 31) + 0.03 * math.sin(video_t * 47)
            return (x, y, hcam + shake), (fwd[0], fwd[1], 1.0), 26, shake * 0.3
        if typ == "bumper":
            c = A if sh["car"] == "a" else B
            o = A if sh["look"] == "a" else B
            back = (c.x - math.cos(c.yaw) * 2.6, c.y - math.sin(c.yaw) * 2.6, 0.75)
            return back, (o.x, o.y, 0.7), 18, 0
        if typ == "trackside":
            # cámara fija en el punto por donde pasarán los coches a mitad del plano
            tm = self.sim_time((sh["start"] + sh["end"]) / 2)
            s0 = (self.car("a", tm).s + self.car("b", tm).s) / 2 + 8
            x, y, h = tr.frame(s0, -(ROAD_WIDTH / 2 + 5))
            lead = A if A.s > B.s else B
            return (x, y, 1.6), (lead.x, lead.y, 0.8), 50, 0
        if typ == "side":
            side = sh["side"]
            s_mid = (A.s + B.s) / 2 + 2
            x, y, h = tr.frame(s_mid, side * (ROAD_WIDTH / 2 + 3.5))
            return (x, y, 1.1), (mid[0], mid[1], 0.7), 22, 0
        if typ == "front":
            lead = A if A.s > B.s else B
            x, y, h = tr.frame(lead.s + 11, 0)
            return (x, y, 1.0), (mid[0], mid[1], 0.8), 30, 0
        if typ == "finish_low":
            L = tr.length
            x, y, h = tr.frame(L + 9, ROAD_WIDTH / 2 + 1.5)
            fx, fy, _ = tr.frame(L - 12, 0)
            return (x, y, 0.4), (fx, fy, 0.6), 24, 0
        # orbit_end: celebración del ganador
        w = A if self.spec.winner == "a" else B
        ang = w.yaw + 2.2 + u * 1.6
        return (w.x + math.cos(ang) * 9, w.y + math.sin(ang) * 9, 2.4 + u * 3), (w.x, w.y, 0.7), 28, 0

    # ── datos para audio/HUD ──
    def timeline(self):
        rows = []
        fps = self.spec.fps
        for f in range(self.frames):
            vt = f / fps
            t = self.sim_time(vt)
            A, B = self.car("a", t), self.car("b", t)
            cam, look, lens, roll = self.camera(vt)
            rows.append({"f": f, "vt": vt, "t": t, "a": A.__dict__, "b": B.__dict__, "cam": cam, "shot": self.shot_at(vt)["type"], "slowmo": self.is_slowmo(vt)})
        return rows


if __name__ == "__main__":
    r = Race()
    print(f"Circuito: {r.track.length:.0f} m · vídeo {r.duration:.1f} s · {r.frames} fotogramas")
    for vt in [0, 5, 10, 20, 30, 38, 40, r.duration - 0.1]:
        t = r.sim_time(vt)
        A, B = r.car("a", t), r.car("b", t)
        print(f"v={vt:5.1f} t={t:5.1f} A s={A.s:7.1f} {A.speed*3.6:5.0f}km/h g{A.gear} | B s={B.s:7.1f} {B.speed*3.6:5.0f}km/h | líder {r.leader(t)} | {r.shot_at(vt)['type']}")
