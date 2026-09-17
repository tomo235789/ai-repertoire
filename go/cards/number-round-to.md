---
id: number-round-to
lang: go
title: 数値を指定した小数桁数で四捨五入する
tags: [四捨五入, 小数桁, 丸め, round, precision, decimal-places, half-away-from-zero]
lib: stdlib
fn: math.Round
since: "1.10"
verified: 2026-09-17
status: public
---

小数第 n 位（負なら 10 の n 乗の位）で四捨五入した数値を返す。`math.Round` は整数にしか丸めないので、10 の累乗を掛けて割るイディオムで桁を指定する。表示用の桁揃えや集計値の丸めに使う。

## Signature

```go
func Round(x float64) float64
```

## Usage

```go
import "math"

func roundTo(x float64, digits int) float64 {
	p := math.Pow(10, float64(digits))
	return math.Round(x*p) / p
}

roundTo(1.2345, 2) // => 1.23
roundTo(1250, -2)  // => 1300
roundTo(2.5, 0)    // => 3
```

## Contract

- `math.Round` は最も近い整数へ丸め、`.5` は **0 から遠い方** へ（`Round(2.5)` は `3`、`Round(-2.5)` は `-3`、`Round(0.5)` は `1`）。偶数丸めではない
- 桁指定は `math.Round(x*p) / p`（`p` は 10 の `digits` 乗）。`digits` が負なら 10 の位・100 の位で丸める（`roundTo(1250, -2)` は `1300`、`roundTo(1234.5678, -2)` は `1200`）
- 浮動小数点の補正はしない。変数 `x = 1.005` では `x*100` が `100.49999999999999` なので `roundTo(1.005, 2)` は `1`。一方 `2.675*100` は `267.5` になるので `roundTo(2.675, 2)` は `2.68`
- `Round(NaN)` は `NaN`、`Round(±Inf)` は `±Inf`、`Round(±0)` は `±0`。`roundTo(-0.4, 0)` は `-0`（`math.Signbit` が `true`）
- `p` が `+Inf` や `0` になるほど極端な `digits`（`±400` など）では `NaN`
- 入力を変更しない純粋関数。panic しない

## Alternatives

- 偶数丸め（銀行家の丸め）なら `math.RoundToEven`（`RoundToEven(2.5)` は `2`）。Python の `round` と同じ意味論
- 桁を揃えた文字列（`"1.50"`）が欲しいなら `fmt.Sprintf("%.2f", x)` か `strconv.FormatFloat(x, 'f', 2, 64)`。2 進数の値を正しく丸めるので `Sprintf("%.2f", 2.675)` は `"2.67"`、`Sprintf("%.0f", 2.5)` は `"2"`
- 切り上げ・切り捨てなら `math.Ceil` / `math.Floor`（同じイディオムで桁指定できる）
- 金額など誤差を許容できない値は整数（最小単位）で扱う

## Pitfalls

- `.5` の扱いが 3 言語で全部違う。TypeScript（es-toolkit の `round`）は正の無限大方向で `round(-2.5)` は `-2`、Python の `round` は偶数丸めで `round(2.5)` は `2`。`math.Round` は `-3` と `3`
- 定数だけの式はコンパイル時に任意精度で計算される。リテラルで `math.Round(1.005*100)/100` と書くと `1.01` になるが、変数経由では `1`。テストの期待値をリテラルの式で作ると本番と食い違う
- `fmt.Sprintf` の丸めとは一致しない。`Sprintf("%.1f", 1.45)` は `"1.4"` だが `roundTo(1.45, 1)` は `1.5`
- 整数にするなら `int(math.Round(x))`。`int(x)` はゼロ方向の切り捨て

## Test

`examples/number-round-to_test.go`
