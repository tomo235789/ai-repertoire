---
id: collection-flatten
lang: cpp
title: ネストした配列を指定の深さまで平坦化する
tags: [平坦化, 展開, 連結, flatten, flat, join, concat]
lib: stdlib
fn: std::views::join
since: "C++20"
verified: 2026-09-17
preserves_order: true
status: public
---

範囲の範囲を 1 段開いて 1 本の範囲にする遅延ビュー。ページごとに取得した結果の連結などに使う。

## Signature

```cpp
constexpr auto std::views::join(R&& r)  // r | std::views::join
```

## Usage

```cpp
#include <ranges>
#include <vector>

std::vector<std::vector<int>> nested{{1, 2}, {}, {3}, {4, 5}};
auto flat = nested | std::views::join;
// => 1, 2, 3, 4, 5  1 段だけ開く
auto v = nested | std::views::join | std::ranges::to<std::vector>();  // ranges::to は C++23
// => std::vector<int>{1, 2, 3, 4, 5}
```

## Contract

- 順序を保持する。外側の並び順も内側の並び順も保つ
- 開くのは 1 段だけ。要素がさらに範囲でもそのまま返す。2 段開くなら `join` を 2 回つなぐ
- 遅延評価。左辺値の外側範囲は `ref_view` で借用し（元の範囲をビューより長く生存させる）、右辺値のコンテナは `owning_view` で所有する。走査時に基底の要素を読む
- 入力を変更しない。要素は元の要素への参照で、書き込むと元が変わる
- 内側の範囲が左辺値参照で得られる（コンテナのコンテナ）なら bidirectional まで。`transform` が値で返す内側の範囲を join すると input range になり、forward ではない（走査は 1 回にとどめ、必要なら `ranges::to` で確定させる）
- 内側の範囲は同じ型なら何でもよい（`vector<list<int>>` など）
- 外側が空、または空の内側だけなら空。結果は sized ではなく、要素数は `ranges::distance` で数える
- 例外は投げない

## Alternatives

- 区切りを挟むなら `views::join_with(sep)`（C++23）。`vector<string>` を `std::string_view(", ")` でつないで `ranges::to<string>()` など。`sep` は範囲か要素 1 つ
- 各要素を変換しながら 1 段開くなら `xs | views::transform(f) | views::join`
- `ranges::to` が無い C++20 では `for (auto& x : nested | views::join) out.push_back(x);`
- 深さを問わず全部開く機能は無い。段数分 `join` をつなぐ

## Pitfalls

- es-toolkit の `flatten(arr, depth)` は深さを取り非配列要素はそのまま残すが、C++ は 1 段固定で、要素型が範囲でなければコンパイルエラー（`vector<int>` は join できない）
- `vector<string>` を join すると `char` の範囲になる（Python と同じ）。文字列連結なら `ranges::to<string>()`、区切り付きなら `join_with`
- 文字列リテラルは渡さない。`| join_with(", ")` は libstdc++ ではリテラルが `const char*` に decay してコンパイルエラーになり、直接呼び出し `join_with(words, ", ")` は配列として受理されるが末尾の NUL まで区切りに含む（`"ab, \0cd"`）。`std::string_view(", ")` を渡す。1 文字なら `'-'` でよい
- 型の違う範囲を 1 本につなぐことはできない（C++26 の `views::concat`）。同じ要素型なら片方を `vector` にまとめてから join する

## Test

`examples/collection-flatten_test.cpp`
