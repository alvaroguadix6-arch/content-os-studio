# Simulaciones (mismo estilo que el vídeo de la gravedad)

Plantilla común en `motor.py` (ilustración plana a doble resolución, cámara siempre en movimiento,
texto palabra a palabra con palabras clave en amarillo, indicador inferior, destellos en los cortes,
globo con los continentes reales) y montaje común en `montaje.py` (voz Kokoro em_alex, música
ambiental y efectos generados por código, MP4 comprimido ~10 MB).

| Vídeo | Guion | Animación |
|---|---|---|
| Tierra sin luz solar 5 años | guiones/sol.json | sol.py |
| Mares secos | guiones/mares.json | mares.py |
| España isla (costas reales) | guiones/espana.json | espana.py |
| 10 datos del espacio | guiones/espacio.json | espacio.py |
| 10 datos de GTA 6 (solo confirmados, 17-11-2026) | guiones/gta6.json | gta6.py |

    python ../gravedad/voz.py voz/ --guion guiones/sol.json --speed 1.12   # narración
    python sol.py plan voz/                                                 # comprobar sincronía escena/frase
    python sol.py render voz/ frames/                                       # fotogramas
    python montaje.py sol --narracion voz/ --frames frames/ --out sol.mp4   # MP4 final

Mapas: máscara de tierra/mar de `global-land-mask` (datos GLOBE de NOAA).

## Quiz del mapa de España (`quiz.py`)

Cinco preguntas, cuenta atrás de 5 s y la provincia se ilumina con la respuesta (voz de Alex, música y efectos).
Contenido en `quizzes/<nombre>.json` (`q`, `prov` tal cual aparece en `provincias.geojson`, `punto` [lon, lat], `respuesta`, `detalle`, `voz_q`, `voz_a`).

```bash
QUIZ=monumentos python quiz.py frames/ narracion/        # fotogramas
QUIZ=monumentos python montaje.py quiz --narracion narracion/ --frames frames/ --out quiz.mp4
```
La narración se genera con `gravedad/voz.py` (preguntas con pausa de 5 s para la cuenta atrás).
Listos: monumentos, comida, extremos, naturaleza, fiestas.

### Quiz de otros países
Añade `"mapa": "<pais>"` y `"pais": "<NOMBRE>"` al JSON: usa `quizzes/mapas/<pais>.geojson` (regiones de Natural Earth,
dominio público), ajusta el país a la pantalla y hace zoom al revelar si la región es pequeña. `prov` puede ser una lista
(p. ej. Lima = ["Lima", "Lima Province"]). Mapas: Francia, Perú, Inglaterra, Colombia, Venezuela, Argentina, Chile,
Alemania, Italia y Portugal (`fiestas_<pais>.json`).
