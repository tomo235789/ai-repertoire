---
id: url-is-absolute
lang: typescript
title: URL が絶対か判定する
tags: [URL判定, 絶対URL, 妥当性検証, スキーム, is-absolute-url, validate-url, can-parse, url-check]
lib: stdlib
fn: URL.canParse
since: "ES2023"
verified: 2026-09-17
status: public
---

文字列がスキーム付きの絶対 URL として解析できるかを例外なしで判定する。入力値の検証や、相対パスと絶対 URL で処理を分けるときに使う。

## Signature

```ts
static canParse(url: string | URL, base?: string | URL): boolean
```

## Usage

```ts
URL.canParse('https://example.com/a');   // => true
URL.canParse('example.com/a');           // => false（スキームが無い）
URL.canParse('/a/b');                    // => false
URL.canParse('//cdn.example.com/x.js');  // => false（スキーム相対はベース無しでは解析できない）
URL.canParse('/a/b', 'https://example.com'); // => true（ベースがあれば相対でも解析できる）
```

## Contract

- ベース無しでは、スキーム（`英字:` で始まる）があって解析できるときだけ `true`。`example.com`、`/a`、`//host/a`、`''`、`http://`（ホストなし）は `false`
- `base` を渡すと `new URL(url, base)` が成功するかを返す。相対参照でも `true` になり、不正な `base` なら `false`
- スキームらしきものは何でも通る: `mailto:a@b`、`data:,x`、`javascript:alert(1)`、`a:b`、`c:\a`（ドライブレターがスキーム `c:` として解析される）は `true`
- 前後の空白は取り除いて判定する（`' https://example.com '` は `true`）。パス中の空白は `true`（エンコードされる）
- 引数は文字列に変換される。`undefined` や `null` は `'undefined'` / `'null'` として `false`。引数なしは `TypeError`
- 例外を投げず、副作用も無い

## Alternatives

- 旧イディオムは `try { new URL(s); return true } catch { return false }`。`new URL` は失敗すると `TypeError`（Node では `code: 'ERR_INVALID_URL'`）を投げる
- 解析結果も欲しいなら `URL.parse(s)`（Node 22.1+）。失敗時は `null`
- `http(s)` だけを許可するなら `URL.canParse(s) && /^https?:$/.test(new URL(s).protocol)`

## Pitfalls

- 「URL として妥当か」ではなく「WHATWG URL パーサが解析できるか」。`javascript:` や `data:` も `true` なので、リンク先として使うなら `protocol` を別に確認する
- Windows のパス `C:\Users\...` は `true` になる。ファイルパスと URL を区別する用途には使えない
- スキーム相対 `//host/path` はベース無しでは `false`。ブラウザで受け取る値には `base` に `location.href` を渡す
- Python には同等の関数が無く、`urllib.parse.urlparse(s).scheme != ''` が近い（`c:\a` も `scheme == 'c'` になる）

## Test

`examples/url-is-absolute.test.ts`
