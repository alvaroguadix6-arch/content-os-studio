import { useEffect, useState } from 'react';
import { useStore } from '../store.jsx';
import { exportBackup, importBackup, storageEstimate, wipeAll } from '../lib/db.js';
import { deleteVoices } from '../engine/tts.js';
import { webCodecsAvailable } from '../engine/render.js';

export default function Settings() {
  const store = useStore();
  const { settings, setSettings, notify } = store;
  const [usage, setUsage] = useState(null);
  const [showYt, setShowYt] = useState(false);
  const [showAi, setShowAi] = useState(false);

  useEffect(() => {
    storageEstimate().then(setUsage);
  }, []);

  async function backup() {
    const blob = await exportBackup();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `content-os-copia-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
  }

  const isStandalone = window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone;

  return (
    <div>
      <h2>Ajustes</h2>
      <p className="sub">Todo se guarda solo en este teléfono. Las claves nunca se suben a GitHub ni a ningún servidor de Content-OS.</p>

      {!isStandalone && (
        <div className="notice info">
          📲 <b>Instálalo como app:</b> en Safari pulsa el botón Compartir (cuadrado con flecha) → «Añadir a pantalla de inicio».
        </div>
      )}

      <div className="card">
        <h3>Funciones y costes</h3>
        <dl className="kv small">
          <dt>Guiones (biblioteca)</dt>
          <dd><span className="chip badge-real">GRATIS</span></dd>
          <dt>Voz española (Piper)</dt>
          <dd><span className="chip badge-real">GRATIS</span> descarga única ≈63 MB</dd>
          <dt>Vídeo MP4, música, subtítulos</dt>
          <dd><span className="chip badge-real">GRATIS</span> en el teléfono</dd>
          <dt>Imágenes Wikimedia</dt>
          <dd><span className="chip badge-real">GRATIS</span> con atribución</dd>
          <dt>Estadísticas YouTube</dt>
          <dd><span className="chip badge-real">GRATIS</span> requiere clave propia</dd>
          <dt>Guiones con IA (Claude)</dt>
          <dd><span className="chip badge-paid">DE PAGO</span> opcional</dd>
          <dt>Publicación automática</dt>
          <dd><span className="chip">NO ACTIVA</span> requiere integraciones oficiales</dd>
        </dl>
        <p className="tiny muted">Exportación de vídeo en este navegador: {webCodecsAvailable() ? 'rápida (WebCodecs)' : 'en tiempo real (MediaRecorder)'}.</p>
      </div>

      <div className="card">
        <h3>Clave de YouTube (opcional, gratis)</h3>
        <p className="small muted">
          Permite ver visualizaciones, «me gusta» y comentarios reales de vídeos de YouTube en Tendencias. Se crea gratis en Google Cloud Console → «YouTube Data API v3» → Credenciales →
          Clave de API.
        </p>
        <div className="row">
          <input className="grow" type={showYt ? 'text' : 'password'} value={settings.youtubeApiKey} onChange={(e) => setSettings({ youtubeApiKey: e.target.value.trim() })} placeholder="AIza…" autoComplete="off" />
          <button className="btn sm" onClick={() => setShowYt(!showYt)}>
            {showYt ? '🙈' : '👁'}
          </button>
        </div>
      </div>

      <div className="card">
        <h3>
          Clave de Claude <span className="chip badge-paid">DE PAGO</span>
        </h3>
        <p className="small muted">
          Opcional. Solo para escribir guiones sobre temas libres con IA. Se obtiene en console.anthropic.com y se paga por uso (céntimos por guion). No la necesitas para crear vídeos.
        </p>
        <div className="row">
          <input className="grow" type={showAi ? 'text' : 'password'} value={settings.anthropicApiKey} onChange={(e) => setSettings({ anthropicApiKey: e.target.value.trim() })} placeholder="sk-ant-…" autoComplete="off" />
          <button className="btn sm" onClick={() => setShowAi(!showAi)}>
            {showAi ? '🙈' : '👁'}
          </button>
        </div>
      </div>

      <div className="card">
        <h3>Exportación</h3>
        <label className="field">
          <span>Método de exportación</span>
          <select value={settings.method} onChange={(e) => setSettings({ method: e.target.value })}>
            <option value="auto">Automático (recomendado)</option>
            <option value="mediarecorder">Compatibilidad (tiempo real)</option>
          </select>
        </label>
        <p className="tiny muted">Si un vídeo sale sin sonido o corrupto, prueba «Compatibilidad».</p>
      </div>

      <div className="card stack">
        <h3>Datos</h3>
        {usage && <p className="small muted">Espacio usado: {usage.usedMB} MB de {usage.quotaMB} MB disponibles.</p>}
        <button className="btn block" onClick={backup}>
          💾 Exportar copia de seguridad (sin vídeos ni claves)
        </button>
        <label className="btn block">
          📂 Importar copia
          <input
            type="file"
            accept="application/json"
            hidden
            onChange={async (e) => {
              try {
                await importBackup(e.target.files[0]);
                notify('Copia importada. Recargando…');
                setTimeout(() => location.reload(), 800);
              } catch (err) {
                notify(err.message, 'bad');
              }
            }}
          />
        </label>
        <button
          className="btn block"
          onClick={() => {
            store.removeDemos();
            notify('Ejemplos de demostración borrados');
          }}
        >
          🧹 Borrar proyectos DEMO
        </button>
        <button
          className="btn block"
          onClick={async () => {
            await deleteVoices();
            notify('Voces borradas del teléfono');
          }}
        >
          🗣️ Borrar voces descargadas
        </button>
        <button
          className="btn danger block"
          onClick={async () => {
            if (confirm('¿Borrar TODO (proyectos, vídeos, ajustes)? No se puede deshacer.')) {
              await wipeAll();
              await deleteVoices();
              location.reload();
            }
          }}
        >
          Borrar todos los datos
        </button>
      </div>

      <p className="tiny muted" style={{ textAlign: 'center' }}>
        Content-OS v0.1 · Voz: Piper (MIT) · Imágenes: Wikimedia Commons · Música generada por la app
      </p>
    </div>
  );
}
