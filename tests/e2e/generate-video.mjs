// Prueba de extremo a extremo: usa el panel como lo haría una persona en un iPhone
// (pantalla de móvil, toques) y genera un vídeo MP4 completo.
//
// Uso:
//   npm run build && npx vite preview --port 4173 &
//   npm run e2e
// Variables opcionales:
//   BASE_URL     (por defecto http://localhost:4173/)
//   MODELS_DIR   carpeta con es_ES-davefx-medium.onnx(.json) para no descargar de Hugging Face
//   PW_PATH      ruta del paquete playwright si no está instalado en el proyecto
//   TOPIC        id del tema (por defecto senal-wow)
//   IMAGES       "wikimedia" para probar imágenes libres (necesita red)

import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { getTopic } from '../../src/lib/content.js';

const require = createRequire(import.meta.url);
const { chromium, devices } = require(process.env.PW_PATH || 'playwright');

const BASE = process.env.BASE_URL || 'http://localhost:4173/';
const OUT = path.resolve('test-output');
const MODELS = process.env.MODELS_DIR;
const TOPIC = process.env.TOPIC || 'senal-wow';
fs.mkdirSync(OUT, { recursive: true });

const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1' } : undefined;
const browser = await chromium.launch({ proxy });
const { defaultBrowserType, ...iphone } = devices['iPhone 13'];
const context = await browser.newContext({ ...iphone, ignoreHTTPSErrors: !!proxy });
const page = await context.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('console', (m) => m.type() === 'error' && !/404|Failed to load resource|commons.wikimedia.org/.test(m.text()) && errors.push(m.text()));

if (MODELS) {
  await page.route('https://huggingface.co/**', (route) => {
    const f = path.join(MODELS, route.request().url().split('/').pop());
    if (!fs.existsSync(f)) return route.fulfill({ status: 404, body: 'no' });
    return route.fulfill({ body: fs.readFileSync(f), headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/octet-stream' } });
  });
}

const shot = (name) => page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false });
const step = (m) => console.log(`▶ ${m}`);

step('Abrir panel');
await page.goto(BASE);
await page.getByText('Crea tu primer vídeo').waitFor();
await shot('01-panel');

step('Generar guion');
await page.getByRole('link', { name: /Guiones/ }).click();
const topic = getTopic(TOPIC);
const selects = page.locator('select');
const category = topic?.category || 'misterios';
await selects.nth(0).selectOption(category);
await page.getByText('30 s').click();
await selects.nth(1).selectOption(TOPIC);
await page.getByRole('button', { name: /Generar guion/ }).click();
await page.getByText('Verifica antes de publicar').waitFor();
await shot('02-guion');

step('Guardar y producir');
await page.getByRole('button', { name: /Guardar y producir/ }).click();
await page.getByRole('button', { name: /Generar vídeo MP4/ }).waitFor();

if (process.env.IMAGES === 'wikimedia') {
  step('Buscar imágenes libres en Wikimedia');
  await page.getByRole('button', { name: /Libres/ }).click();
  await page.getByRole('button', { name: /Buscar imágenes libres/ }).click();
  const ok = page.getByText('Imágenes asignadas');
  const bad = page.locator('.notice.bad');
  await Promise.race([ok.waitFor({ timeout: 60000 }), bad.waitFor({ timeout: 60000 })]);
  if (await bad.isVisible()) {
    console.warn('  ⚠ Wikimedia no disponible:', await bad.textContent(), '→ se usan fondos animados');
    await page.getByRole('button', { name: /Animadas/ }).click();
  }
}
if (process.env.PHOTO) {
  step('Subir una foto propia para la escena 1');
  await page.getByRole('button', { name: /Mis fotos/ }).click();
  await page.locator('input[type=file][accept="image/*"]').first().setInputFiles(process.env.PHOTO);
  await page.waitForTimeout(1500);
}
await shot('03-produccion');

step('Generar vídeo (voz + música + subtítulos + MP4)');
const t0 = Date.now();
await page.getByRole('button', { name: /Generar vídeo MP4/ }).click();
await page.getByText('Vídeo producido').waitFor({ timeout: 300000 });
console.log(`  vídeo generado en ${Math.round((Date.now() - t0) / 1000)} s`);
await page.waitForTimeout(800);
await shot('04-video-listo');

step('Extraer el MP4 guardado en el teléfono');
const { b64, meta } = await page.evaluate(async () => {
  const open = () =>
    new Promise((res, rej) => {
      const r = indexedDB.open('keyval-store');
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
  const db = await open();
  const read = (k) =>
    new Promise((res) => {
      const tx = db.transaction('keyval').objectStore('keyval').get(k);
      tx.onsuccess = () => res(tx.result);
    });
  const projects = await read('projects');
  const p = projects.find((x) => x.video && !x.demo);
  const blob = await read('blob:' + p.video.key);
  const buf = new Uint8Array(await blob.arrayBuffer());
  let s = '';
  for (let i = 0; i < buf.length; i += 32768) s += String.fromCharCode(...buf.subarray(i, i + 32768));
  return { b64: btoa(s), meta: p.video };
});
const ext = meta.ext || 'mp4';
fs.writeFileSync(path.join(OUT, `primer-video.${ext}`), Buffer.from(b64, 'base64'));
console.log('  ', meta);

step('Aprobar');
await page.getByRole('button', { name: /Aprobar/ }).first().click();
await page.getByRole('button', { name: /Preparar publicación/ }).click();
await page.getByText('Publicación automática desactivada').waitFor();
await shot('05-publicar');

step('Calendario');
await page.getByRole('link', { name: /Calendario/ }).click();
await shot('06-calendario');

step('Panel');
await page.getByRole('link', { name: /Panel/ }).click();
await shot('07-panel-final');

if (process.env.TREND_URL) {
  step('Tendencias');
  await page.getByRole('link', { name: /Tendencias/ }).click();
  await page.locator('input[type=url]').fill(process.env.TREND_URL);
  await page.getByRole('button', { name: /Analizar/ }).click();
  await page.getByText('Ideas originales para ti').waitFor({ timeout: 30000 });
  await shot('08-tendencias');
}

await browser.close();
if (errors.length) {
  console.error('Errores en la página:', errors);
  process.exit(1);
}
console.log('✅ Prueba completada. Resultados en test-output/');
