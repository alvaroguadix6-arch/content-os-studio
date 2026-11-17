import { useStore } from '../store.jsx';
import { STATUSES } from '../lib/db.js';
import { StatusChip, DemoBadge } from './common.jsx';

export const MAX_SLOTS = 7;

export function nextDays(n = 7, from = new Date()) {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(from);
    d.setDate(d.getDate() + i);
    return d.toISOString().slice(0, 10);
  });
}

export default function Calendar() {
  const { projects, updateProject, notify } = useStore();
  const days = nextDays(MAX_SLOTS);
  const byDay = Object.fromEntries(days.map((d) => [d, projects.find((p) => p.scheduledDate === d)]));
  const unscheduled = projects.filter((p) => !p.scheduledDate || !days.includes(p.scheduledDate));

  function assign(day, id) {
    const current = byDay[day];
    if (current) updateProject(current.id, { scheduledDate: null });
    if (id) updateProject(id, { scheduledDate: day });
    notify(id ? 'Programado en el calendario' : 'Hueco liberado');
  }

  return (
    <div>
      <h2>Calendario</h2>
      <p className="sub">Organiza hasta 7 vídeos para los próximos 7 días (uno por día). Cambia el estado de cada uno según avanza.</p>
      <div className="row small" style={{ marginBottom: 12 }}>
        {Object.entries(STATUSES).map(([k]) => (
          <StatusChip key={k} status={k} />
        ))}
      </div>
      <div className="days">
        {days.map((d) => {
          const p = byDay[d];
          const date = new Date(d + 'T12:00:00');
          return (
            <div className="day" key={d}>
              <div className="date">
                <span>{date.toLocaleDateString('es-ES', { weekday: 'short' })}</span>
                <b>{date.getDate()}</b>
                <span>{date.toLocaleDateString('es-ES', { month: 'short' })}</span>
              </div>
              <div>
                {p ? (
                  <>
                    <div className="row between">
                      <a href={`#/proyecto/${p.id}`} style={{ color: 'inherit', fontWeight: 700, textDecoration: 'none' }} className="grow">
                        {p.title}
                      </a>
                      <DemoBadge demo={p.demo} />
                    </div>
                    <div className="row" style={{ marginTop: 6 }}>
                      <select
                        style={{ width: 'auto', padding: '6px 8px', fontSize: 14 }}
                        value={p.status}
                        onChange={(e) => {
                          if (e.target.value === 'aprobado' && !p.video) return notify('Primero produce el vídeo', 'bad');
                          updateProject(p.id, { status: e.target.value });
                        }}
                        aria-label="Estado"
                      >
                        {Object.entries(STATUSES).map(([k, s]) => (
                          <option key={k} value={k}>
                            {s.label}
                          </option>
                        ))}
                      </select>
                      <button className="btn sm ghost" onClick={() => assign(d, null)}>
                        Quitar
                      </button>
                    </div>
                  </>
                ) : (
                  <select value="" onChange={(e) => assign(d, e.target.value)} style={{ fontSize: 14 }} aria-label="Asignar proyecto">
                    <option value="">＋ Asignar un proyecto…</option>
                    {unscheduled.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.title} ({STATUSES[u.status].label})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>
          );
        })}
      </div>
      {unscheduled.length > 0 && <p className="small muted" style={{ marginTop: 12 }}>{unscheduled.length} proyecto(s) sin fecha en esta semana.</p>}
    </div>
  );
}
