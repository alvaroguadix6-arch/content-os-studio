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
La narración se genera con `gravedad/voz.py` (preguntas con pausa de 5 s para la cuenta atrás):
`python formatos.py guion-quiz <tema> voz/guion.json`. Temas: `python formatos.py temas` (nuevos: gentilicios,
castillos e islas, este último con Canarias y Baleares).

### Desde el móvil, en lote: Actions → «Render quiz/conquista»
Escribe uno o varios temas (`islas,castillos`) y, si quieres, un episodio de Conquista; confirma con `RENDER`.
Máximo 5 vídeos por ejecución y 2 a la vez. Cada artefacto (7 días) trae el MP4, la portada, `descripcion.txt`,
`hashtags.txt`, la vista de zona segura y la hoja de control de calidad. Un último trabajo descarga cada
artefacto y comprueba que los archivos se abren (`tools/verificar_descargas.py`).

### Zonas seguras (Reels, TikTok y Shorts)
`zona_segura.py` define la zona común (arriba 250 px, abajo 480 px, iconos a la derecha desde x=870 entre
y=900 e y=1600, 110 px de margen lateral). `formatos.py zonas quiz <tema> voz/` recorre el vídeo y falla si algún
texto o rótulo queda tapado más de 0,6 s; el workflow lo comprueba antes de montar. El recuadro de Canarias está
abajo a la izquierda, dentro de la zona. Pruebas: `python3 render3d/tests/test_formatos.py`.

### Quiz de otros países
Añade `"mapa": "<pais>"` y `"pais": "<NOMBRE>"` al JSON: usa `quizzes/mapas/<pais>.geojson` (regiones de Natural Earth,
dominio público), ajusta el país a la pantalla y hace zoom al revelar si la región es pequeña. `prov` puede ser una lista
(p. ej. Lima = ["Lima", "Lima Province"]). Mapas: Francia, Perú, Inglaterra, Colombia, Venezuela, Argentina, Chile,
Alemania, Italia y Portugal (`fiestas_<pais>.json`).

## Paquetes de instagram-agent (`nivel_oculto.py`)

Adaptador genérico: convierte cualquier paquete exportado desde el repositorio privado (`paquetes/AAAA-Www/<id>.json`)
en un vídeo con esta misma plantilla. Una escena por frase; el tipo de escena sale del `visual_brief`
(`mapa` → globo real, `simulacion`, `animacion` → ciudad, `archivo`, `grafico` → cifra y barras, `texto`) y los
rótulos de `on_screen_text` aparecen como tarjeta roja bajo los subtítulos. Los números se pasan a letra para la voz.

    python nivel_oculto.py guion ../../paquetes/2026-W49/x.json voz/guion.json
    python ../gravedad/voz.py voz/ --guion voz/guion.json --motor kokoro --voz em_alex
    PAQUETE=../../paquetes/2026-W49/x.json python nivel_oculto.py plan voz/
    PAQUETE=../../paquetes/2026-W49/x.json python nivel_oculto.py render voz/ frames/
    PAQUETE=../../paquetes/2026-W49/x.json python montaje.py nivel_oculto --narracion voz/ --frames frames/ --out x.mp4

En GitHub: **Actions → Render paquete → Run workflow** (solo manual, escribe `RENDER`). Antes de renderizar,
`tools/check_paquetes.py` valida que el paquete no contiene datos privados. Para piezas especiales se puede seguir
escribiendo un módulo propio (como `caso_cooper.py`): el adaptador es la base automática.
Pruebas: `python3 render3d/tests/test_nivel_oculto.py`.
