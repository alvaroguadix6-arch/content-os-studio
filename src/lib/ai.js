// OPCIONAL y DE PAGO: genera guiones sobre cualquier tema con la API de Claude (Anthropic).
// Solo se usa si pegas tu propia clave en Ajustes. La clave se guarda únicamente en tu
// teléfono y las peticiones van directamente de tu teléfono a Anthropic.
// Sin clave, Content-OS usa el generador gratuito basado en la biblioteca de temas.

import Anthropic from '@anthropic-ai/sdk';

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['title', 'segments', 'hashtags', 'sources', 'uncertain'],
  properties: {
    title: { type: 'string' },
    segments: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['kind', 'text'],
        properties: { kind: { type: 'string', enum: ['gancho', 'contexto', 'desarrollo', 'giro', 'cierre'] }, text: { type: 'string' } },
      },
    },
    hashtags: { type: 'array', items: { type: 'string' } },
    sources: { type: 'array', items: { type: 'string' } },
    uncertain: { type: 'array', items: { type: 'string' } },
  },
};

export async function generateWithClaude({ apiKey, topic, category, duration = 45 }) {
  if (!apiKey) throw new Error('Falta la clave de la API de Claude (Ajustes).');
  const client = new Anthropic({ apiKey, dangerouslyAllowBrowser: true });
  const words = Math.round(duration * 2.5);
  const response = await client.beta.messages.create({
    model: 'claude-opus-5-5',
    max_tokens: 4000,
    betas: ['server-side-fallback-2026-07-01'],
    fallbacks: 'default',
    output_config: { effort: 'low', format: { type: 'json_schema', schema: SCHEMA } },
    system:
      'Eres guionista de vídeos cortos verticales (TikTok, Reels, Shorts) en español de España. ' +
      'Escribes guiones con un gancho fuerte en la primera frase, frases cortas fáciles de locutar y un giro final. ' +
      'Usa solo hechos bien documentados. No inventes cifras, fechas ni citas. Si un dato es una estimación, dilo en el texto. ' +
      'Enumera en "uncertain" cualquier afirmación que convenga verificar y en "sources" fuentes públicas (p. ej. artículos de Wikipedia) para comprobarlo.',
    messages: [
      {
        role: 'user',
        content: `Tema: ${topic}\nCategoría: ${category}\nDuración: unos ${duration} segundos (unas ${words} palabras en total).\nDevuelve entre 5 y 8 segmentos (una o dos frases cada uno), empezando por "gancho" y terminando por "cierre" con una pregunta o llamada a seguir la cuenta.`,
      },
    ],
  });
  if (response.stop_reason === 'refusal') throw new Error('La IA no pudo generar este guion. Prueba con otro tema.');
  const text = response.content.find((b) => b.type === 'text')?.text;
  if (!text) throw new Error('La respuesta de la IA llegó vacía.');
  const data = JSON.parse(text);
  return {
    title: data.title,
    segments: data.segments.map((s, i) => ({ ...s, id: `s${i + 1}` })),
    hashtags: data.hashtags.map((h) => h.replace(/^#/, '')),
    source: data.sources.join('\n'),
    uncertain: data.uncertain,
    generator: 'ia-claude',
  };
}
