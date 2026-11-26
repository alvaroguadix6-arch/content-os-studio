# Estado de content-os-studio · cierre de la fase 1 (26-11-2026)

Sin datos privados: estadísticas, votos detallados por usuario y enlaces de descarga están en el repo privado
`instagram-agent` (`docs/CONTINUIDAD.md`).

## Qué funciona
- **Render en lote** desde el móvil (Actions → «Render quiz/conquista»): quiz, episodios de Conquista y paquetes,
  hasta 8 vídeos por ejecución, 4 a la vez, varios lotes en paralelo. Un quiz tarda ~6 min; una historia, ~20.
- **Cada vídeo** sale con MP4 1080×1920, portada, descripción, hashtags, `plataformas.txt` (Instagram, TikTok,
  YouTube Shorts), vista de zona segura y hoja de control. Un trabajo final descarga los artefactos y verifica
  que se abren y su calidad (tabla única).
- **Controles**: zonas seguras con la voz real antes de montar; audio a −14 LUFS y pico real ≤ −1 dBTP; QC de
  formato, silencios, planos congelados y negros; filtro de datos privados en paquetes; pruebas en cada PR.
- **Fase 1**: 24 vídeos producidos y verificados (quiz, retos, Conquista ep. 3, historias, ciencia y misterios).

## Incidencias resueltas en esta fase
| problema | causa | solución permanente |
| --- | --- | --- |
| Render fallaba al instalar | Python 3.14 en el runner, `blis` sin paquete | Python 3.12 y versiones fijadas |
| Canarias tapada | recuadro en y=1450 | maquetación nueva + prueba |
| Picos de audio > −1 dBTP | picos entre muestras del AAC | limitador sobremuestreado + medida y recodificación |
| Votos perdidos en Conquista | nombres bilingües («Alacant/Alicante») | `datos.py` acepta ambos + prueba |
| Faisanes paró en zonas seguras | panel «archivo» hasta x=890 | escena corregida + prueba de todas las escenas en cada PR |

## Próximos pasos
- **Conquista diaria (prioritario)**: cada día, render del episodio siguiente antes de las 16:00 para publicarlo a
  las 18:30 (ep. 4 el 27-11, ep. 5 el 28-11…), también si no hay votos nuevos.
Ver `docs/CONTINUIDAD.md` en el repo privado: reserva para la semana del 03-12, escenas propias para historias,
encadenar repos y publicación con aprobación (solo con autorización del usuario).
