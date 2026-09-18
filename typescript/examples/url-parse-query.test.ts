// カード url-parse-query の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

describe('url-parse-query: URLSearchParams', () => {
  it('get は最初の値、getAll は全部、無いキーは null / []', () => {
    const p = new URLSearchParams('tag=a&tag=b&q=x');
    expect(p.get('tag')).toBe('a');
    expect(p.getAll('tag')).toEqual(['a', 'b']);
    expect(p.get('missing')).toBeNull();
    expect(p.getAll('missing')).toEqual([]);
  });

  it('値は常に文字列', () => {
    const p = new URLSearchParams('page=42&flag=true');
    expect(p.get('page')).toBe('42');
    expect(typeof p.get('page')).toBe('string');
    expect(p.get('flag')).toBe('true');
  });

  it('+ と %20 は空白に、%XX は UTF-8 としてデコードされる', () => {
    const p = new URLSearchParams('a=x+y&b=x%20y&c=%E3%81%82&d=a%2Bb');
    expect(p.get('a')).toBe('x y');
    expect(p.get('b')).toBe('x y');
    expect(p.get('c')).toBe('あ');
    expect(p.get('d')).toBe('a+b');
  });

  it('不正な % は例外にならずそのまま残り、不正な UTF-8 は U+FFFD になる', () => {
    expect(new URLSearchParams('a=%').get('a')).toBe('%');
    expect(new URLSearchParams('a=%zz').get('a')).toBe('%zz');
    expect(new URLSearchParams('a=%E3').get('a')).toBe('\uFFFD');
    expect(() => decodeURIComponent('%zz')).toThrowError(URIError);
    expect(decodeURIComponent('a+b')).toBe('a+b');
  });

  it('空の値と = 無しのキーは "" で has は true', () => {
    const p = new URLSearchParams('a=&b&c=1');
    expect(p.get('a')).toBe('');
    expect(p.get('b')).toBe('');
    expect(p.has('a')).toBe(true);
    expect(p.has('b')).toBe(true);
    expect(p.has('c', '1')).toBe(true);
    expect(p.has('c', '2')).toBe(false);
  });

  it('先頭の ? は 1 つだけ無視し、# は取り除かない', () => {
    expect(new URLSearchParams('?a=1').get('a')).toBe('1');
    expect(new URLSearchParams('??a=1').get('?a')).toBe('1');
    expect(new URLSearchParams('a=1#f').get('a')).toBe('1#f');
    expect(new URL('https://example.com/?a=1#f').searchParams.get('a')).toBe('1');
  });

  it('; は区切りにならない', () => {
    expect(new URLSearchParams('a=1;b=2').get('a')).toBe('1;b=2');
  });

  it('反復順は出現順で、Object.fromEntries は重複キーの最後が勝つ', () => {
    const p = new URLSearchParams('b=1&a=2&b=3');
    expect([...p.entries()]).toEqual([['b', '1'], ['a', '2'], ['b', '3']]);
    expect(Object.fromEntries(p)).toEqual({ b: '3', a: '2' });
  });

  it('__proto__ も普通のキーとして扱う', () => {
    const obj = Object.fromEntries(new URLSearchParams('__proto__=x'));
    expect(Object.getPrototypeOf(obj)).toBe(Object.prototype);
    expect(Object.hasOwn(obj, '__proto__')).toBe(true);
  });
});
