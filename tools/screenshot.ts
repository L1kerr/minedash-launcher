// Дымовой скриншот: запускает НАСТОЯЩИЙ лаунчер (dist-electron/main.js),
// после старта снимает его окно в D:\Temp\opencode\smoke2\screenshot.png
import * as fs from 'node:fs';
import { spawn } from 'node:child_process';
import * as path from 'node:path';

const OUT = 'D:\\Temp\\opencode\\smoke2';
fs.mkdirSync(OUT, { recursive: true });

const electron = path.join(process.cwd(), 'node_modules', 'electron', 'cli.js');
const proc = spawn(process.execPath, [electron, '.'], {
  cwd: process.cwd(),
  env: { ...process.env, MINEDASH_SHOT: '1', MINEDASH_NO_AUTH: '1' },
  stdio: ['ignore', 'pipe', 'pipe']
});
let out = '';
proc.stdout.on('data', (d) => (out += d));
proc.stderr.on('data', (d) => (out += d));

// даём окну появиться
await new Promise((r) => setTimeout(r, 9000));

// снимаем окно через PowerShell-независимый способ: просим сам Electron снять скрин через DevTools
// проще: запускаем второй процесс, который через remote debugging не нужен —
// вместо этого main.js лаунчера при MINEDASH_SHOT сам снимает скриншот.

// контроль: ждём файл
const shot = path.join(OUT, 'screenshot.png');
let ok = false;
for (let i = 0; i < 15; i++) {
  if (fs.existsSync(shot) && fs.statSync(shot).size > 5000) { ok = true; break; }
  await new Promise((r) => setTimeout(r, 1000));
}
proc.kill();
console.log(ok ? 'SMOKE OK' : 'SMOKE FAIL: скриншот не создан');
console.log('--- ошибки рендерера ---');
console.log(out.split('\n').filter((l) => /Uncaught|TypeError|ReferenceError|Cannot find/.test(l)).join('\n') || '(нет)');
fs.writeFileSync(path.join(OUT, 'stdout.log'), out);
process.exit(ok ? 0 : 1);
