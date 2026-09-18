---
id: url-parse-query
lang: typescript
title: クエリ文字列を解析する
tags: [クエリ文字列, URLデコード, 検索パラメータ, 複数値, query-string, url-decode, search-params, parse-query]
lib: stdlib
fn: URLSearchParams
since: "ES2015"
verified: 2026-09-17
status: public
---

`a=1&a=2&q=x+y` の形のクエリ文字列からキーごとの値を取り出す。リクエストの URL やリダイレクト先の解析に使う。

## Signature

```ts
new URLSearchParams(init?: string | Record<string, string> | Iterable<[string, string]>): URLSearchParams
```

## Usage

```ts
const params = new URL('https://example.com/search?q=foo+bar&tag=a&tag=b&page=2').searchParams;

params.get('q');        // => 'foo bar'（+ は空白にデコード）
params.get('tag');      // => 'a'（最初の値だけ）
params.getAll('tag');   // => ['a', 'b']
params.get('missing');  // => null
params.get('page');     // => '2'（文字列。数値にはならない）
Object.fromEntries(params); // => { q: 'foo bar', tag: 'b', page: '2' }（重複キーは最後が勝つ）
```

## Contract

- `get(name)` は最初の値、`getAll(name)` は全部の値を配列で返す。無いキーは `null` / `[]`
- 値は常に文字列。`'42'` は数値にならず、`'true'` も真偽値にならない。変換は自分で行う
- `+` と `%20` は空白に、`%XX` は UTF-8 としてデコードされる。不正な `%`（`%zz` や単独の `%`）は例外にならずそのまま残り、不正な UTF-8 は U+FFFD になる
- `a=` も `a`（`=` 無し）も値 `''` で、`has('a')` は `true`。`has(name, value)` で値の一致まで確認できる（Node 20+）
- 文字列で作るとき先頭の `?` を 1 つだけ無視する。`#...` は取り除かない（`'a=1#f'` は値 `'1#f'`）。フラグメント付きの URL 全体は `new URL(s).searchParams` で解析する
- 区切りは `&` だけ。`;` は区切りにならない
- 反復順は出現順で、`Object.fromEntries` は重複キーの最後の値を残す

## Alternatives

- `decodeURIComponent` は単一の値のデコード用で、`+` を空白にせず、不正な `%` で `URIError` を投げる
- `qs` パッケージは `a[]=1` や `a[b]=1` をオブジェクトに展開する。標準 API はキー `'a[]'` のまま
- 組み立ては同じクラスの `append` / `toString`（カード url-build-query）

## Pitfalls

- `Object.fromEntries(params)` は複数値を潰す。チェックボックスやタグなど複数値のキーは `getAll` で取る
- `get` の返り値は `string | null` なので、`Number(params.get('page'))` は無いときに `0` になる。`null` を先に判定する
- キーが `'__proto__'` でも普通の文字列キーとして扱われる（`Object.fromEntries` でも prototype を汚染しない）
- Python の `urllib.parse.parse_qs` は常にリストを返し、空の値を既定で捨てる（`keep_blank_values=True` で残る）。`URLSearchParams` は空の値も残す

## Test

`examples/url-parse-query.test.ts`
