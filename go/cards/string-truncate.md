---
id: string-truncate
lang: go
title: 長い文字列を省略記号付きで切り詰める
tags: [切り詰め, 省略, 文字数制限, 省略記号, truncate, ellipsis, clip, shorten]
lib: samber/lo
fn: lo.Ellipsis
since: "1.38"
verified: 2026-09-17
status: public
---

文字列が上限を超えるとき、末尾を `...` に置き換えて上限のルーン数に収める。一覧表示のタイトルや通知本文の切り詰めに使う。

## Signature

```go
func Ellipsis(str string, length int) string
```

## Usage

```go
import "github.com/samber/lo"

text := "The quick brown fox jumps over the lazy dog"
lo.Ellipsis(text, 30)             // => "The quick brown fox jumps o..."
lo.Ellipsis(text, 20)             // => "The quick brown f..."
lo.Ellipsis(text, 100)            // => "The quick brown fox jumps over the lazy dog"
lo.Ellipsis("日本語の文章です", 5) // => "日本..."
```

## Contract

- `length` は **省略記号 `...` を含めた** 結果の最大ルーン数。切り詰めるときは先頭 `length - 3` ルーン + `...`
- 長さは **ルーン（コードポイント）単位**。バイト長ではないので日本語や絵文字を途中で分断しない（`Ellipsis("日本語の文章です", 5)` は 5 ルーン・9 バイト）。ZWJ で結合した絵文字列はコードポイントごとに分かれる
- 先に `strings.TrimSpace` で前後の空白を落とし、切り出した本文の末尾の空白も落とす。切り詰めない場合も前後の空白は消える（`"  padded text  "`, 20 → `"padded text"`）。切り位置の直前が空白なら結果は `length` より短くなる（`"hello world"`, 9 → `"hello..."`）
- 空白を落とした後のルーン数が `length` 以下ならそのまま返す
- 切り詰めが必要で `length` が 3 以下（0 や負数を含む）なら `"..."` だけを返す。この場合は結果が `length` を超える（`Ellipsis("abcd", 2)` は `"..."`）
- 省略記号は ASCII の `...` 固定。空文字は `""`。純粋関数で panic しない

## Alternatives

- 省略記号を変えたい・単語境界で切りたい場合は `r := []rune(s)` にして `string(r[:n]) + "…"`。長さの判定は `len(s)`（バイト数）ではなく `utf8.RuneCountInString(s)`
- 書記素（表示上の 1 文字）単位の分割は標準に無い。`github.com/rivo/uniseg` などを使う
- 空白の正規化だけなら `strings.Join(strings.Fields(s), " ")`

## Pitfalls

- TypeScript（es-toolkit/compat の `truncate`）と同じく `length` に省略記号の分が含まれる。「本文 n 文字 + 省略記号」なら `n + 3`
- `truncate` は `omission` / `separator` を指定でき入力の空白を保つが、`Ellipsis` は `...` 固定で前後の空白を落とす。Python の `textwrap.shorten` は常に単語境界で切る
- `s[:n]` はバイト位置で切るので UTF-8 の途中で切れて壊れた文字列になる。自前で切るときは `[]rune` を経由する
- `length` が 3 以下だと `...` だけになり `length` を超える。上限が厳密なら呼び出し側で `length >= 4` を保証する

## Test

`examples/string-truncate_test.go`
