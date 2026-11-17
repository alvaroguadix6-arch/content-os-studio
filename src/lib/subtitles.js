// Subtítulos sincronizados.
// La voz se sintetiza frase a frase, así que conocemos el inicio y el final exactos
// de cada frase. Dentro de cada frase repartimos el tiempo entre palabras según su
// longitud (y añadimos pausas en comas y puntos), que es como se distribuye el habla.

const MAX_WORDS = 3;
const MAX_CHARS = 18;

function wordWeight(w) {
  let weight = w.replace(/[^\p{L}\p{N}]/gu, '').length + 1.5;
  if (/[,;:]$/.test(w)) weight += 2.5;
  if (/[.!?…]$/.test(w)) weight += 4;
  return weight;
}

/**
 * @param {Array<{text:string,start:number,end:number}>} timedSegments  tiempos en segundos
 * @returns {Array<{start:number,end:number,text:string,words:Array<{text:string,start:number,end:number}>}>}
 */
export function buildCues(timedSegments) {
  const cues = [];
  for (const seg of timedSegments) {
    const words = seg.text.trim().split(/\s+/).filter(Boolean);
    if (!words.length) continue;
    // Pequeño margen: Piper deja silencios al principio y al final de cada frase.
    const lead = Math.min(0.08, (seg.end - seg.start) * 0.05);
    const start = seg.start + lead;
    const end = Math.max(start + 0.2, seg.end - lead);
    const total = words.reduce((a, w) => a + wordWeight(w), 0);
    let t = start;
    const timed = words.map((w) => {
      const d = ((end - start) * wordWeight(w)) / total;
      const item = { text: w, start: t, end: t + d };
      t += d;
      return item;
    });
    // Agrupar en bloques cortos (estilo TikTok/Reels).
    let group = [];
    const flush = () => {
      if (!group.length) return;
      cues.push({
        start: group[0].start,
        end: group[group.length - 1].end,
        text: group.map((g) => g.text).join(' '),
        words: group,
      });
      group = [];
    };
    for (const w of timed) {
      const chars = group.map((g) => g.text).join(' ').length + w.text.length + 1;
      if (group.length >= MAX_WORDS || (group.length && chars > MAX_CHARS)) flush();
      group.push(w);
      if (/[.!?…,;:]$/.test(w.text)) flush();
    }
    flush();
  }
  return cues;
}

export function cueAt(cues, t) {
  // búsqueda binaria
  let lo = 0;
  let hi = cues.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (t < cues[mid].start) hi = mid - 1;
    else if (t >= cues[mid].end) lo = mid + 1;
    else return cues[mid];
  }
  return null;
}

function srtTime(t) {
  const ms = Math.max(0, Math.round(t * 1000));
  const h = String(Math.floor(ms / 3600000)).padStart(2, '0');
  const m = String(Math.floor((ms % 3600000) / 60000)).padStart(2, '0');
  const s = String(Math.floor((ms % 60000) / 1000)).padStart(2, '0');
  const r = String(ms % 1000).padStart(3, '0');
  return `${h}:${m}:${s},${r}`;
}

export function toSRT(cues) {
  return cues.map((c, i) => `${i + 1}\n${srtTime(c.start)} --> ${srtTime(c.end)}\n${c.text}\n`).join('\n');
}
