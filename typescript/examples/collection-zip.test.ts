// カード collection-zip の Contract を検証するテスト
import { zip } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('collection-zip: zip', () => {
  it('同じ位置の要素を順序どおりに組にする', () => {
    expect(zip(['a', 'b', 'c'], [1, 2, 3])).toEqual([
      ['a', 1],
      ['b', 2],
      ['c', 3],
    ]);
  });

  it('入力配列を変更せず、タプルは新しい配列で要素は同じ参照', () => {
    const a = { id: 1 };
    const left = [a];
    const right = ['x'];
    const result = zip(left, right);
    expect(left).toEqual([a]);
    expect(right).toEqual(['x']);
    expect(result[0]).not.toBe(left);
    expect(result[0][0]).toBe(a);
  });

  it('最も長い配列に合わせ、足りない位置は undefined で埋める', () => {
    expect(zip([1, 2, 3], ['a'])).toEqual([
      [1, 'a'],
      [2, undefined],
      [3, undefined],
    ]);
    expect(zip([], [1])).toEqual([[undefined, 1]]);
  });

  it('3 つ以上の配列も組にできる', () => {
    expect(zip([1, 2], ['a', 'b'], [true, false])).toEqual([
      [1, 'a', true],
      [2, 'b', false],
    ]);
  });

  it('引数なしやすべて空配列なら空配列を返す', () => {
    expect(zip()).toEqual([]);
    expect(zip([], [])).toEqual([]);
  });
});
