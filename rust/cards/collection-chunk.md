---
id: collection-chunk
lang: rust
title: 配列を固定長の小配列に分割する
tags: [分割, チャンク, バッチ, chunk, split, batch, chunks]
lib: stdlib
fn: slice::chunks
since: "1.0"
verified: 2026-09-17
preserves_order: true
status: public
---

スライスを `chunk_size` 個ずつの部分スライスに切り分ける。API のバッチ送信やページ分割で使う。

## Signature

```rust
pub fn chunks(&self, chunk_size: usize) -> Chunks<'_, T>
```

## Usage

```rust
let xs = [1, 2, 3, 4, 5];
let chunks: Vec<&[i32]> = xs.chunks(2).collect();
// => [[1, 2], [3, 4], [5]]
let owned: Vec<Vec<i32>> = xs.chunks(2).map(<[i32]>::to_vec).collect();
// => [[1, 2], [3, 4], [5]]
```

## Contract

- 順序を保持する。各部分スライスの中も元の並び順のまま
- 入力を変更しない。返り値は元のスライスを借用する部分スライス（`&[T]`）のイテレータで、要素をコピーしない
- 遅延評価。`Chunks` は `ExactSizeIterator` かつ `DoubleEndedIterator` で、`len()` や `rev()` が使える
- 割り切れない場合、最後の部分スライスは `chunk_size` 未満になる。切り捨てない
- `chunk_size` がスライス長を超えると、全体を 1 つの部分スライスとして返す
- 空スライスを渡すと何も返さない（`collect` すると `[]`）
- `chunk_size == 0` なら panic する（`chunk size must be non-zero`）

## Alternatives

- 端数を切り捨てたいなら `chunks_exact(n)`。端数は `.remainder()` で取れる
- 各部分をその場で書き換えるなら `chunks_mut(n)`
- 所有権のある `Vec<Vec<T>>` が欲しいなら `.map(<[T]>::to_vec)`（`T: Clone`）
- スライスでなくイテレータを分割するなら itertools の `Itertools::chunks(n)`（`IntoChunks` を `.into_iter()` して各チャンクを `collect` する）
- 固定長配列 `&[T; N]` で受け取る `array_chunks` は nightly のみ（unstable）

## Pitfalls

- 返るのは借用スライスなので、元の `Vec` を変更・drop する間は保持できない。持ち越すなら `to_vec` で所有権を取る
- `chunk_size` は `usize` なので負数や小数は型で弾かれるが、`0` は実行時 panic。es-toolkit の `chunk` は `Error`、Python の `itertools.batched` は `ValueError` を投げる
- Python の `batched` / es-toolkit の `chunk` と同じく最後が短くなる。切り捨てたいなら `chunks_exact`
- `str` には `chunks` が無い。`as_bytes().chunks(n)` は UTF-8 の境界を壊すので、文字単位なら `s.chars().collect::<Vec<_>>()` にしてから渡す

## Test

`tests/collection_chunk.rs`
