// カード string-case-convert の Contract を検証するテスト
import { camelCase, kebabCase, pascalCase, snakeCase, words } from 'es-toolkit';
import { describe, expect, it } from 'vitest';

describe('string-case-convert: kebabCase', () => {
  it('Usage のとおり 4 つの命名規則に変換できる', () => {
    expect(kebabCase('userProfileURL')).toBe('user-profile-url');
    expect(camelCase('user_profile_url')).toBe('userProfileUrl');
    expect(snakeCase('UserProfileURL')).toBe('user_profile_url');
    expect(pascalCase('user-profile-url')).toBe('UserProfileUrl');
  });

  it('区切り文字・大文字境界・数字で単語に分け、数字は独立した単語になる', () => {
    expect(kebabCase('hello-World_foo bar')).toBe('hello-world-foo-bar');
    expect(kebabCase('version2Update')).toBe('version-2-update');
    expect(camelCase('version2Update')).toBe('version2Update');
    expect(kebabCase('md5 utf8')).toBe('md-5-utf-8');
  });

  it('連続大文字は略語として 1 語にまとめ、直後に小文字が続けばそこで分ける', () => {
    expect(kebabCase('XMLHttpRequest')).toBe('xml-http-request');
    expect(kebabCase('HTTPRequest')).toBe('http-request');
    expect(kebabCase('iOS')).toBe('i-os');
    expect(pascalCase('HTTPRequest')).toBe('HttpRequest');
    expect(camelCase('URLParser')).toBe('urlParser');
  });

  it('記号は出力に残らず、空文字・空白のみ・記号のみは空文字を返す', () => {
    expect(kebabCase('Rock & Roll!')).toBe('rock-roll');
    expect(kebabCase("Don't stop")).toBe('don-t-stop');
    expect(kebabCase('')).toBe('');
    expect(kebabCase('   ')).toBe('');
    expect(kebabCase('---')).toBe('');
  });

  it('非 ASCII 文字も単語として残り、アクセントは除去されない', () => {
    expect(kebabCase('Crème Brûlée')).toBe('crème-brûlée');
    expect(kebabCase('こんにちは 世界')).toBe('こんにちは-世界');
    expect(pascalCase('é-mail')).toBe('ÉMail');
  });

  it('4 関数とも words と同じ単語分割を使う', () => {
    const input = 'camelCaseHTTPRequest2';
    const split = words(input);
    expect(split).toEqual(['camel', 'Case', 'HTTP', 'Request', '2']);
    expect(kebabCase(input)).toBe(split.map((w) => w.toLowerCase()).join('-'));
    expect(snakeCase(input)).toBe(split.map((w) => w.toLowerCase()).join('_'));
  });

  it('どんな文字列でも例外を投げず、同じ入力には同じ結果を返す', () => {
    const input = 'Some Input_value-42';
    expect(() => kebabCase('🚀 emoji ✨')).not.toThrow();
    expect(kebabCase(input)).toBe(kebabCase(input));
  });
  it('絵文字は 1 単語として残り、ZWJ 結合列は要素ごとに分かれる', () => {
    expect(kebabCase('hello 🐶 world')).toBe('hello-🐶-world');
    expect(kebabCase('👨‍👩‍👧 x')).toBe('👨-👩-👧-x');
  });
});
