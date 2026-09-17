// カード collection-sliding-window の Contract を検証するテスト
import { chunk, windowed } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-sliding-window: windowed', () => {
  it('既定では step 1 で、size の窓を順序どおりに返す', () => {
    expect(windowed([1, 2, 3, 4, 5], 3)).toEqual([
      [1, 2, 3],
      [2, 3, 4],
      [3, 4, 5],
    ]);
  });

  it('入力配列を変更せず、各窓は新しい配列で要素は同じ参照', () => {
    const a = { id: 1 };
    const input = [a, { id: 2 }];
    const result = windowed(input, 1);
    expect(input).toHaveLength(2);
    expect(result[0]).not.toBe(input);
    expect(result[0][0]).toBe(a);
  });

  it('step > size なら窓の間の要素を飛ばす', () => {
    expect(windowed([1, 2, 3, 4, 5], 2, 3)).toEqual([
      [1, 2],
      [4, 5],
    ]);
  });

  it('既定では size に満たない末尾の窓を捨て、配列長が size 未満なら空配列', () => {
    expect(windowed([1, 2, 3, 4, 5], 3, 2)).toEqual([
      [1, 2, 3],
      [3, 4, 5],
    ]);
    expect(windowed([1, 2, 3, 4], 3, 2)).toEqual([[1, 2, 3]]);
    expect(windowed([1, 2], 3)).toEqual([]);
  });

  it('partialWindows: true なら末尾の短い窓も返す', () => {
    expect(windowed([1, 2, 3, 4, 5], 3, 2, { partialWindows: true })).toEqual([
      [1, 2, 3],
      [3, 4, 5],
      [5],
    ]);
    expect(windowed([1, 2], 3, 1, { partialWindows: true })).toEqual([[1, 2], [2]]);
  });

  it('step = size かつ partialWindows: true は chunk と同じ結果になる', () => {
    const input = [1, 2, 3, 4, 5];
    expect(windowed(input, 2, 2, { partialWindows: true })).toEqual(chunk(input, 2));
  });

  it('空配列は空配列を返す', () => {
    expect(windowed([], 2)).toEqual([]);
  });

  it('size または step が正の整数でなければ例外を投げる', () => {
    expect(() => windowed([1, 2, 3], 0)).toThrow('Size must be a positive integer.');
    expect(() => windowed([1, 2, 3], -1)).toThrow();
    expect(() => windowed([1, 2, 3], 1.5)).toThrow();
    expect(() => windowed([1, 2, 3], Number.NaN)).toThrow();
    expect(() => windowed([1, 2, 3], 2, 0)).toThrow('Step must be a positive integer.');
    expect(() => windowed([1, 2, 3], 2, -1)).toThrow();
    expect(() => windowed([1, 2, 3], 2, 1.5)).toThrow();
  });
});
