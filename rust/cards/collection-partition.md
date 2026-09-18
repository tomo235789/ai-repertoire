---
id: collection-partition
lang: rust
title: 条件で配列を 2 つに振り分ける
tags: [振り分け, 二分, 条件分割, partition, split, separate, filter-both]
lib: stdlib
fn: Iterator::partition
since: "1.0"
verified: 2026-09-17
preserves_order: true
status: public
---

述語が真になる要素と偽になる要素を、1 回の走査で 2 つのコレクションに振り分ける。`filter` を 2 回書きたくなったときに使う。

## Signature

```rust
fn partition<B, F>(self, f: F) -> (B, B) where B: Default + Extend<Self::Item>, F: FnMut(&Self::Item) -> bool
```

## Usage

```rust
let (even, odd): (Vec<i32>, Vec<i32>) = (1..=5).partition(|n| n % 2 == 0);
// even => [2, 4]
// odd  => [1, 3, 5]
```

## Contract

- 順序を保持する。両方のコレクションとも元の並び順のまま（`Vec` / `String` など順序を持つ型の場合）
- イテレータを消費する。`iter()` で呼べば要素は元への参照、`into_iter()` で呼べば所有権ごと移る
- 即時評価。返る時点で入力をすべて読み終えている
- 返り値は `(真の要素, 偽の要素)` の組。**真が先**
- 返り値の型は `Default + Extend` なら何でもよく、型注釈で決める（`Vec`、`HashSet`、`String` など）。2 つは同じ型。`HashSet` など順序を持たない型では走査順の保証は無い
- `f` は各要素につきちょうど 1 回、先頭から順に呼ばれる
- 空の入力を渡すと空のコレクション 2 つを返す
- panic しない

## Alternatives

- 振り分けながら別々の型に変換したいなら itertools の `partition_map(|x| Either::Left(..) / Either::Right(..))`
- スライスをその場で並べ替える `partition_in_place` は nightly のみ（unstable）
- 述語を 2 回評価してよければ `filter(p)` と `filter(|x| !p(x))` の 2 回走査
- 3 つ以上に分けたいなら `into_group_map_by`（collection-group-by）

## Pitfalls

- 返り値の型は推論できないので `let (a, b): (Vec<_>, Vec<_>) = ...` の注釈が必須
- Python の `more_itertools.partition` は `(偽, 真)` の順で遅延だが、Rust は `(真, 偽)` の順で即時。es-toolkit の `[truthy, falsy]` と同じ順
- 述語の引数は `&Self::Item` なので `iter()` からだと `&&T` になる。`|n| **n > 0` か `|&&n| n > 0` と書く
- `Option` / `Result` を振り分けたいなら `partition_map` で `Either` に写すか、`Result` の `Vec` なら `partition(Result::is_ok)` の後に `unwrap` する

## Test

`tests/collection_partition.rs`
