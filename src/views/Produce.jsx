import { useEffect, useRef, useState } from 'react';
import { useStore } from '../store.jsx';
import { renderVideo, previewFrame, unlockAudio } from '../engine/render.js';
import { VOICES, PiperVoice, isVoiceDownloaded } from '../engine/tts.js';
import { searchCommons, fetchImageBlob, shrinkImage } from '../engine/images.js';
import { putBlob, getBlob, deleteBlob } from '../lib/db.js';
import { Seg, StatusChip, DemoBadge, Thumb, useBlobUrl } from './common.jsx';
import { go } from '../nav.js';

export default function Produce({ projectId }) {
  const { projects } = useStore();
  const project = projects.find((p) => p.id === projectId);
  if (!project) return <PickProject projects={projects} />;
  return <Producer key={project.id} project={project} />;
}

function PickProject({ projects }) {
  const pending = projects.filter((p) => p.status !== 'aprobado');
  return (
    <div>
      <h2>Producción</h2>
      <p className="sub">Elige el guion que quieres convertir en vídeo vertical 9:16.</p>
      {pending.length === 0 && (
        <div className="card">
          <p>No hay guiones pendientes.</p>
          <a className="btn primary" href="#/guiones">
            Crear un guion
          </a>
        </div>
      )}
      {pending.map((p) => (
        <a key={p.id} className="card proj" href={`#/producir/${p.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'grid' }}>
          <Thumb project={p} />
          <div>
            <div className="row">
              <StatusChip status={p.status} />
              <DemoBadge demo={p.demo} />
            </div>
            <h3>{p.title}</h3>
            <span className="small muted">{p.segments.length} escenas · {p.video ? 'ya tiene vídeo' : 'sin vídeo'}</span>
          </div>
        </a>
      ))}
    </div>
  );
}

export async function shareOrDownload(blob, filename, notify) {
  const file = new File([blob], filename, { type: blob.type || 'video/mp4' });
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: filename });
      return;
    } catch (e) {
      if (e.name === 'AbortError') return;
    }
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
  notify?.('Descarga iniciada');
}

function Producer({ project }) {
  const store = useStore();
  const { settings, setSettings, updateProject, notify } = store;
  const [imageMode, setImageMode] = useState(project.imageMode || 'generado');
  const [images, setImages] = useState(project.images || []);
  const [imgBlobs, setImgBlobs] = useState([]);
  const [candidates, setCandidates] = useState(null);
  const [searching, setSearching] = useState(false);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState('');
  const [voiceReady, setVoiceReady] = useState(null);
  const [testing, setTesting] = useState(false);
  const [recording, setRecording] = useState(null);
  const recRef = useRef(null);
  const abortRef = useRef(null);
  const canvasRef = useRef(null);
  const videoUrl = useBlobUrl(project.video?.key);
  const recordingUrl = useBlobUrl(project.recordingKey);
  const segs = project.segments.filter((s) => s.text.trim());

  useEffect(() => {
    isVoiceDownloaded(settings.voiceId).then(setVoiceReady);
  }, [settings.voiceId]);

  // Cargar imágenes guardadas
  useEffect(() => {
    (async () => {
      const blobs = await Promise.all(segs.map((_, i) => (images[i]?.key ? getBlob(images[i].key) : null)));
      setImgBlobs(blobs);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [images]);

  // Vista previa
  useEffect(() => {
    if (canvasRef.current && !progress) previewFrame(canvasRef.current, project, 1.2, imageMode === 'generado' ? [] : imgBlobs);
  }, [project, imgBlobs, imageMode, progress]);

  function saveImages(next) {
    setImages(next);
    updateProject(project.id, { images: next, credits: next.filter((x) => x?.credit).map((x) => x.credit), imageMode });
  }

  async function searchImages() {
    setSearching(true);
    setError('');
    try {
      const kws = project.keywords?.length ? project.keywords : [project.title];
      const all = [];
      for (const kw of kws) {
        const r = await searchCommons(kw, { limit: 6 });
        for (const x of r) if (!all.some((y) => y.url === x.url)) all.push(x);
      }
      if (!all.length) throw new Error('No se encontraron imágenes libres para este tema. Prueba con tus propias fotos.');
      setCandidates(all);
      // Asignación automática: una imagen distinta por escena (repitiendo si faltan)
      const next = [];
      for (let i = 0; i < segs.length; i++) {
        const c = all[i % all.length];
        const key = `${project.id}-img-${i}`;
        await putBlob(key, await fetchImageBlob(c.url));
        next.push({ key, credit: { author: c.author, license: c.license, page: c.page, title: c.title }, url: c.url });
      }
      saveImages(next);
      notify('Imágenes asignadas');
    } catch (e) {
      setError(e.message.includes('Failed to fetch') ? 'No hay conexión con Wikimedia Commons.' : e.message);
    } finally {
      setSearching(false);
    }
  }

  async function swapImage(i) {
    if (!candidates?.length) return;
    const cur = candidates.findIndex((c) => c.url === images[i]?.url);
    const c = candidates[(cur + 1) % candidates.length];
    const key = `${project.id}-img-${i}`;
    await putBlob(key, await fetchImageBlob(c.url));
    const next = [...images];
    next[i] = { key, credit: { author: c.author, license: c.license, page: c.page, title: c.title }, url: c.url, v: Date.now() };
    saveImages(next);
  }

  async function uploadImage(i, file) {
    if (!file) return;
    const blob = await shrinkImage(file);
    const key = `${project.id}-img-${i}`;
    await putBlob(key, blob);
    const next = [...images];
    while (next.length < segs.length) next.push(null);
    next[i] = { key, credit: null, own: true, v: Date.now() };
    saveImages(next);
  }

  async function removeImage(i) {
    await deleteBlob(images[i]?.key);
    const next = [...images];
    next[i] = null;
    saveImages(next);
  }

  async function testVoice() {
    setTesting(true);
    setError('');
    try {
      const ac = unlockAudio();
      const v = new PiperVoice(settings.voiceId);
      await v.load((p, cached) => setProgress(cached ? null : { label: `Descargando voz: ${Math.round(p * 100)} %`, value: p }));
      setProgress(null);
      const { samples, sampleRate } = await v.synthesize(segs[0]?.text || 'Hola, esta es la voz de Content-OS.', { speed: settings.speed });
      const buf = ac.createBuffer(1, samples.length, sampleRate);
      buf.copyToChannel(samples, 0);
      const src = ac.createBufferSource();
      src.buffer = buf;
      src.connect(ac.destination);
      src.start();
      setVoiceReady(true);
    } catch (e) {
      setError('No se pudo cargar la voz: ' + e.message);
      setProgress(null);
    } finally {
      setTesting(false);
    }
  }

  async function toggleRecord() {
    if (recording) {
      recRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      const chunks = [];
      mr.ondataavailable = (e) => chunks.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: mr.mimeType });
        const key = `${project.id}-voz`;
        await putBlob(key, blob);
        updateProject(project.id, { recordingKey: key, recordingAt: Date.now() });
        setRecording(null);
        notify('Grabación guardada');
      };
      recRef.current = mr;
      mr.start();
      setRecording(Date.now());
    } catch {
      setError('No se pudo acceder al micrófono. Revisa los permisos de Safari.');
    }
  }

  async function uploadRecording(file) {
    if (!file) return;
    const key = `${project.id}-voz`;
    await putBlob(key, file);
    updateProject(project.id, { recordingKey: key, recordingAt: Date.now() });
    notify('Audio cargado');
  }

  async function produce() {
    setError('');
    unlockAudio();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    const prevStatus = project.status;
    updateProject(project.id, { status: 'produciendo', imageMode });
    setProgress({ label: 'Empezando…', value: 0 });
    try {
      const recordingBlob = settings.voiceMode === 'grabada' ? await getBlob(project.recordingKey) : null;
      if (settings.voiceMode === 'grabada' && !recordingBlob) throw new Error('Primero graba o sube tu voz.');
      const out = await renderVideo(
        project,
        settings,
        { images: imageMode === 'generado' ? [] : imgBlobs, recording: recordingBlob },
        { onProgress: (p) => setProgress(p), signal: ctrl.signal },
      );
      const ext = out.mimeType.includes('mp4') ? 'mp4' : 'webm';
      const vkey = `${project.id}-video`;
      const tkey = `${project.id}-thumb`;
      await putBlob(vkey, out.blob);
      await putBlob(tkey, out.thumb);
      updateProject(project.id, {
        status: 'listo',
        videoOutdated: false,
        thumbKey: tkey + '',
        video: {
          key: vkey,
          ext,
          mimeType: out.mimeType,
          duration: out.duration,
          width: out.width,
          height: out.height,
          method: out.method,
          sizeMB: Math.round((out.blob.size / 1e6) * 10) / 10,
          createdAt: new Date().toISOString(),
          rev: Date.now(),
        },
      });
      notify('¡Vídeo listo! 🎉');
    } catch (e) {
      updateProject(project.id, { status: project.video ? 'listo' : prevStatus === 'produciendo' ? 'pendiente' : prevStatus });
      setError(e.message || String(e));
    } finally {
      setProgress(null);
      abortRef.current = null;
    }
  }

  const busy = !!progress;

  return (
    <div>
      <div className="row between">
        <h2 className="grow">{project.title}</h2>
        <StatusChip status={project.status} />
      </div>
      <p className="sub">
        {segs.length} escenas · <a href={`#/guiones/${project.id}`}>✏️ modificar guion</a>
      </p>

      {project.video && !busy && (
        <div className="card">
          <h3>Vídeo producido {project.videoOutdated && <span className="chip badge-demo">guion cambiado: vuelve a generar</span>}</h3>
          <div className="video-wrap">{videoUrl && <video key={project.video.rev} src={videoUrl} controls playsInline preload="metadata" />}</div>
          <p className="tiny muted">
            {project.video.width}×{project.video.height} · {Math.round(project.video.duration)} s · {project.video.sizeMB} MB · {project.video.ext.toUpperCase()} · {project.video.method}
          </p>
          <div className="row">
            {project.status === 'listo' && (
              <button
                className="btn ok grow"
                onClick={() => {
                  updateProject(project.id, { status: 'aprobado', approvedAt: new Date().toISOString() });
                  notify('Vídeo aprobado ✅');
                }}
              >
                ✔ Aprobar
              </button>
            )}
            <button className="btn grow" onClick={async () => shareOrDownload(await getBlob(project.video.key), `${slug(project.title)}.${project.video.ext}`, notify)}>
              ⬇️ Guardar / compartir
            </button>
            {project.status === 'aprobado' && (
              <button className="btn primary grow" onClick={() => go(`publicar/${project.id}`)}>
                🚀 Preparar publicación
              </button>
            )}
          </div>
        </div>
      )}

      {busy ? (
        <div className="card">
          <h3>Produciendo…</h3>
          <div className="progress">
            <div style={{ width: `${Math.round((progress.value || 0) * 100)}%` }} />
          </div>
          <p className="small">{progress.label}</p>
          <p className="tiny muted">Mantén Content-OS abierto y la pantalla encendida hasta que termine.</p>
          <button className="btn danger sm" onClick={() => abortRef.current?.abort()}>
            Cancelar
          </button>
        </div>
      ) : (
        <>
          <div className="card">
            <h3>1 · Imágenes y escenas</h3>
            <Seg
              value={imageMode}
              onChange={(v) => {
                setImageMode(v);
                updateProject(project.id, { imageMode: v });
              }}
              options={[
                ['generado', '✨ Animadas'],
                ['wikimedia', '🖼️ Libres'],
                ['propias', '📷 Mis fotos'],
              ]}
            />
            <p className="small muted">
              {imageMode === 'generado' && 'Fondos animados creados por la app según el tema. Sin derechos de autor y sin conexión.'}
              {imageMode === 'wikimedia' && 'Imágenes de Wikimedia Commons con licencias libres (CC0, CC BY, CC BY-SA). Los créditos se añaden solos a la descripción.'}
              {imageMode === 'propias' && 'Sube una foto por escena desde tu carrete. Las escenas sin foto usan el fondo animado.'}
            </p>
            {imageMode === 'wikimedia' && (
              <button className="btn block" disabled={searching} onClick={searchImages}>
                {searching ? 'Buscando…' : images.some(Boolean) ? '🔄 Volver a buscar imágenes' : '🔎 Buscar imágenes libres'}
              </button>
            )}
            {imageMode !== 'generado' && (
              <div className="stack" style={{ marginTop: 10 }}>
                {segs.map((s, i) => (
                  <SceneImage
                    key={i}
                    i={i}
                    seg={s}
                    item={images[i]}
                    blob={imgBlobs[i]}
                    mode={imageMode}
                    onSwap={() => swapImage(i)}
                    onUpload={(f) => uploadImage(i, f)}
                    onRemove={() => removeImage(i)}
                    canSwap={!!candidates?.length}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <h3>2 · Voz</h3>
            <Seg
              value={settings.voiceMode}
              onChange={(v) => setSettings({ voiceMode: v })}
              options={[
                ['piper', '🗣️ Voz IA gratis'],
                ['grabada', '🎙️ Mi voz'],
                ['sin-voz', '🔇 Sin voz'],
              ]}
            />
            {settings.voiceMode === 'piper' && (
              <div style={{ marginTop: 10 }}>
                <label className="field">
                  <span>Voz española (Piper, código abierto)</span>
                  <select value={settings.voiceId} onChange={(e) => setSettings({ voiceId: e.target.value })}>
                    {Object.entries(VOICES).map(([id, v]) => (
                      <option key={id} value={id}>
                        {v.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Velocidad: {settings.speed.toFixed(2)}×</span>
                  <input type="range" min="0.85" max="1.35" step="0.05" value={settings.speed} onChange={(e) => setSettings({ speed: Number(e.target.value) })} />
                </label>
                <div className="row">
                  <button className="btn sm" disabled={testing} onClick={testVoice}>
                    {testing ? 'Cargando…' : '▶ Probar voz'}
                  </button>
                  <span className="tiny muted">
                    {voiceReady ? '✅ Voz guardada en el teléfono' : `Primera vez: descarga ≈${VOICES[settings.voiceId]?.sizeMB || 63} MB (mejor con wifi)`}
                  </span>
                </div>
              </div>
            )}
            {settings.voiceMode === 'grabada' && (
              <div style={{ marginTop: 10 }} className="stack">
                <p className="small muted">Lee el guion completo de una vez. Los subtítulos se reparten automáticamente según el texto.</p>
                <div className="row">
                  <button className={`btn ${recording ? 'danger' : 'primary'}`} onClick={toggleRecord}>
                    {recording ? '⏹ Parar grabación' : '🎙️ Grabar'}
                  </button>
                  <label className="btn">
                    📁 Subir audio
                    <input type="file" accept="audio/*" hidden onChange={(e) => uploadRecording(e.target.files[0])} />
                  </label>
                </div>
                {recordingUrl && <audio key={project.recordingAt} src={recordingUrl} controls style={{ width: '100%' }} />}
                <details>
                  <summary className="small">Ver guion para leer</summary>
                  <p className="small">{segs.map((s) => s.text).join(' ')}</p>
                </details>
              </div>
            )}
            {settings.voiceMode === 'sin-voz' && <p className="small muted">Vídeo solo con subtítulos y música (los tiempos se calculan por la longitud del texto).</p>}
          </div>

          <div className="card">
            <h3>3 · Estilo y calidad</h3>
            <label className="field">
              <span>Resolución</span>
              <Seg
                value={settings.resolution}
                onChange={(v) => setSettings({ resolution: v })}
                options={[
                  ['720', '720×1280 (rápido)'],
                  ['1080', '1080×1920 (HD)'],
                ]}
              />
            </label>
            <div className="row between" style={{ marginBottom: 10 }}>
              <label className="row small">
                <input type="checkbox" checked={settings.music} onChange={(e) => setSettings({ music: e.target.checked })} /> Música propia (sin derechos)
              </label>
              <label className="row small">
                <input type="checkbox" checked={settings.sfx} onChange={(e) => setSettings({ sfx: e.target.checked })} /> Efectos
              </label>
            </div>
            <label className="field">
              <span>Tu @usuario en el vídeo (opcional)</span>
              <input type="text" value={settings.handle} onChange={(e) => setSettings({ handle: e.target.value })} placeholder="@tucuenta" />
            </label>
            <p className="small muted" style={{ marginBottom: 6 }}>
              Vista previa (aproximada):
            </p>
            <div className="video-wrap" style={{ maxHeight: 360, width: 202 }}>
              <canvas ref={canvasRef} width={360} height={640} />
            </div>
          </div>

          {error && <div className="notice bad">{error}</div>}
          <button className="btn primary block" style={{ minHeight: 54, fontSize: 17 }} onClick={produce} disabled={settings.voiceMode === 'grabada' && !project.recordingKey}>
            🎬 {project.video ? 'Volver a generar vídeo' : 'Generar vídeo MP4'}
          </button>
          <p className="tiny muted" style={{ textAlign: 'center' }}>
            Tarda aproximadamente lo que dura el vídeo. Todo se procesa en tu teléfono.
          </p>
        </>
      )}
    </div>
  );
}

function SceneImage({ i, seg, item, blob, mode, onSwap, onUpload, onRemove, canSwap }) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    if (!blob) return setUrl(null);
    const u = URL.createObjectURL(blob);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [blob]);
  return (
    <div className="segment" style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 10 }}>
      <div className="thumb" style={{ width: 64, height: 96 }}>
        {url ? <img src={url} alt="" /> : '✨'}
      </div>
      <div>
        <div className="kind">
          Escena {i + 1} · {seg.kind}
        </div>
        <div className="small" style={{ margin: '2px 0 6px' }}>
          {seg.text.slice(0, 90)}
          {seg.text.length > 90 ? '…' : ''}
        </div>
        {item?.credit && (
          <div className="tiny muted" style={{ marginBottom: 6 }}>
            © {item.credit.author} · {item.credit.license}
          </div>
        )}
        <div className="row">
          {mode === 'wikimedia' && canSwap && (
            <button className="btn sm" onClick={onSwap}>
              🔄 Otra
            </button>
          )}
          <label className="btn sm">
            📷 Foto
            <input type="file" accept="image/*" hidden onChange={(e) => onUpload(e.target.files[0])} />
          </label>
          {item && (
            <button className="btn sm ghost" onClick={onRemove}>
              Quitar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function slug(s) {
  return (
    s
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 50) || 'video'
  );
}
