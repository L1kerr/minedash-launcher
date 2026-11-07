import { describe, expect, it } from 'vitest';
import { fmtBytes, fmtSpeed, pct } from '../src/lib/format';

describe('fmtBytes', () => {
  it('форматирует байты', () => expect(fmtBytes(0)).toBe('0 Б'));
  it('форматирует байты ниже КБ', () => expect(fmtBytes(1023)).toBe('1023 Б'));
  it('форматирует КБ без дробной части', () => expect(fmtBytes(2048)).toBe('2 КБ'));
  it('форматирует МБ с одним знаком', () => expect(fmtBytes(5 * 1024 * 1024)).toBe('5.0 МБ'));
  it('форматирует ГБ с двумя знаками', () =>
    expect(fmtBytes(3 * 1024 * 1024 * 1024)).toBe('3.00 ГБ'));
});

describe('fmtSpeed', () => {
  it('добавляет суффикс скорости', () => expect(fmtSpeed(1024 * 1024)).toBe('1.0 МБ/с'));
});

describe('pct', () => {
  it('возвращает 0 при нулевом total', () => expect(pct(10, 0)).toBe(0));
  it('считает процент', () => expect(pct(1, 4)).toBe(25));
  it('округляет', () => expect(pct(1, 3)).toBe(33));
  it('не превышает 100', () => expect(pct(10, 4)).toBe(100));
});
