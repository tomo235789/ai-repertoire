// カード object-invert の Contract を検証するテスト
import { invert } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('object-invert: invert', () => {
  it('キーと値を入れ替えた新しいオブジェクトを返し、入力を変更しない', () => {
    const codeToName = { 1: 'red', 2: 'blue' };
    const result = invert(codeToName);
    expect(result).toEqual({ red: '1', blue: '2' });
    expect(codeToName).toEqual({ 1: 'red', 2: 'blue' });
  });

  it('返り値の値は元のキーを文字列にしたもの', () => {
    const result = invert({ 1: 'x' }) as Record<string, unknown>;
    expect(typeof result.x).toBe('string');
    expect(result.x).toBe('1');
  });

  it('値が重複したら Object.keys の順で最後のキーが残る（整数風キーは昇順）', () => {
    expect(invert({ b: 1, a: 1 })).toEqual({ 1: 'a' });
    expect(invert({ 2: 'x', 1: 'x' })).toEqual({ x: '2' });
  });

  it('継承したプロパティとシンボルキーは無視する', () => {
    const sym = Symbol('s');
    const obj: Record<string | symbol, string> = Object.create({ inherited: 'i' });
    obj.own = 'o';
    obj[sym] = 's';
    expect(invert(obj)).toEqual({ o: 'own' });
  });

  it('空オブジェクトは空オブジェクトを返す', () => {
    expect(invert({})).toEqual({});
  });
});
