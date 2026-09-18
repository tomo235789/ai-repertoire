// カード map-count-by の Contract を検証するテスト
import { countBy } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('map-count-by: countBy', () => {
  it('キーごとの出現回数をオブジェクトで返す', () => {
    expect(countBy(['a', 'b', 'a'], (x) => x)).toEqual({ a: 2, b: 1 });
    expect(countBy([1, 2, 3, 4, 5], (n) => (n % 2 === 0 ? 'even' : 'odd'))).toEqual({ odd: 3, even: 2 });
  });

  it('mapper は各要素につき 1 回、先頭から (item, index, array) で呼ばれる', () => {
    const calls: [number, number, number][] = [];
    countBy([5, 6], (item, index, array) => {
      calls.push([item, index, array.length]);
      return item;
    });
    expect(calls).toEqual([[5, 0, 2], [6, 1, 2]]);
  });

  it('入力配列を変更せず、返り値は Object.prototype を継承した新しいオブジェクト', () => {
    const input = [1, 2, 1];
    const result = countBy(input, (x) => x);
    expect(input).toEqual([1, 2, 1]);
    expect(Object.getPrototypeOf(result)).toBe(Object.prototype);
  });

  it('キーは文字列化される。1 と "1" は同じキー、undefined / オブジェクトも文字列になる', () => {
    expect(countBy([1, '1'], (x) => x)).toEqual({ 1: 2 });
    expect(countBy([1, 2], () => undefined as unknown as string)).toEqual({ undefined: 2 });
    expect(countBy([1, 2], () => ({}) as unknown as string)).toEqual({ '[object Object]': 2 });
    expect(countBy([true, false, true], (x) => String(x))).toEqual({ true: 2, false: 1 });
  });

  it('symbol はそのままキーになる', () => {
    const sym = Symbol('s');
    expect(countBy([1, 2], () => sym)[sym]).toBe(2);
  });

  it('整数風のキーは Object.keys で昇順・先頭に並ぶ', () => {
    expect(Object.keys(countBy(['b', 2, 'a', 1], (x) => x))).toEqual(['1', '2', 'b', 'a']);
  });

  it('Object.prototype にある名前をキーにすると継承プロパティを拾って正しく数えられない', () => {
    const result = countBy([1, 2], () => 'toString');
    expect(Object.hasOwn(result, 'toString')).toBe(true);
    expect(result.toString).not.toBe(2);
    expect(typeof result.toString).toBe('string'); // 関数の文字列表現に 1 が連結される
    expect(typeof countBy([1], () => 'constructor').constructor).toBe('string');
  });

  it('空配列には {} を返す', () => {
    expect(countBy([], (x) => x)).toEqual({});
  });
});
