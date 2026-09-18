// カード validation-brand-type の Contract を検証するテスト
import { describe, expect, expectTypeOf, it } from 'vitest';
import { z } from 'zod';

const UserId = z.string().min(1).brand<'UserId'>();
type UserId = z.infer<typeof UserId>;
const OrderId = z.string().brand<'OrderId'>();
type OrderId = z.infer<typeof OrderId>;

function find(id: UserId): string {
  return id;
}

describe('validation-brand-type: brand', () => {
  it('実行時は何もせず、元スキーマの検証結果をそのまま返す', () => {
    const id = UserId.parse('u_1');
    expect(id).toBe('u_1');
    expect(typeof id).toBe('string');
    expect(UserId.safeParse('').success).toBe(false);
    expect(UserId.safeParse(1).success).toBe(false);
  });

  it('z.infer は string & $brand で、素の string は代入できない', () => {
    expectTypeOf<UserId>().toEqualTypeOf<string & z.$brand<'UserId'>>();
    const id = UserId.parse('u_1');
    expect(find(id)).toBe('u_1');
    // @ts-expect-error 素の string は UserId に代入できない
    find('u_1');
    const plain: string = id; // UserId は string として使える
    expect(plain).toBe('u_1');
  });

  it('ブランド名が違う型同士は代入できない', () => {
    const orderId: OrderId = OrderId.parse('o_1');
    // @ts-expect-error OrderId は UserId に代入できない
    find(orderId);
    expect(orderId).toBe('o_1');
  });

  it('実引数で brand("UserId") と書いても同じ型になる', () => {
    const ByValue = z.string().brand('UserId');
    expectTypeOf<z.infer<typeof ByValue>>().toEqualTypeOf<UserId>();
    expect(find(ByValue.parse('u_2'))).toBe('u_2');
  });

  it('引数を省略した brand() は名目型にならない', () => {
    const Plain = z.string().brand();
    expectTypeOf<z.infer<typeof Plain>>().toEqualTypeOf<string>();
    expect(Plain.parse('x')).toBe('x');
  });

  it('brand の後にもメソッドを続けられる', () => {
    const Optional = UserId.optional();
    expect(Optional.parse(undefined)).toBeUndefined();
    expectTypeOf<z.infer<typeof Optional>>().toEqualTypeOf<UserId | undefined>();
  });

  it('キャストは検証を素通りする', () => {
    const forged = '' as UserId;
    expect(find(forged)).toBe('');
  });
});
