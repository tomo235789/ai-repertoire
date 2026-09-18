// カード json-parse-safe の Contract を検証するテスト
import { attempt } from 'es-toolkit';
import { describe, expect, expectTypeOf, it } from 'vitest';
import { z } from 'zod';

const parseJson = (text: string) => attempt<unknown, SyntaxError>(() => JSON.parse(text));

describe('json-parse-safe: attempt(() => JSON.parse(text))', () => {
  it('解析できれば [null, 値]、失敗は [SyntaxError, null] で例外は伝播しない', () => {
    expect(parseJson('{"name":"alice"}')).toEqual([null, { name: 'alice' }]);
    const [err, value] = parseJson('{oops');
    expect(err).toBeInstanceOf(SyntaxError);
    expect(value).toBeNull();
  });

  it('値は unknown として受け取り、zod で型付きにする', () => {
    const [, raw] = parseJson('{"name":"alice"}');
    expectTypeOf(raw).toEqualTypeOf<unknown>();
    expect(z.object({ name: z.string() }).safeParse(raw)).toEqual({ success: true, data: { name: 'alice' } });
  });

  it('失敗する入力', () => {
    for (const text of ['', 'undefined', '{a:1}', '{"a":1,}', 'NaN', "'s'"]) {
      expect(parseJson(text)[0], text).toBeInstanceOf(SyntaxError);
    }
  });

  it('成功するが注意が要る入力', () => {
    expect(parseJson('1e400')).toEqual([null, Number.POSITIVE_INFINITY]);
    expect(parseJson('12345678901234567890')).toEqual([null, 12345678901234567000]);
    expect(parseJson('9007199254740993')).toEqual([null, 9007199254740992]);
    expect(parseJson('null')).toEqual([null, null]);
    expect(parseJson('"s"')).toEqual([null, 's']);
  });

  it('__proto__ キーは自身のプロパティになり、プロトタイプは汚染されない', () => {
    const [, raw] = parseJson('{"__proto__":{"polluted":true},"a":1}');
    const obj = raw as Record<string, unknown>;
    expect(Object.hasOwn(obj, '__proto__')).toBe(true);
    expect(Object.getPrototypeOf(obj)).toBe(Object.prototype);
    expect(({} as Record<string, unknown>).polluted).toBeUndefined();
    const cleaned = z.object({ a: z.number() }).parse(obj);
    expect(Object.hasOwn(cleaned, '__proto__')).toBe(false);
    const assigned = Object.assign({}, obj) as Record<string, unknown>;
    expect(Object.getPrototypeOf(assigned)).not.toBe(Object.prototype); // 罠
    expect(assigned.polluted).toBe(true);
    const spread = { ...obj };
    expect(Object.getPrototypeOf(spread)).toBe(Object.prototype);
  });

  it('reviver で値を変換でき、context.source で元の文字列が取れる', () => {
    const [, revived] = attempt<unknown, SyntaxError>(() =>
      JSON.parse('{"at":"2026-09-17T00:00:00.000Z"}', (key, value: unknown) => (key === 'at' ? new Date(value as string) : value)),
    );
    expect(revived).toEqual({ at: new Date('2026-09-17T00:00:00.000Z') });
    // 第 3 引数 context は TypeScript 5.9 の lib に型が無いのでキャストする
    const bigintReviver = ((_key: string, value: unknown, context: { source: string }) =>
      typeof value === 'number' ? BigInt(context.source) : value) as (key: string, value: unknown) => unknown;
    const [, big] = attempt<unknown, SyntaxError>(() => JSON.parse('{"n":12345678901234567890}', bigintReviver));
    expect(big).toEqual({ n: 12345678901234567890n });
  });
});
