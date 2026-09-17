---
id: number-mean
lang: cpp
title: 数値配列の平均を求める
tags: [平均, 算術平均, 集計, mean, average, fold, statistics]
lib: stdlib
fn: std::ranges::fold_left
since: "C++23"
verified: 2026-09-17
status: public
---

数値列の算術平均を `double` で返す。計測値やスコアの平均を出すときに使う。標準に `mean` は無いので、`fold_left` で合計して要素数で割る。

## Signature

```cpp
template<std::ranges::input_range R, class T, class F> constexpr auto std::ranges::fold_left(R&& r, T init, F f);  // fold_left(v, 0.0, std::plus{}) / v.size()
```

## Usage

```cpp
#include <algorithm>
#include <functional>
#include <vector>

std::vector<int> v{1, 2, 3, 4};
double mean = std::ranges::fold_left(v, 0.0, std::plus{}) / v.size();
// => 2.5（初期値 0.0 で double に昇格。[1, 2] も 1.5 になる）
```

## Contract

- 初期値を `0.0` にすると要素が `int` でも `double` で合計され、`size()` で割った結果も `double`（`{1, 2}` は `1.5`）。初期値 `0`（`int`）で `int` を足して `int` で割ると整数除算になる（`{1, 2}` は `1`）
- **空なら 0 除算**。`double` の `0.0 / 0` は IEEE 754 環境（`std::numeric_limits<double>::is_iec559`）で `NaN` になり例外は投げない。整数同士の 0 除算は **未定義動作**（実際にはクラッシュする）。空を区別したいなら先に `empty()` を判定する
- 入力を変更しない。`size()` を持つ範囲なら 1 回だけ走査する
- 合計は左から順の素朴な加算で補正しない。`{0.1, 0.2, 0.3}` の平均は `0.20000000000000004`（TypeScript の `mean` と同じ、Python の `fmean` は `0.19999999999999998`）
- 要素に `NaN` があれば `NaN`。`inf` と `-inf` を両方含んでも `NaN`
- `size()` が無いビュー（`views::filter` など）は forward 以上の範囲なら `std::ranges::distance(r)` で数えられるが、走査が 2 回になる。`views::istream | views::filter` のような単一パスの input range は合計を取った時点で消費され、その後の `distance` は `0` を返して平均が壊れる。合計と個数を同じ走査で集計する: `auto [sum, n] = fold_left(r, std::pair{0.0, 0}, [](auto acc, auto x) { return std::pair{acc.first + x, acc.second + 1}; });`

## Alternatives

- 2 値の中点なら `std::midpoint(a, b)`（C++20）。整数同士はオーバーフローせず `a` 側に丸める（`midpoint(1, 2)` は `1`）、`double` なら `1.5`
- 構造体のメンバの平均は `v | std::views::transform(&Item::score)` を渡す（number-sum-by）
- C++20 以前は `std::accumulate(v.begin(), v.end(), 0.0) / v.size()`
- 中央値は `std::ranges::nth_element` で中央の要素を選ぶ

## Pitfalls

- 空配列の扱いが言語で違う。TypeScript（es-toolkit の `mean`）は `NaN`、Python の `fmean` は `StatisticsError`、C++ は `double` なら `NaN`、整数なら未定義動作
- `int` の合計を `size()`（`size_t`）で割ると **合計が符号なしに変換される**。`-4 / v.size()` は巨大な正の値になる。初期値 `0.0` で `double` にするか、`static_cast<double>` してから割る
- `int` の合計は `INT_MAX` を超えると未定義動作。`0.0` か `0LL` を初期値にする
- `NaN` は `==` で比較できない。`std::isnan` で判定する

## Test

`examples/number-mean_test.cpp`
