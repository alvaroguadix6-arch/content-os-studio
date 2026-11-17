// Almacenamiento local en el propio teléfono (IndexedDB).
// Nada se sube a ningún servidor: tus proyectos, vídeos y claves se quedan en tu dispositivo.

import { get, set, del, keys } from 'idb-keyval';

export const STATUSES = {
  pendiente: { label: 'Pendiente', color: '#94a3b8' },
  produciendo: { label: 'Produciendo', color: '#f59e0b' },
  listo: { label: 'Listo', color: '#38bdf8' },
  aprobado: { label: 'Aprobado', color: '#22c55e' },
};

export const DEFAULT_SETTINGS = {
  voiceId: 'es_ES-davefx-medium',
  voiceMode: 'piper',
  speed: 1.1,
  resolution: '720',
  music: true,
  sfx: true,
  handle: '',
  youtubeApiKey: '',
  anthropicApiKey: '',
  method: 'auto',
};

export async function loadProjects() {
  return (await get('projects')) || null;
}
export async function saveProjects(projects) {
  await set('projects', projects);
}
export async function loadSettings() {
  return { ...DEFAULT_SETTINGS, ...((await get('settings')) || {}) };
}
export async function saveSettings(s) {
  await set('settings', s);
}
export async function loadTrends() {
  return (await get('trends')) || [];
}
export async function saveTrends(t) {
  await set('trends', t);
}
export async function putBlob(key, blob) {
  await set('blob:' + key, blob);
}
export async function getBlob(key) {
  return key ? await get('blob:' + key) : null;
}
export async function deleteBlob(key) {
  if (key) await del('blob:' + key);
}
export async function storageEstimate() {
  try {
    const e = await navigator.storage?.estimate?.();
    return e ? { usedMB: Math.round(e.usage / 1e6), quotaMB: Math.round(e.quota / 1e6) } : null;
  } catch {
    return null;
  }
}
export async function requestPersistence() {
  try {
    return await navigator.storage?.persist?.();
  } catch {
    return false;
  }
}

export async function exportBackup() {
  const data = {
    app: 'content-os',
    version: 1,
    exportedAt: new Date().toISOString(),
    projects: await loadProjects(),
    trends: await loadTrends(),
    settings: { ...(await loadSettings()), youtubeApiKey: '', anthropicApiKey: '' }, // las claves NO se exportan
  };
  return new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
}

export async function importBackup(file) {
  const data = JSON.parse(await file.text());
  if (data.app !== 'content-os') throw new Error('Este archivo no es una copia de Content-OS.');
  if (data.projects) await saveProjects(data.projects);
  if (data.trends) await saveTrends(data.trends);
  return data;
}

export async function wipeAll() {
  for (const k of await keys()) await del(k);
}

export function uid() {
  return Math.random().toString(36).slice(2, 8) + Date.now().toString(36).slice(-4);
}
