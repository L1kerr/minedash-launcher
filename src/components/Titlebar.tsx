import { useEffect, useState } from 'react';
import { Globe, MessageCircle, Minus, Square, X, Boxes } from 'lucide-react';
import { api } from '../lib/api';

export default function Titlebar() {
  const [, setMaximized] = useState(false);

  useEffect(() => {
    api.win.isMaximized().then(setMaximized);
    api.win.onMaximized(setMaximized);
  }, []);

  return (
    <header className="titlebar">
      <div className="titlebar-left">
        <div className="brand">
          <Boxes size={22} strokeWidth={1.6} />
        </div>
        <button className="pill pill-icon" title="Сайт" onClick={() => api.app.openExternal('https://minedash.fun')}>
          <Globe size={15} strokeWidth={1.8} />
        </button>
        <button className="pill pill-icon" title="Discord" onClick={() => api.app.openExternal('https://discord.gg/minedash')}>
          <MessageCircle size={15} strokeWidth={1.8} />
        </button>
      </div>
      <div className="titlebar-center">
        <span className="window-title">MineDash Launcher</span>
      </div>
      <div className="titlebar-right">
        <div className="winbtns">
          <button className="winbtn" onClick={() => api.win.minimize()} aria-label="Свернуть">
            <Minus size={11} strokeWidth={1.3} />
          </button>
          <button className="winbtn" onClick={() => api.win.maximize()} aria-label="Развернуть">
            <Square size={11} strokeWidth={1.2} />
          </button>
          <button className="winbtn danger" onClick={() => api.win.close()} aria-label="Закрыть">
            <X size={11} strokeWidth={1.3} />
          </button>
        </div>
      </div>
    </header>
  );
}
