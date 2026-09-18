// カード validation-parse-schema の Contract を検証するテスト
import { describe, expect, expectTypeOf, it } from 'vitest';
import { z } from 'zod';

const User = z.object({ name: z.string(), age: z.number().int() });

describe('validation-parse-schema: z.object().parse', () => {
  it('成功すると型付きの新しいオブジェクトを返し、入力は変更しない', () => {
    const input = { name: 'alice', age: 20, extra: true };
    const result = User.parse(input);
    expect(result).toEqual({ name: 'alice', age: 20 });
    expect(result).not.toBe(input);
    expect(input).toEqual({ name: 'alice', age: 20, extra: true });
    expectTypeOf(result).toEqualTypeOf<{ name: string; age: number }>();
  });

  it('ネストしたオブジェクト・配列は新しく作られ、Date は同じ参照', () => {
    const when = new Date(0);
    const input = { inner: { v: 1 }, list: [1, 2], when };
    const Nested = z.object({ inner: z.object({ v: z.number() }), list: z.array(z.number()), when: z.date() });
    const result = Nested.parse(input);
    expect(result.inner).not.toBe(input.inner);
    expect(result.list).not.toBe(input.list);
    expect(result.when).toBe(when);
  });

  it('失敗すると全項目の issue を持つ ZodError を投げる', () => {
    let caught: unknown;
    try {
      User.parse({ name: 1, age: '20' });
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(z.ZodError);
    expect(caught).toBeInstanceOf(Error);
    const error = caught as z.ZodError;
    expect(error.name).toBe('ZodError');
    expect(error.issues).toHaveLength(2);
    expect(error.issues.map((i) => [i.code, i.path])).toEqual([
      ['invalid_type', ['name']],
      ['invalid_type', ['age']],
    ]);
    expect(error.issues[0]?.message).toBe('Invalid input: expected string, received number');
  });

  it('未知キーは既定で除去、strict なら失敗、passthrough なら残す', () => {
    const input = { name: 'alice', age: 20, extra: true };
    expect(User.parse(input)).not.toHaveProperty('extra');
    expect(() => User.strict().parse(input)).toThrow(z.ZodError);
    expect(z.strictObject(User.shape).safeParse(input).error?.issues[0]?.code).toBe('unrecognized_keys');
    expect(User.passthrough().parse(input)).toEqual(input);
    expect(z.looseObject(User.shape).parse(input)).toEqual(input);
  });

  it('null / undefined は path: [] の invalid_type', () => {
    for (const bad of [null, undefined]) {
      const result = User.safeParse(bad);
      expect(result.success).toBe(false);
      expect(result.error?.issues[0]).toMatchObject({ code: 'invalid_type', path: [] });
    }
  });

  it('default は欠けたキーを補う', () => {
    expect(z.object({ role: z.string().default('member') }).parse({})).toEqual({ role: 'member' });
  });

  it('非同期スキーマを同期 parse すると ZodError ではない例外、parseAsync なら通る', async () => {
    const Async = z.string().refine(async (s) => s.length > 0);
    expect(() => Async.parse('x')).toThrow(/synchronous parse/);
    expect(() => Async.parse('x')).not.toThrow(z.ZodError);
    await expect(Async.parseAsync('x')).resolves.toBe('x');
  });

  it('transform 内で投げた例外は ZodError にならず伝播する', () => {
    const Boom = z.string().transform(() => {
      throw new RangeError('boom');
    });
    expect(() => Boom.parse('x')).toThrow(RangeError);
  });
});
