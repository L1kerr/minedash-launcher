import { ProgressState } from '../shared/types';
import { fmtBytes, fmtSpeed, pct } from '../lib/format';
import { Image, Settings, Server } from 'lucide-react';

interface Props {
  serverName: string;
  version: string;
  state: 'idle' | 'working' | 'running';
  progress: (ProgressState & { stage: string }) | null;
  onPlay: () => void;
  onSettings: () => void;
  onBackgrounds: () => void;
  onWorkshop: () => void;
}

export default function Playbar({ serverName, version, state, progress, onPlay, onSettings, onBackgrounds, onWorkshop }: Props) {
  const p = pct(progress?.done ?? 0, progress?.total ?? 0);
  return (
    <footer className="playbar">
      <div className="playbar-info">
        <b className="playbar-server">
          <Server size={15} strokeWidth={1.8} />
          {serverName}
        </b>
        <span className="playbar-meta">
          Версия {version}
          <i className="dot ok" />
          Онлайн
        </span>
      </div>
      <div className="playbar-actions">
        {state === 'working' && progress && (
          <div className="progress-wrap">
            <div className="progress-text">
              <span>{progress.stage}</span>
              <span>
                {p}%{progress.speed > 0 ? ` · ${fmtSpeed(progress.speed)}` : ''}
                {progress.total > (1 << 24) ? ` · ${fmtBytes(progress.done)} / ${fmtBytes(progress.total)}` : ''}
              </span>
            </div>
            <div className="progress-bar">
              <i style={{ width: p + '%' }} />
            </div>
          </div>
        )}
        <button
          className={'play-btn' + (state === 'working' ? ' busy' : '') + (state === 'running' ? ' live' : '')}
          onClick={onPlay}
          disabled={state === 'working' || state === 'running'}
        >
          {state === 'running' ? 'В ИГРЕ' : state === 'working' ? 'ЗАГРУЗКА…' : 'ИГРАТЬ'}
        </button>
        <button className="icon-btn" title="Сменить фон" onClick={onBackgrounds}>
          <Image size={18} strokeWidth={1.7} />
        </button>
        {/* Workshop временно скрыт — вернём после доработки
        <button className="icon-btn" title="Workshop — своя стилистика" onClick={onWorkshop}>
          <Sparkles size={18} strokeWidth={1.7} />
        </button>
        */}
        <button className="icon-btn" title="Настройки" onClick={onSettings}>
          <Settings size={18} strokeWidth={1.7} />
        </button>
      </div>
    </footer>
  );
}
