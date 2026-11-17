// Imágenes libres de Wikimedia Commons (sin clave, sin coste).
// Cada imagen guarda su autor y licencia para incluir los créditos en la descripción.

const API = 'https://commons.wikimedia.org/w/api.php';

function stripHtml(s = '') {
  return s.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
}

const ALLOWED_LICENSES = /^(cc0|cc by|cc-by|public domain|pd|cc by-sa|cc-by-sa)/i;

export async function searchCommons(query, { limit = 6, fetchImpl = fetch } = {}) {
  const params = new URLSearchParams({
    action: 'query',
    format: 'json',
    origin: '*',
    generator: 'search',
    gsrsearch: `${query} filetype:bitmap`,
    gsrnamespace: '6',
    gsrlimit: String(limit * 2),
    prop: 'imageinfo',
    iiprop: 'url|extmetadata|size|mime',
    iiurlwidth: '1080',
  });
  const r = await fetchImpl(`${API}?${params}`);
  if (!r.ok) throw new Error(`Wikimedia respondió ${r.status}`);
  const j = await r.json();
  const pages = Object.values(j.query?.pages || {}).sort((a, b) => (a.index ?? 0) - (b.index ?? 0));
  const out = [];
  for (const p of pages) {
    const ii = p.imageinfo?.[0];
    if (!ii || !/jpeg|png|webp/.test(ii.mime || '')) continue;
    const meta = ii.extmetadata || {};
    const license = stripHtml(meta.LicenseShortName?.value || '');
    if (!ALLOWED_LICENSES.test(license)) continue;
    if (ii.width < 500) continue;
    out.push({
      url: ii.thumburl || ii.url,
      page: ii.descriptionurl,
      title: p.title.replace(/^File:/, ''),
      author: stripHtml(meta.Artist?.value || 'Autor desconocido').slice(0, 80),
      license,
    });
    if (out.length >= limit) break;
  }
  return out;
}

export async function fetchImageBlob(url) {
  const r = await fetch(url, { mode: 'cors' });
  if (!r.ok) throw new Error(`No se pudo descargar la imagen (${r.status})`);
  return await r.blob();
}

export async function blobToBitmap(blob) {
  if (window.createImageBitmap) {
    try {
      return await createImageBitmap(blob);
    } catch {
      /* Safari antiguo: usamos <img> */
    }
  }
  const url = URL.createObjectURL(blob);
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    return img;
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }
}

/** Reduce una foto subida desde el iPhone para no llenar la memoria. */
export async function shrinkImage(blob, maxSide = 1440) {
  const bmp = await blobToBitmap(blob);
  const k = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
  const c = document.createElement('canvas');
  c.width = Math.round(bmp.width * k);
  c.height = Math.round(bmp.height * k);
  c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
  return await new Promise((res) => c.toBlob(res, 'image/jpeg', 0.86));
}
