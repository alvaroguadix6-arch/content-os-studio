// Copia los ficheros WASM necesarios (motor ONNX y fonemizador de Piper) a public/vendor
// para que la app funcione sin depender de CDNs externos.
import { cpSync, mkdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();
const out = join(root, 'public', 'vendor');
const jobs = [
  ['node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.wasm', 'ort/ort-wasm-simd-threaded.wasm'],
  ['node_modules/onnxruntime-web/dist/ort-wasm-simd-threaded.mjs', 'ort/ort-wasm-simd-threaded.mjs'],
  ['node_modules/@diffusionstudio/piper-wasm/build/piper_phonemize.js', 'piper/piper_phonemize.js'],
  ['node_modules/@diffusionstudio/piper-wasm/build/piper_phonemize.wasm', 'piper/piper_phonemize.wasm'],
  ['node_modules/@diffusionstudio/piper-wasm/build/piper_phonemize.data', 'piper/piper_phonemize.data'],
];
for (const [from, to] of jobs) {
  const src = join(root, from);
  if (!existsSync(src)) { console.warn('[copy-vendor] falta', from); continue; }
  const dest = join(out, to);
  mkdirSync(join(dest, '..'), { recursive: true });
  cpSync(src, dest);
}
console.log('[copy-vendor] ficheros copiados a public/vendor');
