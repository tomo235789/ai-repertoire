// カード object-pick の Contract を検証するテスト
import { pick } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('object-pick: pick', () => {
  it('指定したキーだけを持つ新しいオブジェクトを返す', () => {
    const user = { id: 1, name: 'a', password: 'x' };
    expect(pick(user, ['id', 'name'])).toEqual({ id: 1, name: 'a' });
  });

  it('入力を変更せず、ネストした値は同じ参照（浅いコピー）', () => {
    const nested = { x: 1 };
    const input = { n: nested, other: 2 };
    const result = pick(input, ['n']);
    expect(input).toEqual({ n: { x: 1 }, other: 2 });
    expect(result).not.toBe(input);
    expect(result.n).toBe(nested);
  });

  it('自身のプロパティだけを対象にし、継承したプロパティは取り出せない', () => {
    const obj: Record<string, number> = Object.create({ inherited: 1 });
    obj.own = 2;
    expect(pick(obj, ['inherited', 'own'])).toEqual({ own: 2 });
  });

  it('存在しないキーは無視し、undefined を持つ自身のキーは含める', () => {
    const obj: Record<string, number | undefined> = { a: 1, u: undefined };
    const result = pick(obj, ['a', 'missing', 'u']);
    expect(Object.hasOwn(result, 'missing')).toBe(false);
    expect(Object.hasOwn(result, 'u')).toBe(true);
    expect(result).toEqual({ a: 1, u: undefined });
  });

  it('返り値のキー順は keys の並び順で、重複は 1 つにまとまる', () => {
    expect(Object.keys(pick({ a: 1, b: 2, c: 3 }, ['c', 'a', 'c']))).toEqual(['c', 'a']);
  });

  it('keys が空なら空オブジェクトを返す', () => {
    expect(pick({ a: 1 }, [])).toEqual({});
  });
});
