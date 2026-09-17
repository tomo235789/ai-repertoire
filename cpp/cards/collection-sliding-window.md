---
id: collection-sliding-window
lang: cpp
title: 配列をスライディングウィンドウで走査する
tags: [スライディングウィンドウ, 移動窓, 移動平均, sliding-window, slide, rolling, adjacent]
lib: stdlib
fn: std::views::slide
since: "C++23"
verified: 2026-09-17
preserves_order: true
status: public
---

幅 `n` の窓を 1 つずつずらしながら部分範囲として取り出す遅延ビュー。移動平均や隣接要素の比較に使う。

## Signature

```cpp
constexpr auto std::views::slide(R&& r, std::ranges::range_difference_t<R> n)  // r | std::views::slide(n)
```

## Usage

```cpp
#include <ranges>
#include <vector>

std::vector<int> v{1, 2, 3, 4, 5};
for (auto w : v | std::views::slide(3)) { /* w は元の要素を指すビュー */ }
// => [1, 2, 3] [2, 3, 4] [3, 4, 5]
auto vv = v | std::views::slide(3) | std::ranges::to<std::vector<std::vector<int>>>();
// => {{1, 2, 3}, {2, 3, 4}, {3, 4, 5}}
```

## Contract

- 順序を保持する。窓は先頭から 1 つずつずれた開始位置で並び、窓の中も元の並び順
- 幅 `n` に満たない窓は作らない。範囲の長さが `n` 未満なら空、`n` と等しければ窓 1 つ。窓の数は `max(0, size - n + 1)`（符号なしで `size - n + 1` と書くと `size < n - 1` でアンダーフローする）
- 遅延評価。左辺値の範囲は `ref_view` で借用し（元の範囲をビューより長く生存させる）、右辺値のコンテナは `owning_view` で所有する。各窓は基底の要素を指すビュー（`vector` では `std::span`、forward range では `subrange`）。窓経由で書き込むと元の要素が変わる
- 入力を変更しない
- 元が random_access かつ sized なら結果も random_access / sized で、`size()` と添字が使える。forward 以上の範囲でも走査できる
- ずらし幅（step）の引数は無い。`slide(n) | views::stride(step)` で組み合わせる
- `n <= 0` は事前条件違反（未定義動作）。例外は投げない

## Alternatives

- 幅がコンパイル時定数なら `views::adjacent<N>`（各窓が `tuple<T&, ...>` で構造化束縛できる）。`N == 2` は `views::pairwise`
- 重ならない分割は `views::chunk`（collection-chunk。末尾の短い塊も出る）
- 移動平均は `v | views::slide(n) | views::transform([n](auto w) { return std::ranges::fold_left(w, 0.0, std::plus{}) / n; })`
- C++20 の場合は添字ループ `for (size_t i = 0; i + n <= v.size(); ++i) auto w = std::span(v).subspan(i, n);`

## Pitfalls

- es-toolkit の `windowed` と同じで末尾の短い窓は捨てる。more-itertools の `windowed` は `fillvalue` で埋める。短い窓も含めたい（`partialWindows: true` 相当の）オプションは無い
- `n` が範囲長より大きくても例外にはならず、単に空になる
- 各窓はビューで `vector` ではない。実体化は `ranges::to`
- 窓を `tuple` で受けて `auto [a, b, c]` と書きたいなら `adjacent<3>`。`slide` は幅が実行時の値のとき用

## Test

`examples/collection-sliding-window_test.cpp`
