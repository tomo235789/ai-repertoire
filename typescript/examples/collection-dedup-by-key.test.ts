// カード collection-dedup-by-key の Contract を検証するテスト
import { uniqBy } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-dedup-by-key: uniqBy', () => {
  it('同じキーは最初の要素を残し、順序を保つ', () => {
    const users = [
      { id: 1, name: 'a' },
      { id: 2, name: 'b' },
      { id: 1, name: 'c' },
    ];
    expect(uniqBy(users, (u) => u.id)).toEqual([
      { id: 1, name: 'a' },
      { id: 2, name: 'b' },
    ]);
  });

  it('入力配列を変更せず、要素は同じ参照を返す', () => {
    const a = { id: 1 };
    const input = [a, { id: 1 }];
    const result = uniqBy(input, (u) => u.id);
    expect(input).toHaveLength(2);
    expect(result[0]).toBe(a);
  });

  it('mapper は各要素につき 1 回、先頭から順に呼ばれる', () => {
    const seen: number[] = [];
    uniqBy([10, 20, 10], (n) => {
      seen.push(n);
      return n;
    });
    expect(seen).toEqual([10, 20, 10]);
  });

  it('キー比較は SameValueZero（NaN 同士は等しい、オブジェクトは参照）', () => {
    expect(uniqBy([Number.NaN, Number.NaN], (n) => n)).toHaveLength(1);
    expect(uniqBy([{ k: 1 }, { k: 1 }], (o) => ({ k: o.k }))).toHaveLength(2);
  });

  it('空配列は空配列を返す', () => {
    expect(uniqBy([], (x) => x)).toEqual([]);
  });
});
