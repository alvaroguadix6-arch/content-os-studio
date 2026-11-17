// Dibuja cada fotograma del vídeo vertical 9:16 en un <canvas>.
// Fondos animados generados por código (sin derechos de autor), imágenes con efecto
// Ken Burns, título de gancho, subtítulos con la palabra activa resaltada y barra de progreso.

import { cueAt } from '../lib/subtitles.js';
import { CATEGORIES } from '../lib/content.js';

const PALETTES = {
  space: { bg: ['#05061a', '#16123f', '#2b1458'], accent: '#8f7bff', glow: '#5ac8fa' },
  mystery: { bg: ['#050807', '#0f1f1a', '#1f1030'], accent: '#38e0a1', glow: '#a855f7' },
  ocean: { bg: ['#020b1a', '#05305a', '#0a5b7a'], accent: '#4fd1ff', glow: '#7cf3ff' },
  history: { bg: ['#120b05', '#3a2412', '#5b3a1c'], accent: '#f2b35a', glow: '#ffd89a' },
  lab: { bg: ['#020d10', '#06303a', '#0b4a4f'], accent: '#2ee6d6', glow: '#7bffb0' },
  nature: { bg: ['#03100a', '#0d3a22', '#1d5a2c'], accent: '#a3e635', glow: '#fde68a' },
};

export function makeRng(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return ((s >>> 0) % 100000) / 100000;
  };
}

export function createSceneState({ width, height, theme, seed = 7 }) {
  const rnd = makeRng(seed);
  const particles = Array.from({ length: 140 }, () => ({
    x: rnd(),
    y: rnd(),
    z: 0.2 + rnd() * 0.8,
    r: 0.5 + rnd() * 2,
    p: rnd() * Math.PI * 2,
  }));
  const blobs = Array.from({ length: 4 }, () => ({ x: rnd(), y: rnd(), r: 0.35 + rnd() * 0.4, sp: 0.03 + rnd() * 0.05, p: rnd() * 6 }));
  const nodes = Array.from({ length: 26 }, () => ({ x: rnd(), y: rnd(), vx: rnd() - 0.5, vy: rnd() - 0.5 }));
  return { width, height, theme: PALETTES[theme] ? theme : 'mystery', particles, blobs, nodes };
}

function drawBackground(ctx, st, t) {
  const { width: W, height: H } = st;
  const pal = PALETTES[st.theme];
  const g = ctx.createLinearGradient(0, 0, W * 0.3, H);
  g.addColorStop(0, pal.bg[0]);
  g.addColorStop(0.55, pal.bg[1]);
  g.addColorStop(1, pal.bg[2]);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  // Manchas de luz que se mueven lentamente (nebulosa / niebla)
  ctx.globalCompositeOperation = 'lighter';
  st.blobs.forEach((b, i) => {
    const x = (b.x + Math.sin(t * b.sp + b.p) * 0.15) * W;
    const y = (b.y + Math.cos(t * b.sp * 0.8 + b.p) * 0.12) * H;
    const r = b.r * W;
    const rg = ctx.createRadialGradient(x, y, 0, x, y, r);
    rg.addColorStop(0, (i % 2 ? pal.accent : pal.glow) + '38');
    rg.addColorStop(1, '#00000000');
    ctx.fillStyle = rg;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  });
  ctx.globalCompositeOperation = 'source-over';

  if (st.theme === 'lab') {
    // Red de nodos tipo "simulación"
    ctx.strokeStyle = pal.accent + '30';
    ctx.lineWidth = 1;
    const grid = W / 9;
    const off = (t * 20) % grid;
    for (let x = -grid + off; x < W + grid; x += grid) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
    for (let y = -grid + off; y < H + grid; y += grid) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }
    const pts = st.nodes.map((n) => ({
      x: (((n.x + n.vx * t * 0.03) % 1) + 1) % 1 * W,
      y: (((n.y + n.vy * t * 0.03) % 1) + 1) % 1 * H,
    }));
    ctx.strokeStyle = pal.glow + '55';
    for (let i = 0; i < pts.length; i++)
      for (let j = i + 1; j < pts.length; j++) {
        const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
        if (d < W * 0.22) {
          ctx.globalAlpha = 1 - d / (W * 0.22);
          ctx.beginPath();
          ctx.moveTo(pts[i].x, pts[i].y);
          ctx.lineTo(pts[j].x, pts[j].y);
          ctx.stroke();
        }
      }
    ctx.globalAlpha = 1;
    ctx.fillStyle = pal.glow;
    pts.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
    return;
  }

  // Partículas: estrellas (espacio), burbujas (océano), polvo (resto)
  for (const p of st.particles) {
    let x = p.x * W;
    let y = p.y * H;
    let alpha = 0.5;
    let r = p.r * (W / 720);
    if (st.theme === 'space') {
      y = ((p.y + t * 0.004 * p.z) % 1) * H;
      alpha = 0.35 + 0.65 * Math.abs(Math.sin(t * 1.5 * p.z + p.p));
      ctx.fillStyle = `rgba(255,255,255,${alpha})`;
    } else if (st.theme === 'ocean') {
      y = (1 - ((p.y + t * 0.03 * p.z) % 1)) * H;
      x += Math.sin(t * 2 + p.p) * 6;
      r *= 2;
      ctx.fillStyle = `rgba(180,240,255,${0.18 + 0.2 * p.z})`;
    } else {
      x += Math.sin(t * 0.5 + p.p) * 20 * p.z;
      y = ((p.y - t * 0.006 * p.z + 1) % 1) * H;
      ctx.fillStyle = `rgba(255,240,210,${0.12 + 0.25 * p.z})`;
    }
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  if (st.theme === 'ocean') {
    // Rayos de luz desde la superficie
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 5; i++) {
      const x = W * (0.1 + i * 0.2) + Math.sin(t * 0.4 + i) * 40;
      const lg = ctx.createLinearGradient(x, 0, x + 80, H * 0.8);
      lg.addColorStop(0, 'rgba(160,230,255,0.12)');
      lg.addColorStop(1, 'rgba(160,230,255,0)');
      ctx.fillStyle = lg;
      ctx.beginPath();
      ctx.moveTo(x - 30, 0);
      ctx.lineTo(x + 30, 0);
      ctx.lineTo(x + 160, H * 0.8);
      ctx.lineTo(x + 20, H * 0.8);
      ctx.fill();
    }
    ctx.globalCompositeOperation = 'source-over';
  }
}

function drawImageCover(ctx, img, W, H, progress, index) {
  const iw = img.width;
  const ih = img.height;
  const scale = Math.max(W / iw, H / ih) * (1.06 + 0.12 * progress);
  const dw = iw * scale;
  const dh = ih * scale;
  const dir = index % 2 ? 1 : -1;
  const x = (W - dw) / 2 + dir * (dw - W) * 0.25 * (progress - 0.5);
  const y = (H - dh) / 2 + (dh - H) * 0.15 * (progress - 0.5);
  ctx.drawImage(img, x, y, dw, dh);
}

const UNITS = 'por ciento|km/h|kilómetros por hora|kilómetros|segundos|minutos|horas|años|días|metros|grados|millones|billones|toneladas|veces|pascales';
const FACT_RE = new RegExp(`(\\d[\\d.,]*)\\s*(${UNITS})?`, 'i');

/** Extrae el dato numérico más llamativo de una frase (p. ej. «72 segundos»). */
export function keyFact(text) {
  const m = text.match(FACT_RE);
  if (!m) return null;
  return { value: m[1].replace(/[.,]$/, ''), unit: (m[2] || '').toLowerCase() };
}

function drawCenterIcon(ctx, st, emoji, t, segIndex, fact) {
  const { width: W, height: H } = st;
  const pal = PALETTES[st.theme];
  const cx = W / 2;
  const cy = H * 0.36 + Math.sin(t * 1.2) * 10;
  const R = W * 0.22;
  ctx.save();
  // anillos giratorios
  ctx.strokeStyle = pal.accent + '90';
  ctx.lineWidth = W / 180;
  for (let k = 0; k < 3; k++) {
    ctx.beginPath();
    const a0 = t * (0.4 + k * 0.25) * (k % 2 ? -1 : 1) + segIndex;
    ctx.arc(cx, cy, R * (1 + k * 0.22), a0, a0 + Math.PI * (1.1 + k * 0.2));
    ctx.stroke();
  }
  const rg = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
  rg.addColorStop(0, pal.glow + '55');
  rg.addColorStop(1, pal.glow + '00');
  ctx.fillStyle = rg;
  ctx.beginPath();
  ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.fill();
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  if (fact) {
    const len = fact.value.length;
    const fs = Math.round(R * (len <= 2 ? 0.95 : len <= 4 ? 0.7 : 0.52));
    ctx.font = `900 ${fs}px ${FONT}`;
    ctx.shadowColor = pal.glow;
    ctx.shadowBlur = 30;
    ctx.fillStyle = '#fff';
    ctx.fillText(fact.value, cx, cy - (fact.unit ? R * 0.12 : 0));
    ctx.shadowBlur = 0;
    if (fact.unit) {
      ctx.font = `800 ${Math.round(R * 0.2)}px ${FONT}`;
      ctx.fillStyle = pal.glow;
      ctx.fillText(fact.unit.toUpperCase(), cx, cy + R * 0.42);
    }
  } else {
    ctx.font = `${Math.round(R * 0.95)}px "Apple Color Emoji","Noto Color Emoji","Segoe UI Emoji",sans-serif`;
    ctx.fillText(emoji, cx, cy + R * 0.05);
  }
  ctx.restore();
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function wrapLines(ctx, text, maxWidth) {
  const words = text.split(/\s+/);
  const lines = [];
  let cur = '';
  for (const w of words) {
    const test = cur ? cur + ' ' + w : w;
    if (ctx.measureText(test).width > maxWidth && cur) {
      lines.push(cur);
      cur = w;
    } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}

const FONT = '"SF Pro Display","Helvetica Neue","Arial Black",Arial,sans-serif';

function drawSubtitle(ctx, st, cue, t, style) {
  if (!cue) return;
  const { width: W, height: H } = st;
  const base = Math.round(W * 0.085);
  const pop = Math.min(1, (t - cue.start) / 0.12);
  const scale = 0.86 + 0.14 * easeOut(pop);
  ctx.save();
  ctx.translate(W / 2, H * 0.62);
  ctx.scale(scale, scale);
  ctx.font = `900 ${base}px ${FONT}`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round';
  const upper = style.uppercase !== false;
  const words = cue.words.map((w) => ({ ...w, label: upper ? w.text.toUpperCase() : w.text }));
  // Organizar en líneas
  const maxW = W * 0.86;
  const lines = [];
  let line = [];
  let lw = 0;
  const space = ctx.measureText(' ').width;
  for (const w of words) {
    const ww = ctx.measureText(w.label).width;
    if (line.length && lw + space + ww > maxW) {
      lines.push({ items: line, width: lw });
      line = [];
      lw = 0;
    }
    line.push({ ...w, w: ww });
    lw += (line.length > 1 ? space : 0) + ww;
  }
  if (line.length) lines.push({ items: line, width: lw });
  const lh = base * 1.15;
  lines.forEach((ln, li) => {
    let x = -ln.width / 2;
    const y = (li - (lines.length - 1) / 2) * lh;
    for (const w of ln.items) {
      const active = t >= w.start && t < w.end + 0.05;
      ctx.lineWidth = base * 0.2;
      ctx.strokeStyle = '#000';
      ctx.strokeText(w.label, x, y);
      ctx.fillStyle = active ? style.highlight || '#FFD400' : '#FFFFFF';
      ctx.fillText(w.label, x, y);
      x += w.w + space;
    }
  });
  ctx.restore();
}

function easeOut(x) {
  return 1 - Math.pow(1 - x, 3);
}

function drawTitleCard(ctx, st, title, t, until) {
  const { width: W, height: H } = st;
  const fadeIn = Math.min(1, t / 0.35);
  const fadeOut = Math.min(1, Math.max(0, (until - t) / 0.35));
  const a = Math.min(fadeIn, fadeOut);
  if (a <= 0) return;
  ctx.save();
  ctx.globalAlpha = a;
  const pal = PALETTES[st.theme];
  const fs = Math.round(W * 0.068);
  ctx.font = `900 ${fs}px ${FONT}`;
  const lines = wrapLines(ctx, title.toUpperCase(), W * 0.8);
  const boxH = lines.length * fs * 1.2 + fs * 0.9;
  const y0 = H * 0.13;
  ctx.translate(0, (1 - easeOut(fadeIn)) * -30);
  roundRect(ctx, W * 0.06, y0, W * 0.88, boxH, fs * 0.4);
  ctx.fillStyle = 'rgba(0,0,0,0.55)';
  ctx.fill();
  ctx.lineWidth = 4;
  ctx.strokeStyle = pal.accent;
  ctx.stroke();
  ctx.fillStyle = '#fff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  lines.forEach((l, i) => ctx.fillText(l, W / 2, y0 + fs * 0.45 + fs * 0.6 + i * fs * 1.2));
  ctx.restore();
}

function drawChrome(ctx, st, t, duration, categoryLabel, handle) {
  const { width: W, height: H } = st;
  const pal = PALETTES[st.theme];
  // barra de progreso
  ctx.fillStyle = 'rgba(255,255,255,0.18)';
  ctx.fillRect(0, 0, W, Math.max(6, H * 0.004));
  ctx.fillStyle = pal.accent;
  ctx.fillRect(0, 0, (W * t) / duration, Math.max(6, H * 0.004));
  // etiqueta de categoría
  const fs = Math.round(W * 0.034);
  ctx.font = `800 ${fs}px ${FONT}`;
  const label = categoryLabel.toUpperCase();
  const w = ctx.measureText(label).width + fs * 1.6;
  roundRect(ctx, W * 0.06, H * 0.055, w, fs * 2, fs);
  ctx.fillStyle = 'rgba(0,0,0,0.45)';
  ctx.fill();
  ctx.fillStyle = '#fff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, W * 0.06 + fs * 0.8, H * 0.055 + fs);
  if (handle) {
    ctx.font = `700 ${Math.round(W * 0.03)}px ${FONT}`;
    ctx.fillStyle = 'rgba(255,255,255,0.75)';
    ctx.textAlign = 'center';
    ctx.fillText(handle, W / 2, H * 0.76);
  }
}

/**
 * Dibuja el fotograma en el instante t (segundos).
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} st       estado de escena (createSceneState)
 * @param {object} data     { timeline, cues, duration, images[], title, category, style, handle }
 */
export function drawFrame(ctx, st, data, t) {
  const { width: W, height: H } = st;
  const { timeline, cues, duration, images = [], title, category, style = {}, handle } = data;
  let idx = timeline.findIndex((s, i) => t < (timeline[i + 1]?.start ?? Infinity));
  if (idx < 0) idx = timeline.length - 1;
  const seg = timeline[idx];
  const segStart = idx === 0 ? 0 : seg.start - 0.2;
  const segEnd = timeline[idx + 1]?.start ?? duration;
  const progress = Math.min(1, Math.max(0, (t - segStart) / Math.max(0.1, segEnd - segStart)));

  drawBackground(ctx, st, t);

  const img = images[idx];
  if (img) {
    ctx.save();
    const fade = Math.min(1, (t - segStart) / 0.35);
    // fundido desde la imagen anterior
    const prev = images[idx - 1];
    if (prev && fade < 1) {
      drawImageCover(ctx, prev, W, H, 1, idx - 1);
      ctx.globalAlpha = fade;
    }
    drawImageCover(ctx, img, W, H, progress, idx);
    ctx.restore();
    // oscurecer arriba y abajo para que se lean los textos
    const sh = ctx.createLinearGradient(0, 0, 0, H);
    sh.addColorStop(0, 'rgba(0,0,0,0.55)');
    sh.addColorStop(0.3, 'rgba(0,0,0,0.1)');
    sh.addColorStop(0.5, 'rgba(0,0,0,0.25)');
    sh.addColorStop(1, 'rgba(0,0,0,0.75)');
    ctx.fillStyle = sh;
    ctx.fillRect(0, 0, W, H);
  } else {
    drawCenterIcon(ctx, st, CATEGORIES[category]?.emoji || '🎬', t, idx, seg.fact === undefined ? (seg.fact = keyFact(seg.text)) : seg.fact);
  }

  drawChrome(ctx, st, t, duration, CATEGORIES[category]?.label || 'Content-OS', handle);
  if (title && timeline[0]) drawTitleCard(ctx, st, title, t, timeline[0].end + 0.3);
  drawSubtitle(ctx, st, cueAt(cues, t), t, style);

  // fundido final
  const endFade = Math.min(1, Math.max(0, (t - (duration - 0.4)) / 0.4));
  if (endFade > 0) {
    ctx.fillStyle = `rgba(0,0,0,${endFade})`;
    ctx.fillRect(0, 0, W, H);
  }
}
