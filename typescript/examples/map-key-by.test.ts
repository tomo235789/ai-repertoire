// カード map-key-by の Contract を検証するテスト
import { keyBy } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('map-key-by: keyBy', () => {
  it('キーから要素を引けるオブジェクトを返す', () => {
    const users = [{ id: 'u1', name: 'A' }, { id: 'u2', name: 'B' }];
    const byId = keyBy(users, (u) => u.id);
    expect(byId).toEqual({ u1: { id: 'u1', name: 'A' }, u2: { id: 'u2', name: 'B' } });
    expect(byId.u2.name).toBe('B');
  });

  it('重複キーは最後の要素が残る', () => {
    const items = [{ id: 'x', v: 1 }, { id: 'y', v: 2 }, { id: 'x', v: 3 }];
    const result = keyBy(items, (x) => x.id);
    expect(result).toEqual({ x: { id: 'x', v: 3 }, y: { id: 'y', v: 2 } });
    expect(result.x).toBe(items[2]);
  });

  it('getKeyFromItem は各要素につき 1 回、先頭から (item, index, array) で呼ばれる', () => {
    const calls: [number, number, number][] = [];
    keyBy([5, 6], (item, index, array) => {
      calls.push([item, index, array.length]);
      return item;
    });
    expect(calls).toEqual([[5, 0, 2], [6, 1, 2]]);
  });

  it('入力配列を変更せず、返り値は Object.prototype を継承した新しいオブジェクトで値は同じ参照', () => {
    const items = [{ id: 'a' }, { id: 'b' }];
    const result = keyBy(items, (x) => x.id);
    expect(items).toEqual([{ id: 'a' }, { id: 'b' }]);
    expect(Object.getPrototypeOf(result)).toBe(Object.prototype);
    expect(result.a).toBe(items[0]);
  });

  it('キーは文字列化される。1 と "1" は同じキー、undefined は "undefined"', () => {
    expect(keyBy([{ id: 1 }, { id: '1' }], (x) => x.id)).toEqual({ 1: { id: '1' } });
    expect(keyBy([1], () => undefined as unknown as string)).toEqual({ undefined: 1 });
    expect(keyBy(['a', 'b'], (_, i) => i)).toEqual({ 0: 'a', 1: 'b' });
  });

  it('整数風のキーは Object.keys で昇順・先頭に並ぶ', () => {
    expect(Object.keys(keyBy(['b', 2, 'a', 1], (x) => x))).toEqual(['1', '2', 'b', 'a']);
  });

  it('Object.prototype にある名前もキーにでき、Object.hasOwn で判定できる', () => {
    expect(Object.hasOwn(keyBy([1], () => 'toString'), 'toString')).toBe(true);
  });

  it('空配列には {} を返す', () => {
    expect(keyBy([], (x) => x)).toEqual({});
  });
});
