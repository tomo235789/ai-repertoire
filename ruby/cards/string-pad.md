---
id: string-pad
lang: ruby
title: 文字列を指定幅まで両側に埋める
tags: [パディング, 中央揃え, 固定幅, 文字埋め, pad, padding, center, fixed-width]
lib: stdlib
fn: String#center
since: "1.9"
verified: 2026-09-17
status: public
---

文字列の左右に文字を詰めて指定の長さにする。固定幅のテキスト表示やログの桁揃えで使う。

## Signature

```ruby
string.center(width, padstr = " ") -> new_string
```

## Usage

```ruby
"abc".center(8)        # => "  abc   "
"abc".center(8, "*")   # => "**abc***"
"abc".center(2)        # => "abc"
"abc".ljust(6, "*")    # => "abc***"
"abc".rjust(6, "*")    # => "***abc"
```

## Contract

- 左右に `padstr`（既定は半角スペース）を詰めて長さ `width` にする。常に新しい文字列を返し、元の文字列は変わらない（`width` 以下でも同じオブジェクトは返さない）
- 余りが奇数なら右側が 1 文字多い（`"abc".center(4)` → `"abc "`、`"ab".center(5)` → `" ab  "`）。`width` の偶奇には依存しない
- `width` が `s.length` 以下（`0`、負数を含む）なら元と同じ内容の文字列を返す。切り詰めない
- `padstr` が複数文字なら左右それぞれの端から繰り返し、端数は切り落とす（`"abc".center(8, "_-")` → `"_-abc_-_"`）
- 空文字を渡すと `padstr` だけで `width` を埋める
- `padstr` が空文字なら `ArgumentError`（`zero width padding`）。`padstr` が `String` でない、`width` が整数に変換できない（`String`、`nil`）と `TypeError`。`width` に `Float` を渡すと切り捨てて使う
- `padstr` と自身のエンコーディングが互換でない（両方に非 ASCII 文字があり、エンコーディングが違うなど）と `Encoding::CompatibilityError`。埋め込みが不要な `width` でも送出する。片方が ASCII のみなら通る
- 長さは文字（コードポイント）単位で数える。全角文字も 1。単一コードポイントの絵文字は 1 だが、結合文字（`e` + U+0301）や ZWJ で結合した絵文字列は複数。`padstr` が全角でも 1 文字として数える
- 純粋関数

## Alternatives

- 片側だけ埋めるなら `ljust` / `rjust`（`padstr` の規則は同じ）
- 数値のゼロ埋めは `format("%03d", n)`。`n.to_s.rjust(3, "0")` は負数で `"0-5"` になる
- `format` の幅指定でも同じことができる: `format("%-8s|", s)`（左寄せ）、`format("%8s|", s)`（右寄せ）。中央揃えは無い

## Pitfalls

- Python の `str.center` は `width` が奇数のとき余りを左に寄せる（`"ab".center(5)` → `'  ab '`）。Ruby は TypeScript 版（es-toolkit の `pad`）と同じで常に右側（`" ab  "`）
- Python の `fillchar` は 1 文字のみだが、Ruby の `padstr` は複数文字を受け付ける。繰り返しの仕方は es-toolkit の `chars` と同じ
- 全角文字も 1 と数えるので表示幅は揃わない。等幅表示で揃えたい場合は表示幅（East Asian Width）を別途計算する
- `ljust` / `rjust` の名前は「文字列をどちらに寄せるか」であって、「どちらに詰めるか」ではない。`rjust` は左に詰めて右寄せにする

## Test

`examples/string-pad_test.rb`
