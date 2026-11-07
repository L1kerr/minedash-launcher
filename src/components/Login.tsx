import { FormEvent, useState } from 'react';
import { api } from '../lib/api';
import { AuthState } from '../shared/types';

interface Props {
  onAuthed: (auth: AuthState) => void;
}

export default function Login({ onAuthed }: Props) {
  const [nick, setNick] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setError(null);
    if (!nick.trim()) return setError('Введите игровой ник.');
    if (!password) return setError('Введите пароль.');
    setBusy(true);
    const res = await api.auth.login(nick, password);
    setBusy(false);
    if (res.ok && res.auth) onAuthed(res.auth);
    else setError(res.error ?? 'Ошибка входа');
  };

  return (
    <div className="login-veil">
      <form className="login-card" onSubmit={submit}>
        <div className="login-brand">
          <svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" strokeWidth="1.6">
            <path d="M12 2.5 21 7.5v9L12 21.5 3 16.5v-9L12 2.5Z" />
            <path d="M3 7.5 12 12.5l9-5M12 12.5v9" />
          </svg>
          <div className="login-brand-meta">
            <div className="login-brand-row">
              <b>MineDash</b>
              <span className="badge-beta">BETA</span>
            </div>
            <span className="login-brand-sub">Community Launcher</span>
          </div>
        </div>
        <h2>Вход в аккаунт</h2>
        <p className="login-hint">
          Ник и пароль выдаются после одобрения заявки в Telegram-боте и регистрации.
        </p>
        <label className="field">
          <span>Игровой ник</span>
          <input
            value={nick}
            maxLength={16}
            autoComplete="username"
            autoFocus
            onChange={(e) => setNick(e.target.value)}
          />
        </label>
        <label className="field">
          <span>Пароль</span>
          <input
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <div className="form-error">{error}</div>}
        <button className="play-btn login-submit" type="submit" disabled={busy}>
          {busy ? 'ПРОВЕРКА…' : 'ВОЙТИ'}
        </button>
      </form>
    </div>
  );
}
