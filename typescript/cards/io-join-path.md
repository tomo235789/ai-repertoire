---
id: io-join-path
lang: typescript
title: パスを結合する
tags: [パス結合, ファイルパス, 正規化, 区切り文字, join-path, path, normalize, separator]
lib: stdlib
fn: path.join
since: "Node 18"
verified: 2026-09-17
status: public
---

パスの断片を OS の区切り文字でつなぎ、`.` や `..`、重複した区切りを正規化する。ファイルの読み書き先を組み立てるときに使う。

## Signature

```ts
function join(...paths: string[]): string
```

## Usage

```ts
import { join, resolve } from 'node:path';

join('logs', 'app', '../db', 'x.sqlite'); // => 'logs/db/x.sqlite'（.. を解決）
join('/var', '/log');                     // => '/var/log'（先頭の / は区切りとして扱う）
join('a/', '/b/');                        // => 'a/b/'（末尾の / は残る）
resolve('logs', 'x.log');                 // => '/現在の作業ディレクトリ/logs/x.log'（絶対パスにする）
resolve('/a', 'b', '/c', 'd');            // => '/c/d'（途中の絶対パスで前が捨てられる）
```

## Contract

- 結果は正規化される: `..` は 1 つ上へ戻り、`.` と重複した区切りは消える。空文字列の引数は無視される
- 引数の先頭の `/` は絶対パスとして扱わない（`join('/a', '/b')` は `'/a/b'`）。`resolve` は途中の絶対パスでそれ以前を捨てる
- ルートより上には戻れない（`join('/a', '..', '..', 'b')` は `'/b'`）。相対パスでは `..` が残る（`join('..', 'a')` は `'../a'`、`join('a', '..', '..')` は `'..'`）
- 引数なし、または結果が空になるときは `'.'`
- 末尾の区切りは残る（`join('a', 'b/')` は `'a/b/'`）
- 文字列以外を渡すと `TypeError`（`ERR_INVALID_ARG_TYPE`）
- 区切り文字は実行 OS に依存する。`path.posix` は常に `/`、`path.win32` は常に `\` で、どの OS でも使える。`posix.join` は `\` を区切りとみなさない

## Alternatives

- 絶対パスが欲しいなら `resolve(...)`。`join` は相対のまま返す
- 分解は `dirname` / `basename` / `extname`、`parse(path)` で一括
- URL は `path.join` で組み立てない（`join('https://x.com', 'a')` は `'https:/x.com/a'` になる）。カード url-join-path の `new URL(path, base)` を使う

## Pitfalls

- ユーザー入力を `join(base, input)` すると `..` で `base` の外へ出られる。`resolve(base, input)` の結果が `base + sep` で始まるか確認する
- Python の `os.path.join('/a', '/b')` は `'/b'`（後の絶対パスで前を捨てる）だが、Node の `join` は `'/a/b'`。その挙動が欲しいなら `resolve`
- `path.join` は文字列操作だけでファイルシステムを見ない。存在確認やシンボリックリンクの解決は `realpath`

## Test

`examples/io-join-path.test.ts`
