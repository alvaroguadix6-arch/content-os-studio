# NIVEL OCULTO · Física («satisfying»)

Formato independiente de los vídeos de curiosidades: fondo negro, figuras de colores, colisiones reales,
sonido sincronizado con los choques, música suave y contador. Sin narración. 1080×1920, 60 fps.

- `sim.py`: motor de física 2D (NumPy + SciPy) + dibujo (Pillow) + audio sintetizado + MP4 (ffmpeg).
- `reglas/*.json`: un vídeo por archivo. Al subir uno nuevo, GitHub Actions lo renderiza gratis
  (`.github/workflows/fisica.yml`) y deja el MP4 como artefacto.
- `plantillas/*.json`: ejemplos para nuevas reglas (velocidad, sin gravedad, obstáculos y caja que gira).

Reglas: `figuras_por_escape`, `figuras_iniciales`, `gravedad`, `rebote`, `velocidad_inicial`,
`acelerar_por_escape`, `velocidad_max`, `abertura`, `lado`, `radio`, `rotacion`, `obstaculos` ([[x, y, r]]),
`max_figuras`, `duracion`, `fps`, `subpasos`, `semilla`, `titulo`, `etiqueta`, `marca`.

Control de calidad: `python sim.py reglas/x.json --stats` simula sin dibujar y muestra el contador y las
«fugas» (figuras que salieran por una pared en vez de por la abertura; debe ser siempre 0).

## Arena circular (`arena.py`) — formatos virales

Si el archivo de reglas lleva `"modo"`, se usa la arena circular:

| modo | qué pasa | ajustes clave |
|---|---|---|
| `batalla` | equipos de colores que se conquistan al chocar; engranaje con brazo giratorio | `equipos`, `iniciales`, `contagio`, `reproducir`, `max_bolas` |
| `crece` | una bola crece con cada rebote hasta llenar el círculo | `crecer`, `gravedad` |
| `anillos` | anillos que giran con un hueco; cada uno que cruza la bola explota | `anillos`, `hueco` (grados) |
| `multiplica` | cada bola se duplica cada N rebotes propios | `rebotes_por_bola`, `max_bolas` |
| `ppt` | piedra, papel o tijera: tres equipos que se convierten | `iniciales`, `contagio` |

Ejemplos listos en `reglas/`. Prueba rápida sin vídeo: `python arena.py reglas/x.json --stats`.
