---
id: url-join-path
lang: typescript
title: URL にパスを結合する
tags: [URL結合, 相対URL, ベースURL, エンドポイント, join-url, resolve-url, base-url, relative-url]
lib: stdlib
fn: URL
since: "ES2015"
verified: 2026-09-17
status: public
---

ベース URL に相対パスを解決して絶対 URL を作る。API のエンドポイントやリンク先を組み立てるときに文字列連結の代わりに使う。

## Signature

```ts
new URL(input: string | URL, base?: string | URL): URL
```

## Usage

```ts
const base = 'https://api.example.com/v1/';

new URL('users', base).href;               // => 'https://api.example.com/v1/users'
new URL('users', 'https://api.example.com/v1').href; // => 'https://api.example.com/users'（末尾 / が無いと v1 が置き換わる）
new URL('/health', base).href;             // => 'https://api.example.com/health'（先頭 / はホスト直下）
new URL('../v2/users', base).href;         // => 'https://api.example.com/v2/users'
new URL('users?page=2', base).href;        // => 'https://api.example.com/v1/users?page=2'
```

## Contract

- `input` は `base` に対する相対参照として解決する。`base` のパスの最後のセグメント（末尾 `/` の後ろ、無ければ最後のファイル名相当）が置き換わる
- `input` が `/` で始まればホスト直下からの絶対パス、`//host/...` ならスキームだけ引き継いで別ホスト、スキーム付きなら `base` を無視する
- `..` は 1 つ上へ戻り、ルートより上には戻れない。`./` は現在の位置
- `base` のクエリとフラグメントは `input` にパスがあれば捨てられる。`input` が `?q=1` だけならパスを保ってクエリを置き換え、`#f` だけならクエリも保つ。`''` は `base` からフラグメントだけ落とした URL
- パスの空白や非 ASCII 文字はパーセントエンコードされる（`'c d/é'` は `'c%20d/%C3%A9'`）
- `base` が省略され `input` が相対、または `base` が不正なら `TypeError`（Node では `code: 'ERR_INVALID_URL'`）
- 純粋関数的に振る舞う。`base` に渡した `URL` オブジェクトは変更しない

## Alternatives

- 文字列連結 `base + path` は `//` の重複や `/` の欠落を起こす（`'https://x.com/a/' + '/c'` は `'https://x.com/a//c'`）。相対参照の解決には使わない
- クエリを付けるなら `url.searchParams.set(...)`（カード url-build-query）
- ファイルパスには `path.join`（カード io-join-path）。URL の `..` 解決とは規則が違う

## Pitfalls

- ベースの末尾 `/` の有無で結果が変わる。`'https://x.com/api/v1'` に `'users'` を足すと `v1` が消える。ディレクトリのつもりのベースは末尾を `/` で終える
- 先頭 `/` の相対パスはベースのパスを全部捨てる。プレフィックス付きで配備される API では `'/users'` ではなく `'users'` を渡す
- `mailto:` のような階層を持たないスキームに相対パスは解決できず `TypeError`
- Python の `urllib.parse.urljoin` と同じ RFC 3986 の解決規則。ただし `urljoin` は不正でも例外を投げない

## Test

`examples/url-join-path.test.ts`
