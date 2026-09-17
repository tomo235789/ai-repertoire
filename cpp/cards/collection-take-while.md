---
id: collection-take-while
lang: cpp
title: 条件を満たす間だけ先頭から要素を取り出す
tags: [先頭から取り出す, 前置部分列, 打ち切り, take-while, prefix, until, drop-while]
lib: stdlib
fn: std::views::take_while
since: "C++20"
verified: 2026-09-17
preserves_order: true
status: public
---

先頭から述語が真である間だけ要素を返し、最初に偽になった時点で打ち切る遅延ビュー。整列済みの列から閾値未満の部分を取るときなどに使う。

## Signature

```cpp
constexpr auto std::views::take_while(R&& r, Pred pred)  // r | std::views::take_while(pred)
```

## Usage

```cpp
#include <ranges>
#include <vector>

std::vector<int> v{1, 2, 3, 4, 1};
auto head = v | std::views::take_while([](int n) { return n < 3; });
// => 1, 2
auto out = head | std::ranges::to<std::vector>();  // ranges::to は C++23
// => std::vector<int>{1, 2}
```

## Contract

- 順序を保持する。結果は入力の先頭部分（前置部分列）
- 遅延評価。ビューは元の範囲への参照と述語のコピーを持つ。終端は走査中に述語で判定され、`size()` は無い（`ranges::distance` で数える）
- 述語は **走査のたびに** 評価される。1 回の `for` では先頭から順に最初に偽になった要素まで呼ばれ、それ以降には呼ばれない。2 回走査すれば 2 倍呼ばれる（libstdc++ の `ranges::to<vector>` は距離を数えてからコピーするので各要素で 2 回評価された）
- 入力を変更しない。要素は元の要素への参照で、書き込むと元が変わる
- すべて真なら全要素、先頭で偽なら空。空の範囲なら空
- 元が random_access なら結果も random_access（ただし sized ではない）
- 自身は例外を投げない。述語が投げた例外はそのまま伝播する

## Alternatives

- 先頭の条件部分を **捨てて** 残りが欲しいなら `views::drop_while`。両者をつなぐと元の範囲に戻る
- 位置に関係なく条件を満たす要素を集めるなら `views::filter`
- 先頭から個数で取るなら `views::take(n)`
- 打ち切り位置を 1 回の走査で確定させるなら `ranges::find_if_not(v, pred)`（即時、イテレータを返す）と `subrange(v.begin(), it)`
- C++20 でも同じ（`take_while` は C++20。`ranges::to` だけ C++23）

## Pitfalls

- `filter` ではない。途中で 1 つでも偽があれば、その後に真の要素があっても取り出さない
- 述語は複数回評価されうるので、副作用やコストの高い処理を入れない
- Python の `itertools.takewhile` はイテレータを消費して偽の要素が失われるが、C++ のビューは forward 以上の範囲を消費しないので `drop_while` で残りを取れる
- 述語がラムダだとビューの型にラムダ型が入る。`auto` で受けるか、その場でつないで使う

## Test

`examples/collection-take-while_test.cpp`
