// カード object-deep-merge の Contract を検証するテスト
import { toMerged } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('object-deep-merge: toMerged', () => {
  it('ネストしたオブジェクトを再帰的にマージする', () => {
    const defaults = { retry: 3, log: { level: 'info', file: 'app.log' } };
    const overrides = { log: { level: 'debug' } };
    expect(toMerged(defaults, overrides)).toEqual({
      retry: 3,
      log: { level: 'debug', file: 'app.log' },
    });
  });

  it('target も source も変更しない（target は深くコピーされる）', () => {
    const target = { a: { x: 1 }, when: new Date(0) };
    const source = { a: { y: 2 } };
    const result = toMerged(target, source);
    expect(target).toEqual({ a: { x: 1 }, when: new Date(0) });
    expect(source).toEqual({ a: { y: 2 } });
    expect(result.a).not.toBe(target.a);
    expect(result.when).not.toBe(target.when);
  });

  it('配列はインデックスごとに上書きし、連結しない', () => {
    expect(toMerged({ a: [1, 2, 3] }, { a: [9] })).toEqual({ a: [9, 2, 3] });
    expect(toMerged({ a: [1] }, { a: [8, 9] })).toEqual({ a: [8, 9] });
    expect(toMerged({ a: [{ x: 1 }] }, { a: [{ y: 2 }] })).toEqual({ a: [{ x: 1, y: 2 }] });
  });

  it('source のプレーンオブジェクト・配列はコピーされ、それ以外のオブジェクトは参照が入る', () => {
    const source = { o: { z: 1 }, arr: [1], d: new Date(0) };
    const result = toMerged({ o: 1 }, source);
    expect(result.o).not.toBe(source.o);
    expect(result.arr).not.toBe(source.arr);
    expect(result.d).toBe(source.d);
  });

  it('source の undefined は定義済みの値を上書きせず、null は上書きする', () => {
    expect(toMerged({ a: 1, b: 2 }, { a: undefined, b: null })).toEqual({ a: 1, b: null });
  });

  it('片方だけがプレーンオブジェクト/配列なら source の値で置き換える', () => {
    expect(toMerged({ a: { x: 1 } }, { a: 5 })).toEqual({ a: 5 });
    expect(toMerged({ a: 5 }, { a: { x: 1 } })).toEqual({ a: { x: 1 } });
    expect(toMerged({ a: null }, { a: [1, 2, 3] })).toEqual({ a: [1, 2, 3] });
  });

  it('source の自身の列挙可能なキーだけを見て、__proto__ は無視する', () => {
    const source: Record<string, number> = Object.create({ inherited: 1 });
    source.own = 2;
    expect(toMerged({}, source)).toEqual({ own: 2 });

    const polluted = JSON.parse('{"__proto__": {"polluted": true}}') as Record<string, unknown>;
    const result = toMerged({}, polluted) as Record<string, unknown>;
    expect(result.polluted).toBeUndefined();
    expect(({} as Record<string, unknown>).polluted).toBeUndefined();
  });
});
