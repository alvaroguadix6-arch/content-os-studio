import { describe, it, expect } from 'vitest';
import { ideaToSpec, findColors, jobFileName } from '../../src/lib/idea3d.js';

describe('idea → encargo 3D', () => {
  it('detecta colores y marcas sin reproducir marcas', () => {
    const r = ideaToSpec('Carrera entre un Ferrari rojo y un Lamborghini amarillo. Gana el rojo.');
    expect(r.spec.car_a_name).toBe('Rosso');
    expect(r.spec.car_b_name).toBe('Giallo');
    expect(r.spec.winner).toBe('a');
    expect(r.notes.join(' ')).toMatch(/genéricos/);
  });
  it('ganador segundo coche', () => {
    const r = ideaToSpec('Un coche azul contra uno naranja; gana el naranja en el último segundo');
    expect(findColors('azul y naranja')).toEqual(['azul', 'naranja']);
    expect(r.spec.winner).toBe('b');
    expect(r.spec.car_b_name).toBe('Arancio');
  });
  it('valores por defecto y calidad', () => {
    const r = ideaToSpec('una carrera épica', { quality: 'rapida' });
    expect(r.spec.car_a_color).toHaveLength(3);
    expect(r.spec.render.samples).toBe(8);
    expect(r.understood.join(' ')).toMatch(/por defecto/);
  });
  it('nombre de archivo del encargo', () => {
    const p = jobFileName({ title: 'Carrera: Rosso contra Giallo' }, new Date('2026-11-17T10:20:00Z'));
    expect(p).toBe('render3d/jobs/carrera-rosso-contra-giallo-202611171020.json');
  });
  it('plantilla inmortal', () => {
    const r = ideaToSpec('', { template: 'inmortal' });
    expect(r.spec.template).toBe('inmortal');
    expect(r.spec.final_text).toBe('¿ACEPTARÍAS SER INMORTAL? 👀');
  });
});
