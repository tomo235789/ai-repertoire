---
id: number-clamp
lang: cpp
title: 数値を上限・下限の範囲に収める
tags: [範囲制限, 上限下限, 飽和, clamp, saturate, bound, min-max]
lib: stdlib
fn: std::clamp
since: "C++17"
verified: 2026-09-17
status: public
---

数値が範囲を超えていたら境界値に置き換える。ページ番号や音量、進捗率など有効範囲が決まっている値の補正に使う。

## Signature

```cpp
template<class T> constexpr const T& std::clamp(const T& v, const T& lo, const T& hi);  // 比較関数を取る 4 引数版もある
```

## Usage

```cpp
#include <algorithm>

std::clamp(120, 0, 100);       // => 100
std::clamp(-5, 0, 100);        // => 0
std::clamp(42, 0, 100);        // => 42
std::clamp(5.0, 0.0, 1.0);     // => 1.0（3 つとも同じ型で渡す）
int page = std::clamp(page_arg, 1, last_page);  // 値で受ける
```

## Contract

- `v < lo` なら `lo`、`hi < v` なら `hi`、それ以外は `v` を返す。境界値は含む（`clamp(0, 0, 100)` は `0`、`clamp(100, 0, 100)` は `100`）
- 返り値は **引数への参照**（`const T&`）。範囲内なら `v` そのものの参照が返る。値で受ければ安全だが、`const int& r = std::clamp(x, 0, 100)` のように参照で受けると `0` や `100` の一時オブジェクトを指して寿命切れになる（GCC 13 以降は `-Wall -Wextra` で `-Wdangling-reference` の警告が出る）
- `hi < lo` は事前条件違反で **未定義動作**。例外は投げない。libstdc++ のアサート（GCC 13 は `-D_GLIBCXX_ASSERTIONS` 指定時、GCC 16 は最適化なしの既定）が有効なら abort し、無効なら黙って値が返る
- 3 引数は同じ型 `T` に推論される。`std::clamp(5, 0.0, 10.0)` は推論の衝突でコンパイルエラー。`std::clamp<double>(5, 0.0, 10.0)` と明示するか全部同じ型で渡す
- `v` が `NaN` なら比較がすべて偽になり `v`（`NaN`）が返る。`lo` や `hi` が `NaN` のときはその境界だけが効かない（`clamp(5.0, NaN, 1.0)` は `1.0`、`clamp(-5.0, NaN, 1.0)` は `-5.0`、`clamp(-5.0, 0.0, NaN)` は `0.0`）
- 第 4 引数に比較関数を渡せる。`std::greater{}` なら `lo >= hi` の順で渡す
- 引数を変更しない。`constexpr` で定数式に使える

## Alternatives

- 構造体のメンバで比較したいなら `std::ranges::clamp(v, lo, hi, {}, &Item::score)`（C++20。射影を渡せる。返り値はやはり参照）
- 上限だけなら `std::min(v, hi)`、下限だけなら `std::max(v, lo)`
- 範囲内かの判定だけなら `lo <= v && v <= hi`

## Pitfalls

- TypeScript（es-toolkit）や Python の `min(max(v, lo), hi)` は `lo > hi` でも `hi` を返すが、C++ は未定義動作。引数の順序を取り違えても検出されないので、呼び出し側で `lo <= hi` を保証する
- es-toolkit の 2 引数形式 `clamp(value, max)` に相当するものは無い。`std::min` を使う
- es-toolkit はどれか 1 つでも `NaN` なら `NaN` を返すが、C++ は `v` が `NaN` のときだけ。境界に `NaN` が混ざっても気付けない（Python と同じ）
- 整数リテラルと `double` 変数を混ぜると（`std::clamp(x, 0, 1.5)`）コンパイルエラーになる。`0.0` と書く

## Test

`examples/number-clamp_test.cpp`
