// カード collection-take-while の Contract を検証するテスト
import { dropWhile, takeWhile } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-take-while: takeWhile', () => {
  it('先頭から条件を満たす間だけ取り出し、最初に偽になった時点で打ち切る', () => {
    expect(takeWhile([1, 2, 3, 1], (n) => n < 3)).toEqual([1, 2]);
  });

  it('入力配列を変更せず、要素は同じ参照を返す', () => {
    const a = { ok: true };
    const input = [a, { ok: false }];
    const result = takeWhile(input, (x) => x.ok);
    expect(input).toHaveLength(2);
    expect(result).not.toBe(input);
    expect(result[0]).toBe(a);
  });

  it('述語は最初に偽を返した要素まで呼ばれ、それ以降は呼ばれない', () => {
    const seen: number[] = [];
    takeWhile([1, 2, 3, 4], (n) => {
      seen.push(n);
      return n < 3;
    });
    expect(seen).toEqual([1, 2, 3]);
  });

  it('戻り値は truthy / falsy で判定する', () => {
    // 型は boolean を要求するが、実装は truthy 判定なので 0 で打ち切られる
    expect(takeWhile([1, 2, 0, 3], (n) => n as unknown as boolean)).toEqual([1, 2]);
  });

  it('すべて真なら浅いコピー、先頭で偽なら空配列を返す', () => {
    const input = [1, 2];
    const all = takeWhile(input, () => true);
    expect(all).toEqual([1, 2]);
    expect(all).not.toBe(input);
    expect(takeWhile(input, () => false)).toEqual([]);
  });

  it('dropWhile と連結すると元配列に戻る', () => {
    const input = [1, 2, 3, 1];
    const pred = (n: number) => n < 3;
    expect([...takeWhile(input, pred), ...dropWhile(input, pred)]).toEqual(input);
  });

  it('空配列は空配列を返す', () => {
    expect(takeWhile([], () => true)).toEqual([]);
  });
});
