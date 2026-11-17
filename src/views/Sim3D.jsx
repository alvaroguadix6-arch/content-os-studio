import { useEffect, useState } from 'react';
import { useStore } from '../store.jsx';
import { TEMPLATES_3D, QUALITY, ideaToSpec, jobFileName } from '../lib/idea3d.js';
import { submitJob, listRenderRuns, listVideoReleases, runLabel, getRepoInfo } from '../lib/github.js';
import { Seg } from './common.jsx';

const EXAMPLES = [
  'Carrera entre un Ferrari rojo y un Lamborghini amarillo, con adelantamientos y final de infarto. Gana el rojo.',
  'Duelo entre un superdeportivo azul y uno naranja; gana el naranja en el último segundo.',
  'Un coche negro contra uno blanco en un circuito junto a la ciudad.',
];

// En GitHub Pages la dirección es https://USUARIO.github.io/REPOSITORIO/ → deducimos el repositorio.
function detectRepo() {
  const { hostname, pathname } = window.location;
  const m = hostname.match(/^([^.]+)\.github\.io$/);
  const seg = pathname.split('/').filter(Boolean)[0];
  return m && seg ? `${m[1]}/${seg}` : '';
}

export default function Sim3D() {
  const store = useStore();
  const { settings, setSettings, notify } = store;
  const [template, setTemplate] = useState('carrera');
  const [idea, setIdea] = useState(EXAMPLES[0]);
  const [quality, setQuality] = useState('normal');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [runs, setRuns] = useState([]);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showToken, setShowToken] = useState(false);
  const [info, setInfo] = useState(null);
  const approved = settings.approved3d || {};
  const repo = settings.ghRepo || detectRepo();
  const branch = settings.ghBranch || 'main';
  const parsed = ideaToSpec(idea, { template, quality });

  async function refresh() {
    if (!repo) return;
    setLoading(true);
    setError('');
    try {
      const inf = await getRepoInfo({ token: settings.ghToken, repo });
      setInfo(inf);
      const [r, v] = await Promise.all([
        settings.ghToken ? listRenderRuns({ token: settings.ghToken, repo }) : Promise.resolve([]),
        listVideoReleases({ token: settings.ghToken, repo }),
      ]);
      setRuns(r);
      setVideos(v);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 60000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.ghToken, repo]);

  async function send() {
    setError('');
    if (!settings.ghToken) return setError('Primero conecta GitHub (más abajo).');
    setBusy(true);
    try {
      const path = jobFileName(parsed.spec);
      await submitJob({ token: settings.ghToken, repo, branch, path, spec: parsed.spec });
      notify('Encargo enviado. El render empieza en 1-2 minutos 🎬');
      setTimeout(refresh, 8000);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h2>Simulaciones 3D</h2>
      <p className="sub">Vídeos 3D reales renderizados con Blender (trazado de rayos) en servidores gratuitos de GitHub. 1080×1920, 30–60 s, con voz, música, efectos, HUD y subtítulos.</p>

      <div className="card">
        <h3>1 · Tipo de vídeo</h3>
        <div className="stack">
          {Object.entries(TEMPLATES_3D).map(([id, t]) => (
            <button
              key={id}
              className="segment"
              style={{ width: '100%', textAlign: 'left', borderColor: template === id ? 'var(--accent)' : undefined, opacity: t.ready ? 1 : 0.55 }}
              onClick={() => t.ready && setTemplate(id)}
              disabled={!t.ready}
            >
              <div className="row between">
                <b>
                  {t.emoji} {t.label}
                </b>
                {t.ready ? <span className="chip badge-real">DISPONIBLE</span> : <span className="chip">PRÓXIMAMENTE</span>}
              </div>
              <div className="small muted">{t.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>2 · Tu idea</h3>
        <textarea value={idea} onChange={(e) => setIdea(e.target.value)} style={{ minHeight: 100 }} />
        <div className="row" style={{ margin: '8px 0' }}>
          {EXAMPLES.map((ex, i) => (
            <button key={i} className="btn sm ghost" onClick={() => setIdea(ex)}>
              Ejemplo {i + 1}
            </button>
          ))}
        </div>
        <div className="notice info small">
          <b>Lo que se va a renderizar:</b>
          <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
            {parsed.understood.map((u) => (
              <li key={u}>{u}</li>
            ))}
            <li>Título: {parsed.spec.title}</li>
          </ul>
          {parsed.notes.map((n) => (
            <div key={n} style={{ marginTop: 6 }}>
              ⚠️ {n}
            </div>
          ))}
        </div>
        <label className="field">
          <span>Calidad</span>
          <Seg value={quality} onChange={setQuality} options={Object.entries(QUALITY).map(([k, q]) => [k, q.label])} />
        </label>
        {error && <div className="notice bad">{error}</div>}
        <button className="btn primary block" style={{ minHeight: 52 }} disabled={busy} onClick={send}>
          {busy ? 'Enviando…' : '🎬 Enviar a renderizar (gratis)'}
        </button>
        {info?.private && (
          <div className="notice warn small" style={{ marginTop: 10 }}>
            Tu repositorio es <b>privado</b>: GitHub regala 2.000 minutos de Actions al mes y cada vídeo de ~45 s consume unos 600–900 minutos (≈2 vídeos al mes). Si se agotan, los renders se paran hasta el mes siguiente; <b>no se cobra nada</b> salvo que tú añadas un método de pago. Si haces el repositorio público, los minutos son ilimitados.
          </div>
        )}
        <p className="tiny muted" style={{ marginTop: 8 }}>
          Se reparte entre 20 servidores de GitHub Actions. No necesitas tener el iPhone abierto: vuelve más tarde y el vídeo aparecerá abajo.
        </p>
      </div>

      <div className="card">
        <div className="row between">
          <h3>3 · Renders y vídeos</h3>
          <button className="btn sm" onClick={refresh} disabled={loading}>
            {loading ? '…' : '🔄'}
          </button>
        </div>
        {runs.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            {runs.slice(0, 5).map((r) => (
              <a key={r.id} href={r.url} target="_blank" rel="noreferrer" className="segment" style={{ display: 'block', textDecoration: 'none', color: 'inherit' }}>
                <div className="row between">
                  <span className="small">{r.title.slice(0, 50)}</span>
                  <span className="chip">{runLabel(r)}</span>
                </div>
                <span className="tiny muted">{new Date(r.created).toLocaleString('es-ES')}</span>
              </a>
            ))}
          </div>
        )}
        {videos.length === 0 && <p className="small muted">Todavía no hay vídeos 3D terminados.</p>}
        {videos.map((v) => (
          <div key={v.id} className="segment">
            <div className="row between">
              <b className="small">{v.title}</b>
              {approved[v.tag] ? <span className="chip badge-real">✔ Aprobado</span> : <span className="chip">Por revisar</span>}
            </div>
            {info && !info.private ? (
              <video src={v.mp4.browser_download_url} controls playsInline preload="none" style={{ width: '100%', aspectRatio: '9/16', background: '#000', borderRadius: 12, marginTop: 8 }} />
            ) : (
              <p className="small muted" style={{ margin: '8px 0' }}>
                Repositorio privado: el vídeo se ve y descarga en GitHub con tu sesión iniciada (botón de abajo).
              </p>
            )}
            <div className="row" style={{ marginTop: 8 }}>
              {!approved[v.tag] && (
                <button className="btn sm ok" onClick={() => setSettings({ approved3d: { ...approved, [v.tag]: new Date().toISOString() } })}>
                  ✔ Aprobar
                </button>
              )}
              <a className="btn sm primary" href={info && !info.private ? v.mp4.browser_download_url : v.url} target="_blank" rel="noreferrer">
                ⬇️ {info && !info.private ? 'Descargar' : 'Ver y descargar en GitHub'} MP4 ({Math.round(v.mp4.size / 1e6)} MB)
              </a>
              {v.credits && (
                <a className="btn sm ghost" href={v.url} target="_blank" rel="noreferrer">
                  Créditos
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Conexión con GitHub</h3>
        <p className="small muted">
          Necesario para enviar encargos desde el iPhone. Crea un token en GitHub → Settings → Developer settings → Fine-grained tokens, solo para el repositorio <b>{repo}</b>, con permisos <b>Contents: Read and write</b> y <b>Actions: Read-only</b>. Se guarda solo en este teléfono.
        </p>
        <label className="field">
          <span>Token</span>
          <div className="row">
            <input className="grow" type={showToken ? 'text' : 'password'} value={settings.ghToken || ''} onChange={(e) => setSettings({ ghToken: e.target.value.trim() })} placeholder="github_pat_…" autoComplete="off" />
            <button className="btn sm" onClick={() => setShowToken(!showToken)}>
              {showToken ? '🙈' : '👁'}
            </button>
          </div>
        </label>
        <div className="row">
          <label className="field grow">
            <span>Repositorio</span>
            <input type="text" value={repo} onChange={(e) => setSettings({ ghRepo: e.target.value.trim() })} />
          </label>
          <label className="field" style={{ width: 130 }}>
            <span>Rama</span>
            <input type="text" value={branch} onChange={(e) => setSettings({ ghBranch: e.target.value.trim() })} />
          </label>
        </div>
      </div>
    </div>
  );
}
