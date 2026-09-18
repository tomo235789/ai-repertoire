// カード set-union の Contract を検証するテスト
import { union as esUnion } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

// tsconfig の lib に Set メソッドの型が無い環境でも通るよう、最小限の型を局所宣言してキャストする
type SetLike<T> = { size: number; has(value: T): boolean; keys(): Iterator<T> };
type SetOps<T> = Set<T> & { union<U>(other: SetLike<U>): Set<T | U> };
const setOf = <T>(...values: T[]): SetOps<T> => new Set(values) as SetOps<T>;

describe('set-union: Set.prototype.union', () => {
  it('this の要素が先、次に other にしか無い要素を other の順で並べた新しい Set を返す', () => {
    const a = setOf(3, 1, 2);
    const b = setOf(2, 4, 1);
    const result = a.union(b);
    expect([...result]).toEqual([3, 1, 2, 4]);
    expect(result).not.toBe(a);
    expect([...b.union(a)]).toEqual([2, 4, 1, 3]);
  });

  it('this も other も変更しない', () => {
    const a = setOf(1);
    const b = setOf(2);
    a.union(b);
    expect([...a]).toEqual([1]);
    expect([...b]).toEqual([2]);
  });

  it('引数は set-like でよく、Map ならキーが要素になる。has は呼ばれない', () => {
    expect([...setOf(1).union(new Map([[2, 'x']]))]).toEqual([1, 2]);
    const called: string[] = [];
    const setLike: SetLike<number> = {
      size: 1,
      has: () => {
        called.push('has');
        return false;
      },
      keys: () => {
        called.push('keys');
        return [2, 2, 3].values();
      },
    };
    expect([...setOf(1).union(setLike)]).toEqual([1, 2, 3]);
    expect(called).toEqual(['keys']);
  });

  it('配列やイテレータを渡すと TypeError', () => {
    expect(() => setOf(1).union([2] as unknown as SetLike<number>)).toThrow(TypeError);
    expect(() => setOf(1).union(setOf(2).values() as unknown as SetLike<number>)).toThrow(TypeError);
  });

  it('同一性は SameValueZero', () => {
    expect(setOf(Number.NaN).union(setOf(Number.NaN)).size).toBe(1);
    expect(setOf(0).union(setOf(-0)).size).toBe(1);
    expect(setOf({ a: 1 }).union(setOf({ a: 1 })).size).toBe(2);
  });

  it('空同士なら空、片方が空なら他方のコピー', () => {
    expect(setOf().union(setOf()).size).toBe(0);
    expect([...setOf(1).union(setOf())]).toEqual([1]);
    expect([...setOf<number>().union(setOf(1))]).toEqual([1]);
  });

  it('返り値は常にプレーンな Set で、サブクラスのインスタンスにはならない', () => {
    class MySet<T> extends Set<T> {}
    const result = (new MySet([1]) as unknown as SetOps<number>).union(setOf(2));
    expect(Object.getPrototypeOf(result)).toBe(Set.prototype);
    expect(result).not.toBeInstanceOf(MySet);
  });

  it('引数が不正なら TypeError または RangeError', () => {
    expect(() => setOf(1).union(null as unknown as SetLike<number>)).toThrow(TypeError);
    expect(() => setOf(1).union({ size: Number.NaN, has: () => false, keys: () => [].values() })).toThrow(TypeError);
    expect(() => setOf(1).union({ size: -1, has: () => false, keys: () => [].values() })).toThrow(RangeError);
    expect(() => setOf(1).union({ size: 1, has: 1 as unknown as () => boolean, keys: () => [].values() })).toThrow(
      TypeError,
    );
  });

  it('es-toolkit の union は配列を返し、arr1 側の重複も除去される', () => {
    expect(esUnion([3, 1, 2], [2, 4, 1])).toEqual([3, 1, 2, 4]);
    expect(esUnion([1, 1, 2], [2])).toEqual([1, 2]);
  });
});
