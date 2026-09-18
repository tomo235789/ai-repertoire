// カード iter-take の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

// tsconfig の lib に Iterator helpers の型が無い環境でも通るよう、使うメソッドだけを局所的に宣言してキャストする
type IterHelper<T> = {
  map<U>(callbackfn: (value: T, index: number) => U): IterHelper<U>;
  take(limit: number): IterHelper<T>;
  drop(count: number): IterHelper<T>;
  toArray(): T[];
} & IteratorObject<T, undefined, unknown>;
const iter = <T>(src: Iterator<T> | Iterable<T>): IterHelper<T> =>
  (globalThis as unknown as { Iterator: { from<T>(src: Iterator<T> | Iterable<T>): IterHelper<T> } }).Iterator.from(src);

function* naturalsGen(): Generator<number, void, undefined> {
  let n = 0;
  while (true) yield n++;
}
const naturals = (): IterHelper<number> => iter(naturalsGen());

describe('iter-take: Iterator.prototype.take', () => {
  it('無限ジェネレータから先頭 n 個を取り出す', () => {
    expect(naturals().take(3).toArray()).toEqual([0, 1, 2]);
  });

  it('遅延評価で、limit を超える要素は元から取り出さない', () => {
    let pulls = 0;
    const counted = () =>
      naturals().map((n) => {
        pulls++;
        return n;
      });
    const taken = counted().take(2);
    expect(pulls).toBe(0);
    taken.next();
    expect(pulls).toBe(1);
    expect(taken.toArray()).toEqual([1]);
    expect(pulls).toBe(2);
    pulls = 0;
    expect(counted().take(0).toArray()).toEqual([]);
    expect(pulls).toBe(0);
  });

  it('元が limit より短ければあるだけ返す', () => {
    expect(iter([1, 2]).take(5).toArray()).toEqual([1, 2]);
    expect(iter([]).take(3).toArray()).toEqual([]);
  });

  it('limit 個目を返した後の next() で終端になり、元の return() が呼ばれる', () => {
    let closed = false;
    function* source() {
      try {
        yield 1;
        yield 2;
        yield 3;
      } finally {
        closed = true;
      }
    }
    const taken = iter(source()).take(1);
    expect(taken.next()).toEqual({ value: 1, done: false });
    expect(closed).toBe(false);
    expect(taken.next()).toEqual({ value: undefined, done: true });
    expect(closed).toBe(true);
  });

  it('1 回しか走査できない', () => {
    const taken = iter([1, 2, 3]).take(2);
    expect(taken.toArray()).toEqual([1, 2]);
    expect(taken.toArray()).toEqual([]);
  });

  it('limit は整数に切り捨てられ、Infinity は全要素', () => {
    expect(iter([1, 2, 3, 4]).take(2.7).toArray()).toEqual([1, 2]);
    expect(iter([1, 2]).take(Number.POSITIVE_INFINITY).toArray()).toEqual([1, 2]);
  });

  it('limit が負数・NaN・数値にできない値・省略なら呼んだ時点で RangeError', () => {
    expect(() => naturals().take(-1)).toThrow(RangeError);
    expect(() => naturals().take(Number.NaN)).toThrow(RangeError);
    expect(() => naturals().take('x' as unknown as number)).toThrow(RangeError);
    expect(() => naturals().take(undefined as unknown as number)).toThrow(RangeError);
  });

  it('drop は先頭 count 個を読み捨て、元が短ければ空になる', () => {
    expect(iter([1, 2, 3, 4]).drop(2).toArray()).toEqual([3, 4]);
    expect(naturals().drop(5).take(2).toArray()).toEqual([5, 6]);
    expect(iter([1, 2]).drop(5).toArray()).toEqual([]);
    expect(() => naturals().drop(-1)).toThrow(RangeError);
  });
});
