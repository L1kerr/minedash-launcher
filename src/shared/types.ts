// Shared contracts between main and renderer.

export interface Settings {
  nickname: string;
  authUrl: string;
  backgroundId: string;
  scene: 'none' | 'heli' | 'train' | 'airship' | 'rocket' | 'jet';
  userTheme?: import('../lib/themes').UserThemeLike | null;
  javaPath: string | null; // null = bundled/auto
  memoryMb: number;
  jvmArgs: string;
  resolutionW: number;
  resolutionH: number;
  fullscreen: boolean;
  serverAddress: string;
  autoJoin: boolean;
  closeOnPlay: boolean;
}

export const DEFAULT_SETTINGS: Settings = {
  nickname: '',
  authUrl: 'http://127.0.0.1:8787',
  backgroundId: 'b:space.png',
  scene: 'heli',
  javaPath: null,
  memoryMb: 4096,
  jvmArgs: '',
  resolutionW: 1280,
  resolutionH: 720,
  fullscreen: false,
  serverAddress: 'mc.minedash.fun',
  autoJoin: true,
  closeOnPlay: false
};

/** Сохранённая сессия MineDash-аккаунта (после входа в лаунчере). */
export interface AuthState {
  token: string;
  nick: string;
  uuid: string;
}

export type LoginResult =
  | { ok: true; auth: AuthState }
  | { ok: false; error: string };

export interface AuthAccountView {
  nick: string;
  uuid: string;
}

export interface ProgressState {
  stage: string; // human readable stage label
  file?: string;
  done: number; // bytes or items done
  total: number;
  speed: number; // bytes/sec
}

export interface LaunchResult {
  ok: boolean;
  error?: string;
}

export interface SkinPayload {
  pngBase64: string; // 64x64 skin
  model: 'classic' | 'slim';
}

export interface BackgroundMeta {
  id: string;
  name: string;
  file: string;
  builtin: boolean;
  category: string;
}

export interface StoreShape {
  settings: Settings;
  skin: { model: 'classic' | 'slim'; file: string | null } | null;
  backgrounds: { id: string; name: string; file: string }[];
  lastVersion: string;
  lastServer: string;
  auth: AuthState | null;
}
