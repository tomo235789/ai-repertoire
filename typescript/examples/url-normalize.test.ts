// カード url-normalize の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

const norm = (s: string) => new URL(s).href;

describe('url-normalize: URL', () => {
  it('スキームとホストは小文字になり、非 ASCII ホストは Punycode になる', () => {
    expect(norm('HTTPS://Example.COM/A')).toBe('https://example.com/A');
    expect(norm('  https://example.com/a  ')).toBe('https://example.com/a');
    expect(norm('https://日本語.jp/')).toBe('https://xn--wgv71a119e.jp/');
  });

  it('既定ポートは消え、それ以外は残る', () => {
    expect(norm('http://example.com:80/')).toBe('http://example.com/');
    expect(norm('https://example.com:443/')).toBe('https://example.com/');
    expect(norm('https://example.com:80/')).toBe('https://example.com:80/');
    expect(norm('http://example.com:8080/')).toBe('http://example.com:8080/');
    expect(norm('ws://example.com:80/')).toBe('ws://example.com/');
  });

  it('パスの . と .. を解決し、ホストだけなら / になる。末尾 / と // は残る', () => {
    expect(norm('https://example.com/a/../b/./c')).toBe('https://example.com/b/c');
    expect(norm('https://example.com/a/b/../../../c')).toBe('https://example.com/c');
    expect(norm('https://example.com')).toBe('https://example.com/');
    expect(norm('https://example.com/a/')).toBe('https://example.com/a/');
    expect(norm('https://example.com/a//b')).toBe('https://example.com/a//b');
  });

  it('空白と非 ASCII はパーセントエンコードされ、既存の %XX はそのまま', () => {
    expect(norm('https://example.com/a b/é?q=a b#f g')).toBe('https://example.com/a%20b/%C3%A9?q=a%20b#f%20g');
    expect(norm('https://example.com/%7euser')).toBe('https://example.com/%7euser');
    expect(norm('https://example.com/%41')).toBe('https://example.com/%41');
    expect(norm('https://example.com/a%2Fb')).toBe('https://example.com/a%2Fb');
  });

  it('パスとクエリの大文字小文字と順序は変わらない', () => {
    expect(norm('https://example.com/A/B?Q=V&b=2&a=1')).toBe('https://example.com/A/B?Q=V&b=2&a=1');
  });

  it('searchParams.sort() でキー順に並び、同じキーの値の順序は保つ', () => {
    const u = new URL('https://example.com/?b=2&a=1&a=0');
    u.searchParams.sort();
    expect(u.href).toBe('https://example.com/?a=1&a=0&b=2');
  });

  it('searchParams を触ると search が再シリアライズされ、空になれば ? も消える', () => {
    const a = new URL('https://example.com/a?q=a%20b');
    a.searchParams.sort();
    expect(a.href).toBe('https://example.com/a?q=a+b');
    const b = new URL('https://example.com/?a=1');
    b.searchParams.delete('a');
    expect(b.href).toBe('https://example.com/');
  });

  it('触らなければ空の ? と # は残る', () => {
    expect(norm('https://example.com/a?')).toBe('https://example.com/a?');
    expect(norm('https://example.com/a#')).toBe('https://example.com/a#');
  });

  it('同じ URL かの比較は href 同士で行う', () => {
    expect(norm('HTTP://EXAMPLE.com:80/a/./b')).toBe(norm('http://example.com/a/b'));
    expect(norm('https://example.com/a')).not.toBe(norm('https://example.com/a/'));
  });
});
