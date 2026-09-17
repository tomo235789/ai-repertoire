// カード collection-flatten の Contract を検証するテスト
import { flatten, flattenDeep } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-flatten: flatten', () => {
  it('既定では 1 段だけ順序を保って展開する', () => {
    expect(flatten([1, [2, [3, [4]]]])).toEqual([1, 2, [3, [4]]]);
  });

  it('depth で展開する段数を指定できる', () => {
    expect(flatten([1, [2, [3, [4]]]], 2)).toEqual([1, 2, 3, [4]]);
  });

  it('入力配列を変更せず、depth より深い配列は同じ参照を返す', () => {
    const inner = [3];
    const input = [1, [2, inner]];
    const result = flatten(input);
    expect(input).toEqual([1, [2, [3]]]);
    expect(result).not.toBe(input);
    expect(result[2]).toBe(inner);
  });

  it('depth の小数は切り捨て、0 以下なら浅いコピーを返す', () => {
    expect(flatten([1, [2, [3, [4]]]], 2.9)).toEqual([1, 2, 3, [4]]);
    expect(flatten([1, [2]], 0)).toEqual([1, [2]]);
    expect(flatten([1, [2]], -1)).toEqual([1, [2]]);
  });

  it('Infinity を渡すと全段展開し、flattenDeep と同じ結果になる', () => {
    const input = [1, [2, [3, [4]]]];
    expect(flatten(input, Number.POSITIVE_INFINITY)).toEqual([1, 2, 3, 4]);
    expect(flattenDeep(input)).toEqual([1, 2, 3, 4]);
  });

  it('配列以外（文字列）は展開しない', () => {
    expect(flatten(['ab', ['cd']])).toEqual(['ab', 'cd']);
  });

  it('疎配列の空きスロットは undefined として残る', () => {
    const sparse: (number | undefined)[] = [1, , 2]; // eslint-disable-line no-sparse-arrays
    expect(flatten(sparse)).toEqual([1, undefined, 2]);
    expect(flatten(sparse)).toHaveLength(3);
  });

  it('空配列は空配列を返す', () => {
    expect(flatten([])).toEqual([]);
  });
});
