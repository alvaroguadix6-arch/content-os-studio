// Voz española GRATUITA que funciona dentro del navegador (también en iPhone).
// Usa Piper (modelos neuronales de código abierto, licencia MIT) ejecutado con ONNX Runtime.
// La primera vez descarga el modelo de voz (~63 MB) desde Hugging Face y lo guarda en el
// teléfono; después funciona sin volver a descargarlo.

import * as ort from 'onnxruntime-web/wasm';

export const VOICES = {
  'es_ES-davefx-medium': {
    label: 'David · España · masculina',
    path: 'es/es_ES/davefx/medium/es_ES-davefx-medium.onnx',
    sizeMB: 63,
  },
  'es_ES-sharvard-medium:F': {
    label: 'Sharvard · España · femenina',
    path: 'es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx',
    speaker: 1,
    sizeMB: 77,
  },
  'es_ES-sharvard-medium:M': {
    label: 'Sharvard · España · masculina 2',
    path: 'es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx',
    speaker: 0,
    sizeMB: 77,
  },
  'es_MX-ald-medium': {
    label: 'Ald · México · masculina',
    path: 'es/es_MX/ald/medium/es_MX-ald-medium.onnx',
    sizeMB: 63,
  },
};
export const DEFAULT_VOICE = 'es_ES-davefx-medium';
export const VOICE_HOST = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/';
const CACHE_NAME = 'content-os-voces-v1';

function assetUrl(rel) {
  return new URL(rel, document.baseURI).href;
}

async function fetchWithProgress(url, onProgress) {
  let cache = null;
  try {
    cache = await caches.open(CACHE_NAME);
    const hit = await cache.match(url);
    if (hit) {
      onProgress?.(1, true);
      return await hit.arrayBuffer();
    }
  } catch {
    cache = null; // Cache API no disponible (p. ej. modo privado)
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`No se pudo descargar ${url.split('/').pop()} (HTTP ${res.status})`);
  const total = Number(res.headers.get('Content-Length')) || 0;
  const reader = res.body?.getReader();
  let buf;
  if (reader) {
    const chunks = [];
    let loaded = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      loaded += value.length;
      if (total) onProgress?.(loaded / total, false);
    }
    buf = new Uint8Array(loaded);
    let o = 0;
    for (const c of chunks) {
      buf.set(c, o);
      o += c.length;
    }
    buf = buf.buffer;
  } else {
    buf = await res.arrayBuffer();
  }
  onProgress?.(1, false);
  if (cache) {
    try {
      await cache.put(url, new Response(buf.slice(0), { headers: { 'Content-Type': 'application/octet-stream' } }));
    } catch {
      /* sin espacio: seguimos sin caché */
    }
  }
  return buf;
}

export async function isVoiceDownloaded(voiceId) {
  try {
    const v = VOICES[voiceId];
    const cache = await caches.open(CACHE_NAME);
    return !!(await cache.match(VOICE_HOST + v.path));
  } catch {
    return false;
  }
}

export async function deleteVoices() {
  try {
    await caches.delete(CACHE_NAME);
  } catch {
    /* nada */
  }
}

let phonemizerScript = null;
function loadPhonemizerScript() {
  if (window.createPiperPhonemize) return Promise.resolve();
  if (!phonemizerScript) {
    phonemizerScript = new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = assetUrl('vendor/piper/piper_phonemize.js');
      s.onload = () => resolve();
      s.onerror = () => reject(new Error('No se pudo cargar el fonemizador de Piper'));
      document.head.appendChild(s);
    });
  }
  return phonemizerScript;
}

// Convierte texto en identificadores de fonemas usando espeak-ng (WASM).
async function phonemize(text, espeakVoice) {
  await loadPhonemizerScript();
  return new Promise((resolve, reject) => {
    let done = false;
    window
      .createPiperPhonemize({
        print: (line) => {
          if (done) return;
          try {
            done = true;
            resolve(JSON.parse(line).phoneme_ids);
          } catch (e) {
            reject(e);
          }
        },
        printErr: (l) => console.warn('[piper]', l),
        locateFile: (f) => assetUrl('vendor/piper/' + f.split('/').pop()),
      })
      .then((mod) => {
        mod.callMain(['-l', espeakVoice, '--input', JSON.stringify([{ text }]), '--espeak_data', '/espeak-ng-data']);
        if (!done) setTimeout(() => !done && reject(new Error('El fonemizador no devolvió resultado')), 50);
      })
      .catch(reject);
  });
}

export class PiperVoice {
  constructor(voiceId = DEFAULT_VOICE) {
    this.voiceId = VOICES[voiceId] ? voiceId : DEFAULT_VOICE;
    this.session = null;
    this.config = null;
  }

  async load(onProgress) {
    if (this.session) return;
    const v = VOICES[this.voiceId];
    ort.env.wasm.wasmPaths = assetUrl('vendor/ort/');
    ort.env.wasm.numThreads = 1; // GitHub Pages no permite hilos compartidos
    const cfgBuf = await fetchWithProgress(VOICE_HOST + v.path + '.json');
    this.config = JSON.parse(new TextDecoder().decode(cfgBuf));
    const model = await fetchWithProgress(VOICE_HOST + v.path, (p, cached) => onProgress?.(p, cached));
    this.session = await ort.InferenceSession.create(new Uint8Array(model), { executionProviders: ['wasm'] });
  }

  /**
   * @param {string} text
   * @param {{speed?: number}} opts  speed 1 = normal, 1.15 = un poco más rápida
   * @returns {Promise<{samples: Float32Array, sampleRate: number}>}
   */
  async synthesize(text, { speed = 1.1 } = {}) {
    if (!this.session) await this.load();
    const cfg = this.config;
    const ids = await phonemize(text, cfg.espeak.voice);
    const inf = cfg.inference;
    const feeds = {
      input: new ort.Tensor('int64', BigInt64Array.from(ids.map(BigInt)), [1, ids.length]),
      input_lengths: new ort.Tensor('int64', BigInt64Array.from([BigInt(ids.length)]), [1]),
      scales: new ort.Tensor('float32', Float32Array.from([inf.noise_scale, inf.length_scale / speed, inf.noise_w]), [3]),
    };
    if (cfg.num_speakers > 1) {
      const sid = VOICES[this.voiceId].speaker ?? 0;
      feeds.sid = new ort.Tensor('int64', BigInt64Array.from([BigInt(sid)]), [1]);
    }
    const out = await this.session.run(feeds);
    const samples = new Float32Array(out.output.data);
    return { samples: trimSilence(samples, cfg.audio.sample_rate), sampleRate: cfg.audio.sample_rate };
  }
}

// Recorta silencios largos al principio y al final (deja ~60 ms).
export function trimSilence(samples, sampleRate, threshold = 0.01) {
  let a = 0;
  let b = samples.length - 1;
  while (a < b && Math.abs(samples[a]) < threshold) a++;
  while (b > a && Math.abs(samples[b]) < threshold) b--;
  const pad = Math.floor(sampleRate * 0.06);
  return samples.slice(Math.max(0, a - pad), Math.min(samples.length, b + pad));
}
