// カード url-join-path の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

const href = (input: string, base?: string) => new URL(input, base).href;

describe('url-join-path: URL', () => {
  it('ベースの最後のセグメントが置き換わり、末尾 / の有無で結果が変わる', () => {
    expect(href('users', 'https://api.example.com/v1/')).toBe('https://api.example.com/v1/users');
    expect(href('users', 'https://api.example.com/v1')).toBe('https://api.example.com/users');
    expect(href('users', 'https://api.example.com')).toBe('https://api.example.com/users');
    expect(href('./users', 'https://api.example.com/v1/')).toBe('https://api.example.com/v1/users');
    expect(href('users/', 'https://api.example.com/v1/')).toBe('https://api.example.com/v1/users/');
  });

  it('先頭 / はホスト直下、//host はスキームだけ引き継ぐ、スキーム付きはベースを無視', () => {
    expect(href('/health', 'https://api.example.com/v1/')).toBe('https://api.example.com/health');
    expect(href('//cdn.example.com/x.js', 'https://api.example.com/v1/')).toBe('https://cdn.example.com/x.js');
    expect(href('//cdn.example.com/x.js', 'http://api.example.com/')).toBe('http://cdn.example.com/x.js');
    expect(href('https://other.example.com/z', 'https://api.example.com/v1/')).toBe('https://other.example.com/z');
  });

  it('.. は 1 つ上へ戻り、ルートより上には戻れない', () => {
    expect(href('../v2/users', 'https://api.example.com/v1/')).toBe('https://api.example.com/v2/users');
    expect(href('../../../x', 'https://api.example.com/a/b/')).toBe('https://api.example.com/x');
  });

  it('クエリとフラグメントの引き継ぎ', () => {
    const base = 'https://api.example.com/v1/items?page=2#top';
    expect(href('users', base)).toBe('https://api.example.com/v1/users');
    expect(href('users?x=1', base)).toBe('https://api.example.com/v1/users?x=1');
    expect(href('?x=1', base)).toBe('https://api.example.com/v1/items?x=1');
    expect(href('#frag', base)).toBe('https://api.example.com/v1/items?page=2#frag');
    expect(href('', base)).toBe('https://api.example.com/v1/items?page=2');
  });

  it('空白や非 ASCII はパーセントエンコードされる', () => {
    expect(href('c d/é', 'https://api.example.com/')).toBe('https://api.example.com/c%20d/%C3%A9');
  });

  it('ベース無しの相対参照や不正なベースは TypeError', () => {
    expect(() => new URL('users')).toThrowError(TypeError);
    expect(() => new URL('users', 'not a url')).toThrowError(TypeError);
    expect(() => new URL('users', 'mailto:a@example.com')).toThrowError(TypeError);
    let code: unknown;
    try {
      new URL('users');
    } catch (e) {
      code = (e as { code?: unknown }).code;
    }
    expect(code).toBe('ERR_INVALID_URL');
  });

  it('URL オブジェクトをベースにしても変更されない', () => {
    const base = new URL('https://api.example.com/v1/');
    expect(href('users', base.href)).toBe('https://api.example.com/v1/users');
    expect(new URL('users', base).href).toBe('https://api.example.com/v1/users');
    expect(base.href).toBe('https://api.example.com/v1/');
  });

  it('文字列連結は // の重複や / の欠落を起こす', () => {
    expect('https://api.example.com/v1/' + '/users').toBe('https://api.example.com/v1//users');
    expect('https://api.example.com/v1' + 'users').toBe('https://api.example.com/v1users');
  });
});
