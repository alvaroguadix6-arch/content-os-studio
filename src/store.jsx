import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import * as db from './lib/db.js';
import { generateScript } from './lib/scriptgen.js';

const Ctx = createContext(null);

function demoProjects() {
  // Ejemplos de DEMOSTRACIÓN (marcados como tal). Se pueden borrar en Ajustes.
  const today = new Date();
  const day = (n) => {
    const d = new Date(today);
    d.setDate(d.getDate() + n);
    return d.toISOString().slice(0, 10);
  };
  const a = generateScript({ topicId: 'pulpo-tres-corazones', duration: 30, seed: 3 });
  const b = generateScript({ topicId: 'tierra-deja-de-girar', duration: 45, seed: 5 });
  const now = new Date().toISOString();
  return [
    { ...a, id: 'demo-1', demo: true, status: 'pendiente', scheduledDate: day(1), createdAt: now, updatedAt: now, imageMode: 'generado' },
    { ...b, id: 'demo-2', demo: true, status: 'pendiente', scheduledDate: day(3), createdAt: now, updatedAt: now, imageMode: 'generado' },
  ];
}

export function StoreProvider({ children }) {
  const [projects, setProjects] = useState(null);
  const [settings, setSettingsState] = useState(db.DEFAULT_SETTINGS);
  const [trends, setTrendsState] = useState([]);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    (async () => {
      const [p, s, t] = await Promise.all([db.loadProjects(), db.loadSettings(), db.loadTrends()]);
      setSettingsState(s);
      setTrendsState(t);
      if (p) setProjects(p);
      else {
        const demo = demoProjects();
        setProjects(demo);
        db.saveProjects(demo);
      }
      db.requestPersistence();
    })();
  }, []);

  const persist = useCallback((next) => {
    setProjects(next);
    db.saveProjects(next);
  }, []);

  const api = useMemo(
    () => ({
      projects: projects || [],
      ready: projects !== null,
      settings,
      trends,
      toast,
      notify(msg, kind = 'ok') {
        setToast({ msg, kind, id: Date.now() });
        setTimeout(() => setToast((t) => (t && Date.now() - t.id > 2500 ? null : t)), 2800);
      },
      setSettings(patch) {
        setSettingsState((s) => {
          const n = { ...s, ...patch };
          db.saveSettings(n);
          return n;
        });
      },
      setTrends(next) {
        setTrendsState(next);
        db.saveTrends(next);
      },
      addProject(p) {
        const now = new Date().toISOString();
        const proj = { status: 'pendiente', imageMode: 'generado', scheduledDate: null, ...p, id: db.uid(), createdAt: now, updatedAt: now };
        persist([proj, ...(projects || [])]);
        return proj;
      },
      updateProject(id, patch) {
        setProjects((prev) => {
          const next = prev.map((p) => (p.id === id ? { ...p, ...patch, updatedAt: new Date().toISOString() } : p));
          db.saveProjects(next);
          return next;
        });
      },
      async removeProject(id) {
        const p = (projects || []).find((x) => x.id === id);
        if (p) {
          await db.deleteBlob(p.video?.key);
          await db.deleteBlob(p.thumbKey);
          for (const im of p.images || []) await db.deleteBlob(im?.key);
          await db.deleteBlob(p.recordingKey);
        }
        persist((projects || []).filter((x) => x.id !== id));
      },
      removeDemos() {
        persist((projects || []).filter((p) => !p.demo));
      },
    }),
    [projects, settings, trends, toast, persist],
  );

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

export function useStore() {
  return useContext(Ctx);
}
