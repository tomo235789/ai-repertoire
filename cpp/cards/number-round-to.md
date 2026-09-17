---
id: number-round-to
lang: cpp
title: 数値を指定した小数桁数で四捨五入する
tags: [四捨五入, 小数桁, 丸め, round, precision, decimal-places, half-away-from-zero]
lib: stdlib
fn: std::round
since: "C++11"
verified: 2026-09-17
status: public
---

小数第 n 位（負なら 10 の n 乗の位）で四捨五入した数値を返す。`std::round` は整数への丸めしかしないので、桁を掛けてから丸めて戻す。`.5` は **0 から遠い方** に丸める（Go と同じ）。

## Signature

```cpp
double std::round(double x);  // 桁指定は std::round(x * p) / p（p = std::pow(10.0, digits)）
```

## Usage

```cpp
#include <cmath>

double round_to(double x, int digits) {
  const double p = std::pow(10.0, digits);
  return std::round(x * p) / p;
}
round_to(1.2345, 2);  // => 1.23
round_to(1250, -2);   // => 1300
round_to(2.5, 0);     // => 3（.5 は 0 から遠い方へ）
round_to(-2.5, 0);    // => -3
```

## Contract

- `std::round` は `.5` を 0 から遠い方へ丸める（`round(0.5)` は `1`、`round(2.5)` は `3`、`round(-2.5)` は `-3`）。偶数丸めではなく、現在の浮動小数点丸めモードにも影響されない
- `digits` が負なら 10 の位・100 の位で丸める（`round_to(1234.5678, -2)` は `1200`）
- 浮動小数点の補正はしない。`x * p` の積の丸めがそのまま結果に出る。`1.005 * 100` は `100.49999999999999` なので `round_to(1.005, 2)` は `1`。一方 `2.675 * 100` は積の時点で `267.5` に丸まるので `round_to(2.675, 2)` は `2.68`（Python の `round(2.675, 2)` は `2.67`）
- `x` が `NaN` なら `NaN`、`±inf` なら `±inf`。`p` が `inf` や `0` になるほど極端な `digits`（`±400` など）では `NaN`
- `round(-0.4)` は `-0.0`（符号付き零）。`== 0.0` は真だが `std::signbit` は真
- 例外を投げない。引数を変更しない純粋関数

## Alternatives

- 表示のためだけなら `std::format("{:.2f}", x)`。こちらは 2 進数の値を正確に丸めるので `2.675` は `"2.67"`、`"{:.0f}"` なら `2.5` は `"2"`（偶数丸め）になり `std::round` と一致しない
- 偶数丸め（現在の丸めモードに従う）なら `std::nearbyint` / `std::rint`（`nearbyint(2.5)` は `2`、`nearbyint(3.5)` は `4`）
- 整数型で受けたいなら `std::lround` / `std::llround`（丸め方は `round` と同じ）
- 切り上げ・切り捨てなら `std::ceil` / `std::floor`、0 方向なら `std::trunc`
- 金額など誤差を許容できない値は整数（最小単位）で扱う

## Pitfalls

- `.5` の扱いが言語で違う。TypeScript（es-toolkit の `round`）は正の無限大方向（`round(-2.5)` は `-2`）、Python は偶数丸め（`round(2.5)` は `2`）、C++ の `std::round` と Go の `math.Round` は 0 から遠い方（`-3` と `3`）。移植すると `.5` ちょうどの値で結果が変わる
- Python の `round(2.675, 2)` は 2 進数の値（`2.67499…`）を正確に丸めて `2.67` だが、C++ のイディオムは `x * p` の積が `267.5` に丸まってから `std::round` するので `2.68`。逆に `1.005` は両者とも `1`。10 進の見た目では予測できない
- 負の桁で `std::pow(10.0, digits)` が 2 進数で正確に表せない場合（`1e-5` など）、`/ p` が不正確になる（確認した環境では `round_to(123456, -5)` が `99999.999999999985`。`std::pow` の丸めは実装依存）。負の桁は `std::round(x / 1e5) * 1e5` のように正の 10 のべき乗で割って掛ける
- `std::round` は `double` を返す。`static_cast<int>` は 0 方向への切り捨てなので、四捨五入した整数が欲しければ `std::lround` を使う

## Test

`examples/number-round-to_test.cpp`
