import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Heart, ImagePlus, Plus, Search, Trash2, Wand2 } from 'lucide-react';
import { api, bgSrc, UserTheme, WorkshopItem } from '../lib/api';
import { BackgroundMeta } from '../shared/types';
import { EMPTY_USER_THEME } from '../lib/themes';
import Modal from './Modal';

interface Props {
  current: UserTheme | null;
  nickname: string;
  onApply: (t: UserTheme) => void;
  onReset: () => void;
  onClose: () => void;
}

type Tab = 'browse' | 'mine' | 'editor';

const CATEGORIES = ['Все', 'Тёмные', 'Неон', 'Природа', 'Ретро', 'Прочее'] as const;

const FIELDS: Array<[keyof UserTheme, string]> = [
  ['bg', 'Фон окна'], ['panel', 'Панель'], ['panel2', 'Панель 2'],
  ['line', 'Линия'], ['line2', 'Линия 2'], ['line3', 'Линия 3'],
  ['chip', 'Чипы'], ['chipHover', 'Чипы (hover)'],
  ['accent', 'Акцент'], ['accentHover', 'Акцент (hover)'], ['cyan', 'Доп. цвет'],
];

export default function WorkshopModal({ current, nickname, onApply, onReset, onClose }: Props) {
  const [tab, setTab] = useState<Tab>('browse');
  const [items, setItems] = useState<WorkshopItem[]>([]);
  const [bgs, setBgs] = useState<BackgroundMeta[]>([]);
  const [query, setQuery] = useState('');
  const [cat, setCat] = useState<string>('Все');
  const [themeCat, setThemeCat] = useState<string>(
    (current as UserTheme & { category?: string } | null)?.category ?? 'Тёмные'
  );
  const [theme, setTheme] = useState<UserTheme>(
    current ? { ...current, author: nickname } : ({ ...EMPTY_USER_THEME, author: nickname } as UserTheme)
  );
  const [status, setStatus] = useState<string | null>(null);

  const refresh = () => api.workshop.list().then(setItems);
  useEffect(() => {
    refresh();
    api.backgrounds.list().then(setBgs);
  }, []);

  const itemCategory = (i: WorkshopItem): string => {
    const t = i.theme as UserTheme & { category?: string };
    return t.category || 'Прочее';
  };
  const filtered = useMemo(
    () => items.filter((i) =>
      (i.title.toLowerCase().includes(query.toLowerCase()) ||
      i.author.toLowerCase().includes(query.toLowerCase())) &&
      (cat === 'Все' || itemCategory(i) === cat)),
    [items, query, cat]
  );
  const mine = useMemo(() => items.filter((i) => i.author === nickname), [items, nickname]);

  return (
    <Modal title="Workshop — стилистики лаунчера" onClose={onClose} xwide>
      <div className="ws-tabs">
        <button className={'ws-tab' + (tab === 'browse' ? ' active' : '')} onClick={() => setTab('browse')}>
          <Download size={13} /> Обзор
        </button>
        <button className={'ws-tab' + (tab === 'mine' ? ' active' : '')} onClick={() => setTab('mine')}>
          <Heart size={13} /> Мои работы
        </button>
        <button className={'ws-tab' + (tab === 'editor' ? ' active' : '')} onClick={() => setTab('editor')}>
          <Wand2 size={13} /> Создать
        </button>
        {tab !== 'editor' && (
          <label className="ws-search">
            <Search size={13} />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Поиск…" />
          </label>
        )}
      </div>

      {tab === 'browse' && (
        <>
          <div className="ws-cats">
            {CATEGORIES.map((c) => (
              <button key={c} className={'ws-cat' + (cat === c ? ' active' : '')} onClick={() => setCat(c)}>
                {c}
              </button>
            ))}
            <span className="ws-count">{filtered.length} работ</span>
          </div>
          <div className="ws-gallery">
          {filtered.map((item, i) => (
            <motion.div
              key={item.id}
              className={'ws-item' + (item.installed ? ' installed' : '')}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <div className="ws-item-preview" style={{ background: item.theme.bg }}>
                {item.preview && <img className="ws-item-bg" src={item.preview} alt="" />}
                <div className="ws-mini in-card">
                  <div className="ws-mini-title" style={{ background: item.theme.panel, borderBottom: `1px solid ${item.theme.line}` }}>
                    <i style={{ background: item.theme.accent }} />
                    <span style={{ color: item.theme.cyan }}>MineDash</span>
                    <em style={{ background: item.theme.chip, borderColor: item.theme.line2 }}>— □ ×</em>
                  </div>
                  <div className="ws-mini-body">
                    <div className="ws-mini-side" style={{ background: item.theme.panel, borderRight: `1px solid ${item.theme.line}` }}>
                      <i className="on" style={{ background: item.theme.accentSoft, borderColor: item.theme.accent }} />
                      <i style={{ background: item.theme.chip, borderColor: item.theme.line2 }} />
                      <i style={{ background: item.theme.chip, borderColor: item.theme.line2 }} />
                    </div>
                    <div className="ws-mini-hero">
                      <b>{item.title}</b>
                      <span style={{ color: item.theme.cyan }}>{item.author}</span>
                    </div>
                  </div>
                  <div className="ws-mini-play" style={{ background: item.theme.panel2, borderTop: `1px solid ${item.theme.line}` }}>
                    <span className="ws-mini-srv">
                      <b>Стиль лаунчера</b>
                      <small style={{ color: item.theme.line3 }}>
                        {item.downloads} загрузок • <i className="ok" style={{ background: '#4ade80' }} /> {item.likes}
                      </small>
                    </span>
                    <em className="ws-mini-btn" style={{ background: item.theme.accent, boxShadow: `0 6px 18px ${item.theme.accentSoft}` }}>ИГРАТЬ</em>
                  </div>
                </div>
                {item.installed && <em className="ws-item-badge">Установлена</em>}
              </div>
              <div className="ws-item-info">
                <b>{item.title}</b>
                <span className="ws-item-author">{item.author}</span>
                <p>{item.description}</p>
              </div>
              <div className="ws-item-foot">
                <button
                  className={'ws-like' + (item.liked ? ' liked' : '')}
                  onClick={async () => setItems(await api.workshop.like(item.id))}
                >
                  <Heart size={13} fill={item.liked ? 'currentColor' : 'none'} /> {item.likes}
                </button>
                <button className={'ws-install' + (item.installed ? ' installed' : '')} onClick={async () => {
                  const r = await api.workshop.install(item.id);
                  onApply(r.theme);
                  setStatus(`«${item.title}» установлена`);
                  refresh();
                }}>
                  {item.installed ? 'Выбрано' : <><Download size={13} /> Установить</>}
                </button>
              </div>
            </motion.div>
          ))}
            {filtered.length === 0 && <div className="ws-empty">Ничего не найдено</div>}
          </div>
        </>
      )}

      {tab === 'mine' && (
        <div className="ws-gallery">
          {mine.map((item) => (
            <div key={item.id} className="ws-item">
              <div className="ws-item-preview" style={{ background: item.theme.bg }}>
                {item.preview && <img className="ws-item-bg" src={item.preview} alt="" />}
                <div className="ws-mini in-card">
                  <div className="ws-mini-title" style={{ background: item.theme.panel, borderBottom: `1px solid ${item.theme.line}` }}>
                    <i style={{ background: item.theme.accent }} />
                    <span style={{ color: item.theme.cyan }}>MineDash</span>
                    <em style={{ background: item.theme.chip, borderColor: item.theme.line2 }}>— □ ×</em>
                  </div>
                  <div className="ws-mini-body">
                    <div className="ws-mini-side" style={{ background: item.theme.panel, borderRight: `1px solid ${item.theme.line}` }}>
                      <i className="on" style={{ background: item.theme.accentSoft, borderColor: item.theme.accent }} />
                      <i style={{ background: item.theme.chip, borderColor: item.theme.line2 }} />
                      <i style={{ background: item.theme.chip, borderColor: item.theme.line2 }} />
                    </div>
                    <div className="ws-mini-hero">
                      <b>{item.title}</b>
                      <span style={{ color: item.theme.cyan }}>{item.author}</span>
                    </div>
                  </div>
                  <div className="ws-mini-play" style={{ background: item.theme.panel2, borderTop: `1px solid ${item.theme.line}` }}>
                    <span className="ws-mini-srv">
                      <b>Стиль лаунчера</b>
                      <small style={{ color: item.theme.line3 }}>
                        {item.downloads} загрузок • <i className="ok" style={{ background: '#4ade80' }} /> {item.likes}
                      </small>
                    </span>
                    <em className="ws-mini-btn" style={{ background: item.theme.accent, boxShadow: `0 6px 18px ${item.theme.accentSoft}` }}>ИГРАТЬ</em>
                  </div>
                </div>
              </div>
              <div className="ws-item-info">
                <b>{item.title}</b>
                <span className="ws-item-author">{item.author}</span>
                <p>Загрузок: {item.downloads} · Лайков: {item.likes}</p>
              </div>
              <div className="ws-item-foot">
                <button className="ws-uninstall" onClick={async () => {
                  await api.workshop.uninstall(item.id);
                  onReset();
                  refresh();
                }}>
                  <Trash2 size={13} /> Удалить
                </button>
              </div>
            </div>
          ))}
          {mine.length === 0 && (
            <div className="ws-empty">
              Пока нет работ. Создай тему во вкладке «Создать» и опубликуй!
            </div>
          )}
        </div>
      )}

      {tab === 'editor' && (
        <div className="ws-layout">
          <div className="ws-editor">
            <div className="ws-row">
              <label className="ws-field">
                <span>Название</span>
                <input value={theme.name} onChange={(e) => setTheme({ ...theme, name: e.target.value })} />
              </label>
              <label className="ws-field">
                <span>Автор</span>
                <input value={nickname || 'Игрок'} readOnly disabled />
              </label>
            </div>
            <label className="ws-field">
              <span>Категория</span>
              <select value={themeCat} onChange={(e) => setThemeCat(e.target.value)}>
                {CATEGORIES.filter((c) => c !== 'Все').map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
            <div className="ws-bg-block">
              <span className="ws-bg-title">Фон лаунчера</span>
              <div className="ws-bg-list">
                <button
                  className={'ws-bg-tile' + (theme.bgId == null ? ' active' : '')}
                  onClick={() => setTheme({ ...theme, bgId: null })}
                >
                  <i style={{ background: theme.bg }} />
                  <em className="ws-bg-check">✓</em>
                  <span>Цвет</span>
                </button>
                {bgs.map((b) => (
                  <button
                    key={b.id}
                    className={'ws-bg-tile' + (theme.bgId === b.id ? ' active' : '')}
                    onClick={() => setTheme({ ...theme, bgId: b.id })}
                  >
                    <img src={bgSrc(b.file)} alt={b.name} />
                    <em className="ws-bg-check">✓</em>
                  </button>
                ))}
                <button
                  className="ws-bg-add"
                  onClick={async () => {
                    const added = await api.backgrounds.add();
                    if (added) {
                      setBgs(await api.backgrounds.list());
                      setTheme((t) => ({ ...t, bgId: added.id }));
                    }
                  }}
                >
                  <ImagePlus size={16} />
                </button>
              </div>
            </div>
            <div className="ws-colors">
              {FIELDS.map(([key, label]) => (
                <label key={key} className="ws-color">
                  <input type="color" value={toHex(theme[key] as string)} onChange={(e) => setTheme({ ...theme, [key]: e.target.value })} />
                  <span>{label}</span>
                </label>
              ))}
              <label className="ws-color">
                <input type="color" value={toHex(theme.accentSoft)} onChange={(e) => setTheme({ ...theme, accentSoft: e.target.value })} />
                <span>Акцент (мягкий)</span>
              </label>
            </div>
          </div>
          <div className="ws-side">
            <div className="ws-preview" style={{ background: theme.bg, borderColor: theme.line2 }}>
              {theme.bgId && (() => {
                const b = bgs.find((x) => x.id === theme.bgId);
                return b ? <img className="ws-prev-bg" src={bgSrc(b.file)} alt="" /> : null;
              })()}
              <div className="ws-mini">
                <div className="ws-mini-title" style={{ background: theme.panel, borderBottom: `1px solid ${theme.line}` }}>
                  <em className="ws-mini-winbtns">
                    <span style={{ background: theme.chip, borderColor: theme.line2 }} />
                    <span style={{ background: theme.chip, borderColor: theme.line2 }} />
                    <span style={{ background: theme.chip, borderColor: theme.line2 }} />
                  </em>
                </div>
                <div className="ws-mini-body">
                  <div className="ws-mini-side" style={{ background: theme.panel, borderRight: `1px solid ${theme.line}` }}>
                    <i className="on" style={{ background: theme.accentSoft, borderColor: theme.accent }} />
                    <i style={{ background: theme.chip, borderColor: theme.line2 }} />
                    <i style={{ background: theme.chip, borderColor: theme.line2 }} />
                    <i className="gap" />
                    <i className="avatar" style={{ background: theme.chip, borderColor: theme.line2 }} />
                    <i className="logout" style={{ background: theme.chip, borderColor: theme.line2 }} />
                  </div>
                </div>
                <div className="ws-mini-play" style={{ background: theme.panel2, borderTop: `1px solid ${theme.line}` }}>
                  <i className="srv" style={{ background: theme.chip, borderColor: theme.line2 }}>
                    <em style={{ background: theme.accent }} />
                  </i>
                  <span className="ws-mini-srv">
                    <b>Create</b>
                    <small style={{ color: theme.line3 }}>Версия 1.21.1 • <i className="ok" style={{ background: '#4ade80' }} /> Онлайн</small>
                  </span>
                  <em className="ws-mini-btn" style={{ background: theme.accent, boxShadow: `0 6px 18px ${theme.accentSoft}` }}>ИГРАТЬ</em>
                  <span className="ws-mini-icons">
                    <i style={{ background: theme.chip, borderColor: theme.line2 }} />
                    <i style={{ background: theme.chip, borderColor: theme.line2 }} />
                    <i style={{ background: theme.chip, borderColor: theme.line2 }} />
                  </span>
                </div>
              </div>
              <span className="ws-prev-hint">Так будет выглядеть лаунчер</span>
            </div>
            <div className="ws-actions">
              <button className="mini-btn primary" onClick={async () => {
                const withCat = { ...theme, category: themeCat };
                await api.theme.set(withCat);
                onApply(withCat);
                setStatus('Тема применена локально');
              }}>Применить</button>
              <button className="mini-btn" onClick={async () => {
                const published = await api.workshop.publish({
                  id: '', title: theme.name, author: nickname || 'Игрок',
                  description: 'Пользовательская тема', theme: { ...theme, category: themeCat },
                  preview: null, likes: 0, downloads: 0, created: 0, installed: false, liked: false,
                });
                await refresh();
                setStatus(`«${published.title}» опубликована`);
                setTab('mine');
              }}>
                <Plus size={13} /> Опубликовать
              </button>
              <button className="mini-btn" onClick={() => api.theme.export().catch((e) => setStatus(String(e)))}>
                Экспорт .mdstyle
              </button>
              <button className="mini-btn" onClick={async () => {
                await api.theme.reset();
                onReset();
                setStatus('Сброшено');
              }}>Сброс</button>
            </div>
            {status && <div className="ws-status">{status}</div>}
            <p className="ws-note">
              Опубликованная работа появится у всех игроков каталога Workshop. Экспорт .mdstyle — файл для передачи вручную.
            </p>
          </div>
        </div>
      )}
      {status && tab !== 'editor' && <div className="ws-status">{status}</div>}
    </Modal>
  );
}

function toHex(color: string): string {
  const m = /^#([0-9a-f]{6})$/i.exec(color.trim());
  return m ? color : '#000000';
}
