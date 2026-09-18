// カード set-difference の Contract を検証するテスト
import { difference as esDifference } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

// tsconfig の lib に Set メソッドの型が無い環境でも通るよう、最小限の型を局所宣言してキャストする
type SetLike<T> = { size: number; has(value: T): boolean; keys(): Iterator<T> };
type SetOps<T> = Set<T> & {
  difference(other: SetLike<unknown>): Set<T>;
  symmetricDifference<U>(other: SetLike<U>): Set<T | U>;
  intersection<U>(other: SetLike<U>): Set<T & U>;
  isSubsetOf(other: SetLike<unknown>): boolean;
  isSupersetOf(other: SetLike<unknown>): boolean;
  isDisjointFrom(other: SetLike<unknown>): boolean;
};
const setOf = <T>(...values: T[]): SetOps<T> => new Set(values) as SetOps<T>;

describe('set-difference: Set.prototype.difference', () => {
  it('this にあって other に無い要素を this の順で並べた新しい Set を返す', () => {
    const a = setOf(4, 3, 2, 1);
    const b = setOf(2, 4, 5);
    const result = a.difference(b);
    expect([...result]).toEqual([3, 1]);
    expect(result).not.toBe(a);
    expect([...b.difference(a)]).toEqual([5]);
  });

  it('this も other も変更しない', () => {
    const a = setOf(1, 2);
    const b = setOf(2);
    a.difference(b);
    expect([...a]).toEqual([1, 2]);
    expect([...b]).toEqual([2]);
  });

  it('引数は set-like でよく、Map ならキーで判定する', () => {
    expect([...setOf('a', 'b').difference(new Map([['a', 1]]))]).toEqual(['b']);
  });

  it('this が other 以下の大きさなら other.has で判定し、大きければ other.keys() を走査する', () => {
    const called: string[] = [];
    const small: SetLike<number> = {
      size: 10,
      has: (v) => {
        called.push(`has${v}`);
        return v === 1;
      },
      keys: () => {
        called.push('keys');
        return [].values();
      },
    };
    expect([...setOf(1, 2).difference(small)]).toEqual([2]);
    expect(called).toEqual(['has1', 'has2']);
    called.length = 0;
    const big: SetLike<number> = {
      size: 1,
      has: (v) => {
        called.push(`has${v}`);
        return false;
      },
      keys: () => {
        called.push('keys');
        return [2].values();
      },
    };
    expect([...setOf(1, 2, 3).difference(big)]).toEqual([1, 3]);
    expect(called).toEqual(['keys']);
  });

  it('配列を渡すと TypeError', () => {
    expect(() => setOf(1).difference([1] as unknown as SetLike<number>)).toThrow(TypeError);
    expect(() => setOf(1).isSubsetOf([1] as unknown as SetLike<number>)).toThrow(TypeError);
  });

  it('同一性は SameValueZero', () => {
    expect([...setOf(Number.NaN, 1).difference(setOf(Number.NaN))]).toEqual([1]);
    expect(setOf({ a: 1 }).difference(setOf({ a: 1 })).size).toBe(1);
  });

  it('this が空、または other が全要素を含むなら空。other が空なら this のコピー', () => {
    expect(setOf<number>().difference(setOf(1)).size).toBe(0);
    expect(setOf(1, 2).difference(setOf(1, 2)).size).toBe(0);
    const a = setOf(1, 2);
    expect(a.difference(a).size).toBe(0);
    const copy = a.difference(setOf());
    expect([...copy]).toEqual([1, 2]);
    expect(copy).not.toBe(a);
  });

  it('返り値は常にプレーンな Set で、サブクラスのインスタンスにはならない', () => {
    class MySet<T> extends Set<T> {}
    const result = (new MySet([1]) as unknown as SetOps<number>).difference(setOf());
    expect(Object.getPrototypeOf(result)).toBe(Set.prototype);
  });

  it('symmetricDifference は this 側の差、other 側の差の順に並ぶ', () => {
    expect([...setOf(3, 1, 2).symmetricDifference(setOf(2, 5, 4))]).toEqual([3, 1, 5, 4]);
  });

  it('intersection は小さい方を走査するため、並びは入力サイズで変わる', () => {
    expect([...setOf(1, 2, 3, 4).intersection(setOf(3, 2))]).toEqual([3, 2]);
    expect([...setOf(3, 2).intersection(setOf(1, 2, 3, 4))]).toEqual([3, 2]);
    expect([...setOf(1, 2, 3).intersection(setOf(3, 2, 5))]).toEqual([2, 3]);
  });

  it('isSubsetOf / isSupersetOf / isDisjointFrom は真偽値を返し、空集合は任意の集合の部分集合', () => {
    expect(setOf(1, 2).isSubsetOf(setOf(1, 2, 3))).toBe(true);
    expect(setOf(1, 2).isSubsetOf(setOf(1))).toBe(false);
    expect(setOf().isSubsetOf(setOf())).toBe(true);
    expect(setOf(1, 2, 3).isSupersetOf(setOf(1))).toBe(true);
    expect(setOf(1).isDisjointFrom(setOf(2))).toBe(true);
    expect(setOf(1).isDisjointFrom(setOf(1))).toBe(false);
  });

  it('es-toolkit の difference は配列を返し、arr1 の重複はそのまま残る', () => {
    expect(esDifference([1, 2, 2, 3], [2])).toEqual([1, 3]);
    expect(esDifference([1, 1, 3], [2])).toEqual([1, 1, 3]);
  });
});
