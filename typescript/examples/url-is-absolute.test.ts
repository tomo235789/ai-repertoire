// カード url-is-absolute の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

describe('url-is-absolute: URL.canParse', () => {
  it('スキーム付きで解析できるときだけ true', () => {
    expect(URL.canParse('https://example.com/a')).toBe(true);
    expect(URL.canParse('example.com/a')).toBe(false);
    expect(URL.canParse('/a/b')).toBe(false);
    expect(URL.canParse('//cdn.example.com/x.js')).toBe(false);
    expect(URL.canParse('')).toBe(false);
    expect(URL.canParse('http://')).toBe(false);
    expect(URL.canParse('https://exa mple.com')).toBe(false);
  });

  it('base があれば相対参照でも true、base が不正なら false', () => {
    expect(URL.canParse('/a/b', 'https://example.com')).toBe(true);
    expect(URL.canParse('//cdn.example.com/x.js', 'https://example.com')).toBe(true);
    expect(URL.canParse('', 'https://example.com')).toBe(true);
    expect(URL.canParse('a', 'not a url')).toBe(false);
    expect(URL.canParse('https://example.com', 'not a url')).toBe(false);
    expect(URL.canParse('a', 'mailto:x@example.com')).toBe(false);
  });

  it('スキームらしきものは何でも通る', () => {
    expect(URL.canParse('mailto:a@example.com')).toBe(true);
    expect(URL.canParse('data:,x')).toBe(true);
    expect(URL.canParse('javascript:alert(1)')).toBe(true);
    expect(URL.canParse('a:b')).toBe(true);
    expect(URL.canParse('c:\\Users\\x')).toBe(true);
    expect(new URL('c:\\Users\\x').protocol).toBe('c:');
  });

  it('前後の空白は無視し、パス中の空白は許す', () => {
    expect(URL.canParse(' https://example.com ')).toBe(true);
    expect(URL.canParse('https://example.com/a b')).toBe(true);
  });

  it('引数は文字列化され、引数なしは TypeError', () => {
    expect(URL.canParse(undefined as never)).toBe(false);
    expect(URL.canParse(null as never)).toBe(false);
    expect(URL.canParse({ toString: () => 'https://example.com' } as never)).toBe(true);
    expect(() => (URL.canParse as () => boolean)()).toThrowError(TypeError);
  });

  it('旧イディオムの new URL は失敗すると TypeError を投げる', () => {
    expect(() => new URL('example.com')).toThrowError(TypeError);
    let code: unknown;
    try {
      new URL('example.com');
    } catch (e) {
      code = (e as { code?: unknown }).code;
    }
    expect(code).toBe('ERR_INVALID_URL');
    expect(URL.parse('example.com')).toBeNull();
    expect(URL.parse('https://example.com/a')?.href).toBe('https://example.com/a');
  });

  it('http(s) だけを許可する判定', () => {
    const isHttp = (s: string) => URL.canParse(s) && /^https?:$/.test(new URL(s).protocol);
    expect(isHttp('https://example.com')).toBe(true);
    expect(isHttp('javascript:alert(1)')).toBe(false);
    expect(isHttp('example.com')).toBe(false);
  });
});
