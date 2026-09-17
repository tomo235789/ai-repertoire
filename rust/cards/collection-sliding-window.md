---
id: collection-sliding-window
lang: rust
title: 配列をスライディングウィンドウで走査する
tags: [スライディングウィンドウ, 移動窓, 連続部分列, sliding-window, windows, rolling, moving]
lib: stdlib
fn: slice::windows
since: "1.0"
verified: 2026-09-17
preserves_order: true
status: public
---

固定長 `size` の窓を 1 つずつずらしながら部分スライスを切り出す。移動平均や隣接要素の比較に使う。

## Signature

```rust
pub fn windows(&self, size: usize) -> Windows<'_, T>
```

## Usage

```rust
let xs = [1, 2, 3, 4, 5];
let windows: Vec<&[i32]> = xs.windows(3).collect();
// => [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
let avg: Vec<f64> = [1.0, 2.0, 3.0, 4.0].windows(2).map(|w| w.iter().sum::<f64>() / 2.0).collect();
// => [1.5, 2.5, 3.5]
```

## Contract

- 順序を保持する。窓は先頭から 1 つずつずれた開始位置で並び、窓の中も元の並び順
- 入力を変更しない。返り値は元のスライスを借用する部分スライス（`&[T]`）のイテレータで、要素をコピーしない
- 遅延評価。`Windows` は `ExactSizeIterator` かつ `DoubleEndedIterator` で、`len()` や `rev()` が使える
- 窓の数は `len - size + 1`。`size` に満たない末尾の窓は **作らない**
- スライス長が `size` 未満なら何も返さない。空スライスも同様（`collect` すると `[]`）
- `size == 0` なら panic する（`window size must be non-zero`）

## Alternatives

- `step` を付けたいなら `windows(size).step_by(step)`
- 窓を固定長のタプルで受けたいなら itertools の `tuple_windows()`（`(a, b)` や `(a, b, c)`。要素は `Clone`）
- 重ならない分割は `chunks(size)`（collection-chunk）。こちらは末尾の短い部分も返す
- 所有権のある `Vec<Vec<T>>` が欲しいなら `.map(<[T]>::to_vec)`

## Pitfalls

- es-toolkit の `windowed` の既定（`partialWindows: false`）と同じで末尾を捨てる。Python の `more_itertools.windowed` は `fillvalue` で埋めるので意味が違う
- `step` 引数は無い。`step_by` で間引くと開始位置は `0, step, 2*step, ...` になる
- 返るのは借用スライスなので、元の `Vec` を変更する間は保持できない。持ち越すなら `to_vec` で所有権を取る
- `size` は `usize` なので負数や小数は型で弾かれるが、`0` は実行時 panic。es-toolkit / Python は例外を投げる

## Test

`tests/collection_sliding_window.rs`
