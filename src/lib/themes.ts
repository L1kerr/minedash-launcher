/**
 * Темы оболочки лаунчера. Палитра подбирается под категорию выбранного фона,
 * чтобы чёрный «корпус» (тайтлбар, сайдбар, плейбар, карточка) не выбивался из сцены.
 */

export interface LauncherTheme {
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

const DEFAULT_THEME: LauncherTheme = {
  bg: '#0a0c0f',
  panel: '#0d1116',
  panel2: '#10141a',
  line: '#1b2128',
  line2: '#232a31',
  line3: '#2c343d',
  chip: '#14181d',
  chipHover: '#1a2026',
  accent: '#2f6fed',
  accentHover: '#3b82f6',
  accentSoft: 'rgba(47, 111, 237, 0.14)',
  cyan: '#35b6d9'
};

const THEMES: Record<string, Partial<LauncherTheme>> = {
  // холодный индиго с бирюзой
  Космос: {
    bg: '#070a12',
    panel: '#0a0e18',
    panel2: '#0d1220',
    line: '#161c2c',
    line2: '#1d2537',
    line3: '#273142',
    chip: '#111726',
    chipHover: '#18202f',
    accent: '#3d6cf0',
    accentHover: '#4d7cf8',
    accentSoft: 'rgba(61, 108, 240, 0.16)',
    cyan: '#4fc3e8'
  },
  // тёплая охра и песок
  Пустоши: {
    bg: '#120c07',
    panel: '#17100a',
    panel2: '#1d140c',
    line: '#2a1d12',
    line2: '#352618',
    line3: '#432f1e',
    chip: '#1a120b',
    chipHover: '#241a11',
    accent: '#d97a2b',
    accentHover: '#e88a37',
    accentSoft: 'rgba(217, 122, 43, 0.16)',
    cyan: '#e0a45c'
  },
  // ночной город с неоновым акцентом
  Город: {
    bg: '#080b12',
    panel: '#0b0f18',
    panel2: '#0e131e',
    line: '#171e2b',
    line2: '#1f2836',
    line3: '#2a3546',
    chip: '#121824',
    chipHover: '#1a2231',
    accent: '#e0417f',
    accentHover: '#ee4f8d',
    accentSoft: 'rgba(224, 65, 127, 0.16)',
    cyan: '#45c7f0'
  },
  // лесная зелень
  Природа: {
    bg: '#0b0d09',
    panel: '#0f120c',
    panel2: '#131710',
    line: '#1c2218',
    line2: '#242c1f',
    line3: '#303a29',
    chip: '#141a11',
    chipHover: '#1c2417',
    accent: '#d99a2b',
    accentHover: '#e8a838',
    accentSoft: 'rgba(217, 154, 43, 0.16)',
    cyan: '#8fc45e'
  },
  // латунь и железо
  Create: {
    bg: '#100d0a',
    panel: '#16120d',
    panel2: '#1b1611',
    line: '#282017',
    line2: '#33291d',
    line3: '#403425',
    chip: '#1a150f',
    chipHover: '#241d14',
    accent: '#c4963e',
    accentHover: '#d6a54a',
    accentSoft: 'rgba(196, 150, 62, 0.16)',
    cyan: '#d8b464'
  }
};

export function themeForCategory(category?: string): LauncherTheme {
  return { ...DEFAULT_THEME, ...(category ? THEMES[category] ?? {} : {}) };
}

/** Пользовательская тема из Workshop перекрывает палитру категории. */
export function themeFromUser(user: UserThemeLike | null | undefined): LauncherTheme | null {
  if (!user) return null;
  return {
    bg: user.bg || DEFAULT_THEME.bg,
    panel: user.panel || DEFAULT_THEME.panel,
    panel2: user.panel2 || DEFAULT_THEME.panel2,
    line: user.line || DEFAULT_THEME.line,
    line2: user.line2 || DEFAULT_THEME.line2,
    line3: user.line3 || DEFAULT_THEME.line3,
    chip: user.chip || DEFAULT_THEME.chip,
    chipHover: user.chipHover || DEFAULT_THEME.chipHover,
    accent: user.accent || DEFAULT_THEME.accent,
    accentHover: user.accentHover || DEFAULT_THEME.accentHover,
    accentSoft: user.accentSoft || DEFAULT_THEME.accentSoft,
    cyan: user.cyan || DEFAULT_THEME.cyan
  };
}

export interface UserThemeLike {
  name?: string;
  author?: string;
  bgId?: string | null;
  bg?: string;
  panel?: string;
  panel2?: string;
  line?: string;
  line2?: string;
  line3?: string;
  chip?: string;
  chipHover?: string;
  accent?: string;
  accentHover?: string;
  accentSoft?: string;
  cyan?: string;
}

export const EMPTY_USER_THEME: UserThemeLike = {
  name: 'Моя тема',
  author: '',
  bgId: null,
  bg: '#0a0c0f',
  panel: '#0d1116',
  panel2: '#10141a',
  line: '#1b2128',
  line2: '#232a31',
  line3: '#2c343d',
  chip: '#14181d',
  chipHover: '#1a2026',
  accent: '#2f6fed',
  accentHover: '#3b82f6',
  accentSoft: 'rgba(47, 111, 237, 0.14)',
  cyan: '#35b6d9'
};

/** Записывает палитру в CSS-переменные документа. */
export function applyTheme(theme: LauncherTheme): void {
  const root = document.documentElement.style;
  root.setProperty('--bg', theme.bg);
  root.setProperty('--panel', theme.panel);
  root.setProperty('--panel-2', theme.panel2);
  root.setProperty('--line', theme.line);
  root.setProperty('--line-2', theme.line2);
  root.setProperty('--line-3', theme.line3);
  root.setProperty('--chip', theme.chip);
  root.setProperty('--chip-hover', theme.chipHover);
  root.setProperty('--accent', theme.accent);
  root.setProperty('--accent-hover', theme.accentHover);
  root.setProperty('--accent-soft', theme.accentSoft);
  root.setProperty('--blue', theme.accent);
  root.setProperty('--blue-2', theme.accent);
  root.setProperty('--cyan', theme.cyan);
}
