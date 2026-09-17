// カード number-clamp の Contract を検証するテスト
import { clamp } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('number-clamp: clamp', () => {
  it('引数 3 個は下限・上限の範囲に収め、境界値を含む', () => {
    expect(clamp(120, 0, 100)).toBe(100);
    expect(clamp(-5, 0, 100)).toBe(0);
    expect(clamp(42, 0, 100)).toBe(42);
    expect(clamp(0, 0, 100)).toBe(0);
    expect(clamp(100, 0, 100)).toBe(100);
  });

  it('引数 2 個は上限のみで、下限は設けない', () => {
    expect(clamp(120, 100)).toBe(100);
    expect(clamp(3, 5)).toBe(3);
    expect(clamp(-1, 5)).toBe(-1);
  });

  it('第 3 引数が undefined または null なら 2 個の形式として扱う', () => {
    expect(clamp(10, 5, undefined as unknown as number)).toBe(5);
    expect(clamp(10, 5, null as unknown as number)).toBe(5);
  });

  it('min > max なら常に max を返す', () => {
    expect(clamp(1, 15, 5)).toBe(5);
    expect(clamp(10, 15, 5)).toBe(5);
    expect(clamp(100, 15, 5)).toBe(5);
  });

  it('どれか 1 つでも NaN なら NaN', () => {
    expect(clamp(Number.NaN, 0, 10)).toBeNaN();
    expect(clamp(5, Number.NaN, 10)).toBeNaN();
    expect(clamp(5, 0, Number.NaN)).toBeNaN();
  });
});
