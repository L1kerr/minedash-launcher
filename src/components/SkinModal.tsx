import { useRef, useState } from 'react';
import { SkinPayload } from '../shared/types';
import { api } from '../lib/api';
import Modal from './Modal';
import SkinPreview from './SkinPreview';

interface Props {
  skin: SkinPayload | null;
  nickname: string;
  authNick?: string;
  onChange: (s: SkinPayload | null) => void;
  onClose: () => void;
}

export default function SkinModal({ skin, nickname, authNick, onChange, onClose }: Props) {
  const [model, setModel] = useState<'classic' | 'slim'>(skin?.model ?? 'classic');
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const accept = async (file: File) => {
    setError(null);
    const img = new Image();
    const url = URL.createObjectURL(file);
    await new Promise<void>((res, rej) => {
      img.onload = () => res();
      img.onerror = () => rej(new Error('bad'));
      img.src = url;
    }).catch(() => null);
    URL.revokeObjectURL(url);
    const valid = img.width % 64 === 0 && (img.height === img.width || img.height === img.width / 2);
    if (!valid) {
      setError('Нужен PNG-скин (64×64, 64×32, 128×128, 128×64 и т.д.)');
      return;
    }
    // ресайзим до стандартного 64×64 / 64×32 (Minecraft требует именно этот размер)
    const targetW = 64;
    const targetH = img.height === img.width ? 64 : 32;
    const c = document.createElement('canvas');
    c.width = targetW;
    c.height = targetH;
    const cx = c.getContext('2d');
    if (!cx) return;
    cx.imageSmoothingEnabled = false;
    cx.drawImage(img, 0, 0, targetW, targetH);
    const resized = c.toDataURL('image/png');
    const next = await api.skin.set(resized, model);
    onChange(next);
  };

  return (
    <Modal title="Профиль" onClose={onClose}>
      <div className="skin-layout">
        <div className="skin-preview">
          {skin ? (
            <SkinPreview base64={skin.pngBase64} model={model} size={220} />
          ) : (
            <div className="skin-empty">скин не задан</div>
          )}
          <div className="skin-name">
            <b>{nickname}</b>
            <span>{authNick ? `аккаунт: ${authNick}` : 'локальная временная сессия'}</span>
          </div>
        </div>
        <div className="skin-side">
          <div className="field-label">Тип модели</div>
          <div className="segmented">
            <button
              className={model === 'classic' ? 'on' : ''}
              onClick={async () => {
                setModel('classic');
                onChange(await api.skin.setModel('classic'));
              }}
            >
              Classic
            </button>
            <button
              className={model === 'slim' ? 'on' : ''}
              onClick={async () => {
                setModel('slim');
                onChange(await api.skin.setModel('slim'));
              }}
            >
              Slim
            </button>
          </div>
          <div className="field-label">Файл скина</div>
          <div
            className={'dropzone' + (drag ? ' drag' : '')}
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              const f = e.dataTransfer.files?.[0];
              if (f) accept(f);
            }}
            onClick={() => fileRef.current?.click()}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.7">
              <path d="M12 16V4.5M7.5 9 12 4.5 16.5 9" />
              <path d="M4.5 15v3.5a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5V15" />
            </svg>
            <span>Перетащите PNG или нажмите</span>
            <input
              ref={fileRef}
              type="file"
              accept="image/png"
              hidden
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) accept(f);
                e.target.value = '';
              }}
            />
          </div>
          {error && <div className="form-error">{error}</div>}
          <button
            className="ghost-btn"
            onClick={async () => {
              onChange(await api.skin.reset());
            }}
          >
            Сбросить к стандартному
          </button>
        </div>
      </div>
    </Modal>
  );
}
