---
id: number-mean
lang: typescript
title: 数値配列の平均を求める
tags: [平均, 算術平均, 集計, mean, average, avg, statistics]
lib: es-toolkit
fn: mean
since: "1.0.0"
verified: 2026-09-17
status: public
---

数値配列の算術平均を返す。計測値やスコアの平均を出すときに使う。

## Signature

```ts
function mean(nums: readonly number[]): number
```

## Usage

```ts
import { mean } from 'es-toolkit';

mean([1, 2, 3, 4, 5]); // => 3
mean([]);              // => NaN
```

## Contract

- `sum(nums) / nums.length` を返す。入力配列を変更しない
- 空配列を渡すと `NaN` を返す（`0 / 0`）。例外は投げない
- 要素に `NaN` があれば `NaN`。`Infinity` と `-Infinity` を両方含んでも `NaN`
- 要素の型変換はしない。`undefined` を含む（欠損・疎な配列）と `NaN`
- 浮動小数点の誤差はそのまま（`mean([0.1, 0.2, 0.3])` は `0.20000000000000004`）

## Alternatives

- オブジェクト配列から値を取り出して平均するなら `meanBy(arr, fn)`
- 外れ値に強い代表値なら `median` / `medianBy`、分布の位置なら `percentile`
- 依存を増やせない場合のみ stdlib で `arr.reduce((a, b) => a + b, 0) / arr.length`
- lodash からの移行は `es-toolkit/compat` の `mean`

## Pitfalls

- 空配列は例外ではなく `NaN`。Python の `statistics.mean([])` は `StatisticsError` を投げる。空を区別したいなら呼び出し側で `length === 0` を先に判定する
- `NaN` は `===` で比較できない。`Number.isNaN` で判定する
- `mean([1, 2])` のような整数の平均も `1.5` になり整数に丸めない（Python 3 の `/` と同じ）

## Test

`examples/number-mean.test.ts`
