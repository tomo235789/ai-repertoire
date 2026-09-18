// カード map-group-to-map の Contract を検証するテスト
import { groupBy as esGroupBy } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

// tsconfig の lib に ES2024 の Map.groupBy / Object.groupBy の型が無い環境でも通るよう、最小限の型を局所宣言してキャストする
type MapGroupBy = <K, T>(items: Iterable<T>, keySelector: (item: T, index: number) => K) => Map<K, T[]>;
const groupBy = (Map as unknown as { groupBy: MapGroupBy }).groupBy;
const objectGroupBy = (Object as unknown as { groupBy: <T>(items: Iterable<T>, fn: (item: T) => PropertyKey) => object })
  .groupBy;

describe('map-group-to-map: Map.groupBy', () => {
  it('キーが最初に現れた順の Map を返し、各グループは元の出現順', () => {
    const items = [{ type: 'b', n: 1 }, { type: 'a', n: 2 }, { type: 'b', n: 3 }];
    const groups = groupBy(items, (x) => x.type);
    expect([...groups.keys()]).toEqual(['b', 'a']);
    expect(groups.get('b')).toEqual([{ type: 'b', n: 1 }, { type: 'b', n: 3 }]);
    expect(groups.get('a')).toEqual([{ type: 'a', n: 2 }]);
  });

  it('keySelector は各要素につき 1 回、先頭から (item, index) で呼ばれる', () => {
    const calls: [string, number][] = [];
    groupBy(['x', 'y', 'z'], (item, index) => {
      calls.push([item, index]);
      return index % 2;
    });
    expect(calls).toEqual([['x', 0], ['y', 1], ['z', 2]]);
  });

  it('入力を変更せず、返り値は新しい Map で要素は同じ参照', () => {
    const items = [{ k: 1 }, { k: 2 }];
    const groups = groupBy(items, (x) => x.k);
    expect(items).toEqual([{ k: 1 }, { k: 2 }]);
    expect(Object.getPrototypeOf(groups)).toBe(Map.prototype);
    expect(groups.get(1)?.[0]).toBe(items[0]);
  });

  it('キーは文字列化されない。1 と "1" は別、NaN 同士は同じ、オブジェクトは参照比較', () => {
    expect([...groupBy([1, '1'], (x) => x).keys()]).toEqual([1, '1']);
    expect(groupBy([1, 2], () => Number.NaN).size).toBe(1);
    const k1 = { id: 1 };
    const k2 = { id: 1 };
    const byObj = groupBy([1, 2, 3], (x) => (x === 2 ? k2 : k1));
    expect(byObj.size).toBe(2);
    expect(byObj.get(k1)).toEqual([1, 3]);
    expect(byObj.get(k2)).toEqual([2]);
    expect(groupBy([1, 2], () => undefined).get(undefined)).toEqual([1, 2]);
  });

  it('配列以外の iterable も受け取れる。array-like は TypeError', () => {
    expect([...groupBy(new Set([1, 2, 3]), (x) => x % 2)]).toEqual([[1, [1, 3]], [0, [2]]]);
    expect(groupBy('aab', (c) => c).get('a')).toEqual(['a', 'a']);
    function* gen() {
      yield 1;
      yield 2;
    }
    expect(groupBy(gen(), (x) => x).size).toBe(2);
    expect(() => groupBy({ length: 1, 0: 'x' } as unknown as Iterable<string>, (x) => x)).toThrow(TypeError);
  });

  it('空の iterable には空の Map を返す', () => {
    expect(groupBy([], (x) => x).size).toBe(0);
  });

  it('items が null / undefined、keySelector が関数でないと TypeError', () => {
    expect(() => groupBy(null as unknown as Iterable<number>, (x) => x)).toThrow(TypeError);
    expect(() => groupBy([1], 1 as unknown as (x: number) => number)).toThrow(TypeError);
  });

  it('Object.groupBy / es-toolkit groupBy はキーを文字列化し整数風キーが先頭に並ぶが、Map.groupBy は出現順', () => {
    const items = [2, 1, 'b', 'a'];
    expect(Object.keys(objectGroupBy(items, (x) => x))).toEqual(['1', '2', 'b', 'a']);
    expect(Object.getPrototypeOf(objectGroupBy(items, (x) => x))).toBeNull();
    expect(Object.keys(esGroupBy(items, (x) => x))).toEqual(['1', '2', 'b', 'a']);
    expect([...groupBy(items, (x) => x).keys()]).toEqual([2, 1, 'b', 'a']);
  });
});
