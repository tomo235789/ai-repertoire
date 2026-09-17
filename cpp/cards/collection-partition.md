---
id: collection-partition
lang: cpp
title: 条件で配列を 2 つに振り分ける
tags: [振り分け, 分割, 二分, partition, split, separate, stable-partition]
lib: stdlib
fn: std::ranges::stable_partition
since: "C++20"
verified: 2026-09-17
preserves_order: true
status: public
---

述語が真の要素を前、偽の要素を後ろに **その場で** 寄せ、境界を返す。有効・無効の振り分けや成功・失敗の仕分けに使う。

## Signature

```cpp
constexpr std::ranges::borrowed_subrange_t<R> std::ranges::stable_partition(R&& r, Pred pred, Proj proj = {})
```

## Usage

```cpp
#include <algorithm>
#include <ranges>
#include <vector>

std::vector<int> v{1, 2, 3, 4, 5};
auto odd = std::ranges::stable_partition(v, [](int n) { return n % 2 == 0; });
auto even = std::ranges::subrange(v.begin(), odd.begin());
// v    => [2, 4, 1, 3, 5]  真の要素が前、偽の要素が後ろ
// even => [2, 4]、odd => [1, 3, 5]
```

## Contract

- 順序を保持する。真側・偽側とも元の相対順のまま（`ranges::partition` は保たない）
- **in place**。範囲そのものを並べ替え、コピーは作らない
- 返り値は **偽側** の `subrange`（`borrowed_subrange_t<R>`。右辺値の非 borrowed 範囲を渡すと `ranges::dangling`）。`begin()` が境界、`end()` が範囲の末尾。真側は `subrange(v.begin(), ret.begin())` で切り出す
- 即時評価。述語は各要素につきちょうど 1 回呼ばれる
- プロジェクションを取る。`stable_partition(v, std::identity{}, &T::active)` のようにメンバで振り分けられる
- すべて真なら返り値は空、すべて偽なら返り値は範囲全体。空の範囲なら空
- bidirectional_range が必要（`vector`、`deque`、`list`）。返り値の `size()` は元が random_access のときだけ使え、`list` では `ranges::distance` で数える
- 述語が投げた例外はそのまま伝播する

## Alternatives

- 元の範囲を壊さず 2 つのコンテナに分けるなら `ranges::partition_copy(v, std::back_inserter(t), std::back_inserter(f), pred)`（真側が先の引数）
- 順序を保たなくてよいなら `ranges::partition`（一時バッファ不要で速いが不安定）
- 片側だけ遅延で欲しいなら `views::filter(pred)` と `views::filter(std::not_fn(pred))`
- 分割済みの範囲の境界だけ取るなら `ranges::partition_point`

## Pitfalls

- es-toolkit の `partition` は `[truthy, falsy]` の新しい配列 2 つを返すが、C++ は in place で返り値は偽側だけ。真側は境界から自分で切り出す
- more-itertools の `partition` は `(偽, 真)` の順のジェネレータ。C++ の「返り値は偽側」と混同しない
- 返り値の `subrange` は元のコンテナのイテレータ。コンテナを変更（`push_back` など）すると無効になる
- 2 つの `vector` として欲しいなら `partition_copy`。要素のコピーが不要なら in place のほうが速い

## Test

`examples/collection-partition_test.cpp`
