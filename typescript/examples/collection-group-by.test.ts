// カード collection-group-by の Contract を検証するテスト
import { groupBy } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-group-by: groupBy', () => {
  it('同じキーの要素を出現順のままグループにまとめる', () => {
    const items = [
      { type: 'a', n: 1 },
      { type: 'b', n: 2 },
      { type: 'a', n: 3 },
    ];
    expect(groupBy(items, (x) => x.type)).toEqual({
      a: [
        { type: 'a', n: 1 },
        { type: 'a', n: 3 },
      ],
      b: [{ type: 'b', n: 2 }],
    });
  });

  it('入力配列を変更せず、要素は同じ参照でプレーンオブジェクトを返す', () => {
    const a = { type: 'a' };
    const input = [a, { type: 'b' }];
    const result = groupBy(input, (x) => x.type);
    expect(input).toHaveLength(2);
    expect(result.a[0]).toBe(a);
    expect(Object.getPrototypeOf(result)).toBe(Object.prototype);
  });

  it('getKeyFromItem は各要素につき 1 回、先頭から順に呼ばれる', () => {
    const seen: number[] = [];
    groupBy([10, 20, 10], (n) => {
      seen.push(n);
      return n;
    });
    expect(seen).toEqual([10, 20, 10]);
  });

  it('数値キーは文字列化され、1 と "1" は同じグループになる', () => {
    const result = groupBy<number | string, number | string>([1, '1', 2], (x) => x);
    expect(result).toEqual({ '1': [1, '1'], '2': [2] });
  });

  it('Object.prototype にある名前もキーにできる', () => {
    expect(groupBy(['x', 'y'], () => 'toString')).toEqual({ toString: ['x', 'y'] });
  });

  it('空配列は空オブジェクトを返す', () => {
    expect(groupBy([], (x) => x)).toEqual({});
  });
});
