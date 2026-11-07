import * as crypto from 'node:crypto';
import * as zlib from 'node:zlib';

export interface ZipEntry {
  name: string;
  data?: Buffer;
  /** 0 = store, 8 = deflate. По умолчанию deflate, если задан data. */
  method?: 0 | 8;
}

export function crc32(buf: Buffer): number {
  let c = ~0;
  for (const b of buf) {
    c ^= b;
    for (let i = 0; i < 8; i++) c = c & 1 ? (c >>> 1) ^ 0xedb88320 : c >>> 1;
  }
  return ~c >>> 0;
}

export function sha1(buf: Buffer): string {
  return crypto.createHash('sha1').update(buf).digest('hex');
}

/** Собирает валидный ZIP-архив в памяти (store + deflate), без внешних утилит. */
export function buildZip(entries: ZipEntry[]): Buffer {
  const locals: Buffer[] = [];
  const centrals: Buffer[] = [];
  let offset = 0;

  for (const e of entries) {
    const nameBuf = Buffer.from(e.name, 'utf8');
    const raw = e.data ?? Buffer.alloc(0);
    const method = e.method ?? (e.data === undefined ? 0 : 8);
    const comp = method === 8 ? zlib.deflateRawSync(raw) : raw;
    const crc = crc32(raw);

    const lh = Buffer.alloc(30);
    lh.writeUInt32LE(0x04034b50, 0);
    lh.writeUInt16LE(20, 4);
    lh.writeUInt16LE(method, 8);
    lh.writeUInt32LE(crc, 14);
    lh.writeUInt32LE(comp.length, 18);
    lh.writeUInt32LE(raw.length, 22);
    lh.writeUInt16LE(nameBuf.length, 26);
    locals.push(lh, nameBuf, comp);

    const ch = Buffer.alloc(46);
    ch.writeUInt32LE(0x02014b50, 0);
    ch.writeUInt16LE(20, 4);
    ch.writeUInt16LE(20, 6);
    ch.writeUInt16LE(method, 10);
    ch.writeUInt32LE(crc, 16);
    ch.writeUInt32LE(comp.length, 20);
    ch.writeUInt32LE(raw.length, 24);
    ch.writeUInt16LE(nameBuf.length, 28);
    ch.writeUInt32LE(offset, 42);
    centrals.push(ch, nameBuf);

    offset += lh.length + nameBuf.length + comp.length;
  }

  const cd = Buffer.concat(centrals);
  const eocd = Buffer.alloc(22);
  eocd.writeUInt32LE(0x06054b50, 0);
  eocd.writeUInt16LE(entries.length, 8);
  eocd.writeUInt16LE(entries.length, 10);
  eocd.writeUInt32LE(cd.length, 12);
  eocd.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, cd, eocd]);
}

/** Фейковый JRE-архив Adoptium: один корневой каталог + bin/java.exe. */
export function buildFakeJreZip(): Buffer {
  return buildZip([
    { name: 'jdk-21.0.5+11-jre/' },
    { name: 'jdk-21.0.5+11-jre/bin/' },
    { name: 'jdk-21.0.5+11-jre/bin/java.exe', data: Buffer.from('MZ-fake-java') },
    { name: 'jdk-21.0.5+11-jre/release', data: Buffer.from('JAVA_VERSION="21.0.5"') }
  ]);
}
