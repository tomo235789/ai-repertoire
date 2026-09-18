// カード url-build-query の Contract を検証するテスト
import { describe, expect, it } from 'vitest';

describe('url-build-query: URLSearchParams', () => {
  it('key=value を & でつなぎ、先頭に ? は付かない', () => {
    expect(new URLSearchParams({ q: 'foo', page: '2' }).toString()).toBe('q=foo&page=2');
    expect(new URLSearchParams().toString()).toBe('');
    expect(`${new URLSearchParams({ a: '1' })}`).toBe('a=1');
  });

  it('form-urlencoded でエンコードする（空白は +、+ は %2B）', () => {
    expect(new URLSearchParams({ q: 'foo bar' }).toString()).toBe('q=foo+bar');
    expect(new URLSearchParams({ q: 'a+b' }).toString()).toBe('q=a%2Bb');
    expect(new URLSearchParams({ q: 'a&b=c/?#' }).toString()).toBe('q=a%26b%3Dc%2F%3F%23');
    expect(new URLSearchParams({ q: 'こ' }).toString()).toBe('q=%E3%81%93');
    expect(new URLSearchParams({ q: "*-._!'()~" }).toString()).toBe('q=*-._%21%27%28%29%7E');
  });

  it('encodeURIComponent とは規則が違う', () => {
    expect(encodeURIComponent('foo bar')).toBe('foo%20bar');
    expect(encodeURIComponent("*-._!'()~")).toBe("*-._!'()~");
  });

  it('順序は追加順。append は増やし、set は置き換える', () => {
    const p = new URLSearchParams({ b: '1', a: '2' });
    p.append('a', '3');
    expect(p.toString()).toBe('b=1&a=2&a=3');
    p.set('a', '9');
    expect(p.toString()).toBe('b=1&a=9');
  });

  it('値は文字列化される。undefined / null / 配列 / オブジェクトに注意', () => {
    const p = new URLSearchParams({ a: undefined, b: null, c: 1, d: true, e: [1, 2], f: { x: 1 } } as never);
    expect(p.toString()).toBe('a=undefined&b=null&c=1&d=true&e=1%2C2&f=%5Bobject+Object%5D');
    const filtered = Object.entries({ a: '1', b: undefined }).filter((kv): kv is [string, string] => kv[1] !== undefined);
    expect(new URLSearchParams(filtered).toString()).toBe('a=1');
  });

  it('組の配列・Map・文字列からも作れる', () => {
    expect(new URLSearchParams([['a', '1'], ['a', '2']]).toString()).toBe('a=1&a=2');
    expect(new URLSearchParams(new Map([['a', '1']])).toString()).toBe('a=1');
    expect(new URLSearchParams('?a=1&b=2').toString()).toBe('a=1&b=2');
  });

  it('url.searchParams への変更は href に反映される', () => {
    const url = new URL('https://api.example.com/search');
    url.searchParams.set('q', 'a&b');
    url.searchParams.append('tag', 'x y');
    expect(url.search).toBe('?q=a%26b&tag=x+y');
    expect(url.href).toBe('https://api.example.com/search?q=a%26b&tag=x+y');
  });
});
