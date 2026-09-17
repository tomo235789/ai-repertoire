---
id: collection-chunk
lang: cpp
title: 配列を固定長の小配列に分割する
tags: [分割, チャンク, バッチ, chunk, split, batch, views-chunk]
lib: stdlib
fn: std::views::chunk
since: "C++23"
verified: 2026-09-17
preserves_order: true
status: public
---

範囲を `n` 個ずつの部分範囲に切り分ける遅延ビュー。API のバッチ送信やページ分割で使う。

## Signature

```cpp
constexpr auto std::views::chunk(R&& r, std::ranges::range_difference_t<R> n)  // r | std::views::chunk(n)
```

## Usage

```cpp
#include <ranges>
#include <vector>

std::vector<int> v{1, 2, 3, 4, 5};
for (auto chunk : v | std::views::chunk(2)) { /* chunk は元の要素を指すビュー */ }
// => [1, 2] [3, 4] [5]
auto vv = v | std::views::chunk(2) | std::ranges::to<std::vector<std::vector<int>>>();
// => {{1, 2}, {3, 4}, {5}}
```

## Contract

- 順序を保持する。各チャンクの中も元の並び順のまま
- 遅延評価。左辺値の範囲は `ref_view` で借用し（元の範囲をビューより長く生存させる）、右辺値のコンテナは `owning_view` で所有する。走査時に基底の要素を読むので、借用したビューの作成後に元の範囲を書き換えると結果に反映される
- 入力を変更しない。各チャンクは元の要素を指すビュー（random_access なら `subrange`、forward なら `take_view`。コピーではない）で、チャンク経由で書き込むと元の要素が変わる。`ranges::to<vector<vector<T>>>()` で実体化すると各チャンクが要素をコピーした `vector` になる
- 割り切れない場合、最後のチャンクは `n` 未満になる。切り捨てない
- `n` が範囲の長さ以上なら全体が 1 つのチャンクになる。空の範囲を渡すと空（`size() == 0`）
- 元が random_access かつ sized なら結果も random_access / sized で、`size()` はチャンク数、添字でチャンクを取れる。forward 以上の範囲なら何度でも走査できる
- input range（`views::istream` など）にも使えるが、その場合はチャンクを先頭から順に 1 回しか走査できない
- `n <= 0` は事前条件違反（未定義動作）。例外は投げない
- 左辺値を借用したビューは要素を持たないので、元のコンテナの寿命とイテレータ無効化の規則にそのまま従う（`vector` の再確保後にビューを使わない）。右辺値を渡したビューは要素を保持する基底範囲を所有するので、ビューが生きている間は要素も生きる

## Alternatives

- C++20 の場合は添字ループ `for (size_t i = 0; i < v.size(); i += n) auto c = std::span(v).subspan(i, std::min(n, v.size() - i));`（連続メモリのみ）
- 重なる窓が欲しいなら `views::slide(n)`（collection-sliding-window）
- 隣接する等しい要素ごとに切るなら `views::chunk_by`（collection-group-by）
- 各チャンクの先頭だけ欲しいなら `views::stride(n)`
- 短い末尾チャンクを捨てたいなら `v | views::chunk(n) | views::take(v.size() / n)`

## Pitfalls

- 各チャンクはビューであって `vector` ではない。関数に渡したり保存したりするなら `ranges::to` で実体化する
- es-toolkit の `chunk` や Python の `itertools.batched` は `n < 1` で例外を投げるが、C++ は未定義動作。呼び出し側で検証する
- 最後が短くなる意味論は Python の `batched` と同じ
- `std::string` を渡すと `char`（バイト）単位に切れ、UTF-8 の多バイト文字を分断する

## Test

`examples/collection-chunk_test.cpp`
