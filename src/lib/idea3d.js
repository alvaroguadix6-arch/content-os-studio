// Convierte una idea escrita en español en un "encargo" de render 3D (JSON) que entiende
// render3d/pipeline.py. Solo interpreta lo que la plantilla sabe hacer de verdad; lo que no
// se reconoce se indica como "no interpretado" (no se inventa).

export const TEMPLATES_3D = {
  carrera: {
    label: 'Carrera de superdeportivos',
    emoji: '🏎️',
    ready: true,
    desc: 'Dos superdeportivos en circuito cerrado con ciudad al fondo, salida con semáforo, adelantamientos, cámaras de cine, cámara lenta y foto finish.',
  },
  ciudad: {
    label: 'Simulación en ciudad',
    emoji: '🏙️',
    ready: false,
    desc: 'Sucesos hipotéticos en una ciudad 3D (próxima fase).',
  },
  reto: {
    label: 'Retos y experimentos',
    emoji: '🧪',
    ready: false,
    desc: 'Situaciones sorprendentes con física simulada (próxima fase).',
  },
};

// Colores en espacio lineal (Blender) y nombre visible
export const COLORS = {
  rojo: { rgb: [0.55, 0.0, 0.0], name: 'Rosso' },
  amarillo: { rgb: [0.9, 0.55, 0.0], name: 'Giallo' },
  azul: { rgb: [0.0, 0.08, 0.6], name: 'Blu' },
  verde: { rgb: [0.02, 0.35, 0.05], name: 'Verde' },
  naranja: { rgb: [0.9, 0.22, 0.0], name: 'Arancio' },
  negro: { rgb: [0.01, 0.01, 0.012], name: 'Nero' },
  blanco: { rgb: [0.85, 0.85, 0.85], name: 'Bianco' },
  morado: { rgb: [0.25, 0.02, 0.45], name: 'Viola' },
  gris: { rgb: [0.25, 0.26, 0.28], name: 'Grigio' },
  plata: { rgb: [0.55, 0.56, 0.58], name: 'Argento' },
  rosa: { rgb: [0.85, 0.15, 0.4], name: 'Rosa' },
};

const ALIASES = {
  roja: 'rojo', ferrari: 'rojo', amarilla: 'amarillo', lamborghini: 'amarillo', azúl: 'azul', verdes: 'verde',
  naranjo: 'naranja', negra: 'negro', blanca: 'blanco', morada: 'morado', violeta: 'morado', plateado: 'plata', plateada: 'plata', gris: 'gris',
};

function norm(s) {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

export function findColors(text) {
  const words = norm(text).split(/[^a-zñ]+/);
  const found = [];
  for (const w of words) {
    const c = COLORS[w] ? w : ALIASES[w];
    if (c && !found.includes(c)) found.push(c);
  }
  return found;
}

export const QUALITY = {
  rapida: { label: 'Rápida (~25 min)', samples: 8 },
  normal: { label: 'Normal (~45 min)', samples: 14 },
  alta: { label: 'Alta (~80 min)', samples: 24 },
};

/**
 * @returns {{spec: object, understood: string[], notes: string[]}}
 */
export function ideaToSpec(idea, { template = 'carrera', quality = 'normal' } = {}) {
  const understood = [];
  const notes = [];
  const text = idea || '';
  const n = norm(text);
  const colors = findColors(text);
  const a = colors[0] || 'rojo';
  const b = colors.find((c) => c !== a) || (a === 'amarillo' ? 'rojo' : 'amarillo');
  understood.push(`Coche 1: ${a}${colors[0] ? '' : ' (por defecto)'}`);
  understood.push(`Coche 2: ${b}${colors[1] ? '' : ' (por defecto)'}`);
  if (/ferrari|lamborghini|porsche|mclaren|bugatti|bmw|mercedes|audi/.test(n)) {
    notes.push('Las marcas no se reproducen: se usan superdeportivos genéricos con el color indicado.');
  }
  let winner = 'a';
  const m = n.match(/gana(?:ra|dor)?\s+(?:el\s+|la\s+)?([a-zñ]+)/) || n.match(/([a-zñ]+)\s+gana/);
  if (m) {
    const c = COLORS[m[1]] ? m[1] : ALIASES[m[1]];
    if (c === b) winner = 'b';
    if (c) understood.push(`Gana: ${c}`);
  } else {
    understood.push(`Gana: ${a} (por defecto, final de foto finish)`);
  }
  if (/lluvia|noche|nieve|niebla/.test(n)) notes.push('Clima/noche aún no disponible: se renderiza al atardecer.');
  if (/ciudad|calle|explosi|choque|accidente|avion|meteorito/.test(n) && template === 'carrera') {
    notes.push('Esta plantilla es de carrera en circuito; lo demás de la idea no se aplica todavía.');
  }
  const ca = COLORS[a];
  const cb = COLORS[b];
  const title = `Carrera: ${ca.name} contra ${cb.name}`;
  const spec = {
    template,
    title,
    idea: text.slice(0, 500),
    car_a_name: ca.name,
    car_b_name: cb.name,
    car_a_color: ca.rgb,
    car_b_color: cb.rgb,
    winner,
    render: { samples: QUALITY[quality]?.samples ?? 14, chunk_frames: 35 },
  };
  return { spec, understood, notes };
}

export function jobFileName(spec, now = new Date()) {
  const slug = norm(spec.title).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
  const stamp = now.toISOString().replace(/[-:T]/g, '').slice(0, 12);
  return `render3d/jobs/${slug}-${stamp}.json`;
}
