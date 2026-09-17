---
id: number-sum-by
lang: go
title: 配列の各要素から取り出した数値を合計する
tags: [合計, 集計, 合算, sum, sum-by, total, aggregate]
lib: samber/lo
fn: lo.SumBy
since: "1.38"
verified: 2026-09-17
status: public
---

各要素から数値を取り出して合計する。構造体スライスの数量や金額の集計に使う。

## Signature

```go
func SumBy[T any, R constraints.Float | constraints.Integer | constraints.Complex](collection []T, iteratee func(item T) R) R
```

## Usage

```go
import "github.com/samber/lo"

type item struct{ Name string; Qty int }
items := []item{{"a", 2}, {"b", 3}}
lo.SumBy(items, func(i item) int { return i.Qty })
// => 5
```

## Contract

- 入力スライスを変更しない
- `iteratee` は各要素につきちょうど 1 回、先頭から順に呼ばれる
- 空スライスと `nil` は `0`（`R` のゼロ値）を返す
- 返り値の型は `iteratee` の返り値の型 `R`。整数型は加算が **オーバーフローしても検出されず** 型の幅で巻き戻る（`[]int8{100, 100}` → `-56`、`[]uint8{200, 100}` → `44`）
- 浮動小数点は誤差がそのまま（`0.1 + 0.2` は `0.30000000000000004`、`0.1` を 10 回足すと `0.9999999999999999`）。要素に NaN があれば NaN
- panic しない（`iteratee` が panic すればそのまま伝播する）

## Alternatives

- 要素がそのまま数値なら `lo.Sum(nums)`
- 平均は `lo.MeanBy`（カード number-mean）、最大・最小の要素は `lo.MaxBy` / `lo.MinBy`
- 依存を増やせない場合は `for _, x := range xs { total += f(x) }`

## Pitfalls

- TypeScript（es-toolkit の `sumBy`）は取り出した値が `undefined` なら `NaN`、Python の `sum` は `TypeError` になるが、Go は型で縛られるので実行時の型の事故は起きない。代わりにオーバーフローが無検出
- 小さい整数型（`int32` など）の列を合計するなら `iteratee` の中で `int64` に変換して返す。要素の型のまま合計すると巻き戻る
- 金額など誤差を許せない値は整数（最小単位）で合計する。`float64` を厳密に丸めて合計する関数（Python の `math.fsum` 相当）は標準に無い

## Test

`examples/number-sum-by_test.go`
