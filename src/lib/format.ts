export function fmtBytes(n: number): string {
  if (n >= 1 << 30) return (n / (1 << 30)).toFixed(2) + ' ГБ';
  if (n >= 1 << 20) return (n / (1 << 20)).toFixed(1) + ' МБ';
  if (n >= 1 << 10) return (n / (1 << 10)).toFixed(0) + ' КБ';
  return n + ' Б';
}

export function fmtSpeed(n: number): string {
  return fmtBytes(n) + '/с';
}

export function pct(done: number, total: number): number {
  if (!total) return 0;
  return Math.min(100, Math.round((done / total) * 100));
}
