# Content-OS

Centro de producción de vídeos cortos (TikTok, Instagram Reels y YouTube Shorts), en español,
pensado para manejarse **desde el iPhone**. Todo el trabajo pesado (voz, vídeo, subtítulos, música)
se hace **dentro del propio teléfono**: no hace falta servidor, ni cuentas, ni pagar nada.

Dirección del panel una vez publicado: **https://TU-USUARIO.github.io/NOMBRE-DEL-REPOSITORIO/**

---

## 1. Cómo ponerlo en marcha (una sola vez)

1. Este repositorio debe ser **público**: así GitHub Pages y las máquinas estándar de GitHub Actions
   son gratuitas (documentación oficial: *«Standard GitHub-hosted runners in public repositories»*
   no tienen coste). No contiene claves ni datos personales: las claves opcionales se guardan solo en tu teléfono.
2. **Activar GitHub Pages (gratis):** *Settings* → *Pages* → *Build and deployment* → *Source* = **GitHub Actions**.
3. Pestaña *Actions* → «Publicar panel en GitHub Pages» → *Run workflow* (o espera al siguiente cambio en `main`).
4. En el iPhone, abre **Safari** en `https://TU-USUARIO.github.io/NOMBRE-DEL-REPOSITORIO/`.
5. Pulsa *Compartir* → **Añadir a pantalla de inicio**.

> Seguro anti-cargos: si algún día el repositorio pasa a ser privado, las automatizaciones no arrancan
> ninguna máquina (se omiten y no consumen minutos).

## 2. Cómo crear un vídeo desde el iPhone

1. **Guiones** → elige categoría, tema y duración (30/45/60 s) → *Generar guion*. Puedes editar cada escena.
   Cada tema incluye un enlace para **verificar los datos** antes de publicar.
2. *Guardar y producir* → en **Producir** elige:
   - Imágenes: *Animadas* (fondos creados por la app), *Libres* (Wikimedia Commons, con créditos automáticos) o *Mis fotos*.
   - Voz: *Voz IA gratis* (Piper, española), *Mi voz* (grabas con el micrófono) o *Sin voz*.
   - Resolución 720p (rápido) o 1080p.
3. *Generar vídeo MP4*. La primera vez descarga la voz (≈63 MB, mejor con wifi); después queda guardada.
   Mantén la app abierta y la pantalla encendida hasta que termine.
4. Revisa el vídeo → **Aprobar** (o *Modificar* el guion y volver a generar).
5. **Publicar** → copia el título/descripción/hashtags de cada red y pulsa *Compartir vídeo* para mandarlo
   a TikTok, Instagram, YouTube o guardarlo en Fotos.
6. **Calendario**: asigna hasta 7 vídeos a los próximos 7 días y cambia su estado
   (pendiente → produciendo → listo → aprobado).
7. **Tendencias**: pega enlaces de vídeos para ver sus datos públicos reales, analizar el gancho y recibir ideas originales.

## 3. Qué es real, qué es demostración y qué necesita configuración

| Función | Estado | Coste |
|---|---|---|
| Guiones desde la biblioteca (24 temas con fuente verificable) | ✅ Real | Gratis |
| Guion con tu propio texto | ✅ Real | Gratis |
| Voz española neuronal (Piper, en el teléfono) | ✅ Real | Gratis |
| Grabar tu propia voz | ✅ Real | Gratis |
| Vídeo 9:16 MP4 con subtítulos sincronizados, animaciones, música y efectos propios | ✅ Real | Gratis |
| Imágenes libres de Wikimedia Commons con créditos | ✅ Real | Gratis |
| Calendario de 7 días con estados | ✅ Real | Gratis |
| Textos y hashtags para TikTok, Instagram y YouTube | ✅ Real | Gratis |
| Tendencias: título, autor y miniatura (YouTube y TikTok, vía oEmbed) | ✅ Real | Gratis |
| Tendencias: visualizaciones/likes de YouTube | ⚙️ Necesita tu clave gratuita de YouTube Data API | Gratis |
| Tendencias: estadísticas de TikTok e Instagram | ⛔ No disponible sin APIs oficiales; **no se inventan** | — |
| Guiones sobre cualquier tema con IA (Claude) | ⚙️ Opcional, necesita tu clave de Anthropic | **De pago** (céntimos por guion) |
| Publicación automática en redes | ⛔ Desactivada. Requiere apps aprobadas por TikTok/Meta/Google y tu aprobación | — |
| Proyectos con la etiqueta **DEMO** | 🧪 Ejemplos de demostración (se borran en *Ajustes*) | — |

La música y los efectos los **sintetiza la propia app**, así que no tienen derechos de autor de terceros.

## 4. Limitaciones conocidas

- Los datos (proyectos y vídeos) se guardan **en el navegador del teléfono**. Si borras los datos de Safari,
  se pierden. Usa *Ajustes → Exportar copia* para guardar los guiones, y guarda los vídeos en Fotos.
- En iPhone, si el navegador no permite la exportación rápida (WebCodecs con audio AAC), el vídeo se graba
  **en tiempo real** (un vídeo de 45 s tarda unos 45 s). No bloquees la pantalla durante la producción.
- La voz Piper es buena pero no perfecta (algunas entonaciones). Puedes usar *Mi voz* como alternativa.
- Wikimedia Commons puede limitar búsquedas muy seguidas; si falla, espera un minuto o usa fondos animados.
- Publicar automáticamente exige registrar apps de desarrollador en cada red, pasar sus revisiones y tener
  un pequeño servidor seguro para los permisos. Está preparado el lugar en *Publicar*, pero **no se activa
  sin tu aprobación**.

## 5. Simulaciones 3D (Blender) — NUEVO

Vídeos 3D **reales** (no dibujos 2D): Blender 5.3 con el motor Cycles (trazado de rayos), coches 3D con
licencia CC BY 4.0, circuito, ciudad, gradas, cámaras de cine, cámara lenta, motores sintetizados con
efecto Doppler, narración en español, música propia, HUD de videojuego y subtítulos. Salida MP4 1080×1920.

**Cómo usarlo desde el iPhone (pestaña 🎮 3D):**
1. Una vez: crea un token en GitHub → *Settings* → *Developer settings* → *Personal access tokens* →
   *Fine-grained tokens* → *Generate new token*. Repositorio: solo este repositorio. Permisos:
   **Contents: Read and write** y **Actions: Read-only**. Cópialo en la sección «Conexión con GitHub».
2. Escribe tu idea (p. ej. «Ferrari rojo contra Lamborghini amarillo, gana el rojo»). La app te enseña
   exactamente qué ha entendido (colores, ganador) y qué no puede hacer todavía.
3. Pulsa **Enviar a renderizar**. GitHub reparte el trabajo en hasta 20 servidores. Tarda entre 30 y
   90 minutos según la calidad y la cola.
   Con el repositorio público, las máquinas estándar son gratuitas. Los fotogramas intermedios se borran
   solos al publicar el vídeo para no ocupar el cupo de almacenamiento (500 MB).
4. Cuando termine, el vídeo aparece en la misma pestaña: **Aprobar** y **Descargar MP4**. También queda en
   GitHub → *Releases* con los subtítulos (.srt) y los créditos.

> El panel detecta solo el repositorio a partir de su dirección de GitHub Pages; la rama por defecto es `main`.

**Qué hay disponible hoy:** plantilla «Carrera de superdeportivos». «Simulación en ciudad» y «Retos y
experimentos» aparecen como *próximamente* (no se finge que existan).

**Licencias:** ver `render3d/assets/LICENCIAS.md`. No se usan modelos de marcas: Ferrari y Lamborghini
se sustituyen por superdeportivos genéricos rojo y amarillo. El modelo «Car Concept» exige atribución
(se genera un archivo de créditos con cada vídeo; cópialo en la descripción).

**Renderizar en tu propio ordenador (opcional, más rápido con tarjeta gráfica):**
```bash
pip install bpy==5.3.0 piper-tts numpy scipy pillow     # Python 3.13; o usa Blender instalado
python render3d/pipeline.py all --out trabajo --spec render3d/jobs/carrera-rojo-vs-amarillo.json
```
Sin tarjeta gráfica, un ordenador de 4 núcleos tarda ~30 s por fotograma (≈12 h por vídeo). Con una
tarjeta gráfica NVIDIA/AMD/Apple Silicon y Blender instalado, es mucho más rápido.

---

## Parte técnica

- **Frontend**: React 18 + Vite, aplicación web estática (PWA), navegación por `#/ruta`.
- **Voz**: [Piper](https://github.com/rhasspy/piper) (modelos `es_ES`/`es_MX`, licencia MIT) ejecutado con
  `onnxruntime-web` (WASM) y el fonemizador `piper-wasm`. Los modelos se descargan de Hugging Face y se guardan
  con la Cache API.
- **Vídeo**: `canvas` 720×1280 o 1080×1920 a 30 fps. Exportación con WebCodecs + `mp4-muxer` (H.264 + AAC,
  o H.264 + Opus si el navegador no tiene AAC) y, como alternativa, `MediaRecorder` en tiempo real.
- **Audio**: mezcla con `OfflineAudioContext` (voz + música procedural + efectos + compresor + ducking).
- **Subtítulos**: la voz se sintetiza frase a frase (tiempos exactos por frase) y dentro de cada frase el tiempo
  se reparte por longitud de palabra y pausas de puntuación (`src/lib/subtitles.js`).
- **Datos**: IndexedDB (`idb-keyval`), sin servidor.

```
src/
  engine/   tts.js (voz) · audio.js (mezcla) · scenes.js (fotogramas) · render.js (MP4) · images.js (Wikimedia)
  lib/      content.js (biblioteca de temas) · scriptgen.js · subtitles.js · publish.js · trends.js · db.js · ai.js
  views/    Panel · Tendencias · Guiones · Producir · Calendario · Publicar · Ajustes · Proyecto
tests/
  unit/     pruebas de lógica (vitest)
  e2e/      prueba completa con navegador simulando un iPhone que genera un MP4 real
```

### Comandos

```bash
npm install          # instala dependencias y copia los WASM a public/vendor
npm run dev          # servidor de desarrollo
npm test             # pruebas unitarias
npm run build        # genera dist/ (lo que se publica en GitHub Pages)
npx vite preview --port 4173 & npm run e2e   # prueba completa (necesita Playwright)
```

Variables de la prueba e2e: `BASE_URL`, `MODELS_DIR` (modelo de voz local), `TOPIC`, `IMAGES=wikimedia`,
`PHOTO=/ruta/foto.jpg`, `TREND_URL`, `PW_PATH`.
