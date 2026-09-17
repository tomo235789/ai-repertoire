// カード function-once の Contract を検証するテスト
import { once } from 'es-toolkit';
import { describe, expect, it, vi } from 'vitest';

describe('function-once: once', () => {
  it('2 回目以降は func を呼ばず 1 回目の戻り値（同じ参照）を返す', () => {
    const fn = vi.fn((name: string) => ({ name }));
    const init = once(fn);
    const a = init('first');
    const b = init('second');
    expect(a).toEqual({ name: 'first' });
    expect(b).toBe(a); // 2 回目の引数は無視される
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('1 回目に例外を投げると以後は func を呼ばず undefined を返す', () => {
    const fn = vi.fn(() => {
      throw new Error('boom');
    });
    const init = once(fn);
    expect(() => init()).toThrow('boom');
    expect(init()).toBeUndefined();
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('this は func に渡されない', () => {
    const obj = {
      tag: 'x',
      run: once(function (this: unknown) {
        return this;
      }),
    };
    expect(obj.run()).toBeUndefined();
  });

  it('状態は once した関数ごとに独立し、func 自体は変更しない', () => {
    const fn = vi.fn(() => 1);
    const a = once(fn);
    const b = once(fn);
    a();
    b();
    expect(fn).toHaveBeenCalledTimes(2);
    fn();
    expect(fn).toHaveBeenCalledTimes(3);
  });
});
