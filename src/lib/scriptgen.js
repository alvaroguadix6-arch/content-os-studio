// Generador de guiones SIN coste: combina estructuras de guion virales con los hechos
// documentados de la biblioteca (content.js). No inventa datos: solo reordena y adapta.

import { TOPICS, CTAS, getTopic, CATEGORIES } from './content.js';

// Velocidad media de locución en español con la voz Piper (palabras por segundo).
export const WORDS_PER_SECOND = 2.6;

export function countWords(text) {
  return (text.trim().match(/[\p{L}\p{N}]+(?:[.,'’-][\p{L}\p{N}]+)*/gu) || []).length;
}

export function estimateSeconds(text, wps = WORDS_PER_SECOND) {
  const words = countWords(text);
  const pauses = (text.match(/[.!?…]/g) || []).length * 0.35 + (text.match(/[,;:]/g) || []).length * 0.15;
  return Math.round((words / wps + pauses) * 10) / 10;
}

function pick(arr, rnd) {
  return arr[Math.floor(rnd() * arr.length) % arr.length];
}

// Generador pseudoaleatorio con semilla, para poder reproducir un guion.
export function seededRandom(seed = Date.now()) {
  let s = (typeof seed === 'number' ? seed : hashString(String(seed))) >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function hashString(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/**
 * Genera un guion a partir de un tema de la biblioteca.
 * @param {object} opts
 * @param {string} opts.topicId
 * @param {30|45|60} opts.duration  duración objetivo en segundos
 * @param {number|string} [opts.seed]
 */
export function generateScript({ topicId, duration = 45, seed } = {}) {
  const topic = getTopic(topicId);
  if (!topic) throw new Error(`Tema desconocido: ${topicId}`);
  const rnd = seededRandom(seed ?? `${topicId}-${duration}-${Date.now()}`);
  const target = Math.max(25, Math.min(65, duration));

  const hook = pick(topic.hooks, rnd);
  const cta = pick(CTAS, rnd);
  const segments = [{ kind: 'gancho', text: hook }];
  segments.push({ kind: 'contexto', text: topic.context });

  // Calculamos cuánto ocupan las partes fijas para decidir cuántos "beats" caben.
  const fixedEnd = [
    { kind: 'giro', text: topic.twist },
    { kind: 'cierre', text: `${topic.question} ${cta}` },
  ];
  let used = [...segments, ...fixedEnd].reduce((a, s) => a + estimateSeconds(s.text), 0);
  const beats = [];
  for (const beat of topic.beats) {
    const secs = estimateSeconds(beat);
    if (used + secs > target + 3 && beats.length >= 1) break;
    beats.push({ kind: 'desarrollo', text: beat });
    used += secs;
  }
  // Para 30 s recortamos la pregunta final si nos pasamos mucho.
  if (used > target + 6) {
    fixedEnd[1] = { kind: 'cierre', text: cta };
  }
  const all = [...segments, ...beats, ...fixedEnd].map((s, i) => ({ ...s, id: `s${i + 1}` }));
  const text = all.map((s) => s.text).join(' ');
  return {
    topicId: topic.id,
    category: topic.category,
    title: topic.title,
    theme: topic.theme,
    segments: all,
    source: topic.source,
    keywords: topic.keywords,
    hashtags: topic.hashtags,
    targetDuration: duration,
    estimatedSeconds: Math.round(all.reduce((a, s) => a + estimateSeconds(s.text), 0) + all.length * 0.25),
    wordCount: countWords(text),
    generator: 'plantilla',
  };
}

/** Convierte un texto libre (escrito por ti) en segmentos, uno por frase. */
export function scriptFromText(rawText, { title = 'Guion propio', category = 'curiosidades' } = {}) {
  const sentences = splitSentences(rawText);
  const segments = sentences.map((text, i) => ({
    id: `s${i + 1}`,
    kind: i === 0 ? 'gancho' : i === sentences.length - 1 ? 'cierre' : 'desarrollo',
    text,
  }));
  const theme = CATEGORIES[category]?.theme || 'mystery';
  return {
    topicId: null,
    category,
    title,
    theme,
    segments,
    source: '',
    keywords: [title],
    hashtags: [],
    targetDuration: 45,
    estimatedSeconds: Math.round(segments.reduce((a, s) => a + estimateSeconds(s.text), 0)),
    wordCount: countWords(rawText),
    generator: 'manual',
  };
}

export function splitSentences(text) {
  const parts = text
    .replace(/\s+/g, ' ')
    .trim()
    .match(/[^.!?…]+(?:[.!?…]+|$)/g);
  if (!parts) return [];
  // Unimos frases muy cortas con la siguiente para que las escenas no duren medio segundo.
  const out = [];
  for (const p of parts.map((x) => x.trim()).filter(Boolean)) {
    if (out.length && countWords(out[out.length - 1]) < 4) out[out.length - 1] += ' ' + p;
    else out.push(p);
  }
  return out;
}

export function listTopics(category) {
  return TOPICS.filter((t) => !category || t.category === category).map((t) => ({
    id: t.id,
    title: t.title,
    category: t.category,
  }));
}
