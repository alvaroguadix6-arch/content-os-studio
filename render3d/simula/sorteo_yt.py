"""NIVEL OCULTO · Sorteo (versión YouTube: se participa comentando; suscribirse y «me gusta» son opcionales)."""
from sorteo import BPM, MOOD, Sorteo, main  # noqa: F401


class VIDEO(Sorteo):
    NAME = "sorteo_yt"
    PLATFORM = "YT"


if __name__ == "__main__":
    main(VIDEO)
