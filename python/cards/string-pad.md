---
id: string-pad
lang: python
title: 文字列を指定幅まで両側に埋める
tags: [パディング, 中央揃え, 固定幅, 文字埋め, pad, padding, center, fixed-width]
lib: stdlib
fn: str.center
since: "3.0"
verified: 2026-09-17
status: public
---

文字列の左右に文字を詰めて指定の長さにする。固定幅のテキスト表示やログの桁揃えで使う。

## Signature

```python
str.center(width[, fillchar])
```

## Usage

```python
"abc".center(8)       # => '  abc   '
"abc".center(8, "*")  # => '**abc***'
"abc".center(2)       # => 'abc'
"abc".ljust(6, "*")   # => 'abc***'
"abc".rjust(6, "*")   # => '***abc'
```

## Contract

- 左右に `fillchar`（既定は半角スペース）を詰めて長さ `width` にする。新しい文字列を返し、元の文字列は変わらない（`str` は不変）
- 余りが奇数のとき、1 文字多く付く側は `width` の偶奇で決まる。`width` が偶数なら右（`"abc".center(4)` → `'abc '`）、奇数なら左（`"ab".center(5)` → `'  ab '`）
- `width` が `len(s)` 以下（`0`、負数を含む）なら元の文字列をそのまま返す。切り詰めない
- 空文字を渡すと `fillchar` だけで `width` を埋める
- `fillchar` は 1 文字ちょうどでなければ `TypeError`（空文字・2 文字以上は不可）。`width` が `int` でなければ `TypeError`
- 長さはコードポイントで数える。単一コードポイントの絵文字は 1 だが、ZWJ で結合した絵文字列や肌色修飾子付きは複数。結合文字（`e` + U+0301）は 2 と数える。全角文字も 1
- 純粋関数

## Alternatives

- 片側だけ埋めるなら `str.ljust` / `str.rjust`
- 数値のゼロ埋めは `str.zfill`（符号を先頭に保つ）か f-string の `f"{n:05d}"`
- f-string / `format` の配置指定でも同じことができる: `f"{s:*^8}"`（中央）、`f"{s:<8}"`、`f"{s:>8}"`

## Pitfalls

- TypeScript（es-toolkit）の `pad` は余りを **常に右側** に寄せるが、`str.center` は `width` が奇数なら左に寄せる。`'ab'.center(5)` は `'  ab '`、`pad('ab', 5)` は `' ab  '`
- es-toolkit の `pad` は複数文字の `chars` を繰り返せるが、`fillchar` は 1 文字のみ。複数文字パターンで埋めたい場合は自前で組み立てる
- f-string の `^` 指定は余りを常に右側に寄せる（`f"{'ab':^5}"` → `' ab  '`、es-toolkit と同じ）。`str.center` と混ぜると幅が奇数のとき 1 文字ずれるので、どちらかに統一する
- 全角文字も 1 と数えるので表示幅は揃わない。等幅表示で揃えたい場合は `unicodedata.east_asian_width` で表示幅を別途計算する

## Test

`examples/string-pad_test.py`
