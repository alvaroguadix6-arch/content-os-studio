// Motor de producción: guion → voz → banda sonora → fotogramas → MP4.
// Método 1 (rápido): WebCodecs + mp4-muxer → MP4 H.264/AAC más rápido que tiempo real.
// Método 2 (compatibilidad): MediaRecorder → graba en tiempo real (en iPhone sale MP4).

import { PiperVoice } from './tts.js';
import { buildSoundtrack, SAMPLE_RATE } from './audio.js';
import { createSceneState, drawFrame } from './scenes.js';
import { buildCues } from '../lib/subtitles.js';
import { estimateSeconds, hashString } from '../lib/scriptgen.js';
import { blobToBitmap } from './images.js';

const FPS = 30;
let sharedAudioCtx = null;

/** Llamar dentro del toque del botón: iOS solo permite audio tras una interacción. */
export function unlockAudio() {
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!sharedAudioCtx) sharedAudioCtx = new AC({ sampleRate: SAMPLE_RATE });
    sharedAudioCtx.resume();
  } catch {
    /* sin audio */
  }
  return sharedAudioCtx;
}

const voiceCache = new Map();
async function getVoice(voiceId, onProgress) {
  if (!voiceCache.has(voiceId)) voiceCache.set(voiceId, new PiperVoice(voiceId));
  const v = voiceCache.get(voiceId);
  await v.load(onProgress);
  return v;
}

export function webCodecsAvailable() {
  return typeof window.VideoEncoder === 'function' && typeof window.AudioEncoder === 'function' && typeof window.VideoFrame === 'function';
}

async function pickVideoConfig(width, height, bitrate) {
  if (typeof window.VideoEncoder !== 'function') return null;
  const codecs = ['avc1.640028', 'avc1.4d0028', 'avc1.42002a', 'avc1.42001f'];
  for (const codec of codecs) {
    const cfg = { codec, width, height, bitrate, framerate: FPS, avc: { format: 'avc' } };
    try {
      const r = await VideoEncoder.isConfigSupported(cfg);
      if (r.supported) return cfg;
    } catch {
      /* siguiente */
    }
  }
  return null;
}

async function pickAudioConfig(codec = 'mp4a.40.2') {
  if (typeof window.AudioEncoder !== 'function') return null;
  const cfg = { codec, sampleRate: codec === 'opus' ? 48000 : SAMPLE_RATE, numberOfChannels: 2, bitrate: 128000 };
  try {
    const r = await AudioEncoder.isConfigSupported(cfg);
    return r.supported ? cfg : null;
  } catch {
    return null;
  }
}

function recorderDoesH264Aac() {
  return ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4;codecs=avc1,mp4a'].some((m) => window.MediaRecorder?.isTypeSupported?.(m));
}

// Cambia la frecuencia de muestreo (necesario para Opus, que trabaja a 48 kHz).
async function resample(buffer, rate) {
  if (buffer.sampleRate === rate) return buffer;
  const ctx = new OfflineAudioContext(buffer.numberOfChannels, Math.ceil(buffer.duration * rate), rate);
  const src = ctx.createBufferSource();
  src.buffer = buffer;
  src.connect(ctx.destination);
  src.start();
  return await ctx.startRendering();
}

const tick = () => new Promise((r) => setTimeout(r, 0));

async function encodeWithWebCodecs({ canvas, ctx, st, data, audio: audioIn, width, height, onProgress, signal, vcfg, acfg }) {
  const { Muxer, ArrayBufferTarget } = await import('mp4-muxer');
  const isOpus = acfg.codec === 'opus';
  const audio = isOpus ? await resample(audioIn, 48000) : audioIn;
  const rate = acfg.sampleRate;
  const muxer = new Muxer({
    target: new ArrayBufferTarget(),
    video: { codec: 'avc', width, height, frameRate: FPS },
    audio: { codec: isOpus ? 'opus' : 'aac', numberOfChannels: 2, sampleRate: rate },
    fastStart: 'in-memory',
    firstTimestampBehavior: 'offset',
  });
  let failure = null;
  const venc = new VideoEncoder({ output: (c, m) => muxer.addVideoChunk(c, m), error: (e) => (failure = e) });
  venc.configure(vcfg);
  const aenc = new AudioEncoder({ output: (c, m) => muxer.addAudioChunk(c, m), error: (e) => (failure = e) });
  aenc.configure(acfg);

  // Audio en bloques de 1024 muestras (planar)
  const L = audio.getChannelData(0);
  const R = audio.numberOfChannels > 1 ? audio.getChannelData(1) : L;
  const block = 4096;
  for (let i = 0; i < audio.length; i += block) {
    const n = Math.min(block, audio.length - i);
    const buf = new Float32Array(n * 2);
    buf.set(L.subarray(i, i + n), 0);
    buf.set(R.subarray(i, i + n), n);
    const ad = new AudioData({
      format: 'f32-planar',
      sampleRate: rate,
      numberOfFrames: n,
      numberOfChannels: 2,
      timestamp: Math.round((i / rate) * 1e6),
      data: buf,
    });
    aenc.encode(ad);
    ad.close();
  }

  const total = Math.ceil(data.duration * FPS);
  for (let i = 0; i < total; i++) {
    if (signal?.aborted) throw new Error('Producción cancelada');
    if (failure) throw failure;
    drawFrame(ctx, st, data, i / FPS);
    const frame = new VideoFrame(canvas, { timestamp: Math.round((i * 1e6) / FPS), duration: Math.round(1e6 / FPS) });
    venc.encode(frame, { keyFrame: i % (FPS * 2) === 0 });
    frame.close();
    while (venc.encodeQueueSize > 6) await new Promise((r) => setTimeout(r, 4));
    if (i % 10 === 0) {
      onProgress?.({ step: 'video', label: `Creando fotogramas (${i}/${total})`, value: i / total });
      await tick();
    }
  }
  await venc.flush();
  await aenc.flush();
  if (failure) throw failure;
  muxer.finalize();
  return {
    blob: new Blob([muxer.target.buffer], { type: 'video/mp4' }),
    mimeType: 'video/mp4',
    method: isOpus ? 'WebCodecs (MP4 H.264 + Opus)' : 'WebCodecs (MP4 H.264 + AAC)',
  };
}

function pickRecorderMime() {
  const opts = ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4;codecs=avc1,mp4a', 'video/mp4', 'video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'];
  return opts.find((m) => window.MediaRecorder?.isTypeSupported?.(m)) || '';
}

async function encodeWithMediaRecorder({ canvas, ctx, st, data, audio, onProgress, signal, bitrate }) {
  if (!window.MediaRecorder || !canvas.captureStream) throw new Error('Este navegador no puede exportar vídeo. Usa Safari actualizado en iPhone o Chrome en ordenador.');
  const ac = unlockAudio();
  if (ac.state !== 'running') await ac.resume().catch(() => {});
  const dest = ac.createMediaStreamDestination();
  const src = ac.createBufferSource();
  src.buffer = audio;
  src.connect(dest);
  const stream = canvas.captureStream(FPS);
  dest.stream.getAudioTracks().forEach((tr) => stream.addTrack(tr));
  const mimeType = pickRecorderMime();
  const rec = new MediaRecorder(stream, { mimeType: mimeType || undefined, videoBitsPerSecond: bitrate, audioBitsPerSecond: 128000 });
  const chunks = [];
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  const stopped = new Promise((r) => (rec.onstop = r));
  drawFrame(ctx, st, data, 0);
  rec.start(500);
  const t0 = ac.currentTime + 0.15;
  src.start(t0);
  await new Promise((resolve, reject) => {
    const loop = () => {
      if (signal?.aborted) {
        rec.stop();
        return reject(new Error('Producción cancelada'));
      }
      const t = Math.max(0, ac.currentTime - t0);
      drawFrame(ctx, st, data, Math.min(t, data.duration - 0.001));
      onProgress?.({ step: 'video', label: `Grabando en tiempo real (${Math.floor(t)}/${Math.ceil(data.duration)} s) — no bloquees la pantalla`, value: t / data.duration });
      if (t >= data.duration + 0.1) return resolve();
      setTimeout(loop, 1000 / FPS);
    };
    loop();
  });
  rec.stop();
  await stopped;
  src.disconnect();
  const type = (mimeType || chunks[0]?.type || 'video/webm').split(';')[0];
  return { blob: new Blob(chunks, { type }), mimeType: type, method: `MediaRecorder (${type})` };
}

/**
 * Produce el vídeo completo.
 * @param {object} project   guion con segments[]
 * @param {object} settings  { voiceId, speed, resolution, music, sfx, handle, voiceMode, method }
 * @param {object} assets    { images: Blob[] (uno por segmento, o null), recording: Blob|null }
 */
export async function renderVideo(project, settings = {}, assets = {}, { onProgress, signal } = {}) {
  const segments = project.segments.filter((s) => s.text.trim());
  if (!segments.length) throw new Error('El guion está vacío.');
  const width = settings.resolution === '1080' ? 1080 : 720;
  const height = Math.round((width * 16) / 9);
  const bitrate = width === 1080 ? 8_000_000 : 4_500_000;
  const voiceMode = settings.voiceMode || 'piper';

  // 1) VOZ
  let voices = segments.map(() => null);
  let durations;
  let timelineOptions;
  if (voiceMode === 'piper') {
    onProgress?.({ step: 'voz', label: 'Preparando la voz española…', value: 0 });
    const voice = await getVoice(settings.voiceId, (p, cached) =>
      onProgress?.({ step: 'voz', label: cached ? 'Voz cargada desde el teléfono' : `Descargando voz (solo la primera vez): ${Math.round(p * 100)} %`, value: p * 0.5 }),
    );
    for (let i = 0; i < segments.length; i++) {
      if (signal?.aborted) throw new Error('Producción cancelada');
      onProgress?.({ step: 'voz', label: `Generando locución (${i + 1}/${segments.length})`, value: 0.5 + (0.5 * i) / segments.length });
      voices[i] = await voice.synthesize(segments[i].text, { speed: settings.speed || 1.1 });
      await tick();
    }
    durations = voices.map((v) => v.samples.length / v.sampleRate);
  } else if (voiceMode === 'grabada' && assets.recording) {
    onProgress?.({ step: 'voz', label: 'Procesando tu grabación…', value: 0.3 });
    const ac = new OfflineAudioContext(1, 1, SAMPLE_RATE);
    const decoded = await ac.decodeAudioData(await assets.recording.arrayBuffer());
    const est = segments.map((s) => estimateSeconds(s.text));
    const sum = est.reduce((a, b) => a + b, 0);
    durations = est.map((e) => (e / sum) * decoded.duration);
    voices[0] = { samples: decoded.getChannelData(0), sampleRate: decoded.sampleRate };
    timelineOptions = { gap: 0 };
  } else {
    durations = segments.map((s) => Math.max(1.5, estimateSeconds(s.text)));
  }

  // 2) BANDA SONORA
  onProgress?.({ step: 'audio', label: 'Mezclando voz, música y efectos…', value: 0 });
  const { buffer, timeline, duration } = await buildSoundtrack({
    segments,
    voices,
    durations,
    theme: project.theme,
    options: { music: settings.music !== false, sfx: settings.sfx !== false },
    timelineOptions,
  });
  const cues = buildCues(timeline);

  // 3) IMÁGENES
  const images = [];
  for (let i = 0; i < segments.length; i++) {
    const b = assets.images?.[i];
    images.push(b ? await blobToBitmap(b).catch(() => null) : null);
  }

  // 4) FOTOGRAMAS + CODIFICACIÓN
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d', { alpha: false });
  const st = createSceneState({ width, height, theme: project.theme, seed: hashString(project.id || project.title) });
  const data = {
    timeline,
    cues,
    duration,
    images,
    title: project.title,
    category: project.category,
    style: settings.subtitleStyle || {},
    handle: settings.handle,
  };

  // Orden de preferencia: 1) WebCodecs H.264+AAC  2) MediaRecorder MP4 H.264+AAC
  // 3) WebCodecs H.264+Opus  4) MediaRecorder con lo que haya.
  let result = null;
  if (settings.method !== 'mediarecorder' && webCodecsAvailable()) {
    const vcfg = await pickVideoConfig(width, height, bitrate);
    let acfg = await pickAudioConfig('mp4a.40.2');
    if (!acfg && !recorderDoesH264Aac()) acfg = await pickAudioConfig('opus');
    if (vcfg && acfg) {
      try {
        result = await encodeWithWebCodecs({ canvas, ctx, st, data, audio: buffer, width, height, onProgress, signal, vcfg, acfg });
      } catch (e) {
        if (signal?.aborted) throw e;
        console.warn('WebCodecs falló, usando MediaRecorder', e);
      }
    }
  }
  if (!result) result = await encodeWithMediaRecorder({ canvas, ctx, st, data, audio: buffer, onProgress, signal, bitrate });

  // 5) MINIATURA
  drawFrame(ctx, st, data, Math.min(1.2, duration / 3));
  const thumb = await new Promise((r) => canvas.toBlob(r, 'image/jpeg', 0.8));

  onProgress?.({ step: 'fin', label: '¡Vídeo listo!', value: 1 });
  return { ...result, thumb, duration, cues, timeline, width, height };
}

/** Dibuja un fotograma de vista previa sin generar voz (tiempos estimados). */
export async function previewFrame(canvas, project, t = 1, images = []) {
  const segments = project.segments.filter((s) => s.text.trim());
  let acc = 0.35;
  const timeline = segments.map((s) => {
    const d = Math.max(1.5, estimateSeconds(s.text));
    const item = { ...s, start: acc, end: acc + d };
    acc += d + 0.22;
    return item;
  });
  const duration = acc + 1;
  const ctx = canvas.getContext('2d');
  const st = createSceneState({ width: canvas.width, height: canvas.height, theme: project.theme, seed: hashString(project.id || project.title) });
  const bitmaps = await Promise.all(segments.map((_, i) => (images[i] ? blobToBitmap(images[i]).catch(() => null) : null)));
  drawFrame(ctx, st, { timeline, cues: buildCues(timeline), duration, images: bitmaps, title: project.title, category: project.category }, Math.min(t, duration - 0.5));
  return duration;
}
