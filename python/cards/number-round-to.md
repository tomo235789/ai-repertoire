---
id: number-round-to
lang: python
title: 数値を指定した小数桁数で四捨五入する
tags: [四捨五入, 小数桁, 丸め, 偶数丸め, round, precision, decimal-places, banker-rounding]
lib: stdlib
fn: round
since: "3.0"
verified: 2026-09-17
status: public
---

小数第 n 位（負なら 10 の n 乗の位）で丸めた数値を返す。ただし `.5` は **偶数丸め（銀行家の丸め）** で、一般的な四捨五入とは違う。表示用の桁揃えや集計値の丸めに使う。

## Signature

```python
round(number, ndigits=None)
```

## Usage

```python
round(1.2345)      # => 1
round(1.2345, 2)   # => 1.23
round(1250, -2)    # => 1200（偶数丸め）
round(2.5)         # => 2（偶数丸め）
round(2.675, 2)    # => 2.67（浮動小数点の表現誤差）
```

## Contract

- `ndigits` を省略（または `None`）すると `int` を返す。`ndigits` を指定すると（`0` でも）入力と同じ型を返す（`round(2.5, 0)` は `2.0`）
- `.5` は偶数丸め。`round(0.5)` は `0`、`round(1.5)` は `2`、`round(2.5)` は `2`、`round(-2.5)` は `-2`
- `ndigits` が負なら 10 の位・100 の位で丸める。`int` でも偶数丸めで `round(1250, -2)` は `1200`、`round(1350, -2)` は `1400`
- 浮動小数点の補正はしない。`2.675` は 2 進数では `2.67499...` なので `round(2.675, 2)` は `2.67`。`round(1.005, 2)` は `1.0`
- `Decimal` を渡すと `Decimal` の丸めモード（既定 `ROUND_HALF_EVEN`）で丸め、`round(Decimal("2.675"), 2)` は `Decimal("2.68")`
- `ndigits` が `int` でないと `TypeError`。`ndigits` 省略時に `NaN` を渡すと `ValueError`、`inf` なら `OverflowError`。`ndigits` を指定すれば float の `NaN` / `inf` はそのまま返る（`Decimal("Infinity")` は既定のコンテキストで `InvalidOperation`）
- `round(-0.4, 0)` は `-0.0`（符号付き零）

## Alternatives

- 一般的な四捨五入（`.5` を 0 から遠い方へ）なら `Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`。`Decimal(2.675)` と書くと 2 進数の値がそのまま入り `2.67` になるので `str` を経由するか文字列リテラルで作る
- 桁を揃えた文字列（`'1.50'`）が欲しいなら `f"{x:.2f}"`。これも偶数丸め（`f"{2.5:.0f}"` は `'2'`）
- 切り上げ・切り捨てなら `math.ceil` / `math.floor`（整数のみ。小数桁なら `Decimal.quantize` に `ROUND_CEILING` / `ROUND_FLOOR`）
- 金額など誤差を許容できない値は整数（最小単位）か `Decimal` で扱う

## Pitfalls

- TypeScript 版（es-toolkit の `round`）は `.5` を正の無限大方向に丸める（`round(2.5)` は `3`、`round(-2.5)` は `-2`）。Python は `2` と `-2`。移植すると `.5` ちょうどの値で結果が変わる
- `round(2.675, 2)` が `2.67` になるのは偶数丸めのせいではなく、`2.675` が 2 進数では `2.67499…` として格納されている表現誤差のため。10 進の見た目で「四捨五入なら 2.68」と考えると食い違う
- `ndigits` を省略すると型が `int` に変わる。`float` のまま丸めたいなら `round(x, 0)`
- 表示のためだけなら `round` ではなく書式指定（`f"{x:.2f}"`）を使う。`round(1.5, 1)` の結果を文字列化しても末尾の `0` は付かない

## Test

`examples/number-round-to_test.py`
