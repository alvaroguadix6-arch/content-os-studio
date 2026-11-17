import { useEffect, useState } from 'react';
import { useStore } from './store.jsx';
import Panel from './views/Panel.jsx';
import Trends from './views/Trends.jsx';
import Scripts from './views/Scripts.jsx';
import Produce from './views/Produce.jsx';
import Calendar from './views/Calendar.jsx';
import Publish from './views/Publish.jsx';
import Settings from './views/Settings.jsx';
import ProjectView from './views/ProjectView.jsx';
import Sim3D from './views/Sim3D.jsx';

const TABS = [
  ['panel', '🏠', 'Panel'],
  ['tendencias', '📈', 'Tendencias'],
  ['guiones', '✍️', 'Guiones'],
  ['3d', '🎮', '3D'],
  ['producir', '🎬', 'Producir'],
  ['calendario', '🗓️', 'Calendario'],
  ['publicar', '🚀', 'Publicar'],
];

function useRoute() {
  const parse = () => (window.location.hash.replace(/^#\/?/, '') || 'panel').split('/');
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const on = () => {
      setRoute(parse());
      window.scrollTo(0, 0);
    };
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return route;
}

export default function App() {
  const store = useStore();
  const [page, param] = useRoute();

  let view;
  if (!store.ready) view = <p className="muted">Cargando…</p>;
  else if (page === 'tendencias') view = <Trends />;
  else if (page === 'guiones') view = <Scripts editId={param} />;
  else if (page === 'producir') view = <Produce projectId={param} />;
  else if (page === 'calendario') view = <Calendar />;
  else if (page === 'publicar') view = <Publish projectId={param} />;
  else if (page === 'ajustes') view = <Settings />;
  else if (page === 'proyecto') view = <ProjectView projectId={param} />;
  else if (page === '3d') view = <Sim3D />;
  else view = <Panel />;

  return (
    <div className="app">
      <header className="topbar">
        <div className="logo">▶</div>
        <h1>
          Content-OS
          <small>Centro de producción de vídeos cortos</small>
        </h1>
        <a className="iconbtn" href="#/ajustes" aria-label="Ajustes">
          ⚙️
        </a>
      </header>
      <main>{view}</main>
      <nav className="tabbar">
        {TABS.map(([id, icon, label]) => (
          <a key={id} href={`#/${id}`} className={page === id || (id === 'panel' && page === 'proyecto') ? 'on' : ''}>
            <span>{icon}</span>
            <span>{label}</span>
          </a>
        ))}
      </nav>
      {store.toast && <div className={`toast ${store.toast.kind === 'bad' ? 'bad' : ''}`}>{store.toast.msg}</div>}
    </div>
  );
}
