---
id: number-mean
lang: python
title: 数値配列の平均を求める
tags: [平均, 算術平均, 集計, mean, average, avg, statistics]
lib: stdlib
fn: statistics.fmean
since: "3.8"
verified: 2026-09-17
status: public
---

数値列の算術平均を `float` で返す。計測値やスコアの平均を出すときに使う。`statistics.mean` より速く、返り値の型が常に `float` で予測しやすい。

## Signature

```python
statistics.fmean(data, weights=None)
```

## Usage

```python
from statistics import fmean

fmean([1, 2, 3, 4, 5])               # => 3.0
fmean([1, 2])                        # => 1.5
fmean([1, 2, 3], weights=[3, 1, 1])  # => 1.6
```

## Contract

- 常に `float` を返す（`int`、`Decimal`、`Fraction` を渡しても）
- 空を渡すと `StatisticsError`（`ValueError` のサブクラス）を投げる。`NaN` は返さない
- 入力を変更しない。リスト以外のイテラブル（イテレータ、集合）も受け付け、1 回だけ走査する
- 合計を `math.fsum` で求めてから個数で割る。`fmean([0.1, 0.2, 0.3])` は `0.19999999999999998`
- 要素に `NaN` があれば `NaN`。`inf` を含めば `inf`。`inf` と `-inf` を両方含むと `ValueError`
- 数値でない要素（`str`、`None`）があると `TypeError`。`bool` は `1` / `0` として扱う
- `weights` を渡すと加重平均（3.11+）。長さが `data` と違うと `StatisticsError`

## Alternatives

- 入力の型を保ちたいなら `statistics.mean`。`int` の平均が割り切れれば `int`（`mean([1, 3])` は `2`）、`Fraction` なら `Fraction`。分数で厳密に計算するので `mean([0.1, 0.2, 0.3])` は `0.2`
- 外れ値に強い代表値なら `statistics.median`、分布の位置なら `statistics.quantiles`
- 依存を増やせず型も気にしないなら `sum(xs) / len(xs)`。空なら `ZeroDivisionError`

## Pitfalls

- TypeScript 版（es-toolkit の `mean`）は空配列で `NaN` を返すが、`fmean` は例外。空を `NaN` にしたければ `fmean(xs) if xs else math.nan`
- 合計の方法が違うので最下位ビットで結果が異なり得る。`[0.1, 0.2, 0.3]` の平均は es-toolkit で `0.20000000000000004`、`fmean` で `0.19999999999999998`
- ジェネレータを渡すと消費される。同じデータで分散なども求めるなら先に `list` にする
- `statistics.mean` は `fmean` より遅く、`int` を渡すと結果が `int` になることがある。数値計算の途中で使うなら `fmean` に統一する

## Test

`examples/number-mean_test.py`
