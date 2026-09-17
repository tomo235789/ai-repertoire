// カード collection-sort-by の Contract を検証するテスト
import { sortBy } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-sort-by: sortBy', () => {
  it('複数キーを左から順に評価し、前のキーが等しいときだけ次のキーで比較する', () => {
    const rows = [
      { g: 'b', v: 2 },
      { g: 'a', v: 9 },
      { g: 'b', v: 1 },
    ];
    expect(sortBy(rows, ['g', (r) => r.v])).toEqual([
      { g: 'a', v: 9 },
      { g: 'b', v: 1 },
      { g: 'b', v: 2 },
    ]);
  });

  it('安定ソート。キーが等しい要素は元の相対順を保つ', () => {
    const rows = [
      { k: 1, n: 'a' },
      { k: 0, n: 'b' },
      { k: 1, n: 'c' },
      { k: 0, n: 'd' },
    ];
    expect(sortBy(rows, ['k']).map((r) => r.n)).toEqual(['b', 'd', 'a', 'c']);
  });

  it('入力配列を変更せず、要素は同じ参照を返す', () => {
    const first = { v: 2 };
    const input = [first, { v: 1 }];
    const result = sortBy(input, ['v']);
    expect(input.map((r) => r.v)).toEqual([2, 1]);
    expect(result).not.toBe(input);
    expect(result[1]).toBe(first);
  });

  it('キー関数は比較のたびに呼ばれ、各要素 1 回ではない', () => {
    let calls = 0;
    sortBy([{ v: 3 }, { v: 1 }, { v: 2 }], [
      (r) => {
        calls += 1;
        return r.v;
      },
    ]);
    expect(calls).toBeGreaterThan(3);
  });

  it('null と undefined はこの順で末尾に置かれる', () => {
    const rows = [{ k: null }, { k: 2 }, { k: undefined }, { k: 1 }];
    expect(sortBy(rows, ['k']).map((r) => r.k)).toEqual([1, 2, null, undefined]);
  });

  it('文字列はコード単位で比較し、ロケールは考慮しない', () => {
    const rows = [{ s: 'b' }, { s: 'B' }, { s: 'a' }];
    expect(sortBy(rows, ['s']).map((r) => r.s)).toEqual(['B', 'a', 'b']);
  });

  it('空配列は空配列を返す', () => {
    expect(sortBy([] as { k: number }[], ['k'])).toEqual([]);
  });
});
