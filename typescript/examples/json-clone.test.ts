// カード json-clone の Contract を検証するテスト
import { cloneDeep } from 'es-toolkit';
import { describe, expect, expectTypeOf, it } from 'vitest';

describe('json-clone: structuredClone', () => {
  it('全階層を複製し、元の値は変更しない', () => {
    const src = { when: new Date(0), tags: new Set(['a']), nested: { n: [1, 2] } };
    const copy = structuredClone(src);
    copy.nested.n.push(3);
    copy.tags.add('b');
    expect(src.nested.n).toEqual([1, 2]);
    expect(src.tags).toEqual(new Set(['a']));
    expect(copy).not.toBe(src);
    expect(copy.nested).not.toBe(src.nested);
    expectTypeOf(copy).toEqualTypeOf<typeof src>();
  });

  it('Date / RegExp / Map / Set / TypedArray / Error / bigint / NaN / -0 / undefined を保持する', () => {
    const src = {
      d: new Date(0),
      r: /a/gi,
      m: new Map([[1, { x: 1 }]]),
      s: new Set([1]),
      ta: new Uint8Array([1, 2]),
      buf: new Uint8Array([9]).buffer,
      err: new TypeError('boom'),
      big: 10n,
      nan: Number.NaN,
      neg0: -0,
      u: undefined,
    };
    const copy = structuredClone(src);
    expect(copy.d).toBeInstanceOf(Date);
    expect(copy.d.getTime()).toBe(0);
    expect(copy.r).toBeInstanceOf(RegExp);
    expect(copy.r.flags).toBe('gi');
    expect(copy.m).toBeInstanceOf(Map);
    expect(copy.m.get(1)).toEqual({ x: 1 });
    expect(copy.m.get(1)).not.toBe(src.m.get(1));
    expect(copy.s).toBeInstanceOf(Set);
    expect(copy.ta).toBeInstanceOf(Uint8Array);
    expect(copy.buf).toBeInstanceOf(ArrayBuffer);
    expect(copy.err).toBeInstanceOf(TypeError);
    expect(copy.err.message).toBe('boom');
    expect(copy.big).toBe(10n);
    expect(copy.nan).toBeNaN();
    expect(Object.is(copy.neg0, -0)).toBe(true);
    expect(Object.hasOwn(copy, 'u')).toBe(true);
  });

  it('循環参照と共有参照の構造を保つ', () => {
    const src: Record<string, unknown> = { v: 1 };
    src.self = src;
    const shared = { x: 1 };
    src.a = shared;
    src.b = shared;
    const copy = structuredClone(src);
    expect(copy.self).toBe(copy);
    expect(copy.a).toBe(copy.b);
    expect(copy.a).not.toBe(shared);
  });

  it('関数 / symbol 値 / WeakMap / Promise / Proxy は DataCloneError', () => {
    for (const bad of [{ fn: () => 1 }, { s: Symbol('x') }, new WeakMap(), Promise.resolve(1), new Proxy({}, {})]) {
      let caught: unknown;
      try {
        structuredClone(bad);
      } catch (e) {
        caught = e;
      }
      expect(caught).toBeInstanceOf(DOMException);
      expect(caught).toBeInstanceOf(Error);
      expect(caught).toMatchObject({ name: 'DataCloneError', code: 25 });
    }
    expect(() => structuredClone({ ok: 1, nested: { fn: () => 1 } })).toThrow(DOMException);
  });

  it('symbol キーは落ち、getter は値として複製される', () => {
    const key = Symbol('k');
    const copy = structuredClone({ [key]: 1, a: 1 });
    expect(Object.getOwnPropertySymbols(copy)).toEqual([]);
    const withGetter = structuredClone({
      get g() {
        return 1;
      },
    });
    expect(withGetter.g).toBe(1);
    expect(Object.getOwnPropertyDescriptor(withGetter, 'g')?.get).toBeUndefined();
  });

  it('クラスインスタンスはプレーンオブジェクトになり、Error の独自サブクラスは Error になる', () => {
    class Point {
      constructor(public x: number) {}
      get doubled() {
        return this.x * 2;
      }
      norm() {
        return this.x;
      }
    }
    const copy = structuredClone(new Point(1));
    expect(copy).toEqual({ x: 1 });
    expect(copy instanceof Point).toBe(false);
    expect(Object.getPrototypeOf(copy)).toBe(Object.prototype);
    expect((copy as { doubled?: number }).doubled).toBeUndefined();
    expect(typeof (copy as { norm?: unknown }).norm).toBe('undefined');
    class MyError extends Error {}
    expect(structuredClone(new MyError('m')).constructor).toBe(Error);
    expect(structuredClone(new RangeError('r'))).toBeInstanceOf(RangeError);
  });

  it('freeze は外れ、RegExp の lastIndex は 0 に戻る', () => {
    expect(Object.isFrozen(structuredClone(Object.freeze({ a: 1 })))).toBe(false);
    const re = /a/g;
    re.lastIndex = 3;
    expect(structuredClone(re).lastIndex).toBe(0);
  });

  it('transfer は ArrayBuffer を移動し、元は byteLength 0 になる', () => {
    const buf = new ArrayBuffer(4);
    const moved = structuredClone(buf, { transfer: [buf] });
    expect(moved.byteLength).toBe(4);
    expect(buf.byteLength).toBe(0);
  });

  it('cloneDeep はプロトタイプを保ち、関数・symbol は参照のままコピーする', () => {
    class Point {
      constructor(public x: number) {}
      norm() {
        return this.x;
      }
    }
    const p = cloneDeep(new Point(1));
    expect(p).toBeInstanceOf(Point);
    expect(p.norm()).toBe(1);
    const fn = () => 1;
    const sym = Symbol('x');
    const withFn = cloneDeep({ fn, sym, d: new Date(0), m: new Map([[1, 2]]) });
    expect(withFn.fn).toBe(fn);
    expect(withFn.sym).toBe(sym);
    expect(withFn.d).toBeInstanceOf(Date);
    expect(withFn.m).toBeInstanceOf(Map);
    const circular: Record<string, unknown> = { v: 1 };
    circular.self = circular;
    const copied = cloneDeep(circular);
    expect(copied.self).toBe(copied);
    expect(copied).not.toBe(circular);
  });
});
