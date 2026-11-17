import { useStore } from '../store.jsx';
import { STATUSES, getBlob } from '../lib/db.js';
import { StatusChip, DemoBadge, CategoryChip, useBlobUrl, fmtDate } from './common.jsx';
import { shareOrDownload, slug } from './Produce.jsx';
import { go } from '../nav.js';

export default function ProjectView({ projectId }) {
  const store = useStore();
  const p = store.projects.find((x) => x.id === projectId);
  const videoUrl = useBlobUrl(p?.video?.key);
  if (!p) return <p className="muted">Proyecto no encontrado. <a href="#/panel">Volver</a></p>;

  return (
    <div>
      <div className="row">
        <StatusChip status={p.status} />
        <DemoBadge demo={p.demo} />
        <CategoryChip category={p.category} />
      </div>
      <h2 style={{ marginTop: 8 }}>{p.title}</h2>
      <p className="sub">
        Creado {fmtDate(p.createdAt)}
        {p.scheduledDate && <> · programado {fmtDate(p.scheduledDate)}</>}
      </p>

      <div className="card">
        <h3>Vista previa</h3>
        {p.video ? (
          <>
            <div className="video-wrap">{videoUrl && <video key={p.video.rev} src={videoUrl} controls playsInline preload="metadata" />}</div>
            {p.videoOutdated && <div className="notice warn">El guion cambió después de producir este vídeo. Vuelve a generarlo.</div>}
          </>
        ) : (
          <p className="muted">Todavía no hay vídeo. Pulsa «Producir».</p>
        )}
        <div className="row">
          {p.status === 'listo' && (
            <button
              className="btn ok grow"
              onClick={() => {
                store.updateProject(p.id, { status: 'aprobado', approvedAt: new Date().toISOString() });
                store.notify('Vídeo aprobado ✅');
              }}
            >
              ✔ Aprobar
            </button>
          )}
          <a className="btn grow" href={`#/guiones/${p.id}`}>
            ✏️ Modificar
          </a>
          <a className="btn grow primary" href={`#/producir/${p.id}`}>
            🎬 {p.video ? 'Rehacer' : 'Producir'}
          </a>
        </div>
        {p.video && (
          <div className="row" style={{ marginTop: 8 }}>
            <button className="btn grow" onClick={async () => shareOrDownload(await getBlob(p.video.key), `${slug(p.title)}.${p.video.ext}`, store.notify)}>
              ⬇️ Guardar / compartir
            </button>
            <a className="btn grow" href={`#/publicar/${p.id}`}>
              🚀 Textos para redes
            </a>
          </div>
        )}
      </div>

      <div className="card">
        <h3>Estado</h3>
        <select
          value={p.status}
          onChange={(e) => {
            if (e.target.value === 'aprobado' && !p.video) return store.notify('Primero produce el vídeo', 'bad');
            store.updateProject(p.id, { status: e.target.value });
          }}
        >
          {Object.entries(STATUSES).map(([k, s]) => (
            <option key={k} value={k}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      <div className="card">
        <h3>Guion</h3>
        {p.segments.map((s) => (
          <p key={s.id} style={{ margin: '0 0 8px' }}>
            <span className="kind tiny" style={{ color: 'var(--accent2)', fontWeight: 800, textTransform: 'uppercase' }}>
              {s.kind}
            </span>
            <br />
            {s.text}
          </p>
        ))}
        {p.source && (
          <p className="small">
            🔎 Fuente para verificar:{' '}
            {p.source.split('\n').map((src) => (
              <a key={src} href={src} target="_blank" rel="noreferrer" style={{ wordBreak: 'break-all', display: 'block' }}>
                {src}
              </a>
            ))}
          </p>
        )}
      </div>

      <button
        className="btn danger block"
        onClick={async () => {
          if (confirm('¿Borrar este proyecto y su vídeo? No se puede deshacer.')) {
            await store.removeProject(p.id);
            go('panel');
          }
        }}
      >
        Borrar proyecto
      </button>
    </div>
  );
}
