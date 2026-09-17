---
id: string-truncate
lang: python
title: 長い文字列を省略記号付きで切り詰める
tags: [切り詰め, 省略, 文字数制限, 省略記号, truncate, ellipsis, clip, shorten]
lib: stdlib
fn: textwrap.shorten
since: "3.4"
verified: 2026-09-17
status: public
---

文字列が上限を超えるとき、単語境界で切って末尾に省略記号を付け、上限に収める。一覧表示のタイトルや通知本文の切り詰めに使う。

## Signature

```python
textwrap.shorten(text, width, **kwargs)
```

## Usage

```python
from textwrap import shorten

text = "The quick brown fox jumps over the lazy dog"
shorten(text, 20)                     # => 'The quick [...]'
shorten(text, 20, placeholder="...")  # => 'The quick brown...'
shorten(text, 20, placeholder="…")    # => 'The quick brown fox…'
shorten(text, 100)                    # => 'The quick brown fox jumps over the lazy dog'
```

## Contract

- 先に連続する空白（改行・タブを含む）を半角スペース 1 つにまとめ、前後の空白を落とす。収まる場合もこの正規化は行われる（`"  a   b "` → `'a b'`）
- 正規化後の長さが `width` 以下なら省略記号を付けずに返す
- 超える場合は **単語境界で** 切り、`placeholder`（既定 `' [...]'`）を付けて `width` 以内にする。`width` は省略記号込みの上限で、結果は `width` を超えない
- 先頭の単語すら入らないときは `placeholder` の先頭空白を除いたものだけを返す（`shorten("abcdefghij", 10, placeholder="...")` は収まるので `'abcdefghij'`、`shorten("abcdefghijk", 10, placeholder="...")` は `'...'`）
- 既定で `-` も区切りになる（`break_on_hyphens=True`。`shorten("hello-world foo", 10, placeholder="...")` は `'hello-...'`。既定の placeholder `' [...]'` だと幅 10 には最初の単語すら入らず `'[...]'` になる）
- `width` が `placeholder.lstrip()` より短いと `ValueError`。`width <= 0` も `ValueError`
- 空文字・空白のみは `''`。純粋関数

## Alternatives

- 文字数で機械的に切るなら `s[:n] + "..."`（結果は `n + 3` 文字。`len(s) <= n` の判定は自前で行う）
- 単語境界で複数行に折り返すなら `textwrap.wrap` / `textwrap.fill`
- 空白の正規化だけなら `" ".join(s.split())`

## Pitfalls

- TypeScript（es-toolkit/compat）の `truncate` は文字位置で切るが、`shorten` は常に単語境界で切る。空白を含まない文字列（URL、日本語の文）は 1 単語扱いになり、収まらなければ省略記号だけになる（`shorten("日本語の文章です", 5, placeholder="…")` → `'…'`）
- `truncate` は入力の空白を保つが、`shorten` は連続空白と改行をまとめる。整形済みテキストには使わない
- 既定の `placeholder` は先頭に空白を含む `' [...]'`。`'...'` にしたければ明示する
- `width` は結果全体の上限。「本文 n 文字 + 省略記号」ではない

## Test

`examples/string-truncate_test.py`
