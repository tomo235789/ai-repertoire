// カード validation-email の Contract を検証するテスト
import { describe, expect, it } from 'vitest';
import { z } from 'zod';

const Email = z.email();
const accepts = (schema: { safeParse: (v: unknown) => { success: boolean } }, v: unknown) => schema.safeParse(v).success;

describe('validation-email: z.email', () => {
  it('文字列以外は invalid_type、形式不一致は invalid_format', () => {
    expect(Email.safeParse(123).error?.issues[0]).toMatchObject({ code: 'invalid_type' });
    expect(Email.safeParse('nope').error?.issues[0]).toMatchObject({
      code: 'invalid_format',
      format: 'email',
      message: 'Invalid email address',
    });
  });

  it('値は変換せずそのまま返す', () => {
    expect(Email.parse('USER@EXAMPLE.COM')).toBe('USER@EXAMPLE.COM');
    expect(accepts(Email, ' user@example.com')).toBe(false);
    expect(accepts(Email, 'user@example.com ')).toBe(false);
  });

  it('既定の正規表現で通る例', () => {
    for (const v of ['user@example.com', 'first.last+tag@example.co.jp', 'USER@EXAMPLE.COM', 'a@b.co', 'user@example-.com']) {
      expect(accepts(Email, v), v).toBe(true);
    }
  });

  it('既定の正規表現で通らない例', () => {
    for (const v of [
      'user@localhost',
      'user@example',
      'a@b.c',
      '"quoted"@example.com',
      'user@[192.168.0.1]',
      '.user@example.com',
      'user..dot@example.com',
      'user@exa_mple.com',
      'ユーザー@example.com',
      'user name@example.com',
    ]) {
      expect(accepts(Email, v), v).toBe(false);
    }
  });

  it('pattern で基準を差し替えられる', () => {
    const html5 = z.email({ pattern: z.regexes.html5Email });
    expect(accepts(html5, 'user@localhost')).toBe(true);
    expect(accepts(html5, 'a@b.c')).toBe(true);
    expect(accepts(html5, '"quoted"@example.com')).toBe(false);
    const rfc = z.email({ pattern: z.regexes.rfc5322Email });
    expect(accepts(rfc, '"quoted"@example.com')).toBe(true);
    expect(accepts(rfc, 'user@[192.168.0.1]')).toBe(true);
    const unicode = z.email({ pattern: z.regexes.unicodeEmail });
    expect(accepts(unicode, 'ユーザー@example.com')).toBe(true);
    expect(accepts(unicode, 'user name@example.com')).toBe(false);
  });

  it('文字列メソッドを続けて呼べる。trim は検証の後なので pipe で前に置く', () => {
    expect(Email.max(5).safeParse('user@example.com').error?.issues[0]?.code).toBe('too_big');
    expect(Email.toLowerCase().parse('USER@EXAMPLE.COM')).toBe('user@example.com');
    expect(accepts(Email.trim(), ' user@example.com ')).toBe(false);
    expect(z.string().trim().pipe(Email).parse(' user@example.com ')).toBe('user@example.com');
  });

  it('z.string().email() は非推奨だが動作する', () => {
    expect(accepts(z.string().email(), 'user@example.com')).toBe(true);
  });
});
