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
