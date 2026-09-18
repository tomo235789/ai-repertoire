// カード iter-lazy-filter の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

// tsconfig の lib に Iterator helpers の型が無い環境でも通るよう、使うメソッドだけを局所的に宣言してキャストする
type IterHelper<T> = {
  map<U>(callbackfn: (value: T, index: number) => U): IterHelper<U>;
  filter(predicate: (value: T, index: number) => unknown): IterHelper<T>;
  take(limit: number): IterHelper<T>;
  toArray(): T[];
} & IteratorObject<T, undefined, unknown>;
const iter = <T>(src: Iterator<T> | Iterable<T>): IterHelper<T> =>
  (globalThis as unknown as { Iterator: { from<T>(src: Iterator<T> | Iterable<T>): IterHelper<T> } }).Iterator.from(src);

function* naturalsGen(): Generator<number, void, undefined> {
  let n = 0;
  while (true) yield n++;
}
const naturals = (): IterHelper<number> => iter(naturalsGen());

describe('iter-lazy-filter: Iterator.prototype.filter', () => {
  it('遅延評価で、next() のたびに真の要素が見つかるまで元を進める', () => {
    const calls: number[] = [];
    const filtered = iter([1, 2, 3, 4]).filter((x) => {
      calls.push(x);
      return x % 2 === 0;
    });
    expect(calls).toEqual([]);
    expect(filtered.next()).toEqual({ value: 2, done: false });
    expect(calls).toEqual([1, 2]);
    expect(filtered.toArray()).toEqual([4]);
    expect(calls).toEqual([1, 2, 3, 4]);
  });

  it('無限ジェネレータでも必要な分しか判定しない', () => {
    expect(naturals().filter((n) => n % 3 === 0).take(3).toArray()).toEqual([0, 3, 6]);
  });

  it('順序を保持し、index は落とした要素も数えた元の位置', () => {
    const seen: number[] = [];
    const result = iter(['a', 'b', 'c', 'd'])
      .filter((_, i) => {
        seen.push(i);
        return i !== 1;
      })
      .toArray();
    expect(result).toEqual(['a', 'c', 'd']);
    expect(seen).toEqual([0, 1, 2, 3]);
  });

  it('filter の後ろの map の index は絞り込み後の連番になる', () => {
    expect(iter([10, 11, 12, 13]).filter((x) => x % 2 === 1).map((x, i) => [x, i]).toArray()).toEqual([
      [11, 0],
      [13, 1],
    ]);
  });

  it('述語の戻り値は truthy 判定', () => {
    expect(iter([0, 1, '', null, 'a']).filter((x) => x).toArray()).toEqual([1, 'a']);
  });

  it('1 回しか走査できず、要素は同じ参照のまま', () => {
    const obj = { v: 1 };
    const filtered = iter([obj]).filter(() => true);
    expect(filtered.toArray()[0]).toBe(obj);
    expect(filtered.toArray()).toEqual([]);
  });

  it('空のイテレータからは空を返し、例外を投げない', () => {
    expect(iter([]).filter(() => true).toArray()).toEqual([]);
  });

  it('述語が関数でないと呼んだ時点で TypeError', () => {
    expect(() => iter([1]).filter(null as unknown as (v: number) => boolean)).toThrow(TypeError);
  });
});
