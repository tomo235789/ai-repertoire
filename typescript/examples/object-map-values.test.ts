// カード object-map-values の Contract を検証するテスト
import { mapValues } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('object-map-values: mapValues', () => {
  it('キーを保ったまま各値を変換する', () => {
    const scores = { alice: [80, 90], bob: [70] };
    expect(mapValues(scores, (list) => list.length)).toEqual({ alice: 2, bob: 1 });
  });

  it('キーの順序を保持し、継承したプロパティとシンボルキーは含めない', () => {
    const sym = Symbol('s');
    const obj: Record<string | symbol, number> = Object.create({ inherited: 1 });
    obj.b = 2;
    obj.a = 3;
    obj[sym] = 4;
    const result = mapValues(obj, (v) => v);
    expect(Object.keys(result)).toEqual(['b', 'a']);
    expect('inherited' in result).toBe(false);
    expect(Object.getOwnPropertySymbols(result)).toEqual([]);
  });

  it('入力を変更せず、コールバックが返した値がそのまま入る', () => {
    const nested = { x: 1 };
    const input = { n: nested };
    const result = mapValues(input, (v) => v);
    expect(input).toEqual({ n: { x: 1 } });
    expect(result).not.toBe(input);
    expect(result.n).toBe(nested);
  });

  it('コールバックは各キーにつき 1 回、(value, key, object) で順に呼ばれる', () => {
    const input = { a: 1, b: 2 };
    const calls: Array<[number, string, object]> = [];
    mapValues(input, (value, key, object) => {
      calls.push([value, key, object]);
      return value;
    });
    expect(calls).toEqual([
      [1, 'a', input],
      [2, 'b', input],
    ]);
  });

  it('空オブジェクトは空オブジェクトを返す', () => {
    expect(mapValues({}, (v) => v)).toEqual({});
  });

  it('コールバックが投げた例外はそのまま伝播する', () => {
    expect(() =>
      mapValues({ a: 1 }, () => {
        throw new Error('boom');
      }),
    ).toThrow('boom');
  });
});
