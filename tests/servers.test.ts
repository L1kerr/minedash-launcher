import { describe, expect, it } from 'vitest';
import { SERVERS } from '../src/lib/servers';
import { DEFAULT_SETTINGS } from '../src/shared/types';

describe('SERVERS', () => {
  it('содержит create и survival', () => {
    expect(SERVERS.map((s) => s.id)).toEqual(['create', 'survival']);
  });

  it('все серверы полностью описаны', () => {
    for (const s of SERVERS) {
      expect(s.tag).toMatch(/-СЕРВЕР$/);
      expect(s.name.length).toBeGreaterThan(0);
      expect(s.subtitle.length).toBeGreaterThan(0);
      expect(s.description.length).toBeGreaterThan(0);
      expect(s.address).toContain('.');
      expect(s.version).toMatch(/^\d+\.\d+(\.\d+)?$/);
    }
  });

  it('id уникальны', () => {
    expect(new Set(SERVERS.map((s) => s.id)).size).toBe(SERVERS.length);
  });

  it('адрес сервера по умолчанию совпадает со списком', () => {
    expect(SERVERS.some((s) => s.address === DEFAULT_SETTINGS.serverAddress)).toBe(true);
  });
});
