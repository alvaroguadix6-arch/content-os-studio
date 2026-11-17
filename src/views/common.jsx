import { useEffect, useState } from 'react';
import { STATUSES, getBlob } from '../lib/db.js';
import { CATEGORIES } from '../lib/content.js';

export function StatusChip({ status }) {
  const s = STATUSES[status] || STATUSES.pendiente;
  return (
    <span className="chip">
      <span className="dot" style={{ background: s.color }} />
      {s.label}
    </span>
  );
}

export function DemoBadge({ demo }) {
  return demo ? <span className="chip badge-demo">DEMO</span> : null;
}

export function CategoryChip({ category }) {
  const c = CATEGORIES[category];
  return c ? (
    <span className="chip">
      {c.emoji} {c.label}
    </span>
  ) : null;
}

/** Devuelve una URL temporal para un Blob guardado en el teléfono. */
export function useBlobUrl(key) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    let u = null;
    let alive = true;
    if (!key) {
      setUrl(null);
      return;
    }
    getBlob(key).then((b) => {
      if (b && alive) {
        u = URL.createObjectURL(b);
        setUrl(u);
      }
    });
    return () => {
      alive = false;
      if (u) URL.revokeObjectURL(u);
    };
  }, [key]);
  return url;
}

export function Thumb({ project }) {
  const url = useBlobUrl(project.thumbKey);
  return <div className="thumb">{url ? <img src={url} alt="" /> : CATEGORIES[project.category]?.emoji || '🎬'}</div>;
}

export function Seg({ value, onChange, options }) {
  return (
    <div className="seg">
      {options.map(([v, label]) => (
        <button key={v} type="button" className={value === v ? 'on' : ''} onClick={() => onChange(v)}>
          {label}
        </button>
      ))}
    </div>
  );
}

export async function copyText(text, notify) {
  try {
    await navigator.clipboard.writeText(text);
    notify?.('Copiado ✅');
  } catch {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    notify?.('Copiado ✅');
  }
}

export function fmtDate(iso) {
  if (!iso) return '';
  const d = new Date(iso.length === 10 ? iso + 'T12:00:00' : iso);
  return d.toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric', month: 'short' });
}

export function fmtSecs(s) {
  if (s == null) return '';
  return `${Math.round(s)} s`;
}
