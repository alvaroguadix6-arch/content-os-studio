# CLAUDE.md · content-os-studio (repositorio PÚBLICO de Nivel Oculto)

Producción y render gratuito de vídeos verticales (1080×1920, 30 fps) para @niveloculto_tv con GitHub Actions.
**Responde siempre en español de España.** Estado y continuidad: `docs/ESTADO.md` (público) y, en el repo privado
`instagram-agent`, `docs/CONTINUIDAD.md` (con estadísticas y enlaces de descarga).

## ⭐ Regla prioritaria: Conquista diaria
«Tu pueblo conquista España» tiene un episodio nuevo **todos los días a las 18:30**, sin excepción y con numeración
consecutiva, también sin votos nuevos (el guion lo cubre: «Hoy el mapa no se ha movido…»). El render del episodio
debe estar listo para descargar **antes de las 16:00**; si falla, arreglarlo es lo primero (sin relajar el QC).
Sigue siendo manual (`RENDER`): no se publica nada ni se activa ninguna automatización.
Lo pide el workflow manual «Conquista del día» del repo privado: sube el CSV agregado (o `votos/epNN.pendiente` si no
se pudieron leer los comentarios: el episodio sale igual y no se inventa nada) y `render3d/conquista/pedido.json`;
ese push lanza aquí `conquista-del-dia.yml` (mismo render y controles, con un reintento).

## Reglas
- **Repositorio público**: nunca estadísticas privadas, comentarios, nombres de usuario, credenciales ni tokens.
  Solo entran paquetes saneados desde `instagram-agent` (`paquetes/AAAA-Www/*.json`) y votos agregados de Conquista
  (`render3d/conquista/temporada1/votos/epNN.csv`: pueblo, provincia, votos).
- **No publicar nada** en redes. Los workflows solo generan artefactos descargables (7 días). Sin secretos.
- Todos los renders son **manuales**, solo desde `main` y con `RENDER`. Coste 0 € (runners gratis en repo público).
- **No desactivar ni relajar los controles de calidad** (zonas seguras, audio, QC, verificación de descargas).
- Sin force push. Rama por tarea → PR → squash con `[skip ci]` en el título.
  Si el PR toca `render3d/` o `tools/`, deja al menos un commit **sin** `[skip ci]` para que corra
  «Pruebas del motor de vídeo» antes de fusionar.

## Motores (render3d/)
| archivo | qué hace |
| --- | --- |
| `simula/quiz.py` + `quizzes/*.json` | Quiz del mapa de España (y de otros países). Canarias en recuadro abajo a la izquierda. |
| `conquista/` | «Tu pueblo conquista España»: `contar.py` (votos), `conquista.py` (territorios), `episodio.py` (vídeo), `datos.py` (municipios INE/IGN). |
| `simula/nivel_oculto.py` | Adaptador de paquetes (historias, ciencia, misterios, simulaciones); escenas por tipo y motivos de meteorito. |
| `simula/escenas.py` | **Escenas con datos** (fase 2): mapa real de España, globo girado al lugar, contador, comparación, línea de tiempo, 100 personas, relojes, documento y figuras. Se activan con `visual_brief[].escena`; las producciones nuevas deben usarlas en cada frase. |
| `simula/motor.py` | Base de escenas, subtítulos palabra a palabra y marca. |
| `simula/montaje.py` | Música, efectos y audio final (−14 LUFS dos pasadas, pico real ≤ −1 dBTP garantizado). |
| `simula/zona_segura.py` | Zona segura común Reels/TikTok/Shorts y comprobador automático (`Registro`, `fuera_de_zona`). |
| `simula/formatos.py` | Lote validado, guion de quiz, portada, descripción, hashtags y `plataformas.txt`. |
| `gravedad/voz.py` | Voz Kokoro `em_alex` (gratis). |
| `tools/qc_video.py`, `tools/qc_lote.py`, `tools/verificar_descargas.py`, `tools/check_paquetes.py` | Calidad y seguridad. |

## Workflows
`render-quiz-conquista.yml` (lotes ≤ 8, 4 a la vez; quiz, Conquista y paquetes; también reutilizable) ·
`conquista-del-dia.yml` (lo lanza el pedido del repo privado o a mano con `RENDER`; render + reintento) · `lote-semanal.yml` (lo lanza `render3d/lote/pedido.json` desde «Producción semanal» del repo privado; lotes de ≤ 8 de uno en uno, mismos controles) · `render-paquete.yml` ·
`qc-video.yml` (QC de una ejecución por `run_id`) · `pruebas-render.yml` (en cada PR) · `fisica.yml`, `render-3d.yml`
(motores antiguos) · `deploy.yml` (GitHub Pages) · `test.yml`.

## Pruebas
```bash
python3 render3d/tests/test_formatos.py            # todas (incluye zonas seguras de todas las escenas, ~5 min)
python3 render3d/tests/test_formatos.py rapidas    # rápidas (las que corre cada máquina de render)
python3 render3d/tests/test_nivel_oculto.py
```
Dependencias de render fijadas en `render3d/requirements-paquete.txt` (Python 3.12, solo paquetes precompilados).
