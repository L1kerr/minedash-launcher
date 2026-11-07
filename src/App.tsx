import { useCallback, useEffect, useState } from 'react';
import { AuthState, BackgroundMeta, ProgressState, Settings, SkinPayload, StoreShape } from './shared/types';
import BackgroundsModal from './components/BackgroundsModal';
import WorkshopModal from './components/WorkshopModal';
import Hero from './components/Hero';
import Login from './components/Login';
import Playbar from './components/Playbar';
import SettingsModal from './components/SettingsModal';
import Sidebar from './components/Sidebar';
import SkinModal from './components/SkinModal';
import Titlebar from './components/Titlebar';
import { api, bgSrc } from './lib/api';
import { applyTheme, themeForCategory, themeFromUser } from './lib/themes';
import { SERVERS } from './lib/servers';

type ModalKind = null | 'skin' | 'settings' | 'backgrounds' | 'workshop';

export default function App() {
  const [store, setStore] = useState<StoreShape | null>(null);
  const [skin, setSkin] = useState<SkinPayload | null>(null);
  const [backgrounds, setBackgrounds] = useState<BackgroundMeta[]>([]);
  const [serverId, setServerId] = useState('create');
  const [modal, setModal] = useState<ModalKind>(null);
  const [state, setState] = useState<'idle' | 'working' | 'running'>('idle');
  const [progress, setProgress] = useState<(ProgressState & { stage: string }) | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [booting, setBooting] = useState(true);
  const [update, setUpdate] = useState<{ version: string; notes: string } | null>(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    (async () => {
      const s = await api.store.get();
      setStore(s);
      setServerId(s.lastServer);
      api.skin.get().then(setSkin);
      api.backgrounds.list().then(setBackgrounds);
      const restored = await api.auth.restore();
      setAuth(restored);
      setBooting(false);
      // автопроверка обновлений
      api.app.updateCheck()
        .then((r) => {
          if (r.available && r.info) setUpdate({ version: r.info.version, notes: r.info.notes });
        })
        .catch(() => undefined);
    })();
    api.game.onProgress((p) => {
      setProgress(p);
      setState((cur) => (cur === 'running' ? cur : 'working'));
    });
    api.game.onState((s) => {
      if (s === 'running') {
        setState('running');
        setProgress(null);
      } else {
        setState('idle');
        setProgress(null);
      }
    });
    api.game.onExit(() => setState('idle'));
    api.game.onError((e) => {
      setState('idle');
      setProgress(null);
      setToast(e);
    });
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 6000);
    return () => clearTimeout(t);
  }, [toast]);

  // палитра: пользовательская тема (Workshop) перекрывает категорию фона
  useEffect(() => {
    if (!store) return;
    const user = themeFromUser(store.settings.userTheme as never);
    const cat = backgrounds.find((b) => b.id === store.settings.backgroundId)?.category;
    applyTheme(user ?? themeForCategory(cat));
  }, [store?.settings.userTheme, store?.settings.backgroundId, backgrounds]);

  const patchSettings = useCallback(async (patch: Partial<Settings>) => {
    const next = await api.store.setSettings(patch);
    setStore((prev) => (prev ? { ...prev, settings: next } : prev));
  }, []);

  if (booting || !store) return <div className="boot" />;

  if (!auth) {
    return (
      <div className="shell">
        <Titlebar />
        <Login onAuthed={(a) => setAuth(a)} />
      {update && (
        <div className="update-banner">
          <span>Доступна версия {update.version}{update.notes ? ` — ${update.notes}` : ''}</span>
          <button
            className="mini-btn primary"
            disabled={updating}
            onClick={async () => {
              setUpdating(true);
              try {
                await api.app.updateInstall();
              } catch (e) {
                setToast(String(e));
                setUpdating(false);
              }
            }}
          >
            {updating ? 'Обновляю…' : 'Обновить'}
          </button>
          <button className="mini-btn" onClick={() => setUpdate(null)}>✕</button>
        </div>
      )}
      {toast && <div className="toast">{toast}</div>}
      </div>
    );
  }

  const server = SERVERS.find((s) => s.id === serverId) ?? SERVERS[0];
  const bg = backgrounds.find((b) => b.id === store.settings.backgroundId) ?? backgrounds[0];

  const play = async () => {
    setState('working');
    setProgress({ stage: 'Подготовка', done: 0, total: 1, speed: 0 });
    const res = await api.game.launch();
    if (!res.ok) {
      setState('idle');
      setProgress(null);
      setToast(res.error ?? 'Не удалось запустить игру');
    }
  };

  const logout = async () => {
    await api.auth.logout();
    setAuth(null);
  };

  return (
    <div className="shell">
      <Titlebar />
      <div className="body">
        <Sidebar
          current={serverId}
          onSelect={(id) => {
            setServerId(id);
            api.app.setLastServer(id);
          }}
          skinBase64={skin?.pngBase64 ?? null}
          onProfile={() => setModal('skin')}
          nickname={auth.nick}
          onLogout={logout}
        />
        <main className="stage">
          <Hero
            server={server}
            bgUrl={bg ? bgSrc(bg.file) : null}
            bgId={bg?.id ?? null}
            bgFile={bg?.file ?? null}
            scene={store.settings.scene}
          />
          <Playbar
            serverName="Create"
            version={server.version}
            state={state}
            progress={progress}
            onPlay={play}
            onSettings={() => setModal('settings')}
            onBackgrounds={() => setModal('backgrounds')}
            onWorkshop={() => setModal('workshop')}
          />
        </main>
      </div>

      {modal === 'skin' && (
        <SkinModal skin={skin} nickname={store.settings.nickname} authNick={auth?.nick} onChange={setSkin} onClose={() => setModal(null)} />
      )}
      {modal === 'settings' && (
        <SettingsModal settings={store.settings} onChange={patchSettings} onClose={() => setModal(null)} />
      )}
      {modal === 'backgrounds' && (
        <BackgroundsModal
          currentId={store.settings.backgroundId}
          scene={store.settings.scene}
          onApply={(id) => patchSettings({ backgroundId: id })}
          onScene={(s) => patchSettings({ scene: s })}
          onClose={() => setModal(null)}
        />
      )}
      {modal === 'workshop' && (
        <WorkshopModal
          current={store.settings.userTheme as never}
          nickname={auth.nick}
          onApply={(t) => setStore((prev) => (prev ? { ...prev, settings: { ...prev.settings, userTheme: t } } : prev))}
          onReset={() => setStore((prev) => (prev ? { ...prev, settings: { ...prev.settings, userTheme: null } } : prev))}
          onClose={() => setModal(null)}
        />
      )}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
