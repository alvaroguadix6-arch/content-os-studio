import { useEffect, useState } from 'react';
import { useStore } from '../store.jsx';
import { CATEGORIES, TOPICS, getTopic } from '../lib/content.js';
import { generateScript, scriptFromText, estimateSeconds, countWords } from '../lib/scriptgen.js';
import { generateWithClaude } from '../lib/ai.js';
import { Seg } from './common.jsx';
import { go } from '../nav.js';

const KINDS = ['gancho', 'contexto', 'desarrollo', 'giro', 'cierre'];

export default function Scripts({ editId }) {
  const store = useStore();
  const editing = editId ? store.projects.find((p) => p.id === editId) : null;
  const [mode, setMode] = useState('biblioteca');
  const [category, setCategory] = useState('misterios');
  const [topicId, setTopicId] = useState(TOPICS.find((t) => t.category === 'misterios').id);
  const [duration, setDuration] = useState(45);
  const [draft, setDraft] = useState(null);
  const [freeText, setFreeText] = useState('');
  const [freeTitle, setFreeTitle] = useState('');
  const [aiTopic, setAiTopic] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (editing) setDraft(JSON.parse(JSON.stringify(editing)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editId]);

  useEffect(() => {
    const pre = sessionStorage.getItem('content-os:idea');
    if (pre && !editId) {
      sessionStorage.removeItem('content-os:idea');
      const t = getTopic(pre);
      if (t) {
        setCategory(t.category);
        setTopicId(t.id);
        setDraft(generateScript({ topicId: t.id, duration }));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const topics = TOPICS.filter((t) => t.category === category);

  function generate() {
    setError('');
    setDraft(generateScript({ topicId, duration }));
  }

  async function generateAI() {
    setError('');
    setBusy(true);
    try {
      const r = await generateWithClaude({ apiKey: store.settings.anthropicApiKey, topic: aiTopic, category: CATEGORIES[category].label, duration });
      setDraft({ ...r, category, theme: CATEGORIES[category].theme, keywords: [aiTopic], targetDuration: duration });
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function fromText() {
    if (!freeText.trim()) return setError('Escribe primero el texto del guion.');
    setDraft(scriptFromText(freeText, { title: freeTitle || 'Guion propio', category }));
  }

  function updateSeg(i, patch) {
    setDraft((d) => ({ ...d, segments: d.segments.map((s, k) => (k === i ? { ...s, ...patch } : s)) }));
  }
  function removeSeg(i) {
    setDraft((d) => ({ ...d, segments: d.segments.filter((_, k) => k !== i) }));
  }
  function addSeg() {
    setDraft((d) => ({ ...d, segments: [...d.segments, { id: 's' + Date.now(), kind: 'desarrollo', text: '' }] }));
  }
  function moveSeg(i, dir) {
    setDraft((d) => {
      const s = [...d.segments];
      const j = i + dir;
      if (j < 0 || j >= s.length) return d;
      [s[i], s[j]] = [s[j], s[i]];
      return { ...d, segments: s };
    });
  }

  function save(thenProduce) {
    const clean = { ...draft, segments: draft.segments.filter((s) => s.text.trim()).map((s, i) => ({ ...s, id: s.id || `s${i + 1}` })) };
    if (!clean.segments.length) return setError('El guion está vacío.');
    if (editing) {
      store.updateProject(editing.id, { ...clean, status: 'pendiente', videoOutdated: !!editing.video });
      store.notify('Guion actualizado');
      go(thenProduce ? `producir/${editing.id}` : `proyecto/${editing.id}`);
    } else {
      const p = store.addProject({ ...clean, question: getTopic(clean.topicId)?.question });
      store.notify('Proyecto guardado');
      go(thenProduce ? `producir/${p.id}` : `proyecto/${p.id}`);
    }
  }

  const fullText = draft ? draft.segments.map((s) => s.text).join(' ') : '';
  const secs = draft ? Math.round(draft.segments.reduce((a, s) => a + estimateSeconds(s.text), 0) + draft.segments.length * 0.22 + 1.3) : 0;

  return (
    <div>
      <h2>{editing ? 'Modificar guion' : 'Guiones'}</h2>
      <p className="sub">Guiones en español de 30 a 60 segundos: misterios, curiosidades, ciencia, simulaciones e historias.</p>

      {!editing && (
        <div className="card">
          <div style={{ marginBottom: 12 }}>
            <Seg
              value={mode}
              onChange={setMode}
              options={[
                ['biblioteca', '📚 Biblioteca'],
                ['propio', '✍️ Mi texto'],
                ['ia', '🤖 IA'],
              ]}
            />
          </div>
          <label className="field">
            <span>Categoría</span>
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setTopicId(TOPICS.find((t) => t.category === e.target.value).id);
              }}
            >
              {Object.entries(CATEGORIES).map(([k, c]) => (
                <option key={k} value={k}>
                  {c.emoji} {c.label}
                </option>
              ))}
            </select>
          </label>

          {mode !== 'propio' && (
            <label className="field">
              <span>Duración objetivo</span>
              <Seg
                value={duration}
                onChange={setDuration}
                options={[
                  [30, '30 s'],
                  [45, '45 s'],
                  [60, '60 s'],
                ]}
              />
            </label>
          )}

          {mode === 'biblioteca' && (
            <>
              <label className="field">
                <span>Tema ({topics.length} disponibles, con fuente verificable)</span>
                <select value={topicId} onChange={(e) => setTopicId(e.target.value)}>
                  {topics.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.title}
                    </option>
                  ))}
                </select>
              </label>
              <button className="btn primary block" onClick={generate}>
                ✨ Generar guion (gratis)
              </button>
            </>
          )}

          {mode === 'propio' && (
            <>
              <label className="field">
                <span>Título</span>
                <input type="text" value={freeTitle} onChange={(e) => setFreeTitle(e.target.value)} placeholder="Ej.: El faro que nadie apagó" />
              </label>
              <label className="field">
                <span>Tu guion (se divide en escenas por frases)</span>
                <textarea style={{ minHeight: 160 }} value={freeText} onChange={(e) => setFreeText(e.target.value)} placeholder="Escribe o pega aquí tu texto…" />
              </label>
              <div className="small muted" style={{ marginBottom: 10 }}>
                {countWords(freeText)} palabras · ≈ {Math.round(estimateSeconds(freeText))} s
              </div>
              <button className="btn primary block" onClick={fromText}>
                Preparar escenas
              </button>
            </>
          )}

          {mode === 'ia' && (
            <>
              <div className="notice warn">
                <span className="chip badge-paid">DE PAGO · OPCIONAL</span> Escribe sobre cualquier tema usando la API de Claude. Necesita tu propia clave de Anthropic (Ajustes)
                y cada guion cuesta unos céntimos. Sin clave, usa la Biblioteca (gratis).
              </div>
              <label className="field">
                <span>Tema</span>
                <input type="text" value={aiTopic} onChange={(e) => setAiTopic(e.target.value)} placeholder="Ej.: El misterio de la isla de Pascua" />
              </label>
              <button className="btn primary block" disabled={!store.settings.anthropicApiKey || !aiTopic || busy} onClick={generateAI}>
                {busy ? 'Escribiendo…' : '🤖 Generar con IA'}
              </button>
              {!store.settings.anthropicApiKey && (
                <p className="small muted">
                  No hay clave configurada. <a href="#/ajustes">Ir a Ajustes</a>
                </p>
              )}
            </>
          )}
          {error && <div className="notice bad" style={{ marginTop: 12 }}>{error}</div>}
        </div>
      )}

      {draft && (
        <div className="card">
          <label className="field">
            <span>Título del vídeo</span>
            <input type="text" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
          </label>
          <div className="row between small" style={{ marginBottom: 10 }}>
            <span className="muted">
              {countWords(fullText)} palabras · duración estimada <b style={{ color: secs > 62 ? 'var(--warn)' : 'var(--text)' }}>≈ {secs} s</b>
            </span>
            <span className="chip">{draft.generator === 'ia-claude' ? '🤖 IA' : draft.generator === 'manual' ? '✍️ Propio' : '📚 Biblioteca'}</span>
          </div>
          {secs > 62 && <div className="notice warn">Pasa de 60 s. Acorta alguna escena para Shorts.</div>}

          {draft.segments.map((s, i) => (
            <div className="segment" key={s.id || i}>
              <div className="row between">
                <select className="kind" style={{ width: 'auto', padding: '4px 8px', fontSize: 12 }} value={s.kind} onChange={(e) => updateSeg(i, { kind: e.target.value })}>
                  {KINDS.map((k) => (
                    <option key={k}>{k}</option>
                  ))}
                </select>
                <div className="row">
                  <span className="tiny muted">≈ {estimateSeconds(s.text)} s</span>
                  <button className="btn sm ghost" onClick={() => moveSeg(i, -1)} aria-label="Subir">
                    ↑
                  </button>
                  <button className="btn sm ghost" onClick={() => moveSeg(i, 1)} aria-label="Bajar">
                    ↓
                  </button>
                  <button className="btn sm ghost" onClick={() => removeSeg(i)} aria-label="Borrar">
                    🗑
                  </button>
                </div>
              </div>
              <textarea value={s.text} onChange={(e) => updateSeg(i, { text: e.target.value })} />
            </div>
          ))}
          <button className="btn sm" onClick={addSeg}>
            ＋ Añadir escena
          </button>

          {draft.source && (
            <div className="notice info" style={{ marginTop: 12 }}>
              🔎 <b>Verifica antes de publicar:</b>{' '}
              {draft.source.split('\n').map((src) => (
                <a key={src} href={src} target="_blank" rel="noreferrer" style={{ display: 'block', wordBreak: 'break-all' }}>
                  {src}
                </a>
              ))}
            </div>
          )}
          {draft.uncertain?.length > 0 && (
            <div className="notice warn">
              <b>La IA recomienda comprobar:</b>
              <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
                {draft.uncertain.map((u) => (
                  <li key={u}>{u}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="stack" style={{ marginTop: 12 }}>
            <button className="btn primary block" onClick={() => save(true)}>
              🎬 Guardar y producir vídeo
            </button>
            <div className="row">
              <button className="btn grow" onClick={() => save(false)}>
                💾 Guardar
              </button>
              {!editing && draft.generator === 'plantilla' && (
                <button className="btn grow" onClick={generate}>
                  🔄 Otra versión
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
