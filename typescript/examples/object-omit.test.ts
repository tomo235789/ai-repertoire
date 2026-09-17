// カード object-omit の Contract を検証するテスト
import { omit } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('object-omit: omit', () => {
  it('指定したキーを除いた新しいオブジェクトを返す', () => {
    const user = { id: 1, name: 'a', password: 'x' };
    expect(omit(user, ['password'])).toEqual({ id: 1, name: 'a' });
  });

  it('入力を変更せず、ネストした値は同じ参照（浅いコピー）', () => {
    const nested = { x: 1 };
    const input = { n: nested, other: 2 };
    const result = omit(input, ['other']);
    expect(input).toEqual({ n: { x: 1 }, other: 2 });
    expect(result).not.toBe(input);
    expect(result.n).toBe(nested);
  });

  it('自身の列挙可能なプロパティだけをコピーし、継承したプロパティは含めない。シンボルキーは残る', () => {
    const sym = Symbol('s');
    const obj: Record<string | symbol, number> = Object.create({ inherited: 1 });
    obj.own = 2;
    obj[sym] = 3;
    const result = omit(obj, []);
    expect(Object.keys(result)).toEqual(['own']);
    expect('inherited' in result).toBe(false);
    expect(result[sym]).toBe(3);
  });

  it('残ったキーの順序は元のまま', () => {
    expect(Object.keys(omit({ c: 1, a: 2, b: 3 }, ['a']))).toEqual(['c', 'b']);
  });

  it('存在しないキーを指定しても無視する', () => {
    const obj: Record<string, number> = { a: 1 };
    expect(omit(obj, ['missing'])).toEqual({ a: 1 });
  });

  it('すべて除くと空オブジェクト、keys が空なら同じ内容の浅いコピー', () => {
    expect(omit({ a: 1 }, ['a'])).toEqual({});
    const input = { a: 1 };
    const copy = omit(input, []);
    expect(copy).toEqual(input);
    expect(copy).not.toBe(input);
  });
});
