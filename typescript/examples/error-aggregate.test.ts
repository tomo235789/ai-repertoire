// カード error-aggregate の Contract を検証するテスト
import { inspect } from 'node:util';
import { describe, expect, it } from 'vitest';

describe('error-aggregate: AggregateError', () => {
  it('iterable を配列にコピーして errors に持ち、要素は Error でなくてもよい', () => {
    const source = new Set([new Error('x'), 'plain']);
    const err = new AggregateError(source, 'two failures');
    expect(err.errors).toEqual([new Error('x'), 'plain']);
    expect(Array.isArray(err.errors)).toBe(true);
    const list = [1, 2];
    const fromArray = new AggregateError(list);
    list.push(3);
    expect(fromArray.errors).toEqual([1, 2]); // コピーなので元の配列を変えても影響しない
  });

  it('message は省略すると空文字、name は AggregateError、cause も使える', () => {
    expect(new AggregateError([]).message).toBe('');
    const err = new AggregateError([new Error('a')], 'multiple', { cause: 'root' });
    expect(err.name).toBe('AggregateError');
    expect(err.message).toBe('multiple');
    expect(err.cause).toBe('root');
    expect(err).toBeInstanceOf(AggregateError);
    expect(err).toBeInstanceOf(Error);
    expect(String(err)).toBe('AggregateError: multiple');
  });

  it('errors は列挙されず JSON.stringify に出ない。util.inspect では [errors] として出る', () => {
    const err = new AggregateError([new Error('a'), 'b'], 'multiple');
    expect(Object.keys(err)).toEqual([]);
    expect(JSON.stringify(err)).toBe('{}');
    const shown = inspect(err).replace(/\n\s+at .*/g, '');
    expect(shown).toContain('[errors]: [');
    expect(shown).toContain('Error: a');
    expect(shown).toContain("'b'");
  });

  it('Promise.any はすべて reject したとき AggregateError で reject し、errors は入力順', async () => {
    const err = await Promise.any([
      Promise.reject(new Error('a')),
      new Promise((_, reject) => setTimeout(() => reject(new Error('b')), 0)),
    ]).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(AggregateError);
    expect((err as AggregateError).message).toBe('All promises were rejected');
    expect((err as AggregateError).errors.map((e) => (e as Error).message)).toEqual(['a', 'b']);
    const empty = await Promise.any([]).catch((e: unknown) => e);
    expect((empty as AggregateError).errors).toEqual([]);
  });

  it('Promise.any は 1 つでも成功すればその値で resolve する', async () => {
    await expect(Promise.any([Promise.reject(new Error('a')), Promise.resolve('ok')])).resolves.toBe('ok');
  });

  it('allSettled の失敗をまとめて 1 つの AggregateError にする', async () => {
    const results = await Promise.allSettled([Promise.resolve(1), Promise.reject(new Error('x')), Promise.reject(new Error('y'))]);
    const failures = results.filter((r): r is PromiseRejectedResult => r.status === 'rejected').map((r) => r.reason as unknown);
    const err = new AggregateError(failures, `${failures.length} 件の取得に失敗`);
    expect(err.message).toBe('2 件の取得に失敗');
    expect(err.errors.map((e) => (e as Error).message)).toEqual(['x', 'y']);
    for (const e of err.errors) expect(e).toBeInstanceOf(Error); // errors は unknown[] なので絞り込んで使う
  });

  it('errors に AggregateError を入れて入れ子にできる', () => {
    const inner = new AggregateError([new Error('a')], 'inner');
    const outer = new AggregateError([inner, new Error('b')], 'outer');
    expect(outer.errors[0]).toBe(inner);
    expect((outer.errors[0] as AggregateError).errors).toHaveLength(1);
  });
});
