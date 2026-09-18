---
id: collection-sort-by
lang: rust
title: 複数のキーで配列を昇順に並べ替える
tags: [並べ替え, ソート, 整列, 複数キー, sort-by, sort_by_key, multi-key, stable-sort]
lib: stdlib
fn: slice::sort_by_key
since: "1.7"
verified: 2026-09-17
preserves_order: true
status: public
---

キー関数の返り値でスライスをその場で昇順に並べ替える。複数キーはタプルを返す。

## Signature

```rust
pub fn sort_by_key<K, F>(&mut self, f: F) where F: FnMut(&T) -> K, K: Ord
```

## Usage

```rust
let mut rows = vec![("b", 2), ("a", 9), ("b", 1)];
rows.sort_by_key(|r| (r.0, r.1));
// => [("a", 9), ("b", 1), ("b", 2)]
```

## Contract

- 安定ソート。キーが等しい要素は元の相対順を保つ
- その場で並べ替える（`&mut self`）。返り値は無い
- 即時評価。戻った時点で並べ替えが終わっている
- 複数キーはタプルを返す。左から順に比較し、前が等しいときだけ次で比較する
- `f` は同じ要素に対して複数回呼ばれうる（現行実装では比較のたび）。呼ばれる回数や順序に依存しない。重いキーは `sort_by_cached_key`（各要素につき最大 1 回）
- キーの型は `Ord`。`f64` は `Ord` でないので使えず、`Option` は `None` が先頭、`&str` はバイト順（大文字が小文字より前）
- 空スライスでも panic しない

## Alternatives

- 非破壊で並べ替えた新しいイテレータが欲しいなら itertools の `sorted_by_key`（`std::vec::IntoIter` を返す）
- キーの計算が重いなら `sort_by_cached_key`（各要素につき最大 1 回だけ呼び、キーを別途確保する）
- 安定性が不要で速度優先なら `sort_unstable_by_key`
- 降順は `sort_by_key(|x| std::cmp::Reverse(x.v))`。キーごとに向きを変えるなら `sort_by(|a, b| a.g.cmp(&b.g).then(b.v.cmp(&a.v)))`
- `f64` は `sort_by(|a, b| a.v.total_cmp(&b.v))`

## Pitfalls

- es-toolkit の `sortBy` / Python の `sorted` は新しい配列を返すが、`sort_by_key` は元の `Vec` を書き換える。元を残すなら `sorted_by_key` か `to_vec()` してから
- キー関数は参照を返せない（`|p| &p.name` はライフタイムエラー）。`sort_by(|a, b| a.name.cmp(&b.name))` にするか `sort_by_cached_key(|p| p.name.clone())` を使う
- `f64` を `sort_by_key` に渡すとコンパイルエラー（`Ord` でない）。`total_cmp` を使うと `NaN` は正の無限大より後ろに並び、`-0.0` は `0.0` より前
- Python と同じく `NaN` を含む `partial_cmp().unwrap()` は panic する。`total_cmp` を使う

## Test

`tests/collection_sort_by.rs`
