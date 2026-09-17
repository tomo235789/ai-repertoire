// カード function-memoize の Contract を検証するテスト
import { memoize } from 'es-toolkit';
import { describe, expect, it, vi } from 'vitest';

describe('function-memoize: memoize', () => {
  it('第 1 引数をキーにして 2 回目以降は fn を呼ばない', () => {
    const fn = vi.fn((n: number) => n * 2);
    const m = memoize(fn);
    expect(m(2)).toBe(4);
    expect(m(2)).toBe(4);
    expect(m(3)).toBe(6);
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('fn には第 1 引数だけが渡され、第 2 引数以降はキーに含まれない', () => {
    const fn = vi.fn((a: number, b?: number) => [a, b]);
    const m = memoize(fn);
    expect(m(1, 2)).toEqual([1, undefined]);
    expect(m(1, 3)).toEqual([1, undefined]); // キャッシュヒット
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('getCacheKey の戻り値をキーにできる', () => {
    const fn = vi.fn((u: { id: number }) => u.id * 10);
    const m = memoize(fn, { getCacheKey: (u) => u.id });
    expect(m({ id: 1 })).toBe(10);
    expect(m({ id: 1 })).toBe(10);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('キー比較は SameValueZero（オブジェクトは参照、NaN 同士は等しい）', () => {
    const objFn = vi.fn((o: { x: number }) => o.x);
    const m = memoize(objFn);
    m({ x: 1 });
    m({ x: 1 });
    expect(objFn).toHaveBeenCalledTimes(2);
    const nanFn = vi.fn((n: number) => n);
    const mn = memoize(nanFn);
    mn(Number.NaN);
    mn(Number.NaN);
    expect(nanFn).toHaveBeenCalledTimes(1);
  });

  it('fn が例外を投げた場合は保存せず、次回また呼ぶ', () => {
    let attempts = 0;
    const m = memoize((n: number) => {
      attempts++;
      if (attempts === 1) throw new Error('first');
      return n;
    });
    expect(() => m(1)).toThrow('first');
    expect(m(1)).toBe(1);
    expect(m.cache.size).toBe(1);
  });

  it('cache オプションで差し替えたキャッシュがそのまま公開される', () => {
    const cache = new Map<number, number>();
    const m = memoize((n: number) => n + 1, { cache });
    m(1);
    expect(m.cache).toBe(cache);
    expect(cache.get(1)).toBe(2);
    m.cache.clear();
    expect(cache.size).toBe(0);
  });

  it('this を保持し、fn 自体は変更しない', () => {
    const fn = function (this: { base: number }, n: number) {
      return this.base + n;
    };
    const obj = { base: 100, calc: memoize(fn) };
    expect(obj.calc(1)).toBe(101);
    expect(fn.call({ base: 5 }, 1)).toBe(6);
  });
});
