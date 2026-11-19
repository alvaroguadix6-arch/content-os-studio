"""NIVEL OCULTO · Sorteo (versión Instagram: seguir, me gusta y comentar)."""
from sorteo import BPM, MOOD, Sorteo, main  # noqa: F401


class VIDEO(Sorteo):
    NAME = "sorteo_ig"
    PLATFORM = "IG"


if __name__ == "__main__":
    main(VIDEO)
