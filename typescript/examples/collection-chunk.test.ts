// カード collection-chunk の Contract を検証するテスト
import { chunk } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-chunk: chunk', () => {
  it('順序を保ったまま size ごとに分割し、最後は短くなる', () => {
    expect(chunk([1, 2, 3, 4, 5], 2)).toEqual([[1, 2], [3, 4], [5]]);
  });

  it('入力配列を変更しない', () => {
    const input = [1, 2, 3];
    const result = chunk(input, 2);
    expect(input).toEqual([1, 2, 3]);
    expect(result[0]).not.toBe(input);
  });

  it('空配列は空配列を返す', () => {
    expect(chunk([], 3)).toEqual([]);
  });

  it('size が正の整数でなければ例外を投げる', () => {
    expect(() => chunk([1, 2], 0)).toThrow();
    expect(() => chunk([1, 2], -1)).toThrow();
    expect(() => chunk([1, 2], 1.5)).toThrow();
    expect(() => chunk([1, 2], Number.NaN)).toThrow();
  });
});
