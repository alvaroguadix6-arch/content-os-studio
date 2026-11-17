"""«¿QUÉ PASARÍA SI FUERAS INMORTAL?» — guion técnico (sin Blender).

Define escenas, cámara fotograma a fotograma, narración, rótulos de época y textos.
La usan la escena 3D, el audio y el HUD, para que todo esté sincronizado.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field


def smooth(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(a, b, t):
    return tuple(lerp(x, y, t) for x, y in zip(a, b))


# Posiciones de los "decorados" (lejos unos de otros dentro del mismo archivo de Blender)
CITY = (0.0, 0.0, 0.0)
EARTH = (0.0, 60000.0, 0.0)
SCORCHED = (30000.0, 0.0, 0.0)
SPACE = (-30000.0, 0.0, 0.0)
EARTH_R = 60.0


@dataclass
class StorySpec:
    title: str = "¿Qué pasaría si fueras inmortal?"
    fps: int = 30
    final_text: str = "¿ACEPTARÍAS SER INMORTAL? 👀"
    style: str = "toon"  # "toon" = personaje 2D de dibujos animados; "3d" = figura 3D con capucha
    narration: list = field(default_factory=list)

    @classmethod
    def from_json(cls, path):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        s = cls()
        for k, v in d.items():
            if hasattr(s, k):
                setattr(s, k, v)
        return s


# Escenas (segundos de vídeo)
SCENES = [
    ("rayo", 0.0, 9.0),        # gancho + descubre que es inmortal
    ("siglo", 9.0, 18.5),      # +100 años: la ciudad cambia
    ("ruinas", 18.5, 28.0),    # +500 años: generaciones que desaparecen
    ("tierra", 28.0, 39.0),    # millones de años: la Tierra se transforma
    ("sol", 39.0, 49.5),       # el Sol al final de su vida
    ("espacio", 49.5, 57.0),   # solo en el espacio + pregunta final
]
LIGHTNING_T = 1.05  # el rayo cae en el segundo ~1 (gancho)

ERAS = [
    (9.3, 18.3, "+100 AÑOS"),
    (18.8, 27.8, "+500 AÑOS"),
    (28.6, 32.2, "+1 MILLÓN DE AÑOS"),
    (32.2, 35.6, "+250 MILLONES DE AÑOS"),
    (35.6, 38.8, "+1.000 MILLONES DE AÑOS"),
    (39.4, 49.2, "+5.000 MILLONES DE AÑOS"),
]

DEFAULT_NARRATION = [
    (0.1, "¿Y si no pudieras morir? ¡Nunca jamás!"),
    (2.2, "Te cae un rayo, y nada. Te aplasta un piano, ¡y te levantas! Te atropella un coche, ¡y sales volando y caes de pie, como si nada!"),
    (9.2, "Pasan cien años. Tus amigos envejecen y se van, uno a uno, pero tú sigues exactamente igual. Tu ciudad se llena de rascacielos y coches voladores, y ya ni la reconoces."),
    (18.7, "Quinientos años. Veinte generaciones han nacido y han muerto delante de ti. Tu familia, tus amigos, tus vecinos, todos. Y ya nadie en el mundo, absolutamente nadie, recuerda tu nombre."),
    (28.15, "Un millón de años después, la humanidad ha cambiado por completo, o ha desaparecido."),
    (32.3, "Los continentes chocan y se unen en uno solo, gigantesco."),
    (35.6, "El Sol brilla cada vez más, ¡y los océanos se evaporan!"),
    (39.3, "Cinco mil millones de años: el Sol se hincha hasta convertirse en una gigante roja, más de cien veces más grande. ¡Y después se apaga!"),
    (46.0, "Todo lo que has conocido, cada persona, cada lugar, ha desaparecido."),
    (49.7, "Y al final, solo quedas tú, flotando en la oscuridad. Solo. Para siempre."),
    (54.0, "¿Aceptarías ser inmortal?"),
]


class Story:
    def __init__(self, spec: StorySpec | None = None):
        self.spec = spec or StorySpec()
        self.duration = SCENES[-1][2]
        self.frames = int(round(self.duration * self.spec.fps))
        self.shots = [{"type": n, "start": a, "end": b} for n, a, b in SCENES]

    # compatibilidad con el resto del sistema
    def shot_at(self, t):
        for s in self.shots:
            if s["start"] <= t < s["end"]:
                return s
        return self.shots[-1]

    def scene(self, t):
        return self.shot_at(t)["type"]

    def local(self, t):
        s = self.shot_at(t)
        return (t - s["start"]) / (s["end"] - s["start"]), s

    def narration(self):
        return self.spec.narration or DEFAULT_NARRATION

    def expression(self, t):
        """Expresión del personaje 2D en cada momento: (cara, brazos)."""
        name = self.scene(t)
        if name == "rayo":
            if t < LIGHTNING_T + 0.15:
                return "normal", "abajo"
            return ("sorprendido", "abajo") if t < 5.0 else ("asombrado", "abiertos")
        if name == "siglo":
            return "asombrado", "abajo"
        if name == "ruinas":
            return "triste", "abajo"
        if name == "sol":
            u, _ = self.local(t)
            return ("asombrado", "abajo") if u < 0.66 else ("sorprendido", "abajo")
        if name == "espacio":
            return ("normal", "abajo") if t > self.duration - 3.0 else ("triste", "abajo")
        return "normal", "abajo"

    def era(self, t):
        for a, b, txt in ERAS:
            if a <= t < b:
                return txt, (t - a) / (b - a)
        return None, 0

    # Posición del personaje (siempre el mismo modelo)
    def hero(self, t):
        name = self.scene(t)
        u, _ = self.local(t)
        if name in ("rayo", "siglo", "ruinas"):
            return (CITY[0], CITY[1], 0.0), 0.0, 0.0
        if name == "tierra":
            # de pie en una colina al principio; luego la cámara se va al espacio
            return (EARTH[0], EARTH[1] - EARTH_R * 3, EARTH[2] + EARTH_R * 0.0 - 1000), 0.0, 0.0
        if name == "sol":
            return (SCORCHED[0], SCORCHED[1], 0.0), 0.0, 0.0
        # espacio: flota y gira despacio
        return (SPACE[0], SPACE[1], 0.0), u * 0.9, 0.25 + u * 0.4

    def camera(self, t):
        """(posición, punto al que mira, focal mm)"""
        name = self.scene(t)
        u, s = self.local(t)
        hx, hy, hz = CITY
        if name == "rayo":
            # Gancho: empuje rápido hacia el personaje, luego órbita lenta
            if t < 2.2:
                k = smooth(0, 2.2, t)
                pos = lerp3((hx + 2, hy - 22, 6.5), (hx + 1.2, hy - 5.0, 1.7), k)
                return pos, (hx, hy, 1.4 + 0.6 * (1 - k)), lerp(24, 35, k)
            a = -1.4 + (t - 2.2) * 0.12
            return (hx + math.cos(a) * 5.2, hy + math.sin(a) * 5.2, 1.5), (hx, hy, 1.45), 35
        if name == "siglo":
            # plano general que sube despacio: la ciudad crece a su alrededor (time-lapse)
            pos = lerp3((hx - 9, hy - 16, 2.0), (hx - 14, hy - 26, 9.0), smooth(0, 1, u))
            return pos, (hx, hy, 2.2 + 6 * u), 28
        if name == "ruinas":
            a = 0.6 + u * 1.1
            r = lerp(7.0, 11.0, u)
            return (hx + math.cos(a) * r, hy + math.sin(a) * r, lerp(1.3, 3.2, u)), (hx, hy, 1.3), 30
        if name == "tierra":
            ex, ey, ez = EARTH
            # la cámara se aleja de la Tierra y la rodea: los continentes cambian
            a = -1.57 + u * 0.9
            r = lerp(EARTH_R * 3.4, EARTH_R * 4.4, smooth(0, 1, u))
            return (ex + math.cos(a) * r, ey + math.sin(a) * r, ez + EARTH_R * 0.5), (ex, ey, ez), 40
        if name == "sol":
            sx, sy, sz = SCORCHED
            # contrapicado: el personaje de espaldas frente a la gigante roja
            pos = lerp3((sx - 1.2, sy - 6.5, 0.6), (sx - 0.6, sy - 4.2, 0.9), smooth(0, 1, u))
            return pos, (sx, sy + 20, 4.0 + 2 * u), 22
        sx, sy, sz = SPACE
        r = lerp(4.0, 40.0, smooth(0.15, 1.0, u))
        return (sx + r * 0.3, sy - r, sz + r * 0.25), (sx, sy, 0.9), 35

    def timeline(self):
        rows = []
        for f in range(self.frames):
            t = f / self.spec.fps
            rows.append({"f": f, "vt": t, "scene": self.scene(t)})
        return rows


if __name__ == "__main__":
    s = Story()
    print(f"vídeo {s.duration:.1f} s · {s.frames} fotogramas")
    for n, a, b in SCENES:
        print(f"  {n:8s} {a:5.1f}–{b:5.1f}")
