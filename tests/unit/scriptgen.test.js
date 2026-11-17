import { describe, it, expect } from 'vitest';
import { generateScript, scriptFromText, splitSentences, estimateSeconds, countWords } from '../../src/lib/scriptgen.js';
import { TOPICS, CATEGORIES } from '../../src/lib/content.js';

describe('biblioteca de temas', () => {
  it('cada tema tiene fuente, gancho, contexto, giro y categoría válida', () => {
    for (const t of TOPICS) {
      expect(CATEGORIES[t.category], t.id).toBeTruthy();
      expect(t.source, t.id).toMatch(/^https:\/\//);
      expect(t.hooks.length, t.id).toBeGreaterThan(0);
      expect(t.beats.length, t.id).toBeGreaterThan(0);
      expect(t.twist.length, t.id).toBeGreaterThan(10);
    }
  });
  it('cubre las 5 categorías pedidas', () => {
    for (const c of Object.keys(CATEGORIES)) expect(TOPICS.some((t) => t.category === c)).toBe(true);
  });
  it('ids únicos', () => {
    expect(new Set(TOPICS.map((t) => t.id)).size).toBe(TOPICS.length);
  });
});

describe('generateScript', () => {
  it('genera guiones de 30 a 60 s para todos los temas', () => {
    for (const t of TOPICS) {
      for (const d of [30, 45, 60]) {
        const s = generateScript({ topicId: t.id, duration: d, seed: 42 });
        expect(s.segments[0].kind).toBe('gancho');
        expect(s.segments.at(-1).kind).toBe('cierre');
        expect(s.estimatedSeconds, `${t.id} ${d}`).toBeGreaterThanOrEqual(18);
        expect(s.estimatedSeconds, `${t.id} ${d}`).toBeLessThanOrEqual(66);
      }
    }
  });
  it('30 s es más corto o igual que 60 s', () => {
    const a = generateScript({ topicId: 'senal-wow', duration: 30, seed: 1 });
    const b = generateScript({ topicId: 'senal-wow', duration: 60, seed: 1 });
    expect(a.wordCount).toBeLessThanOrEqual(b.wordCount);
  });
  it('es reproducible con la misma semilla', () => {
    const a = generateScript({ topicId: 'hachiko', duration: 45, seed: 7 });
    const b = generateScript({ topicId: 'hachiko', duration: 45, seed: 7 });
    expect(a).toEqual(b);
  });
  it('error con tema desconocido', () => {
    expect(() => generateScript({ topicId: 'nope' })).toThrow();
  });
});

describe('texto propio', () => {
  it('divide en frases y une frases muy cortas', () => {
    expect(splitSentences('Hola. Esto es una prueba larga de verdad. ¿Y ahora qué?')).toEqual(['Hola. Esto es una prueba larga de verdad.', '¿Y ahora qué?']);
  });
  it('crea segmentos', () => {
    const s = scriptFromText('Primera frase bastante larga aquí. Segunda frase también bastante larga. Tercera y última frase del guion.', { title: 'X' });
    expect(s.segments).toHaveLength(3);
    expect(s.segments[0].kind).toBe('gancho');
  });
  it('cuenta palabras y estima segundos', () => {
    expect(countWords('En 1977, el radiotelescopio captó una señal.')).toBe(7);
    expect(estimateSeconds('uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece.')).toBeGreaterThan(4);
  });
});
