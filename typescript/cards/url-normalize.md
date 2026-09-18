---
id: url-normalize
lang: typescript
title: URL を正規化する
tags: [URL正規化, 同一判定, 重複排除, 標準形, normalize-url, canonical, dedupe-url, url-equality]
lib: stdlib
fn: URL
since: "ES2015"
verified: 2026-09-17
status: public
---

表記ゆれのある URL を `new URL(s).href` で標準形にする。同じ URL かの比較やキャッシュキー、クローラの重複排除に使う。

## Signature

```ts
new URL(input: string | URL, base?: string | URL): URL // .href で正規化された文字列
```

## Usage

```ts
new URL('HTTPS://Example.COM:443/a/../b/./c?x=1#f').href;
// => 'https://example.com/b/c?x=1#f'（スキーム・ホストは小文字、既定ポート除去、パス正規化）
new URL('https://example.com/a b/é').href;
// => 'https://example.com/a%20b/%C3%A9'

const u = new URL('https://example.com/?b=2&a=1');
u.searchParams.sort();
u.href; // => 'https://example.com/?a=1&b=2'（クエリの順序も揃える）
```

## Contract

- スキームとホストは小文字になる。ホストの前後の空白と制御文字は除かれ、非 ASCII ホストは Punycode（`xn--`）になる
- そのスキームの既定ポート（`http:80`、`https:443`、`ws:80`、`ftp:21`）は消える。それ以外のポートは残る
- パスは `.` と `..` を解決する。ホストだけの URL のパスは `/` になる。末尾の `/` の有無は区別され、`//` の重複も残る
- パス・クエリ・フラグメントの空白と非 ASCII 文字はパーセントエンコードされる。既にある `%XX` はそのまま（大文字化も復号もしない。`%7e` と `~` は別物）
- パスとクエリの大文字小文字は変わらない。クエリの順序も変わらず、`searchParams.sort()` でキー順に並べ替える（同じキーの値の順序は保つ）
- `searchParams` を触ると `search` が再シリアライズされる（`%20` が `+` になるなど）。空になれば `?` も消える
- 触らなければ空のクエリ `?` と空のフラグメント `#` は残る

## Alternatives

- 比較だけなら `new URL(a).href === new URL(b).href`。オブジェクト同士に等価比較は無い
- `www.` の除去、末尾 `/` の統一、`utm_*` の削除、フラグメント除去のような「意味的な」正規化は `normalize-url` パッケージ。標準 API は構文上の正規化だけ
- `URL.parse(s)`（Node 22.1+）は不正なとき `null` を返す。判定はカード url-is-absolute

## Pitfalls

- `example.com/a` と `example.com/a/` は別の URL のまま。統一したければ `pathname` を自分で整える
- `searchParams.sort()` は `search` を書き換えるので、署名済み URL（署名対象にクエリの順序が含まれるもの）に使うと壊れる
- `%7E` を `~` に戻すような RFC 3986 のエンコード正規化はしない。同じ資源でも文字列が違えば別扱いになる
- Python の `urllib.parse.urlsplit` はホストの小文字化も既定ポート除去もしない。WHATWG URL 準拠の挙動が欲しければ `urllib3.util.parse_url` などを使う

## Test

`examples/url-normalize.test.ts`
