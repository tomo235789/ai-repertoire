// カード error-invariant の Contract を検証するテスト
import { invariant } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('error-invariant: invariant', () => {
  it('truthy なら何もせず undefined を返す', () => {
    expect(invariant(true, 'x')).toBeUndefined();
    expect(invariant(1, 'x')).toBeUndefined();
    expect(invariant('a', 'x')).toBeUndefined();
    expect(invariant({}, 'x')).toBeUndefined();
  });

  it('falsy なら文字列を message にした Error を投げる', () => {
    for (const falsy of [false, 0, '', null, undefined, Number.NaN]) {
      expect(() => invariant(falsy, 'precondition')).toThrow(new Error('precondition'));
    }
    const err = (() => {
      try {
        invariant(false, 'msg');
      } catch (e) {
        return e as Error;
      }
    })();
    expect(err!.name).toBe('Error');
    expect(err!.constructor).toBe(Error);
  });

  it('Error インスタンスを渡すとそのオブジェクトをそのまま投げる', () => {
    class NotFound extends Error {}
    const custom = new NotFound('missing', { cause: 'db' });
    expect(() => invariant(null, custom)).toThrow(custom);
    try {
      invariant(0, custom);
    } catch (e) {
      expect(e).toBe(custom); // 同一オブジェクト
    }
  });

  it('asserts condition で呼び出し後の型が絞り込まれる', () => {
    const user: { id: number; email?: string } | undefined = { id: 1, email: 'A@example.com' };
    invariant(user, 'user not found');
    const id: number = user.id; // undefined が外れている
    invariant(user.email, 'email is required');
    const lower: string = user.email.toLowerCase(); // string | undefined → string
    expect([id, lower]).toEqual([1, 'a@example.com']);
    const value: unknown = 'text';
    invariant(typeof value === 'string', 'must be string');
    expect(value.length).toBe(4); // unknown → string
  });

  it('0 や空文字が正当な値では明示的に比較する', () => {
    const count: number | undefined = 0;
    expect(() => invariant(count, 'count')).toThrow('count');
    expect(() => invariant(count !== undefined, 'count')).not.toThrow();
  });

  it('第 2 引数に undefined が渡ると undefined が throw される', () => {
    const message = undefined as unknown as string;
    let thrown: unknown = 'not thrown';
    try {
      invariant(false, message);
    } catch (e) {
      thrown = e;
    }
    expect(thrown).toBeUndefined();
  });
});
