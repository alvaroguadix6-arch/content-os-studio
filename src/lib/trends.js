// Análisis de tendencias a partir de enlaces.
// Solo mostramos datos REALES que las plataformas exponen públicamente (oEmbed)
// o mediante la API oficial de YouTube si configuras tu propia clave gratuita.
// Nunca se inventan visualizaciones ni estadísticas: si un dato no está disponible, se indica.

import { TOPICS, CATEGORIES } from './content.js';

export function detectPlatform(url) {
  let u;
  try {
    u = new URL(url.trim());
  } catch {
    return { platform: null, error: 'El enlace no es válido.' };
  }
  const host = u.hostname.replace(/^www\.|^m\./, '');
  if (host === 'youtu.be') return { platform: 'youtube', id: u.pathname.slice(1).split('/')[0], url: u.href };
  if (host.endsWith('youtube.com')) {
    const shorts = u.pathname.match(/\/shorts\/([\w-]{6,})/);
    const id = shorts?.[1] || u.searchParams.get('v');
    return { platform: 'youtube', id, url: u.href };
  }
  if (host.endsWith('tiktok.com')) {
    const m = u.pathname.match(/\/video\/(\d+)/);
    return { platform: 'tiktok', id: m?.[1] || null, url: u.href };
  }
  if (host.endsWith('instagram.com')) {
    const m = u.pathname.match(/\/(reel|reels|p)\/([\w-]+)/);
    return { platform: 'instagram', id: m?.[2] || null, url: u.href };
  }
  return { platform: null, error: 'Solo se admiten enlaces de TikTok, Instagram o YouTube.' };
}

/** Pide los datos públicos de un vídeo. Devuelve solo lo que la plataforma ofrece. */
export async function fetchVideoData(url, { youtubeApiKey, fetchImpl = fetch } = {}) {
  const info = detectPlatform(url);
  if (!info.platform) throw new Error(info.error);
  const result = {
    platform: info.platform,
    url: info.url,
    id: info.id,
    title: null,
    author: null,
    thumbnail: null,
    stats: null,
    statsSource: null,
    fetchedAt: new Date().toISOString(),
    notes: [],
  };

  if (info.platform === 'instagram') {
    result.notes.push(
      'Instagram no permite leer datos de publicaciones sin una app de Meta aprobada y un token oficial. Puedes pegar el texto de la publicación manualmente para analizarlo.',
    );
    return result;
  }

  const endpoint =
    info.platform === 'youtube'
      ? `https://www.youtube.com/oembed?format=json&url=${encodeURIComponent(info.url)}`
      : `https://www.tiktok.com/oembed?url=${encodeURIComponent(info.url)}`;
  try {
    const r = await fetchImpl(endpoint);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const j = await r.json();
    result.title = j.title || null;
    result.author = j.author_name || null;
    result.thumbnail = j.thumbnail_url || null;
    result.notes.push('Título, autor y miniatura obtenidos del servicio público oEmbed de la plataforma.');
  } catch (e) {
    result.notes.push(`No se pudieron leer los datos públicos (${e.message}). Puede que el vídeo sea privado o el enlace no sea correcto.`);
  }

  if (info.platform === 'youtube') {
    if (youtubeApiKey && info.id) {
      try {
        const r = await fetchImpl(
          `https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet,contentDetails&id=${encodeURIComponent(info.id)}&key=${encodeURIComponent(youtubeApiKey)}`,
        );
        const j = await r.json();
        if (j.error) throw new Error(j.error.message);
        const v = j.items?.[0];
        if (v) {
          result.stats = {
            views: num(v.statistics.viewCount),
            likes: num(v.statistics.likeCount),
            comments: num(v.statistics.commentCount),
          };
          result.description = v.snippet.description;
          result.tags = v.snippet.tags || [];
          result.publishedAt = v.snippet.publishedAt;
          result.duration = v.contentDetails?.duration;
          result.statsSource = 'API oficial de YouTube (datos reales en el momento de la consulta)';
        }
      } catch (e) {
        result.notes.push(`La API de YouTube devolvió un error: ${e.message}`);
      }
    } else {
      result.notes.push('Las visualizaciones y «me gusta» solo se muestran si añades tu clave gratuita de la API de YouTube en Ajustes.');
    }
  } else if (info.platform === 'tiktok') {
    result.notes.push('TikTok no ofrece visualizaciones ni «me gusta» sin su API oficial para investigadores o empresas. No se muestran estadísticas.');
  }
  return result;
}

function num(v) {
  return v == null ? null : Number(v);
}

const HOOK_PATTERNS = [
  { id: 'pregunta', label: 'Pregunta directa', test: (t) => /[¿?]/.test(t), tip: 'Abre con una pregunta que el espectador quiera resolver.' },
  { id: 'numero', label: 'Cifra concreta', test: (t) => /\d/.test(t), tip: 'Los números concretos dan credibilidad y curiosidad.' },
  {
    id: 'que-pasaria',
    label: '«¿Qué pasaría si…?»',
    test: (t) => /qu[eé] pasar[ií]a|what if|y si /i.test(t),
    tip: 'Formato de simulación: plantea un escenario imposible y explica las consecuencias.',
  },
  {
    id: 'misterio',
    label: 'Misterio / secreto',
    test: (t) => /misterio|secreto|nadie|inexplicable|enigma|mystery|secret|nobody|unexplained/i.test(t),
    tip: 'Promete revelar algo oculto o no resuelto.',
  },
  {
    id: 'superlativo',
    label: 'Superlativo / récord',
    test: (t) => /m[aá]s (grande|raro|antiguo|peligroso|extraño)|el mayor|r[eé]cord|most|biggest|largest|oldest|worst|best/i.test(t),
    tip: 'Usa «el más…» para prometer algo excepcional.',
  },
  {
    id: 'contradiccion',
    label: 'Contradicción / mito',
    test: (t) => /mentira|mito|falso|en realidad|verdad|wrong|myth|actually|truth/i.test(t),
    tip: 'Romper una creencia común genera mucha retención.',
  },
  { id: 'historia', label: 'Historia personal', test: (t) => /hombre|mujer|niñ|perro|man|woman|girl|boy|dog/i.test(t), tip: 'Personas o animales concretos generan empatía.' },
  { id: 'pov', label: 'POV / segunda persona', test: (t) => /\bpov\b|\bt[uú]\b|imagina|you /i.test(t), tip: 'Habla directamente al espectador.' },
];

export function analyzeText(text = '') {
  const t = String(text);
  const hashtags = (t.match(/#[\p{L}\p{N}_]+/gu) || []).map((h) => h.toLowerCase());
  const clean = t.replace(/#[\p{L}\p{N}_]+/gu, '').trim();
  const emojis = (t.match(/\p{Extended_Pictographic}/gu) || []).length;
  const patterns = HOOK_PATTERNS.filter((p) => p.test(clean)).map(({ id, label, tip }) => ({ id, label, tip }));
  const words = clean.split(/\s+/).filter(Boolean).length;
  return {
    hashtags,
    emojis,
    words,
    patterns,
    lengthLabel: words <= 8 ? 'Título corto (bueno para móvil)' : words <= 15 ? 'Título de longitud media' : 'Título largo',
  };
}

/** Propone ideas ORIGINALES de la biblioteca relacionadas con el vídeo analizado. */
export function suggestIdeas(text = '', patterns = []) {
  const words = new Set(
    String(text)
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .split(/[^a-z0-9ñ]+/)
      .filter((w) => w.length > 3),
  );
  const ids = new Set(patterns.map((p) => p.id));
  const scored = TOPICS.map((t) => {
    const hay = [t.title, ...t.keywords, ...t.hashtags, t.context]
      .join(' ')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
    let score = 0;
    for (const w of words) if (hay.includes(w)) score += 2;
    if (ids.has('que-pasaria') && t.category === 'simulaciones') score += 3;
    if (ids.has('misterio') && t.category === 'misterios') score += 3;
    if (ids.has('historia') && t.category === 'historias') score += 2;
    if (ids.has('contradiccion') && t.id === 'triangulo-bermudas') score += 2;
    return { t, score };
  })
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
  return scored.map(({ t }) => ({
    topicId: t.id,
    title: t.title,
    category: CATEGORIES[t.category].label,
    angle: ids.has('pregunta') ? 'Abrir con una pregunta' : ids.has('numero') ? 'Abrir con la cifra más sorprendente' : 'Abrir con el dato más chocante',
    hook: t.hooks[0],
  }));
}
