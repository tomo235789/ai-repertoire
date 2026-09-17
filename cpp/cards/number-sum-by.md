---
id: number-sum-by
lang: cpp
title: 配列の各要素から取り出した数値を合計する
tags: [合計, 集計, 畳み込み, sum, sum-by, fold, reduce, aggregate]
lib: stdlib
fn: std::ranges::fold_left
since: "C++23"
verified: 2026-09-17
status: public
---

各要素から数値を取り出して合計する。オブジェクト配列の数量や金額の集計に使う。`views::transform` で取り出してから `fold_left` で畳み込む。

## Signature

```cpp
template<std::ranges::input_range R, class T, class F> constexpr auto std::ranges::fold_left(R&& r, T init, F f);  // 返り値の型は f(init, 要素) の型
```

## Usage

```cpp
#include <algorithm>
#include <functional>
#include <ranges>
#include <vector>

struct Item { const char* name; int qty; };
std::vector<Item> items{{"a", 2}, {"b", 3}};
std::ranges::fold_left(items | std::views::transform(&Item::qty), 0, std::plus{});
// => 5
```

## Contract

- 入力を変更しない。`init` から始めて先頭から順に `acc = f(acc, 要素)` を適用する。取り出し関数（`transform` の関数）は各要素につきちょうど 1 回、先頭から順に呼ばれる
- 空なら `init` をそのまま返す（`0`）
- 返り値の型は `f(init, 要素)` の型で決まる。`0`（`int`）を初期値に `double` を足すと `double` になり、切り捨てない（`std::accumulate` とは違う）。`unsigned char` 同士でも整数昇格で `int`
- `int` の合計が `INT_MAX` を超えると符号付き整数オーバーフローで **未定義動作**。大きくなり得るなら `0LL` を初期値にして `long long` で合計する
- `double` の合計は左から順に素朴に加算し補正しない（`0.1 + 0.2 + 0.3` は `0.60000000000000009`）。要素に `NaN` があれば `NaN`
- 例外は投げない（`f` や取り出し関数が投げた例外はそのまま伝播する）
- 入力は `input_range` であればよい（`std::list` やビューも可）。`std::plus{}` は `std::plus<void>` に推論され、型の違う引数も足せる

## Alternatives

- C++20 以前は `std::accumulate(begin, end, 0.0, f)`。初期値の型が結果の型になるので、`0` を渡して `double` を足すと **整数に切り捨てられる**（`{1.5, 2.25}` の合計が `3`）
- 初期値を与えず先頭要素から畳むなら `std::ranges::fold_left_first(r, std::plus{})`。空なら `std::nullopt`（`std::optional` で返る）
- 加算の順序が不定でよく並列化したいなら `std::reduce`
- 平均は number-mean

## Pitfalls

- TypeScript（es-toolkit の `sumBy`）は取り出した値が `undefined` なら `NaN`、Python は `TypeError` だが、C++ は数値でない型を足そうとした時点でコンパイルエラー。実行時の欠損は起こらない
- `std::accumulate` に `0` を渡す切り捨てが定番の事故。`fold_left` は結果型を演算から決めるのでこの罠が無い
- `std::plus{}` には `<functional>` が要る。ラムダ `[](int acc, const Item& it) { return acc + it.qty; }` を渡せば `transform` 無しでも書ける
- 金額など誤差を許せない値は整数（最小単位）で合計する

## Test

`examples/number-sum-by_test.cpp`
