// Banda sonora: voz + música generada por el propio programa + efectos.
// La música y los efectos se SINTETIZAN aquí mismo (osciladores y ruido), así que son
// 100 % propios y libres de derechos: no hay ningún riesgo de reclamaciones de copyright.

export const SAMPLE_RATE = 44100;

const PROGRESSIONS = {
  mystery: { bpm: 84, chords: [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]] }, // Am F C G
  space: { bpm: 76, chords: [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]] }, // Dm Bb F C
  history: { bpm: 80, chords: [[52, 55, 59], [48, 52, 55], [55, 59, 62], [50, 54, 57]] }, // Em C G D
  ocean: { bpm: 88, chords: [[48, 52, 55], [55, 59, 62], [57, 60, 64], [53, 57, 60]] }, // C G Am F
  lab: { bpm: 96, chords: [[57, 60, 64], [52, 55, 59], [53, 57, 60], [55, 59, 62]] }, // Am Em F G
  nature: { bpm: 90, chords: [[53, 57, 60], [48, 52, 55], [50, 53, 57], [46, 50, 53]] }, // F C Dm Bb
};

const midi = (n) => 440 * Math.pow(2, (n - 69) / 12);

function noiseBuffer(ctx, seconds = 1) {
  const len = Math.floor(ctx.sampleRate * seconds);
  const b = ctx.createBuffer(1, len, ctx.sampleRate);
  const d = b.getChannelData(0);
  let s = 12345;
  for (let i = 0; i < len; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    d[i] = (s / 0x7fffffff) * 2 - 1;
  }
  return b;
}

function scheduleMusic(ctx, dest, theme, duration) {
  const prog = PROGRESSIONS[theme] || PROGRESSIONS.mystery;
  const beat = 60 / prog.bpm;
  const bar = beat * 4;
  const noise = noiseBuffer(ctx, 1);

  const padFilter = ctx.createBiquadFilter();
  padFilter.type = 'lowpass';
  padFilter.frequency.value = 1100;
  padFilter.Q.value = 0.7;
  padFilter.connect(dest);

  for (let t = 0, i = 0; t < duration; t += bar, i++) {
    const chord = prog.chords[i % prog.chords.length];
    // Pad (acorde sostenido)
    for (const note of chord) {
      for (const det of [-6, 6]) {
        const o = ctx.createOscillator();
        o.type = 'sawtooth';
        o.frequency.value = midi(note);
        o.detune.value = det;
        const g = ctx.createGain();
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(0.018, t + 0.6);
        g.gain.setValueAtTime(0.018, t + bar - 0.4);
        g.gain.linearRampToValueAtTime(0, t + bar + 0.3);
        o.connect(g).connect(padFilter);
        o.start(t);
        o.stop(t + bar + 0.35);
      }
    }
    // Bajo en cada pulso
    for (let b = 0; b < 4; b++) {
      const bt = t + b * beat;
      if (bt > duration) break;
      const o = ctx.createOscillator();
      o.type = 'sine';
      o.frequency.value = midi(chord[0] - 12);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, bt);
      g.gain.exponentialRampToValueAtTime(0.22, bt + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, bt + beat * 0.9);
      o.connect(g).connect(dest);
      o.start(bt);
      o.stop(bt + beat);
      // Hi-hat suave en las corcheas a partir del segundo compás
      if (i > 0) {
        for (const off of [0, 0.5]) {
          const ht = bt + off * beat;
          const src = ctx.createBufferSource();
          src.buffer = noise;
          const hp = ctx.createBiquadFilter();
          hp.type = 'highpass';
          hp.frequency.value = 7000;
          const hg = ctx.createGain();
          hg.gain.setValueAtTime(off ? 0.025 : 0.04, ht);
          hg.gain.exponentialRampToValueAtTime(0.0001, ht + 0.05);
          src.connect(hp).connect(hg).connect(dest);
          src.start(ht, Math.random() * 0.5, 0.06);
        }
      }
    }
    // Arpegio ligero (campanita) para dar movimiento
    chord.forEach((note, k) => {
      const at = t + k * beat * 1.33;
      const o = ctx.createOscillator();
      o.type = 'triangle';
      o.frequency.value = midi(note + 12);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, at);
      g.gain.exponentialRampToValueAtTime(0.035, at + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, at + 1.2);
      o.connect(g).connect(dest);
      o.start(at);
      o.stop(at + 1.3);
    });
  }
}

function whoosh(ctx, dest, t, noise) {
  const src = ctx.createBufferSource();
  src.buffer = noise;
  const bp = ctx.createBiquadFilter();
  bp.type = 'bandpass';
  bp.Q.value = 1.2;
  bp.frequency.setValueAtTime(300, t - 0.35);
  bp.frequency.exponentialRampToValueAtTime(4000, t);
  bp.frequency.exponentialRampToValueAtTime(800, t + 0.25);
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, t - 0.35);
  g.gain.exponentialRampToValueAtTime(0.16, t - 0.02);
  g.gain.exponentialRampToValueAtTime(0.0001, t + 0.3);
  src.connect(bp).connect(g).connect(dest);
  src.start(Math.max(0, t - 0.35), 0, 0.7);
}

function impact(ctx, dest, t) {
  const o = ctx.createOscillator();
  o.type = 'sine';
  o.frequency.setValueAtTime(110, t);
  o.frequency.exponentialRampToValueAtTime(38, t + 0.8);
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(0.5, t + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, t + 1.1);
  o.connect(g).connect(dest);
  o.start(t);
  o.stop(t + 1.2);
}

function normalize(samples, peakTarget = 0.92) {
  let peak = 0;
  for (let i = 0; i < samples.length; i++) peak = Math.max(peak, Math.abs(samples[i]));
  if (peak < 1e-4) return samples;
  const k = peakTarget / peak;
  const out = new Float32Array(samples.length);
  for (let i = 0; i < samples.length; i++) out[i] = samples[i] * k;
  return out;
}

/**
 * Calcula la línea de tiempo a partir de las duraciones de cada frase.
 * Exportada por separado para poder probarla sin audio.
 */
export function computeTimeline(segments, durations, { lead = 0.35, gap = 0.22, tail = 1.0 } = {}) {
  let t = lead;
  const timeline = segments.map((s, i) => {
    const start = t;
    const end = start + durations[i];
    t = end + gap;
    return { id: s.id, kind: s.kind, text: s.text, start, end };
  });
  const duration = (timeline.length ? timeline[timeline.length - 1].end : lead) + tail;
  return { timeline, duration };
}

/**
 * @param {object} p
 * @param {Array} p.segments
 * @param {Array<{samples: Float32Array, sampleRate: number}|null>} p.voices  audio por frase (null = sin voz)
 * @param {number[]} p.durations
 * @param {string} p.theme
 * @param {{music?: boolean, sfx?: boolean, musicVolume?: number}} p.options
 */
export async function buildSoundtrack({ segments, voices, durations, theme, options = {}, timelineOptions }) {
  const { music = true, sfx = true, musicVolume = 0.5 } = options;
  const { timeline, duration } = computeTimeline(segments, durations, timelineOptions);
  const ctx = new OfflineAudioContext(2, Math.ceil(duration * SAMPLE_RATE), SAMPLE_RATE);

  const master = ctx.createDynamicsCompressor();
  master.threshold.value = -12;
  master.ratio.value = 3;
  master.connect(ctx.destination);

  const musicBus = ctx.createGain();
  musicBus.gain.value = musicVolume;
  musicBus.connect(master);
  const voiceBus = ctx.createGain();
  voiceBus.gain.value = 1;
  voiceBus.connect(master);

  if (music) {
    scheduleMusic(ctx, musicBus, theme, duration);
    // "Ducking": la música baja mientras habla la voz
    for (const seg of timeline) {
      if (!voices.some(Boolean)) break;
      musicBus.gain.setTargetAtTime(musicVolume * 0.45, Math.max(0, seg.start - 0.1), 0.08);
      musicBus.gain.setTargetAtTime(musicVolume, seg.end + 0.05, 0.25);
    }
    musicBus.gain.setTargetAtTime(0.0001, duration - 0.8, 0.25);
  }

  if (sfx) {
    const noise = noiseBuffer(ctx, 1);
    impact(ctx, master, 0.05);
    timeline.slice(1).forEach((seg) => whoosh(ctx, master, seg.start, noise));
  }

  voices.forEach((v, i) => {
    if (!v) return;
    const samples = normalize(v.samples);
    const buf = ctx.createBuffer(1, samples.length, v.sampleRate);
    buf.copyToChannel(samples, 0);
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(voiceBus);
    src.start(timeline[i].start);
  });

  const buffer = await ctx.startRendering();
  return { buffer, timeline, duration };
}

export function audioBufferToWav(buffer) {
  const ch = buffer.numberOfChannels;
  const len = buffer.length;
  const out = new DataView(new ArrayBuffer(44 + len * ch * 2));
  const w = (o, s) => [...s].forEach((c, i) => out.setUint8(o + i, c.charCodeAt(0)));
  w(0, 'RIFF');
  out.setUint32(4, 36 + len * ch * 2, true);
  w(8, 'WAVE');
  w(12, 'fmt ');
  out.setUint32(16, 16, true);
  out.setUint16(20, 1, true);
  out.setUint16(22, ch, true);
  out.setUint32(24, buffer.sampleRate, true);
  out.setUint32(28, buffer.sampleRate * ch * 2, true);
  out.setUint16(32, ch * 2, true);
  out.setUint16(34, 16, true);
  w(36, 'data');
  out.setUint32(40, len * ch * 2, true);
  const chans = [...Array(ch)].map((_, c) => buffer.getChannelData(c));
  let o = 44;
  for (let i = 0; i < len; i++)
    for (let c = 0; c < ch; c++) {
      const s = Math.max(-1, Math.min(1, chans[c][i]));
      out.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true);
      o += 2;
    }
  return new Blob([out.buffer], { type: 'audio/wav' });
}
