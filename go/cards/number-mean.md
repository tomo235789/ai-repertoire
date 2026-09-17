---
id: number-mean
lang: go
title: 数値配列の平均を求める
tags: [平均, 算術平均, 集計, mean, average, avg, statistics]
lib: samber/lo
fn: lo.Mean
since: "1.38"
verified: 2026-09-17
status: public
---

数値スライスの算術平均を要素と同じ型で返す。計測値やスコアの平均を出すときに使う。

## Signature

```go
func Mean[T constraints.Float | constraints.Integer](collection []T) T
```

## Usage

```go
import "github.com/samber/lo"

lo.Mean([]float64{1, 2, 3, 4, 5}) // => 3
lo.Mean([]float64{})              // => 0
lo.Mean([]int{1, 2})              // => 1（整数除算）
```

## Contract

- `Sum(xs) / T(len(xs))` を返す。入力を変更しない
- 空スライスと `nil` は **`0`** を返す。panic しない
- 返り値の型は要素の型 `T`。整数型なら整数除算でゼロ方向に切り捨てる（`[]int{1, 2}` → `1`、`[]int{-7, -8}` → `-7`）
- 整数型は合計の段階でオーバーフローしても検出されない（`[]int8{100, 100}` → `-28`）
- 要素に NaN があれば NaN。`+Inf` と `-Inf` を両方含むと NaN、`+Inf` と有限値なら `+Inf`
- 浮動小数点の誤差はそのまま（`[]float64{0.1, 0.2, 0.3}` → `0.20000000000000004`）

## Alternatives

- 構造体から値を取り出して平均するなら `lo.MeanBy(xs, func(x T) float64 { ... })`。整数の要素でも `float64` を返せば整数除算を避けられる
- 合計だけなら `lo.Sum` / `lo.SumBy`（カード number-sum-by）
- 依存を増やせない場合はループで合計して `float64(len(xs))` で割る。空の判定は自前で行う

## Pitfalls

- 空の扱いが言語で違う。TypeScript（es-toolkit の `mean`）は `NaN`、Python（`statistics.fmean`）は例外、lo は `0`。「平均 0」と「データ無し」を区別したいなら `len(xs) == 0` を先に判定する
- 整数スライスを渡すと整数の平均になる。`1.5` が欲しければ `[]float64` に変換するか `MeanBy` で `float64` を返す
- 合計してから割るので、大きな整数の列では割る前に合計がオーバーフローする

## Test

`examples/number-mean_test.go`
