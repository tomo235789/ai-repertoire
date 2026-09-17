---
id: collection-group-by
lang: cpp
title: キー関数で配列をグループ化する
tags: [グループ化, 分類, 隣接, group-by, chunk-by, categorize, adjacent]
lib: stdlib
fn: std::views::chunk_by
since: "C++23"
verified: 2026-09-17
preserves_order: true
status: public
---

隣接する要素を述語で比べ、同じグループに入る間だけまとめた部分範囲の遅延ビュー。キーでまとめるなら先にキー順に整列してから使う。

## Signature

```cpp
constexpr auto std::views::chunk_by(R&& r, Pred pred)  // r | std::views::chunk_by(pred)
```

## Usage

```cpp
#include <algorithm>
#include <ranges>
#include <string>
#include <vector>

std::vector<std::string> words{"bob", "apple", "cat", "dove"};
std::ranges::stable_sort(words, {}, &std::string::size);  // 隣接させるために先にキーで整列
auto groups = words | std::views::chunk_by([](auto& a, auto& b) { return a.size() == b.size(); });
// => ["bob", "cat"] ["dove"] ["apple"]
```

## Contract

- 順序を保持する。各グループの中は元の並び順のまま、グループは出現順に並ぶ
- **隣接する** 要素しかまとめない。同じキーが離れて現れると別グループになる（Python の `itertools.groupby` と同じ）。全体でまとめるなら先に `ranges::stable_sort` でキー順に整列する
- 遅延評価。ビューは元の範囲への参照だけを持ち、各グループは元の要素を指す `subrange`。グループ経由で書き込むと元の要素が変わる
- 述語は隣接する 2 要素を受け取り、真なら同じグループに入れる。キーでまとめる形は `chunk_by([](a, b){ return key(a) == key(b); })`。述語は走査のたびに隣接ペアごとに呼ばれる（`begin()` が計算した最初のグループの境界だけはキャッシュされる）
- 入力を変更しない
- 空の範囲を渡すと空のビュー（`begin() == end()`）。結果は sized ではなく、グループ数は `ranges::distance` で数える
- forward 以上の範囲が必要で、結果は bidirectional まで。添字アクセスはできない
- 自身は例外を投げない。述語が投げた例外はそのまま伝播する

## Alternatives

- 隣接に限らずキーごとに集約するなら `std::map<K, std::vector<T>> m; for (auto& x : xs) m[key(x)].push_back(x);`（キー順に並ぶ。ハッシュでよければ `unordered_map`）。C++20 でもこの形
- 件数だけなら `std::map<K, int>` に `++m[key(x)]`
- キーを取り出さず隣接する等しい要素をまとめるなら `chunk_by(std::ranges::equal_to{})`
- `chunk_by(std::ranges::less{})` のように非対称な述語を渡すと「昇順に続く区間」を切り出せる
- 固定長で切るなら `views::chunk`（collection-chunk）

## Pitfalls

- es-toolkit の `groupBy` や more-itertools の `map_reduce` は配列全体をまとめるが、`chunk_by` は隣接する要素だけ。ソート無しで使うと同じキーのグループが何度も現れる
- 述語は 2 引数の「同じグループか」判定であって、キーを返す 1 引数関数ではない。`chunk_by(&T::key)` は渡せない
- 各グループはキーを持たない。キーが必要なら `key(*group.begin())` で取り出す
- 各グループは `subrange` で `vector` ではない。実体化は `ranges::to<vector<vector<T>>>()`

## Test

`examples/collection-group-by_test.cpp`
