import { describe, it, expect } from 'vitest';
import { buildCues, cueAt, toSRT } from '../../src/lib/subtitles.js';

const segs = [
  { text: 'En 1977 llegó una señal del espacio.', start: 0.3, end: 3.0 },
  { text: 'Nadie la ha podido explicar, todavía.', start: 3.2, end: 6.0 },
];

describe('subtítulos', () => {
  const cues = buildCues(segs);
  it('bloques de máximo 3 palabras, en orden y dentro de cada frase', () => {
    for (const c of cues) {
      expect(c.words.length).toBeLessThanOrEqual(3);
      expect(c.end).toBeGreaterThan(c.start);
    }
    for (let i = 1; i < cues.length; i++) expect(cues[i].start).toBeGreaterThanOrEqual(cues[i - 1].end - 1e-9);
    expect(cues[0].start).toBeGreaterThanOrEqual(0.3);
    expect(cues.at(-1).end).toBeLessThanOrEqual(6.0);
  });
  it('conserva todas las palabras', () => {
    const words = cues.flatMap((c) => c.words.map((w) => w.text)).join(' ');
    expect(words).toBe(segs.map((s) => s.text).join(' '));
  });
  it('corta en signos de puntuación', () => {
    expect(cues.some((c) => c.text.endsWith('explicar,'))).toBe(true);
  });
  it('cueAt encuentra el bloque activo', () => {
    expect(cueAt(cues, 0.1)).toBeNull();
    expect(cueAt(cues, 0.5).text.startsWith('En')).toBe(true);
    expect(cueAt(cues, 3.1)).toBeNull();
  });
  it('exporta SRT', () => {
    expect(toSRT(cues)).toMatch(/^1\n00:00:00,3\d\d --> 00:00:0/);
  });
});
