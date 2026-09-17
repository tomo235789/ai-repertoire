---
id: number-clamp
lang: go
title: 数値を上限・下限の範囲に収める
tags: [範囲制限, 上限下限, 飽和, clamp, saturate, bound, min-max]
lib: stdlib
fn: min / max
since: "1.21"
verified: 2026-09-17
status: public
---

数値が範囲を超えていたら境界値に置き換える。ページ番号や音量、進捗率など有効範囲が決まっている値の補正に使う。Go に clamp は無く、Go 1.21 の組み込み `min` / `max` を重ねて書く。

## Signature

```go
min(max(x, lo), hi)
```

## Usage

```go
import "cmp"

func clamp[T cmp.Ordered](x, lo, hi T) T { return min(max(x, lo), hi) }

clamp(120, 0, 100)   // => 100
clamp(-5, 0, 100)    // => 0
clamp(42, 0, 100)    // => 42
clamp(2.5, 0.0, 1.0) // => 1
```

## Contract

- 境界値は含む（`clamp(0, 0, 100)` は `0`、`clamp(100, 0, 100)` は `100`）
- `cmp.Ordered` を満たす型（整数・浮動小数点・文字列）で使える。3 つの引数と返り値は同じ型。定数リテラルだけなら型推論で揃う（`clamp(2.5, 0, 1)` は全部 `float64`）
- `lo > hi` の場合は常に `hi` が返る（`min` が最後に適用されるため）
- 浮動小数点で `x`・`lo`・`hi` のどれか 1 つでも NaN なら NaN を返す（`min` / `max` は NaN を伝播する）
- 引数を変更しない純粋関数。panic しない

## Alternatives

- samber/lo の `lo.Clamp(value, min, max)` は `value < min` なら `min`、`value > max` なら `max` を返す実装。`lo > hi` のとき `x < lo` なら `lo` が返り、境界が NaN のときはその境界だけが効かず `x` がそのまま返る（`lo.Clamp(5.0, math.NaN(), 100)` は `5`）
- 上限だけなら `min(x, hi)`、下限だけなら `max(x, lo)`
- 範囲内かの判定だけなら `lo <= x && x <= hi`

## Pitfalls

- Go 1.21 未満には組み込み `min` / `max` が無い。`math.Min` / `math.Max` は `float64` 専用
- NaN の扱いが言語で違う。TypeScript（es-toolkit の `clamp`）はどれか 1 つでも NaN なら NaN で Go と同じ。Python の `min(max(x, lo), hi)` は `x` が NaN のときだけ NaN で、`lo.Clamp` も境界の NaN を無視する
- `lo > hi` の検証はしないので、引数の順序を取り違えると常に `hi` が返り気付きにくい
- `int` と `float64` を混ぜるとコンパイルエラー。片方を明示的に変換する

## Test

`examples/number-clamp_test.go`
