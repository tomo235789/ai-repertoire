---
id: collection-take-while
lang: rust
title: 条件を満たす間だけ先頭から要素を取り出す
tags: [先頭から取り出す, 前置部分列, 打ち切り, take-while, prefix, until, skip-while]
lib: stdlib
fn: Iterator::take_while
since: "1.0"
verified: 2026-09-17
status: public
---

先頭から述語が真である間だけ要素を返し、最初に偽になった時点で打ち切る。ソート済み列から閾値未満の部分を取るときなどに使う。

## Signature

```rust
fn take_while<P>(self, predicate: P) -> TakeWhile<Self, P> where Self: Sized, P: FnMut(&Self::Item) -> bool
```

## Usage

```rust
let v = vec![1, 2, 5, 3, 1];
let head: Vec<i32> = v.iter().take_while(|&&x| x < 4).copied().collect();
// => [1, 2]

let mut it = v.iter();
let head: Vec<i32> = it.by_ref().take_while(|&&x| x < 4).copied().collect();
let rest: Vec<i32> = it.copied().collect();
// => head = [1, 2], rest = [3, 1]（打ち切りの 5 は消費されて失われる）
```

## Contract

- 順序を保持する。返り値は元の列の先頭部分（前置部分列）。遅延評価で、`collect` などで消費した分だけ入力を読む
- `iter()` なら要素は参照（`&i32`）、`into_iter()` なら所有権が移る。値が欲しければ `copied()` / `cloned()` を挟む
- `predicate` は先頭から順に、最初に偽を返した要素まで呼ばれ、それ以降の要素には呼ばれない（`[1, 2, 5, 3, 1]` に `x < 4` なら 3 回）
- 最初に偽になった要素は結果に含まれないが、元のイテレータからは **消費されている**。`by_ref()` で続きを読むとその要素は飛ばされる
- 一度打ち切ると以後は `None` を返し続ける。元のイテレータにまだ要素があっても再開しない
- すべて真なら全要素、先頭で偽なら空。空のイテレータなら空
- 自身は panic しない。`predicate` の panic はそのまま伝播する

## Alternatives

- 打ち切りの要素を失いたくないなら itertools の `take_while_ref`（`Clone` なイテレータを複製して先読みする）か `peekable()` + `peeking_take_while`。残りは `[5, 3, 1]` になる
- 打ち切りの要素まで含めたいなら itertools の `take_while_inclusive`（`[1, 2, 5]`）
- 先頭の条件を満たす部分を **捨てて** 残りが欲しいなら `skip_while`（`[5, 3, 1]`）。`take_while` と `skip_while` の結果を連結すると元に戻る
- 変換と打ち切りを同時にするなら `map_while`（Rust 1.57）。`Some` の間だけ取り、`["1", "2", "x", "4"]` を `parse().ok()` に通すと `[1, 2]`
- ソート済みスライスなら `partition_point` で境界の添字を 2 分探索し `&v[..n]` でスライスにする

## Pitfalls

- `filter` ではない。途中で 1 つでも偽があれば、その後に真の要素があっても取り出さない
- Python の `itertools.takewhile` と同じ意味論で、打ち切りの要素が消費される点も同じ。TypeScript（es-toolkit の `takeWhile`）は配列を返すので消費の問題は無い
- 述語の引数は `&Self::Item`。`iter()` の上では `&&i32` になるので `|&&x| x < 4` か `|x| **x < 4` と書く
- 無限イテレータ `(1..)` にも使える（遅延評価）。打ち切り条件がいつか偽になることを確認してから `collect` する

## Test

`tests/collection_take_while.rs`
