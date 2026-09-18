---
id: collection-zip
lang: rust
title: 複数の配列を要素ごとに組にする
tags: [組み合わせ, ペア化, 並行走査, zip, pair, tuple, combine]
lib: stdlib
fn: Iterator::zip
since: "1.0"
verified: 2026-09-17
preserves_order: true
status: public
---

2 つのイテレータを同じ位置どうしでタプルにまとめる。ラベルと値のように別々の `Vec` で持っているデータを並べて扱うときに使う。

## Signature

```rust
fn zip<U>(self, other: U) -> Zip<Self, U::IntoIter> where U: IntoIterator
```

## Usage

```rust
let labels = ["a", "b", "c"];
let values = [1, 2, 3];
let pairs: Vec<(&str, i32)> = labels.into_iter().zip(values).collect();
// => [("a", 1), ("b", 2), ("c", 3)]
```

## Contract

- 順序を保持する。i 番目のタプルは各入力の i 番目の要素からなる
- 自身を消費し、`other` は `IntoIterator` なら何でも受け取る（`Vec`、配列、`&[T]`、イテレータ）。`iter()` で呼べば要素は参照
- 遅延評価。タプル 1 つ分ずつ各入力を読み進める
- 長さは **最も短い** 入力に合わせて打ち切る。余った要素は出力に含まれないが、入力から必ず消費されるわけではない。`by_ref()` で渡した後ろ側の残りは続けて読める（先頭側は 1 要素余分に消費されることがある。Pitfalls 参照）
- どちらかが空なら何も返さない（`collect` すると `[]`）
- panic しない

## Alternatives

- 長さの不一致を検出したいなら itertools の `zip_eq`（不一致で panic）
- 最も長い入力に合わせるなら itertools の `zip_longest`（要素は `EitherOrBoth::{Both, Left, Right}`）
- 3 つ以上を組にするなら itertools の `izip!(a, b, c)`（`(x, y, z)` のフラットなタプル）。`zip` を重ねると `((x, y), z)` になる
- 逆操作（タプルのイテレータを 2 つのコレクションに戻す）は `unzip()`
- 添字と組にするなら `enumerate()`

## Pitfalls

- es-toolkit の `zip` は **最も長い** 配列に合わせて `undefined` で埋めるが、Rust の `zip` は Python と同じく最も短い入力で打ち切る。es-toolkit 相当は `zip_longest`
- 長さの不一致は黙って切り捨てられる。データの取り違えを検出したいなら `zip_eq` を使う
- 一般のイテレータ（`chars()` など）では、後ろ側が先に尽きたときに先頭側から 1 要素余分に取り出されて捨てられる。`Vec` / 配列どうしなど一部の組み合わせでは最適化により消費されない
- `zip_eq` の panic メッセージは `itertools: .zip_eq() reached end of one iterator before the other`

## Test

`tests/collection_zip.rs`
