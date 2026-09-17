// カード number-sum-by の Contract を検証するテスト
import { sumBy } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('number-sum-by: sumBy', () => {
  it('各要素から取り出した数値を合計し、入力を変更しない', () => {
    const items = [
      { name: 'a', qty: 2 },
      { name: 'b', qty: 3 },
    ];
    expect(sumBy(items, (item) => item.qty)).toBe(5);
    expect(items).toEqual([
      { name: 'a', qty: 2 },
      { name: 'b', qty: 3 },
    ]);
  });

  it('コールバックは各要素につき 1 回、(element, index) で先頭から順に呼ばれる', () => {
    const calls: Array<[number, number]> = [];
    sumBy([5, 6], (x, i) => {
      calls.push([x, i]);
      return x;
    });
    expect(calls).toEqual([
      [5, 0],
      [6, 1],
    ]);
  });

  it('空配列は 0 を返す', () => {
    expect(sumBy([], () => 1)).toBe(0);
  });

  it('返り値を数値に変換しない（文字列は連結、undefined は NaN）', () => {
    expect(sumBy(['1', '2'], (s) => s as unknown as number)).toBe('012');
    const sparse: Array<{ qty?: number }> = [{ qty: 1 }, {}];
    expect(sumBy(sparse, (x) => x.qty as number)).toBeNaN();
  });

  it('NaN を含むと NaN、浮動小数点の誤差はそのまま', () => {
    expect(sumBy([1, Number.NaN], (x) => x)).toBeNaN();
    expect(sumBy([0.1, 0.2], (x) => x)).toBe(0.30000000000000004);
  });

  it('コールバックが投げた例外はそのまま伝播する', () => {
    expect(() =>
      sumBy([1], () => {
        throw new Error('boom');
      }),
    ).toThrow('boom');
  });
});
