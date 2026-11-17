import { useState } from 'react';
import { useStore } from '../store.jsx';
import { STATUSES } from '../lib/db.js';
import { StatusChip, DemoBadge, CategoryChip, Thumb, Seg, fmtDate, fmtSecs } from './common.jsx';
import { go } from '../nav.js';

export default function Panel() {
  const { projects, updateProject, notify } = useStore();
  const [filter, setFilter] = useState('todos');
  const counts = Object.fromEntries(Object.keys(STATUSES).map((k) => [k, projects.filter((p) => p.status === k).length]));
  const list = projects.filter((p) => filter === 'todos' || p.status === filter);
  const hasReal = projects.some((p) => !p.demo);

  return (
    <div>
      {!hasReal && (
        <div className="hero">
          <h2>Crea tu primer vídeo 🎬</h2>
          <p className="sub" style={{ marginBottom: 6 }}>
            Todo funciona en tu iPhone, gratis y sin cuentas.
          </p>
          <ol className="steps">
            <li>
              <b>Guiones:</b> elige un tema y pulsa «Generar guion».
            </li>
            <li>
              <b>Producir:</b> pulsa «Generar vídeo» (voz española, subtítulos y música incluidos).
            </li>
            <li>
              <b>Aprobar y publicar:</b> revisa el vídeo, apruébalo y copia los textos para cada red.
            </li>
          </ol>
          <button className="btn primary block" onClick={() => go('guiones')}>
            Empezar ahora
          </button>
        </div>
      )}

      <a className="card" href="#/3d" style={{ display: 'block', textDecoration: 'none', color: 'inherit', borderColor: '#2d2766' }}>
        <div className="row between">
          <b>🎮 Simulaciones 3D</b>
          <span className="chip badge-real">NUEVO</span>
        </div>
        <span className="small muted">Carreras de superdeportivos en 3D real (Blender). Escribe una idea y recibe el vídeo.</span>
      </a>

      <div className="stats">
        {Object.entries(STATUSES).map(([k, s]) => (
          <button key={k} className="stat" style={{ borderColor: filter === k ? s.color : undefined }} onClick={() => setFilter(filter === k ? 'todos' : k)}>
            <b style={{ color: s.color }}>{counts[k]}</b>
            <span>{s.label}</span>
          </button>
        ))}
      </div>

      <div className="row between" style={{ marginBottom: 8 }}>
        <h2>Proyectos</h2>
        <button className="btn sm primary" onClick={() => go('guiones')}>
          ＋ Nuevo
        </button>
      </div>
      <div style={{ marginBottom: 12 }}>
        <Seg
          value={filter}
          onChange={setFilter}
          options={[
            ['todos', 'Todos'],
            ['pendiente', 'Pend.'],
            ['produciendo', 'Prod.'],
            ['listo', 'Listos'],
            ['aprobado', 'Aprob.'],
          ]}
        />
      </div>

      {list.length === 0 && <p className="muted">No hay proyectos en este estado.</p>}
      {list.map((p) => (
        <div className="card" key={p.id}>
          <div className="proj">
            <a href={`#/proyecto/${p.id}`}>
              <Thumb project={p} />
            </a>
            <div className="grow">
              <div className="row">
                <StatusChip status={p.status} />
                <DemoBadge demo={p.demo} />
              </div>
              <h3>{p.title}</h3>
              <div className="row small muted" style={{ marginBottom: 8 }}>
                <CategoryChip category={p.category} />
                {p.video ? <span>🎞️ {fmtSecs(p.video.duration)}</span> : <span>Sin vídeo</span>}
                {p.scheduledDate && <span>🗓️ {fmtDate(p.scheduledDate)}</span>}
              </div>
              <div className="row">
                <a className="btn sm" href={`#/proyecto/${p.id}`}>
                  Ver
                </a>
                {p.status !== 'aprobado' && (
                  <a className="btn sm" href={`#/guiones/${p.id}`}>
                    ✏️ Modificar
                  </a>
                )}
                {!p.video && (
                  <a className="btn sm primary" href={`#/producir/${p.id}`}>
                    🎬 Producir
                  </a>
                )}
                {p.status === 'listo' && (
                  <button
                    className="btn sm ok"
                    onClick={() => {
                      updateProject(p.id, { status: 'aprobado', approvedAt: new Date().toISOString() });
                      notify('Vídeo aprobado ✅');
                    }}
                  >
                    ✔ Aprobar
                  </button>
                )}
                {p.status === 'aprobado' && (
                  <a className="btn sm primary" href={`#/publicar/${p.id}`}>
                    🚀 Publicar
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}

      <div className="card soft small">
        <h3>¿Qué es real y qué es demostración?</h3>
        <p className="muted" style={{ margin: 0 }}>
          <span className="chip badge-real">REAL</span> Generar guiones, voz, vídeos MP4, calendario y textos funciona de verdad en tu teléfono.{' '}
          <span className="chip badge-demo">DEMO</span> Los proyectos marcados como DEMO son ejemplos para que veas cómo funciona; puedes producirlos o borrarlos en Ajustes. La
          publicación automática <b>no está activada</b>: necesita integraciones oficiales y tu aprobación.
        </p>
      </div>
    </div>
  );
}
