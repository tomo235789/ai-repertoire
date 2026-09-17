// カード collection-partition の Contract を検証するテスト
import { partition } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-partition: partition', () => {
  it('真の要素と偽の要素に順序を保って振り分ける', () => {
    const [even, odd] = partition([1, 2, 3, 4, 5], (n) => n % 2 === 0);
    expect(even).toEqual([2, 4]);
    expect(odd).toEqual([1, 3, 5]);
  });

  it('入力配列を変更せず、要素は同じ参照を返す', () => {
    const a = { ok: true };
    const input = [a, { ok: false }];
    const [truthy, falsy] = partition(input, (x) => x.ok);
    expect(input).toHaveLength(2);
    expect(truthy[0]).toBe(a);
    expect(falsy[0]).toBe(input[1]);
  });

  it('isInTruthy は各要素につき 1 回、先頭から順に呼ばれる', () => {
    const seen: number[] = [];
    partition([3, 1, 2], (n) => {
      seen.push(n);
      return n > 1;
    });
    expect(seen).toEqual([3, 1, 2]);
  });

  it('戻り値は truthy / falsy で判定する', () => {
    const [truthy, falsy] = partition([0, 1, '', 'a', null], (v) => v);
    expect(truthy).toEqual([1, 'a']);
    expect(falsy).toEqual([0, '', null]);
  });

  it('型ガードを渡すと両側の型が絞り込まれる', () => {
    const [strs, nums] = partition([1, 'a', 2, 'b'], (v): v is string => typeof v === 'string');
    const upper: string[] = strs.map((s) => s.toUpperCase());
    const doubled: number[] = nums.map((n) => n * 2);
    expect(upper).toEqual(['A', 'B']);
    expect(doubled).toEqual([2, 4]);
  });

  it('空配列は空配列の組を返す', () => {
    expect(partition([], () => true)).toEqual([[], []]);
  });
});
