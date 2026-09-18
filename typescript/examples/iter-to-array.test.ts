// カード iter-to-array の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

// tsconfig の lib に Iterator helpers の型が無い環境でも通るよう、使うメソッドだけを局所的に宣言してキャストする
type IterHelper<T> = {
  filter(predicate: (value: T, index: number) => unknown): IterHelper<T>;
  map<U>(callbackfn: (value: T, index: number) => U): IterHelper<U>;
  take(limit: number): IterHelper<T>;
  toArray(): T[];
} & IteratorObject<T, undefined, unknown>;
const IteratorCtor = (
  globalThis as unknown as { Iterator: { from<T>(src: Iterator<T> | Iterable<T>): IterHelper<T>; prototype: { toArray(this: unknown): unknown[] } } }
).Iterator;
const iter = <T>(src: Iterator<T> | Iterable<T>): IterHelper<T> => IteratorCtor.from(src);

describe('iter-to-array: Iterator.prototype.toArray', () => {
  it('イテレータを終端まで進めて新しい配列を返す', () => {
    const src = [1, 2, 3];
    const result = iter(src).toArray();
    expect(result).toEqual([1, 2, 3]);
    expect(Array.isArray(result)).toBe(true);
    expect(result).not.toBe(src);
  });

  it('順序を保持し、要素は同じ参照のまま', () => {
    const a = { v: 1 };
    const b = { v: 2 };
    const result = iter(new Set([b, a])).toArray();
    expect(result[0]).toBe(b);
    expect(result[1]).toBe(a);
  });

  it('既に進めた分は含まれず、呼んだ後はイテレータが空になる', () => {
    const it = iter([1, 2, 3]);
    it.next();
    expect(it.toArray()).toEqual([2, 3]);
    expect(it.toArray()).toEqual([]);
    expect(it.next()).toEqual({ value: undefined, done: true });
  });

  it('ジェネレータの finally が走り、return した値は含まれない', () => {
    let closed = false;
    function* source() {
      try {
        yield 1;
        return 'r';
      } finally {
        closed = true;
      }
    }
    expect(iter(source()).toArray()).toEqual([1]);
    expect(closed).toBe(true);
  });

  it('空のイテレータには [] を返す', () => {
    expect(iter([]).toArray()).toEqual([]);
  });

  it('map / filter / take のチェーンの終端で使える', () => {
    expect(
      iter([1, 2, 3, 4])
        .filter((x) => x % 2 === 0)
        .map((x) => x * 10)
        .toArray(),
    ).toEqual([20, 40]);
    expect(iter(new Map([['a', 1], ['b', 2]]).keys()).toArray()).toEqual(['a', 'b']);
  });

  it('this が next() を持たないと TypeError', () => {
    expect(() => IteratorCtor.prototype.toArray.call([1, 2])).toThrow(TypeError);
  });

  it('Array.from は iterable と array-like をそのまま受け取り、変換関数も渡せる', () => {
    expect(Array.from(iter([1, 2]).take(2))).toEqual([1, 2]);
    expect(Array.from(new Set([3, 1]))).toEqual([3, 1]);
    expect(Array.from({ length: 2, 0: 'x', 1: 'y' })).toEqual(['x', 'y']);
    expect(Array.from([1, 2].values(), (x) => x * 10)).toEqual([10, 20]);
  });
});
