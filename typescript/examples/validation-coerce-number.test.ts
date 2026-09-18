// カード validation-coerce-number の Contract を検証するテスト
import { describe, expect, expectTypeOf, it } from 'vitest';
import { z } from 'zod';

const Num = z.coerce.number();

describe('validation-coerce-number: z.coerce.number', () => {
  it('Number() で変換してから検証する', () => {
    expect(Num.parse('12')).toBe(12);
    expect(Num.parse(' 7 ')).toBe(7);
    expect(Num.parse('1e3')).toBe(1000);
    expect(Num.parse('0x10')).toBe(16);
    expect(Num.parse(true)).toBe(1);
    expect(Num.parse(12n)).toBe(12);
    expect(Num.parse(new Date(1000))).toBe(1000);
    expectTypeOf(Num.parse('12')).toEqualTypeOf<number>();
  });

  it("'' / null / false / [] は 0 になって成功する", () => {
    for (const v of ['', '  ', null, false, []]) {
      expect(Num.safeParse(v)).toEqual({ success: true, data: 0 });
    }
  });

  it("'abc' / undefined / {} は NaN になり invalid_type で失敗する", () => {
    for (const v of ['abc', undefined, {}]) {
      const result = Num.safeParse(v);
      expect(result.success).toBe(false);
      expect(result.error?.issues[0]).toMatchObject({
        code: 'invalid_type',
        message: 'Invalid input: expected number, received NaN',
      });
    }
  });

  it('Infinity は失敗する', () => {
    expect(Num.safeParse(Number.POSITIVE_INFINITY).success).toBe(false);
    expect(Num.safeParse('Infinity').success).toBe(false);
  });

  it('後続のチェックは変換後の値に対して行う', () => {
    const Port = z.coerce.number().int().min(1).max(65535);
    expect(Port.parse('8080')).toBe(8080);
    expect(Port.safeParse('').error?.issues[0]?.message).toBe('Too small: expected number to be >=1');
    expect(Port.safeParse('1.5').error?.issues[0]?.message).toBe('Invalid input: expected int, received number');
  });

  it('optional は undefined を、nullable は null をそのまま通す', () => {
    expect(z.coerce.number().optional().parse(undefined)).toBeUndefined();
    expect(z.coerce.number().optional().parse('')).toBe(0);
    expect(z.coerce.number().nullable().parse(null)).toBeNull();
  });

  it("z.number() は文字列 '12' を拒否する", () => {
    expect(z.number().safeParse('12').error?.issues[0]).toMatchObject({
      code: 'invalid_type',
      message: 'Invalid input: expected number, received string',
    });
  });

  it("空文字を未指定として弾くなら string().min(1).pipe(coerce.number())", () => {
    const Strict = z.string().trim().min(1).pipe(z.coerce.number());
    expect(Strict.safeParse('').success).toBe(false);
    expect(Strict.safeParse(null).success).toBe(false);
    expect(Strict.parse(' 12 ')).toBe(12);
  });
});
