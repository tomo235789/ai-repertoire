// カード iter-lazy-map の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

// tsconfig の lib に Iterator helpers の型が無い環境でも通るよう、使うメソッドだけを局所的に宣言してキャストする
type IterHelper<T> = {
  map<U>(callbackfn: (value: T, index: number) => U): IterHelper<U>;
  filter(predicate: (value: T, index: number) => unknown): IterHelper<T>;
  take(limit: number): IterHelper<T>;
  toArray(): T[];
} & IteratorObject<T, undefined, unknown>;
const IteratorCtor = (globalThis as unknown as { Iterator: { from<T>(src: Iterator<T> | Iterable<T>): IterHelper<T>; prototype: object } }).Iterator;
const iter = <T>(src: Iterator<T> | Iterable<T>): IterHelper<T> => IteratorCtor.from(src);

function* naturalsGen(): Generator<number, void, undefined> {
  let n = 0;
  while (true) yield n++;
}
const naturals = (): IterHelper<number> => iter(naturalsGen());

describe('iter-lazy-map: Iterator.prototype.map', () => {
  it('遅延評価で、next() のたびに 1 要素ずつ変換する', () => {
    const calls: number[] = [];
    const mapped = iter([1, 2, 3]).map((x) => {
      calls.push(x);
      return x * 2;
    });
    expect(calls).toEqual([]);
    expect(mapped.next()).toEqual({ value: 2, done: false });
    expect(calls).toEqual([1]);
    expect(mapped.toArray()).toEqual([4, 6]);
    expect(calls).toEqual([1, 2, 3]);
  });

  it('無限ジェネレータでも必要な分しか計算しない', () => {
    const calls: number[] = [];
    const result = naturals()
      .map((n) => {
        calls.push(n);
        return n * n;
      })
      .take(3)
      .toArray();
    expect(result).toEqual([0, 1, 4]);
    expect(calls).toEqual([0, 1, 2]);
  });

  it('順序を保持し、コールバックは (value, index) で 0 から呼ばれる', () => {
    expect(iter(['a', 'b', 'c']).map((x, i) => `${x}${i}`).toArray()).toEqual(['a0', 'b1', 'c2']);
  });

  it('1 回しか走査できない。消費し切った後は空になる', () => {
    const mapped = iter([1, 2]).map((x) => x);
    expect([...mapped]).toEqual([1, 2]);
    expect([...mapped]).toEqual([]);
    expect(mapped.toArray()).toEqual([]);
  });

  it('返り値は Iterator を継承し、[Symbol.iterator]() は自分自身を返す', () => {
    const mapped = iter([1]).map((x) => x);
    expect(Object.prototype.isPrototypeOf.call(IteratorCtor.prototype, mapped)).toBe(true);
    expect(mapped[Symbol.iterator]()).toBe(mapped);
    expect(Object.prototype.toString.call(mapped)).toBe('[object Iterator Helper]');
  });

  it('途中で break すると元のジェネレータの return() が呼ばれ finally が走る', () => {
    let closed = false;
    function* source() {
      try {
        yield 1;
        yield 2;
      } finally {
        closed = true;
      }
    }
    for (const x of iter(source()).map((v) => v)) {
      if (x === 1) break;
    }
    expect(closed).toBe(true);
  });

  it('入力を変更せず、空のイテレータからは空を返す', () => {
    const src = [1, 2, 3];
    expect(iter(src).map((x) => x * 2).toArray()).toEqual([2, 4, 6]);
    expect(src).toEqual([1, 2, 3]);
    expect(iter([]).map((x) => x).toArray()).toEqual([]);
  });

  it('コールバックが関数でないと呼んだ時点で TypeError', () => {
    expect(() => iter([1]).map(1 as unknown as (v: number) => number)).toThrow(TypeError);
  });

  it('Iterator.from は iterable を Iterator Helper にし、ネイティブのイテレータはそのまま返す', () => {
    expect(iter(new Set([1, 2])).map((x) => x + 1).toArray()).toEqual([2, 3]);
    expect(iter('ab').map((c) => c.toUpperCase()).toArray()).toEqual(['A', 'B']);
    const native = [1].values();
    expect(iter(native)).toBe(native);
    const plain = { next: () => ({ value: undefined, done: true as const }) };
    const wrapped = iter(plain);
    expect(wrapped).not.toBe(plain);
    expect(typeof wrapped.map).toBe('function');
  });
});
