// Conexión con GitHub para encargar renders 3D desde el iPhone.
// Usa un token personal (fine-grained) que guardas SOLO en tu teléfono.
// Permisos necesarios en el token, solo para este repositorio:
//   Contents: Read and write · Actions: Read-only
const API = 'https://api.github.com';

function headers(token) {
  const h = { Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' };
  if (token) h.Authorization = `Bearer ${token}`; // sin token: datos públicos (repositorio público)
  return h;
}

async function gh(path, { token, method = 'GET', body } = {}) {
  const r = await fetch(API + path, {
    method,
    headers: { ...headers(token), ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    let msg = `GitHub respondió ${r.status}`;
    try {
      msg += ': ' + (await r.json()).message;
    } catch {
      /* nada */
    }
    if (r.status === 401) msg = 'Token de GitHub no válido o caducado.';
    if (r.status === 404) msg = token ? 'GitHub no encuentra el repositorio: revisa el nombre y que el token tenga acceso a él.' : 'El repositorio es privado: conecta GitHub con tu token (abajo) para ver y encargar renders.';
    if (r.status === 403) msg += ' (revisa los permisos del token: Contents lectura/escritura y Actions lectura)';
    throw new Error(msg);
  }
  return r.status === 204 ? null : r.json();
}

function b64(str) {
  return btoa(unescape(encodeURIComponent(str)));
}

export async function getRepoInfo({ token, repo }) {
  const j = await gh(`/repos/${repo}`, { token });
  return { private: j.private, defaultBranch: j.default_branch };
}

/** Sube el encargo; el push dispara el workflow "Render 3D (Blender)". */
export async function submitJob({ token, repo, branch, path, spec }) {
  return gh(`/repos/${repo}/contents/${encodeURIComponent(path).replace(/%2F/g, '/')}`, {
    token,
    method: 'PUT',
    body: {
      message: `Encargo de render 3D: ${spec.title}`,
      content: b64(JSON.stringify(spec, null, 2) + '\n'),
      branch,
    },
  });
}

export async function listRenderRuns({ token, repo, branch }) {
  const q = new URLSearchParams({ per_page: '10', ...(branch ? { branch } : {}) });
  const j = await gh(`/repos/${repo}/actions/workflows/render-3d.yml/runs?${q}`, { token });
  return j.workflow_runs.map((r) => ({
    id: r.id,
    title: r.display_title,
    status: r.status,
    conclusion: r.conclusion,
    url: r.html_url,
    created: r.created_at,
    updated: r.updated_at,
  }));
}

/** Los vídeos terminados se publican como Releases (si el repositorio es privado hace falta token). */
export async function listVideoReleases({ token, repo }) {
  const j = await gh(`/repos/${repo}/releases?per_page=20`, { token });
  return j
    .filter((r) => r.tag_name.startsWith('video-'))
    .map((r) => ({
      id: r.id,
      tag: r.tag_name,
      title: r.name,
      url: r.html_url,
      created: r.created_at,
      mp4: r.assets.find((a) => a.name.endsWith('.mp4')),
      srt: r.assets.find((a) => a.name.endsWith('.srt')),
      credits: r.assets.find((a) => a.name.endsWith('-creditos.txt')),
    }))
    .filter((r) => r.mp4);
}

export function runLabel(run) {
  if (run.status === 'completed') return run.conclusion === 'success' ? '✅ Terminado' : run.conclusion === 'cancelled' ? '⏹ Cancelado' : '❌ Error';
  if (run.status === 'in_progress') return '⏳ Renderizando…';
  return '🕒 En cola';
}
