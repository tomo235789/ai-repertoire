// カード number-round-to の Contract を検証するテスト
import { round } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('number-round-to: round', () => {
  it('precision 省略時は整数に、指定時はその桁で四捨五入する', () => {
    expect(round(1.2345)).toBe(1);
    expect(round(1.2345, 2)).toBe(1.23);
    expect(round(1.2345, 3)).toBe(1.235);
  });

  it('precision が負なら 10 の位・100 の位で丸める', () => {
    expect(round(1234.5678, -2)).toBe(1200);
    expect(round(1250, -2)).toBe(1300);
  });

  it('.5 は正の無限大方向に丸める（偶数丸めではない）', () => {
    expect(round(2.5)).toBe(3);
    expect(round(-2.5)).toBe(-2);
    expect(round(-1.5)).toBe(-1);
  });

  it('浮動小数点の補正はしない', () => {
    expect(round(1.005, 2)).toBe(1);
    expect(round(1.255, 2)).toBe(1.25);
  });

  it('precision が整数でなければ例外を投げる', () => {
    expect(() => round(1.2345, 3.1)).toThrow();
    expect(() => round(1.2345, Number.NaN)).toThrow();
  });

  it('NaN と Infinity はそのまま、極端な precision では NaN', () => {
    expect(round(Number.NaN, 2)).toBeNaN();
    expect(round(Number.POSITIVE_INFINITY, 2)).toBe(Number.POSITIVE_INFINITY);
    expect(round(1.1, 400)).toBeNaN();
    expect(round(123, -400)).toBeNaN();
  });
});
