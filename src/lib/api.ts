import type { BackgroundMeta, StoreShape, SkinPayload, AuthState, Settings, ProgressState } from '../shared/types';
import { invoke, convertFileSrc } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

export interface Api {
  win: {
    minimize: () => Promise<void>;
    maximize: () => Promise<void>;
    close: () => Promise<void>;
    isMaximized: () => Promise<boolean>;
    onMaximized: (cb: (m: boolean) => void) => void;
  };
  store: {
    get: () => Promise<StoreShape>;
    setSettings: (patch: Partial<Settings>) => Promise<Settings>;
  };
  skin: {
    get: () => Promise<SkinPayload | null>;
    set: (dataUrl: string, model: 'classic' | 'slim') => Promise<SkinPayload | null>;
    setModel: (model: 'classic' | 'slim') => Promise<SkinPayload | null>;
    reset: () => Promise<SkinPayload | null>;
  };
  backgrounds: {
    list: () => Promise<BackgroundMeta[]>;
    add: () => Promise<BackgroundMeta | null>;
    remove: (id: string) => Promise<BackgroundMeta[]>;
    getDataUrl: (path: string) => Promise<string | null>;
  };
  app: {
    version: () => Promise<string>;
    pickJava: () => Promise<string | null>;
    setLastServer: (id: string) => Promise<void>;
    openExternal: (url: string) => Promise<void>;
    openGameDir: () => Promise<void>;
    updateCheck: () => Promise<UpdateCheck>;
    updateInstall: () => Promise<void>;
  };
  auth: {
    login: (nick: string, password: string) => Promise<{ ok: boolean; auth?: AuthState; error?: string }>;
    restore: () => Promise<AuthState | null>;
    logout: () => Promise<void>;
  };
  theme: {
    get: () => Promise<UserTheme | null>;
    set: (theme: UserTheme) => Promise<UserTheme>;
    reset: () => Promise<void>;
    export: () => Promise<string>;
    import: () => Promise<{ theme: UserTheme; backgroundId: string | null }>;
  };
  workshop: {
    list: () => Promise<WorkshopItem[]>;
    publish: (item: WorkshopItem) => Promise<WorkshopItem>;
    install: (id: string) => Promise<{ theme: UserTheme; backgroundId: string | null }>;
    uninstall: (id: string) => Promise<void>;
    like: (id: string) => Promise<WorkshopItem[]>;
  };
  game: {
    launch: () => Promise<{ ok: boolean; error?: string }>;
    onProgress: (cb: (p: ProgressState) => void) => void;
    onState: (cb: (s: string) => void) => void;
    onLog: (cb: (line: string) => void) => void;
    onExit: (cb: (code: number | null) => void) => void;
    onError: (cb: (error: string) => void) => void;
  };
}

export const api: Api = {
  win: {
    minimize: () => invoke('win_minimize'),
    maximize: () => invoke('win_maximize'),
    close: () => invoke('win_close'),
    isMaximized: () => invoke<boolean>('win_is_maximized'),
    onMaximized: (cb) => { listen('win:maximized', (e) => cb(e.payload as boolean)); },
  },
  store: {
    get: () => invoke('store_get'),
    setSettings: (patch) => invoke('store_set_settings', { patch })
  },
  skin: {
    get: () => invoke('skin_get'),
    set: (dataUrl, model) => invoke('skin_set', { payload: { dataUrl, model } }),
    setModel: (model) => invoke('skin_set_model', { model }),
    reset: () => invoke('skin_reset')
  },
  backgrounds: {
    list: () => invoke('backgrounds_list'),
    add: () => invoke('backgrounds_add'),
    remove: (id) => invoke('backgrounds_remove', { id }),
    getDataUrl: (path: string) => invoke<string | null>('background_get_data_url', { path })
  },
  app: {
    version: () => invoke('app_version'),
    pickJava: () => invoke<string | null>('app_pick_java'),
    setLastServer: (id) => invoke('app_set_last_server', { id }),
    openExternal: (url) => invoke('app_open_external', { url }),
    openGameDir: () => invoke('app_open_game_dir'),
    updateCheck: () => invoke<UpdateCheck>('update_check'),
    updateInstall: () => invoke('update_install')
  },
  auth: {
    login: (nick, password) => invoke('auth_login', { nick, password }),
    restore: () => invoke('auth_restore'),
    logout: () => invoke('auth_logout')
  },
  theme: {
    get: () => invoke<UserTheme | null>('theme_get'),
    set: (theme: UserTheme) => invoke<UserTheme>('theme_set', { theme }),
    reset: () => invoke<void>('theme_reset'),
    export: () => invoke<string>('theme_export'),
    import: () => invoke<{ theme: UserTheme; backgroundId: string | null }>('theme_import')
  },
  workshop: {
    list: () => invoke<WorkshopItem[]>('workshop_list'),
    publish: (item: WorkshopItem) => invoke<WorkshopItem>('workshop_publish', { item }),
    install: (id: string) => invoke<{ theme: UserTheme; backgroundId: string | null }>('workshop_install', { id }),
    uninstall: (id: string) => invoke<void>('workshop_uninstall', { id }),
    like: (id: string) => invoke<WorkshopItem[]>('workshop_like', { id })
  },
  game: {
    launch: () => invoke('game_launch'),
    onProgress: (cb) => { listen('game:progress', (e) => cb(e.payload as ProgressState)); },
    onState: (cb) => { listen('game:state', (e) => cb(e.payload as string)); },
    onLog: (cb) => { listen('game:log', (e) => cb(e.payload as string)); },
    onExit: (cb) => { listen('game:exit', (e) => cb(e.payload as number | null)); },
    onError: (cb) => { listen('game:error', (e) => cb(e.payload as string)); }
  }
};

/** URL для отображения локального файла (замена electron-протокола bg://). */
export function bgSrc(filePath: string): string {
  return convertFileSrc(filePath);
}

export interface UserTheme {
  name: string;
  author: string;
  /** категория для каталога Workshop */
  category?: string;
  bgId?: string | null;
  bg: string;
  panel: string;
  panel2: string;
  line: string;
  line2: string;
  line3: string;
  chip: string;
  chipHover: string;
  accent: string;
  accentHover: string;
  accentSoft: string;
  cyan: string;
}

export interface UpdateInfo {
  version: string;
  url: string;
  notes: string;
}

export interface UpdateCheck {
  available: boolean;
  current: string;
  info: UpdateInfo | null;
}

export interface WorkshopItem {
  id: string;
  title: string;
  author: string;
  description: string;
  theme: UserTheme;
  preview: string | null;
  likes: number;
  downloads: number;
  created: number;
  installed: boolean;
  liked: boolean;
}
