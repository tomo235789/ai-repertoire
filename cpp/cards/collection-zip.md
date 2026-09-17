---
id: collection-zip
lang: cpp
title: 複数の配列を要素ごとに組にする
tags: [組にする, 対応付け, 並行走査, zip, pair, tuple, enumerate]
lib: stdlib
fn: std::views::zip
since: "C++23"
verified: 2026-09-17
preserves_order: true
status: public
---

複数の範囲を同じ位置ごとに参照の `tuple` にまとめる遅延ビュー。ID と名前のように別々の配列で持つデータの並行走査に使う。

## Signature

```cpp
constexpr auto std::views::zip(Rs&&... rs)
```

## Usage

```cpp
#include <ranges>
#include <string>
#include <vector>

std::vector<int> ids{1, 2, 3};
std::vector<std::string> names{"a", "b"};
for (auto [id, name] : std::views::zip(ids, names)) { /* ... */ }
// => (1, "a") (2, "b")  最短に合わせて打ち切る
```

## Contract

- 順序を保持する。i 番目の要素は各範囲の i 番目の要素からなる `std::tuple`
- 長さは **最も短い** 入力に合わせて打ち切る。すべて sized なら結果も sized で `size()` は最小値
- 遅延評価。左辺値の範囲は `ref_view` で借用し（元の範囲をビューより長く生存させる）、右辺値のコンテナは `owning_view` で所有する。走査時に基底の要素を読む
- 入力を変更しない。要素は **参照の tuple**（`tuple<T&, U&>`）で、`auto [a, b]`（`&&` 無し）で受けても書き込みは元の範囲に反映される。const な範囲は `const T&`
- すべて random_access なら結果も random_access で添字アクセスできる
- 引数は可変長（`zip_view` 自体は 1 つ以上のビューを要求する）。いずれかが空なら空。引数なしの `views::zip()` は `views::empty<tuple<>>` と同じ空ビューになると規定されている
- zip した範囲は `ranges::sort` できる（C++23 の proxy reference 対応）。`ranges::sort(views::zip(keys, vals))` でキーと値が同時に並べ替わる
- 自身は例外を投げないが、入力範囲のビュー構築（ムーブなど）や走査が投げた例外はそのまま伝播する

## Alternatives

- 位置と組にするなら `views::enumerate(v)`（`tuple<index, T&>`）
- 組にしてすぐ加工するなら `views::zip_transform(f, a, b)`（`f(x, y)` の結果のビュー）
- `vector<pair<T, U>>` に実体化するなら `views::zip(a, b) | ranges::to<vector<pair<T, U>>>()`（`tuple` → `pair` の変換は C++23 の pair-like 構築で GCC 14 以降）。それ以前は `views::zip_transform([](auto& x, auto& y) { return std::pair{x, y}; }, a, b)`
- C++20 の場合は添字ループ `for (size_t i = 0; i < std::min(a.size(), b.size()); ++i)`
- 最長に合わせて埋める `zip_longest` 相当は無い。長さを先に検査して揃える

## Pitfalls

- es-toolkit の `zip` は最長に合わせて `undefined` で埋めるが、C++ は Python と同じく最短で打ち切る。不一致は黙って切り捨てられるので、必要なら `ranges::size` で検査する
- `auto [a, b]` で受けた `a`、`b` は元の要素への参照。書き換えると元の範囲が変わる。コピーが欲しいなら明示的にコピーする
- 要素は `std::pair` ではなく `std::tuple`。`.first` / `.second` は無く、構造化束縛か `std::get<0>` で取り出す
- 右辺値の `vector` を渡すとビューが所有する（`owning_view`）が、左辺値はビューより長生きさせる

## Test

`examples/collection-zip_test.cpp`
