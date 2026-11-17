import { useStore } from '../store.jsx';
import { buildPublication } from '../lib/publish.js';
import { getBlob } from '../lib/db.js';
import { copyText, StatusChip, Thumb, DemoBadge } from './common.jsx';
import { shareOrDownload, slug } from './Produce.jsx';

const INTEGRATIONS = [
  {
    id: 'tiktok',
    name: 'TikTok',
    need: 'App en TikTok for Developers con la «Content Posting API» aprobada por TikTok (revisión de la app) e inicio de sesión OAuth con tu cuenta.',
  },
  {
    id: 'instagram',
    name: 'Instagram Reels',
    need: 'Cuenta profesional (Business/Creator) vinculada a una página de Facebook, app de Meta con permiso instagram_content_publish aprobado y un servidor que aloje el vídeo con URL pública.',
  },
  {
    id: 'youtube',
    name: 'YouTube Shorts',
    need: 'Proyecto en Google Cloud con YouTube Data API v3, pantalla de consentimiento OAuth verificada por Google y autorización de tu canal.',
  },
];

export default function Publish({ projectId }) {
  const store = useStore();
  const project = store.projects.find((p) => p.id === projectId);
  if (!project) return <Pick projects={store.projects} />;
  const pub = buildPublication(project);
  const { notify, updateProject } = store;
  const marks = project.publishedManually || {};

  return (
    <div>
      <div className="row between">
        <h2 className="grow">Publicar</h2>
        <StatusChip status={project.status} />
      </div>
      <p className="sub">{project.title}</p>

      {project.status !== 'aprobado' && (
        <div className="notice warn">
          Este vídeo aún no está <b>aprobado</b>. Puedes preparar los textos, pero revisa y aprueba el vídeo antes de publicarlo.
        </div>
      )}
      <div className="notice info">
        🔒 <b>Publicación automática desactivada.</b> Content-OS no publica nada por su cuenta. Copia los textos y comparte el vídeo con la app de cada red (botón
        «Compartir vídeo»).
      </div>

      {project.video && (
        <button className="btn primary block" style={{ marginBottom: 12 }} onClick={async () => shareOrDownload(await getBlob(project.video.key), `${slug(project.title)}.${project.video.ext}`, notify)}>
          📤 Compartir vídeo (TikTok, Instagram, YouTube, Fotos…)
        </button>
      )}

      <Block title="🎵 TikTok" items={[['Descripción', pub.tiktok.caption]]} notify={notify} />
      <Block title="📸 Instagram Reels" items={[['Descripción', pub.instagram.caption]]} notify={notify} />
      <Block
        title="▶️ YouTube Shorts"
        items={[
          ['Título', pub.youtube.title],
          ['Descripción', pub.youtube.description],
        ]}
        notify={notify}
      />

      <div className="card">
        <h3>Registro de publicación manual</h3>
        <p className="small muted">Marca dónde lo has publicado tú mismo, para llevar el control.</p>
        {INTEGRATIONS.map((i) => (
          <label key={i.id} className="row small" style={{ marginBottom: 8 }}>
            <input
              type="checkbox"
              checked={!!marks[i.id]}
              onChange={(e) => updateProject(project.id, { publishedManually: { ...marks, [i.id]: e.target.checked ? new Date().toISOString() : null } })}
            />
            Publicado en {i.name}
            {marks[i.id] && <span className="muted">· {new Date(marks[i.id]).toLocaleDateString('es-ES')}</span>}
          </label>
        ))}
      </div>

      <div className="card">
        <h3>Integraciones oficiales (publicación automática)</h3>
        <p className="small muted">Estado actual: ninguna configurada. Para activarlas hace falta lo siguiente, y siempre con tu aprobación antes de cada publicación:</p>
        {INTEGRATIONS.map((i) => (
          <div key={i.id} className="segment">
            <div className="row between">
              <b>{i.name}</b>
              <span className="chip">⛔ No configurada</span>
            </div>
            <p className="small muted" style={{ margin: '6px 0 0' }}>
              {i.need}
            </p>
          </div>
        ))}
        <p className="tiny muted">Estas integraciones son gratuitas en sí, pero requieren registros como desarrollador, revisiones de las plataformas y un pequeño servidor seguro para guardar los permisos (no se pueden guardar claves en GitHub).</p>
      </div>
    </div>
  );
}

function Block({ title, items, notify }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {items.map(([label, text]) => (
        <div key={label} style={{ marginBottom: 10 }}>
          <div className="row between" style={{ marginBottom: 4 }}>
            <span className="small muted">
              {label} · {text.length} caracteres
            </span>
            <button className="btn sm" onClick={() => copyText(text, notify)}>
              📋 Copiar
            </button>
          </div>
          <div className="copybox">{text}</div>
        </div>
      ))}
    </div>
  );
}

function Pick({ projects }) {
  const list = [...projects].sort((a, b) => (a.status === 'aprobado' ? -1 : 1) - (b.status === 'aprobado' ? -1 : 1));
  return (
    <div>
      <h2>Publicar</h2>
      <p className="sub">Elige un proyecto para preparar títulos, descripciones y hashtags para TikTok, Instagram y YouTube.</p>
      {list.map((p) => (
        <a key={p.id} className="card proj" href={`#/publicar/${p.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'grid' }}>
          <Thumb project={p} />
          <div>
            <div className="row">
              <StatusChip status={p.status} />
              <DemoBadge demo={p.demo} />
            </div>
            <h3>{p.title}</h3>
          </div>
        </a>
      ))}
    </div>
  );
}
