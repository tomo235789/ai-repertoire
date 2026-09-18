---
id: collection-flatten
lang: rust
title: ネストした配列を指定の深さまで平坦化する
tags: [平坦化, フラット化, ネスト解除, flatten, flat, nested, concat]
lib: stdlib
fn: Iterator::flatten
since: "1.29"
verified: 2026-09-17
preserves_order: true
status: public
---

入れ子になったイテレータを 1 段開いて 1 本のイテレータにする。ページごとに取得した `Vec` の連結や、`Option` / `Result` の `Some` / `Ok` だけの取り出しに使う。

## Signature

```rust
fn flatten(self) -> Flatten<Self> where Self::Item: IntoIterator
```

## Usage

```rust
let nested = vec![vec![1, 2], vec![], vec![3]];
let flat: Vec<i32> = nested.into_iter().flatten().collect();
// => [1, 2, 3]
let some: Vec<i32> = vec![Some(1), None, Some(3)].into_iter().flatten().collect();
// => [1, 3]
```

## Contract

- 順序を保持する。外側の並び順も内側の並び順も保つ
- 自身を消費する。`iter()` で呼べば要素は内側への参照、`into_iter()` で呼べば所有権ごと移る
- 遅延評価。取り出した分だけ外側・内側を読み進める
- 開くのは 1 段だけ。要素がさらに `IntoIterator` でもそのまま返す。深さの指定は無く、2 段なら `flatten().flatten()`
- 内側は `IntoIterator` なら何でもよく、`Vec`、配列、`Option`、`Result`、`HashSet` が使える。`Option` は `Some` だけ、`Result` は `Ok` だけが残り、`None` / `Err` は捨てられる
- 空の入力、または空の内側だけの入力を渡すと何も返さない（`collect` すると `[]`）
- panic しない

## Alternatives

- 各要素を変換しながら 1 段開くなら `flat_map(|x| ...)`（`map(f).flatten()` と同じ）
- `Vec<Vec<T>>` をすぐ `Vec<T>` にするだけなら `slice::concat()`（`T: Clone`）
- 2 つのイテレータを繋ぐだけなら `chain(other)`
- `Result` の `Err` を捨てずに最初のエラーで止めたいなら `collect::<Result<Vec<_>, _>>()`

## Pitfalls

- es-toolkit の `flatten` は `depth` を取り、Python の `chain.from_iterable` は 1 段固定。Rust は Python と同じ 1 段固定で、段数分だけ `flatten()` を重ねる
- `Vec<&str>` に `flatten()` は使えない（`&str` は `IntoIterator` でない）。文字に分解したいなら `flat_map(|s| s.chars())`
- `Result` を `flatten` すると `Err` が黙って消える。エラーを扱うなら `collect::<Result<_, _>>()` か `partition`
- 内側が `Vec` の `iter()` 由来だと要素は `&T`。所有権が要るなら `into_iter()` か `.copied()` / `.cloned()`

## Test

`tests/collection_flatten.rs`
