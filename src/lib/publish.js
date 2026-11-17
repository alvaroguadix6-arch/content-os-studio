// Prepara títulos, descripciones y hashtags para cada red.
// No publica nada: solo genera textos para copiar o compartir manualmente.

import { CATEGORIES } from './content.js';

export const PLATFORM_LIMITS = {
  tiktok: { caption: 2200, hashtags: 8 },
  instagram: { caption: 2200, hashtags: 30 },
  youtube: { title: 100, description: 5000, hashtags: 15 },
};

const BASE_TAGS = {
  misterios: ['misterios', 'misterio', 'enigmas', 'sabiasque'],
  curiosidades: ['curiosidades', 'sabiasque', 'datoscuriosos', 'aprendeentiktok'],
  ciencia: ['ciencia', 'divulgacion', 'sabiasque', 'aprendeentiktok'],
  simulaciones: ['quepasariasi', 'simulacion', 'ciencia', 'sabiasque'],
  historias: ['historiasreales', 'historia', 'sabiasque', 'curiosidades'],
};

export function normalizeTag(t) {
  return String(t)
    .toLowerCase()
    .replace(/ñ/g, '~')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/~/g, 'ñ')
    .replace(/[^a-z0-9ñ]/g, '');
}

export function buildHashtags(project, platform) {
  const limit = PLATFORM_LIMITS[platform]?.hashtags ?? 10;
  const tags = [...(project.hashtags || []), ...(BASE_TAGS[project.category] || [])];
  if (platform === 'youtube') tags.unshift('shorts');
  if (platform === 'tiktok') tags.push('parati');
  if (platform === 'instagram') tags.push('reels');
  const seen = new Set();
  const out = [];
  for (const t of tags.map(normalizeTag).filter(Boolean)) {
    if (!seen.has(t)) {
      seen.add(t);
      out.push('#' + t);
    }
  }
  return out.slice(0, limit);
}

function truncate(s, n) {
  return s.length <= n ? s : s.slice(0, n - 1).trimEnd() + '…';
}

export function buildPublication(project) {
  const hook = project.segments?.[0]?.text || project.title;
  const summary = (project.segments || [])
    .filter((s) => s.kind === 'contexto' || s.kind === 'giro')
    .map((s) => s.text)
    .join(' ');
  const emoji = CATEGORIES[project.category]?.emoji || '🎬';
  const credits = (project.credits || []).length
    ? '\n\nImágenes: ' + project.credits.map((c) => `${c.author} (${c.license})`).join('; ')
    : '';
  const source = project.source ? `\n\nFuente para verificar: ${project.source}` : '';

  const tt = buildHashtags(project, 'tiktok');
  const ig = buildHashtags(project, 'instagram');
  const yt = buildHashtags(project, 'youtube');

  return {
    tiktok: {
      caption: truncate(`${emoji} ${hook}\n\n${project.question || '¿Lo sabías? Te leo en comentarios 👇'}\n\n${tt.join(' ')}`, PLATFORM_LIMITS.tiktok.caption),
      hashtags: tt,
    },
    instagram: {
      caption: truncate(
        `${emoji} ${project.title}\n\n${hook}\n${summary ? '\n' + summary + '\n' : ''}\n💬 Cuéntame en comentarios si lo sabías.\n🔖 Guárdalo para verlo después.${credits}\n\n${ig.join(' ')}`,
        PLATFORM_LIMITS.instagram.caption,
      ),
      hashtags: ig,
    },
    youtube: {
      title: truncate(`${project.title} ${emoji} #shorts`, PLATFORM_LIMITS.youtube.title),
      description: truncate(
        `${hook}${summary ? '\n\n' + summary : ''}\n\nSuscríbete para más vídeos de ${CATEGORIES[project.category]?.label.toLowerCase() || 'curiosidades'}.${source}${credits}\n\n${yt.join(' ')}`,
        PLATFORM_LIMITS.youtube.description,
      ),
      hashtags: yt,
    },
  };
}
