// カード validation-safe-parse の Contract を検証するテスト
import { describe, expect, expectTypeOf, it } from 'vitest';
import { z } from 'zod';

const User = z.object({ name: z.string(), age: z.number() });

describe('validation-safe-parse: safeParse', () => {
  it('成功なら { success: true, data }、失敗なら { success: false, error } で例外は投げない', () => {
    const ok = User.safeParse({ name: 'alice', age: 20 });
    expect(ok).toEqual({ success: true, data: { name: 'alice', age: 20 } });
    expect('error' in ok).toBe(false);

    const ng = User.safeParse({ name: 'alice', age: '20' });
    expect(ng.success).toBe(false);
    expect(ng.error).toBeInstanceOf(z.ZodError);
    expect('data' in ng).toBe(false);
  });

  it('success で分岐すると data / error の型が確定する', () => {
    const result = User.safeParse({ name: 'alice', age: 20 });
    expectTypeOf(result.data).toEqualTypeOf<{ name: string; age: number } | undefined>();
    if (result.success) {
      expectTypeOf(result.data).toEqualTypeOf<{ name: string; age: number }>();
      expectTypeOf(result.error).toEqualTypeOf<undefined>();
    } else {
      expectTypeOf(result.error).toEqualTypeOf<z.ZodError<{ name: string; age: number }>>();
      expectTypeOf(result.data).toEqualTypeOf<undefined>();
    }
  });

  it('変換規則は parse と同じ（未知キー除去、新しいオブジェクト、入力不変）', () => {
    const input = { name: 'alice', age: 20, extra: true };
    const result = User.safeParse(input);
    expect(result.data).toEqual({ name: 'alice', age: 20 });
    expect(result.data).not.toBe(input);
    expect(input).toHaveProperty('extra', true);
  });

  it('treeifyError / flattenError / prettifyError でエラーを整形できる', () => {
    const result = User.safeParse({ name: 1 });
    if (result.success) throw new Error('unreachable');
    expect(z.treeifyError(result.error)).toEqual({
      errors: [],
      properties: {
        name: { errors: ['Invalid input: expected string, received number'] },
        age: { errors: ['Invalid input: expected number, received undefined'] },
      },
    });
    expect(z.flattenError(result.error)).toEqual({
      formErrors: [],
      fieldErrors: {
        name: ['Invalid input: expected string, received number'],
        age: ['Invalid input: expected number, received undefined'],
      },
    });
    expect(z.prettifyError(result.error)).toBe(
      '✖ Invalid input: expected string, received number\n  → at name\n✖ Invalid input: expected number, received undefined\n  → at age',
    );
  });

  it('非同期スキーマは同期 safeParse では例外、safeParseAsync なら結果を返す', async () => {
    const Async = z.string().refine(async (s) => s.length > 0);
    expect(() => Async.safeParse('x')).toThrow(/synchronous parse/);
    await expect(Async.safeParseAsync('x')).resolves.toEqual({ success: true, data: 'x' });
    await expect(Async.safeParseAsync('')).resolves.toMatchObject({ success: false });
  });

  it('transform / refine 内で投げた例外は捕捉されない', () => {
    const Boom = z.string().transform(() => {
      throw new RangeError('boom');
    });
    expect(() => Boom.safeParse('x')).toThrow(RangeError);
    const BoomRefine = z.string().refine(() => {
      throw new RangeError('boom');
    });
    expect(() => BoomRefine.safeParse('x')).toThrow(RangeError);
  });
});
