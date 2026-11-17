import { useState } from 'react';
import { useStore } from '../store.jsx';
import { fetchVideoData, analyzeText, suggestIdeas, detectPlatform } from '../lib/trends.js';
import { go } from '../nav.js';

const PLATFORM = { youtube: '▶️ YouTube', tiktok: '🎵 TikTok', instagram: '📸 Instagram' };

export default function Trends() {
  const store = useStore();
  const [url, setUrl] = useState('');
  const [manual, setManual] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function analyze() {
    setError('');
    const det = detectPlatform(url);
    if (!det.platform) return setError(det.error);
    setBusy(true);
    try {
      const data = await fetchVideoData(url, { youtubeApiKey: store.settings.youtubeApiKey });
      const text = [data.title, manual].filter(Boolean).join('\n');
      const analysis = analyzeText(text);
      const ideas = suggestIdeas(text, analysis.patterns);
      const entry = { id: Date.now().toString(36), data, manualText: manual, analysis, ideas };
      store.setTrends([entry, ...store.trends].slice(0, 30));
      setUrl('');
      setManual('');
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h2>Tendencias</h2>
      <p className="sub">Pega enlaces de vídeos que funcionan. Content-OS lee solo los datos reales que la plataforma ofrece públicamente y te propone ideas originales.</p>

      <div className="card">
        <label className="field">
          <span>Enlace de TikTok, Instagram Reels o YouTube Shorts</span>
          <input type="url" inputMode="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://www.tiktok.com/@usuario/video/…" />
        </label>
        <label className="field">
          <span>Texto del vídeo (opcional: pega aquí la descripción o lo que dice el gancho)</span>
          <textarea value={manual} onChange={(e) => setManual(e.target.value)} placeholder="Opcional. Útil para Instagram, que no deja leer datos sin integración oficial." />
        </label>
        <button className="btn primary block" disabled={!url || busy} onClick={analyze}>
          {busy ? 'Analizando…' : '🔍 Analizar'}
        </button>
        {error && <div className="notice bad" style={{ marginTop: 10 }}>{error}</div>}
        <p className="tiny muted" style={{ marginTop: 10 }}>
          Nunca se inventan visualizaciones ni estadísticas. Si un dato no está disponible, se indica.
        </p>
      </div>

      {store.trends.map((t) => (
        <TrendCard key={t.id} t={t} onRemove={() => store.setTrends(store.trends.filter((x) => x.id !== t.id))} />
      ))}
    </div>
  );
}

function TrendCard({ t, onRemove }) {
  const { data, analysis, ideas } = t;
  return (
    <div className="card">
      <div className="row between">
        <span className="chip">{PLATFORM[data.platform]}</span>
        <button className="btn sm ghost" onClick={onRemove}>
          ✕
        </button>
      </div>
      <div className="row" style={{ alignItems: 'flex-start', marginTop: 10 }}>
        {data.thumbnail && <img src={data.thumbnail} alt="" style={{ width: 72, height: 96, objectFit: 'cover', borderRadius: 10 }} />}
        <div className="grow">
          <b>{data.title || 'Título no disponible'}</b>
          <div className="small muted">{data.author ? `por ${data.author}` : ''}</div>
          <a className="tiny" href={data.url} target="_blank" rel="noreferrer">
            Abrir vídeo original
          </a>
        </div>
      </div>

      <h3 style={{ marginTop: 12 }}>Datos reales</h3>
      {data.stats ? (
        <>
          <dl className="kv">
            <dt>Visualizaciones</dt>
            <dd>{data.stats.views?.toLocaleString('es-ES') ?? '—'}</dd>
            <dt>Me gusta</dt>
            <dd>{data.stats.likes?.toLocaleString('es-ES') ?? 'oculto por el autor'}</dd>
            <dt>Comentarios</dt>
            <dd>{data.stats.comments?.toLocaleString('es-ES') ?? '—'}</dd>
          </dl>
          <p className="tiny muted">
            Fuente: {data.statsSource} · {new Date(data.fetchedAt).toLocaleString('es-ES')}
          </p>
        </>
      ) : (
        <p className="small muted">Estadísticas no disponibles para este enlace.</p>
      )}
      <ul className="tiny muted" style={{ paddingLeft: 18 }}>
        {data.notes.map((n) => (
          <li key={n}>{n}</li>
        ))}
      </ul>

      <h3>Gancho y formato</h3>
      {analysis.patterns.length ? (
        <div className="stack">
          {analysis.patterns.map((p) => (
            <div key={p.id} className="small">
              <span className="chip">{p.label}</span> <span className="muted">{p.tip}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="small muted">No se detectó un patrón de gancho claro en el texto disponible.</p>
      )}
      <p className="small muted">
        {analysis.lengthLabel} · {analysis.emojis} emojis · {analysis.hashtags.length} hashtags {analysis.hashtags.slice(0, 6).join(' ')}
      </p>

      <h3>Ideas originales para ti</h3>
      {ideas.map((idea) => (
        <div key={idea.topicId} className="segment">
          <div className="kind">{idea.category}</div>
          <b>{idea.title}</b>
          <div className="small muted">
            {idea.angle}: «{idea.hook}»
          </div>
          <button
            className="btn sm primary"
            style={{ marginTop: 6 }}
            onClick={() => {
              sessionStorage.setItem('content-os:idea', idea.topicId);
              go('guiones');
            }}
          >
            ✍️ Crear guion
          </button>
        </div>
      ))}
    </div>
  );
}
