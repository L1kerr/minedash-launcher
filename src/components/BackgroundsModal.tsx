import { useEffect, useState } from 'react';
import { BackgroundMeta } from '../shared/types';
import { api, bgSrc } from '../lib/api';
import Modal from './Modal';

interface Props {
  currentId: string;
  scene: 'none' | 'heli' | 'train' | 'airship' | 'rocket' | 'jet';
  onApply: (id: string) => void;
  onScene: (scene: 'none' | 'heli' | 'train' | 'airship' | 'rocket' | 'jet') => void;
  onClose: () => void;
}

export default function BackgroundsModal({ currentId, scene, onApply, onScene, onClose }: Props) {
  const [items, setItems] = useState<BackgroundMeta[]>([]);
  const [cat, setCat] = useState<string>('Все');

  useEffect(() => {
    api.backgrounds.list().then(setItems);
  }, []);

  const cats = ['Все', ...Array.from(new Set(items.map((b) => b.category)))];
  const visible = cat === 'Все' ? items : items.filter((b) => b.category === cat);

  return (
    <Modal title="Фон лаунчера" onClose={onClose} wide>
      <div className="scene-picker">
        <span className="scene-label">Сцена:</span>
        <div className="scene-seg">
          {([['none', 'Без сцены'], ['heli', 'Вертолёт'], ['train', 'Поезд'], ['airship', 'Дирижабль'], ['rocket', 'Ракета'], ['jet', 'Истребитель']] as const).map(([v, label]) => (
            <button
              key={v}
              className={'scene-opt' + (scene === v ? ' active' : '')}
              onClick={() => onScene(v)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="cat-tabs">
        {cats.map((c) => (
          <button
            key={c}
            className={'cat-tab' + (cat === c ? ' active' : '')}
            onClick={() => setCat(c)}
          >
            {c}
          </button>
        ))}
      </div>
      <div className="bg-grid">
        {visible.map((b) => {
          const src = bgSrc(b.file);
          const isVideo = b.file.endsWith('.mp4') || b.file.endsWith('.webm');
          return (
          <div key={b.id} className={'bg-card' + (b.id === currentId ? ' active' : '')}>
            {isVideo ? (
              <video src={src} autoPlay loop muted playsInline />
            ) : (
              <img
                src={src}
                alt={b.name}
                onError={(e) => {
                  api.backgrounds.getDataUrl(b.file).then((du) => {
                    if (du) (e.target as HTMLImageElement).src = du;
                  });
                }}
              />
            )}
            <div className="bg-card-foot">
              <span>{b.name}</span>
              <div className="bg-card-actions">
                {!b.builtin && (
                  <button
                    className="mini-btn"
                    onClick={async () => {
                      const list = await api.backgrounds.remove(b.id);
                      setItems(list);
                      if (currentId === b.id) onApply(list[0]?.id ?? '');
                    }}
                  >
                    Удалить
                  </button>
                )}
                <button className="mini-btn primary" onClick={() => onApply(b.id)}>
                  {b.id === currentId ? 'Выбран' : 'Выбрать'}
                </button>
              </div>
            </div>
          </div>
          );
        })}
        <button
          className="bg-add"
          onClick={async () => {
            const added = await api.backgrounds.add();
            const list = await api.backgrounds.list();
            setItems(list);
            if (added) onApply(added.id);
          }}
        >
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.7">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Своё изображение
        </button>
      </div>
    </Modal>
  );
}
