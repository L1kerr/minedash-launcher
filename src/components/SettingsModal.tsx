import { useEffect, useState } from 'react';
import { Settings } from '../shared/types';
import { api, UpdateCheck } from '../lib/api';
import { ArrowDownCircle, CheckCircle2, Loader2 } from 'lucide-react';
import Modal from './Modal';

interface Props {
  settings: Settings;
  onChange: (patch: Partial<Settings>) => void;
  onClose: () => void;
}

function Toggle({ on, onClick }: { on: boolean; onClick: () => void }) {
  return (
    <button className={'switch' + (on ? ' on' : '')} onClick={onClick} role="switch" aria-checked={on}>
      <i />
    </button>
  );
}

export default function SettingsModal({ settings, onChange, onClose }: Props) {
  const [s, setS] = useState(settings);
  const set = (patch: Partial<Settings>) => {
    setS((prev) => ({ ...prev, ...patch }));
    onChange(patch);
  };

  return (
    <Modal title="Настройки" onClose={onClose} wide>
      <div className="settings-grid">
        <section>
          <h3>Аккаунт</h3>
          <label className="field">
            <span>Никнейм</span>
            <input value={s.nickname || '—'} readOnly disabled />
          </label>
        </section>

        <section>
          <h3>Игра</h3>
          <label className="field">
            <span>
              Память JVM: <b>{(s.memoryMb / 1024).toFixed(1)} ГБ</b>
            </span>
            <input
              type="range"
              min={2048}
              max={16384}
              step={512}
              value={s.memoryMb}
              onChange={(e) => set({ memoryMb: Number(e.target.value) })}
            />
          </label>
          <label className="field">
            <span>Разрешение</span>
            <select
              value={`${s.resolutionW}x${s.resolutionH}`}
              onChange={(e) => {
                const [w, h] = e.target.value.split('x').map(Number);
                set({ resolutionW: w, resolutionH: h });
              }}
            >
              <option value="1280x720">1280 × 720</option>
              <option value="1600x900">1600 × 900</option>
              <option value="1920x1080">1920 × 1080</option>
              <option value="2560x1440">2560 × 1440</option>
            </select>
          </label>
          <div className="row">
            <span>Полный экран</span>
            <Toggle on={s.fullscreen} onClick={() => set({ fullscreen: !s.fullscreen })} />
          </div>
        </section>

        <section>
          <h3>Лаунчер</h3>
          <div className="row">
            <span>Сворачивать при запуске игры</span>
            <Toggle on={s.closeOnPlay} onClick={() => set({ closeOnPlay: !s.closeOnPlay })} />
          </div>
          <button className="ghost-btn" onClick={() => api.app.openGameDir()}>
            Открыть папку игры
          </button>
          <UpdateBlock />
          <p className="hint">
            Версия лаунчера <VersionTag />
          </p>
        </section>
      </div>
    </Modal>
  );
}

function VersionTag() {
  const [v, setV] = useState('');
  useEffect(() => {
    api.app.version().then(setV);
  }, []);
  return <>{v}</>;
}

function UpdateBlock() {
  const [state, setState] = useState<'idle' | 'checking' | 'available' | 'uptodate' | 'installing' | 'error'>('idle');
  const [info, setInfo] = useState<UpdateCheck | null>(null);
  const [error, setError] = useState('');

  const check = () => {
    setState('checking');
    api.app.updateCheck()
      .then((r) => {
        setInfo(r);
        setState(r.available ? 'available' : 'uptodate');
      })
      .catch((e) => {
        setError(String(e));
        setState('error');
      });
  };

  const install = () => {
    setState('installing');
    api.app.updateInstall().catch((e) => {
      setError(String(e));
      setState('error');
    });
  };

  return (
    <div className="update-block">
      {state === 'idle' && (
        <button className="ghost-btn" onClick={check}>
          Проверить обновления
        </button>
      )}
      {state === 'checking' && (
        <span className="update-status"><Loader2 size={14} className="spin" /> Проверяю…</span>
      )}
      {state === 'uptodate' && (
        <span className="update-status ok"><CheckCircle2 size={14} /> У вас последняя версия</span>
      )}
      {state === 'available' && info?.info && (
        <div className="update-available">
          <span className="update-status"><ArrowDownCircle size={14} /> Доступна версия {info.info.version}</span>
          {info.info.notes && <p className="hint">{info.info.notes}</p>}
          <button className="mini-btn primary" onClick={install}>Обновить</button>
        </div>
      )}
      {state === 'installing' && (
        <span className="update-status"><Loader2 size={14} className="spin" /> Устанавливаю…</span>
      )}
      {state === 'error' && (
        <span className="update-status err">{error}</span>
      )}
    </div>
  );
}
