---
id: number-round-to
lang: ruby
title: 数値を指定した小数桁数で四捨五入する
tags: [四捨五入, 小数桁, 丸め, 偶数丸め, round, precision, decimal-places, half-even]
lib: stdlib
fn: Float#round
since: "2.4"
verified: 2026-09-17
status: public
---

小数第 n 位（負なら 10 の n 乗の位）で丸めた数値を返す。既定は `.5` を 0 から遠い方へ丸める一般的な四捨五入で、`half:` で偶数丸めにも切り替えられる。表示用の桁揃えや集計値の丸めに使う。

## Signature

```ruby
float.round(ndigits = 0, half: :up) -> integer | float
```

## Usage

```ruby
1.2345.round        # => 1
1.2345.round(2)     # => 1.23
1250.0.round(-2)    # => 1300
2.5.round           # => 3
2.5.round(half: :even)  # => 2
2.675.round(2)      # => 2.68
```

## Contract

- `ndigits` を省略するか `0` 以下を渡すと `Integer` を返す。正の `ndigits` なら `Float` を返す（`1.0.round(2)` は `1.0`）
- `.5` の既定（`half: :up`）は 0 から遠い方へ丸める。`2.5.round` は `3`、`-2.5.round` は `-3`、`0.5.round` は `1`
- `half: :even` は偶数丸め（`2.5` → `2`、`3.5` → `4`、`-2.5` → `-2`）。`half: :down` は 0 に近い方（`2.5` → `2`、`-2.5` → `-2`）。`half: nil` は `:up`。それ以外の値は `ArgumentError`
- `ndigits` が負なら 10 の位・100 の位で丸める（`1234.5678.round(-2)` は `1200` の `Integer`）
- 2 進数の表現誤差を補正する。`2.675.round(2)` は `2.68`、`1.005.round(2)` は `1.01`、`1.45.round(1)` は `1.5`（10 進の見た目どおり）。`half: :even` でも同じ補正が効き、`2.675.round(2, half: :even)` は `2.68`、`2.665.round(2, half: :even)` は `2.66`
- `Float::NAN` / `Float::INFINITY` は `ndigits` 省略時に `FloatDomainError`。正の `ndigits` を指定すればそのまま返る
- `ndigits` に `Float` を渡すと整数に切り捨てて使う。`String` や `nil` は `TypeError`
- `Integer#round` も同じ `half:` を受け、負の `ndigits` で 10 の位で丸める（`15.round(-1)` は `20`、`15.round(-1, half: :even)` は `20`、`25.round(-1, half: :even)` は `20`）。正の `ndigits` は何もしない
- 純粋関数。引数を変更しない

## Alternatives

- 桁を揃えた文字列（`"1.50"`）が欲しいなら `format("%.2f", x)`。ただし `format` の `.5` の扱いは `round` と異なる（`format("%.0f", 2.5)` は `"2"`、`format("%.1f", 1.45)` は `"1.4"`）。`round` の結果を揃えて表示したいなら `format("%.2f", x.round(2))`
- 切り上げ・切り捨てなら `ceil(ndigits)` / `floor(ndigits)` / `truncate(ndigits)`
- 金額など誤差を許容できない値は整数（最小単位）か `BigDecimal("2.675").round(2)`（`bigdecimal` gem、既定は `ROUND_HALF_UP`）か `Rational("2.675").round(2)` で扱う

## Pitfalls

- Python の `round()` は偶数丸めで `round(2.5)` が `2`、`round(2.675, 2)` が表現誤差で `2.67`。Ruby は `3` と `2.68`。移植すると `.5` ちょうどの値で結果が変わる
- TypeScript 版（es-toolkit の `round`）は `.5` を正の無限大方向に丸める（`round(-2.5)` は `-2`、Ruby は `-3`）。表現誤差の補正もしないので `round(1.005, 2)` は `1`（Ruby は `1.01`）
- `x.round(0)` は `Integer` を返す。`Float` のまま丸めたいなら `x.round(0).to_f` か `x.round(1)` 等の正の桁を使う
- 結果を文字列化しても末尾の `0` は付かない（`1.5.round(2).to_s` は `"1.5"`）。表示のためだけなら `format` を使う

## Test

`examples/number-round-to_test.rb`
