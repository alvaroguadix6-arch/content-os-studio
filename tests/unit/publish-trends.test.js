import { describe, it, expect } from 'vitest';
import { buildPublication, buildHashtags, PLATFORM_LIMITS } from '../../src/lib/publish.js';
import { detectPlatform, analyzeText, suggestIdeas, fetchVideoData } from '../../src/lib/trends.js';
import { generateScript } from '../../src/lib/scriptgen.js';
import { computeTimeline } from '../../src/engine/audio.js';

const project = { ...generateScript({ topicId: 'juan-pujol-garbo', duration: 45, seed: 2 }), credits: [{ author: 'Ana', license: 'CC BY 4.0' }] };

describe('publicación', () => {
  const pub = buildPublication(project);
  it('respeta límites de cada red', () => {
    expect(pub.youtube.title.length).toBeLessThanOrEqual(PLATFORM_LIMITS.youtube.title);
    expect(pub.tiktok.caption.length).toBeLessThanOrEqual(PLATFORM_LIMITS.tiktok.caption);
    expect(pub.instagram.hashtags.length).toBeLessThanOrEqual(30);
  });
  it('YouTube incluye #shorts y fuente; Instagram incluye créditos', () => {
    expect(pub.youtube.title).toContain('#shorts');
    expect(pub.youtube.description).toContain(project.source);
    expect(pub.instagram.caption).toContain('Ana (CC BY 4.0)');
  });
  it('hashtags sin tildes ni duplicados', () => {
    const tags = buildHashtags({ hashtags: ['España', 'españa', 'Segunda Guerra'], category: 'historias' }, 'tiktok');
    expect(tags).toContain('#españa');
    expect(tags).toContain('#segundaguerra');
    expect(new Set(tags).size).toBe(tags.length);
  });
});

describe('tendencias', () => {
  it('detecta plataformas', () => {
    expect(detectPlatform('https://www.youtube.com/shorts/abc123XYZ').platform).toBe('youtube');
    expect(detectPlatform('https://www.youtube.com/shorts/abc123XYZ').id).toBe('abc123XYZ');
    expect(detectPlatform('https://youtu.be/xyz98765').id).toBe('xyz98765');
    expect(detectPlatform('https://www.tiktok.com/@u/video/7123456789').id).toBe('7123456789');
    expect(detectPlatform('https://www.instagram.com/reel/Cabc_12/').platform).toBe('instagram');
    expect(detectPlatform('https://ejemplo.com').platform).toBeNull();
    expect(detectPlatform('no es un enlace').platform).toBeNull();
  });
  it('analiza ganchos', () => {
    const a = analyzeText('¿Qué pasaría si la Tierra dejara de girar? 🌍 #ciencia #fyp');
    const ids = a.patterns.map((p) => p.id);
    expect(ids).toContain('pregunta');
    expect(ids).toContain('que-pasaria');
    expect(a.hashtags).toEqual(['#ciencia', '#fyp']);
    expect(a.emojis).toBe(1);
  });
  it('propone ideas de la biblioteca', () => {
    const ideas = suggestIdeas('What if the Earth stopped spinning?', [{ id: 'que-pasaria' }]);
    expect(ideas).toHaveLength(3);
    expect(ideas[0].topicId).toBe('tierra-deja-de-girar');
  });
  it('nunca inventa estadísticas: sin clave de YouTube, stats = null', async () => {
    const fake = async () => ({ ok: true, json: async () => ({ title: 'T', author_name: 'A', thumbnail_url: 'x' }) });
    const r = await fetchVideoData('https://www.youtube.com/shorts/abc123XYZ', { fetchImpl: fake });
    expect(r.title).toBe('T');
    expect(r.stats).toBeNull();
    const ig = await fetchVideoData('https://www.instagram.com/reel/abc/', { fetchImpl: fake });
    expect(ig.stats).toBeNull();
    expect(ig.title).toBeNull();
  });
  it('con clave de YouTube usa los datos reales de la API', async () => {
    const fake = async (u) => ({
      ok: true,
      json: async () =>
        u.includes('googleapis')
          ? { items: [{ statistics: { viewCount: '1234', likeCount: '56', commentCount: '7' }, snippet: { description: 'd' }, contentDetails: {} }] }
          : { title: 'T' },
    });
    const r = await fetchVideoData('https://youtu.be/abc12345', { fetchImpl: fake, youtubeApiKey: 'k' });
    expect(r.stats).toEqual({ views: 1234, likes: 56, comments: 7 });
  });
});

describe('línea de tiempo', () => {
  it('encadena frases con pausas', () => {
    const { timeline, duration } = computeTimeline([{ id: 'a', text: 'x' }, { id: 'b', text: 'y' }], [2, 3]);
    expect(timeline[0].start).toBeCloseTo(0.35);
    expect(timeline[1].start).toBeCloseTo(0.35 + 2 + 0.22);
    expect(duration).toBeCloseTo(timeline[1].end + 1);
  });
});
