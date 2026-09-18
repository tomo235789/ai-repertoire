// カード iter-range の Contract を検証するテスト
import { range, rangeRight } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('iter-range: range', () => {
  it('start 以上 end 未満を step 刻みで並べた新しい配列を返す', () => {
    expect(range(4)).toEqual([0, 1, 2, 3]);
    expect(range(1, 4)).toEqual([1, 2, 3]);
    expect(range(0, 20, 5)).toEqual([0, 5, 10, 15]);
    expect(range(0, 10, 3)).toEqual([0, 3, 6, 9]);
    expect(range(3)).not.toBe(range(3));
  });

  it('負の step で降順になる', () => {
    expect(range(0, -4, -1)).toEqual([0, -1, -2, -3]);
  });

  it('届かない範囲は空配列', () => {
    expect(range(5, 1)).toEqual([]);
    expect(range(1, 4, -1)).toEqual([]);
    expect(range(2, 2)).toEqual([]);
    expect(range(0)).toEqual([]);
    expect(range(-3)).toEqual([]);
  });

  it('start / end は小数でもよく、要素数は ceil((end - start) / step)', () => {
    expect(range(0.5, 3)).toEqual([0.5, 1.5, 2.5]);
    expect(range(2.5)).toEqual([0, 1, 2]);
    expect(range(1, 4, 2)).toEqual([1, 3]);
  });

  it('step が 0・小数・NaN なら Error', () => {
    expect(() => range(0, 5, 0)).toThrow(Error);
    expect(() => range(0, 5, 0.5)).toThrow(Error);
    expect(() => range(0, 5, Number.NaN)).toThrow(Error);
  });

  it('end が NaN や Infinity なら RangeError', () => {
    expect(() => range(Number.NaN)).toThrow(RangeError);
    expect(() => range(Number.POSITIVE_INFINITY)).toThrow(RangeError);
  });

  it('rangeRight は同じ要素を逆順に返す', () => {
    expect(rangeRight(4)).toEqual([3, 2, 1, 0]);
    expect(rangeRight(1, 4)).toEqual([3, 2, 1]);
    expect(rangeRight(0, 20, 5)).toEqual([15, 10, 5, 0]);
    expect(rangeRight(0, 10, 3)).toEqual([...range(0, 10, 3)].reverse());
    expect(rangeRight(5, 1)).toEqual([]);
  });
});
