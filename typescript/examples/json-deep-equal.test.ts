// カード json-deep-equal の Contract を検証するテスト
import { isEqual } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('json-deep-equal: isEqual', () => {
  it('ネストした構造をキー順に関係なく比較する', () => {
    expect(isEqual({ a: 1, b: [1, { c: 2 }] }, { b: [1, { c: 2 }], a: 1 })).toBe(true);
    expect(isEqual({ a: 1 }, { a: 2 })).toBe(false);
  });

  it('プリミティブ: NaN 同士と 0 / -0 は true、型違いは false', () => {
    expect(isEqual(Number.NaN, Number.NaN)).toBe(true);
    expect(isEqual(0, -0)).toBe(true);
    expect(isEqual('1', 1)).toBe(false);
    expect(isEqual(null, undefined)).toBe(false);
  });

  it('Date は時刻値、RegExp はソースとフラグで比較する', () => {
    expect(isEqual(new Date(0), new Date(0))).toBe(true);
    expect(isEqual(new Date(0), new Date(1))).toBe(false);
    expect(isEqual(new Date(Number.NaN), new Date(Number.NaN))).toBe(true);
    expect(isEqual(/a/g, /a/g)).toBe(true);
    expect(isEqual(/a/g, /a/i)).toBe(false);
    const moved = /a/g;
    moved.lastIndex = 3;
    expect(isEqual(moved, /a/g)).toBe(true);
  });

  it('Map は挿入順を問わず、Set は要素の中身で比較する', () => {
    expect(isEqual(new Map([[1, { a: 1 }]]), new Map([[1, { a: 1 }]]))).toBe(true);
    expect(isEqual(new Map([['a', 1], ['b', 2]]), new Map([['b', 2], ['a', 1]]))).toBe(true);
    expect(isEqual(new Map([[1, 1]]), new Map([[1, 2]]))).toBe(false);
    expect(isEqual(new Set([1, { a: 1 }]), new Set([{ a: 1 }, 1]))).toBe(true);
    expect(isEqual(new Set([1]), new Set([2]))).toBe(false);
  });

  it('TypedArray は要素値と型、ArrayBuffer は内容で比較する', () => {
    expect(isEqual(new Uint8Array([1, 2]), new Uint8Array([1, 2]))).toBe(true);
    expect(isEqual(new Uint8Array([1, 2]), new Uint8Array([1, 3]))).toBe(false);
    expect(isEqual(new Uint8Array([1]), new Int8Array([1]))).toBe(false);
    expect(isEqual(new Uint8Array([1]).buffer, new Uint8Array([1]).buffer)).toBe(true);
    expect(isEqual(new Uint8Array([1]).buffer, new Uint8Array([2]).buffer)).toBe(false);
  });

  it('Error は name と message で比較する', () => {
    expect(isEqual(new Error('a'), new Error('a'))).toBe(true);
    expect(isEqual(new Error('a'), new Error('b'))).toBe(false);
    expect(isEqual(new Error('a'), new TypeError('a'))).toBe(false);
  });

  it('配列とオブジェクトは別物で、配列は順序も見る', () => {
    expect(isEqual([1], { 0: 1 })).toBe(false);
    expect(isEqual([1, 2], [2, 1])).toBe(false);
  });

  it('プロトタイプが違えば false', () => {
    class P {
      a = 1;
    }
    class Q {
      a = 1;
    }
    expect(isEqual(new P(), new P())).toBe(true);
    expect(isEqual(new P(), new Q())).toBe(false);
    expect(isEqual(new P(), { a: 1 })).toBe(false);
  });

  it('undefined の値とキー無しは区別し、列挙不可は無視、symbol キーは比較する', () => {
    expect(isEqual({ a: undefined }, {})).toBe(false);
    expect({ a: undefined }).toEqual({}); // vitest の toEqual との違い
    expect(isEqual(Object.defineProperty({ a: 1 }, 'hidden', { value: 1 }), { a: 1 })).toBe(true);
    const key = Symbol.for('k');
    expect(isEqual({ [key]: 1 }, { [key]: 1 })).toBe(true);
    expect(isEqual({ [key]: 1 }, { [key]: 2 })).toBe(false);
  });

  it('関数は同じ参照のときだけ true', () => {
    const f = () => 1;
    expect(isEqual(f, f)).toBe(true);
    expect(
      isEqual(
        () => 1,
        () => 1,
      ),
    ).toBe(false);
  });

  it('循環参照でも無限ループにならない', () => {
    const a: Record<string, unknown> = { v: 1 };
    a.self = a;
    const b: Record<string, unknown> = { v: 1 };
    b.self = b;
    expect(isEqual(a, b)).toBe(true);
    const c: Record<string, unknown> = { v: 1 };
    c.self = { v: 1, self: c };
    expect(isEqual(a, c)).toBe(false);
  });
});
