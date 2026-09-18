---
id: url-build-query
lang: typescript
title: クエリ文字列を組み立てる
tags: [クエリ文字列, URLエンコード, 検索パラメータ, GETパラメータ, query-string, url-encode, search-params, build-query]
lib: stdlib
fn: URLSearchParams
since: "ES2015"
verified: 2026-09-17
status: public
---

キーと値の組から `a=1&b=x+y` の形のクエリ文字列を、エンコード込みで作る。API 呼び出しの URL やリンクの組み立てに使う。

## Signature

```ts
new URLSearchParams(init?: string | Record<string, string> | Iterable<[string, string]>): URLSearchParams
```

## Usage

```ts
const params = new URLSearchParams({ q: 'foo bar', page: '2' });
params.append('tag', 'a');
params.append('tag', 'b'); // 同じキーを複数
params.toString();         // => 'q=foo+bar&page=2&tag=a&tag=b'

const url = new URL('https://api.example.com/search');
url.searchParams.set('q', 'a&b');
url.href;                  // => 'https://api.example.com/search?q=a%26b'
```

## Contract

- `toString()` は `key=value` を `&` でつないだ文字列を返す。先頭に `?` は付かない。空なら `''`
- `application/x-www-form-urlencoded` でエンコードする: 空白は `+`、`+` は `%2B`、`&` `=` `/` `?` `#` はパーセントエンコード、非 ASCII は UTF-8 のパーセントエンコード。`*` `-` `.` `_` と英数字はそのまま
- 順序は追加順。`append` は同じキーを増やし、`set` は同じキーを全部消して 1 つにする
- 値は文字列に変換される。`undefined` は `'undefined'`、`null` は `'null'`、配列は `'1,2'`（カンマ区切り）、オブジェクトは `'[object Object]'`。省きたい値は渡す前に除く
- オブジェクト・配列の組（`[['a', '1'], ['a', '2']]`）・`Map`・文字列（先頭の `?` は 1 つ無視）から作れる
- `url.searchParams` への変更は `url.search` と `url.href` に即座に反映される

## Alternatives

- 単一の値をエンコードするだけなら `encodeURIComponent`。ただし空白は `%20`、`!'()*~` はエンコードしない、と規則が違う
- `qs` や `query-string` パッケージは `a[]=1` や `a[b]=1` のような入れ子表記を扱う。標準 API は平坦なキーだけ
- 解析は同じクラスの `get` / `getAll`（カード url-parse-query）

## Pitfalls

- 空白が `+` になるので、`+` をそのまま送る API（例: `%2B` を要求しないパス風の値）とは合わない場合がある。相手が `%20` を要求するなら `encodeURIComponent` で自前で組む
- `{ a: undefined }` が `a=undefined` になる。`Object.entries(obj).filter(([, v]) => v !== undefined)` を通してから渡す
- 配列を渡すと `a=1%2C2` になり、`a=1&a=2` にはならない。複数値は `append` で 1 つずつ入れる
- Python の `urllib.parse.urlencode` と同じ規則（空白は `+`、`doseq=True` で複数値）

## Test

`examples/url-build-query.test.ts`
