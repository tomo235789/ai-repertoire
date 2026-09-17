---
id: collection-group-by
lang: rust
title: キー関数で配列をグループ化する
tags: [グループ化, 分類, 集約, group-by, categorize, bucket, group-map]
lib: itertools
fn: Itertools::into_group_map_by
since: "0.10"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、同じキーの要素を `Vec` にまとめた `HashMap` を作る。カテゴリ別の集計や一覧の見出し分けに使う。

## Signature

```rust
fn into_group_map_by<K, V, F>(self, f: F) -> HashMap<K, Vec<V>> where Self: Iterator<Item = V>, K: Hash + Eq, F: FnMut(&V) -> K
```

## Usage

```rust
use itertools::Itertools;
use std::collections::HashMap;

let items = vec![("a", 1), ("b", 2), ("a", 3)];
let groups: HashMap<&str, Vec<(&str, i32)>> = items.into_iter().into_group_map_by(|x| x.0);
// => {"a": [("a", 1), ("a", 3)], "b": [("b", 2)]}（キーの順は不定）
```

## Contract

- 各グループの `Vec` は元の出現順のまま。ただし **キーの順は不定**（`HashMap`）
- イテレータを消費する。`iter()` で呼べば要素は元への参照、`into_iter()` で呼べば所有権ごと移る
- 即時評価。返る時点で入力をすべて読み終えている
- `f` は各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーの型は `Hash + Eq`。比較は `HashMap` と同じ（`==` とハッシュ）
- 空の入力を渡すと空の `HashMap` を返す
- panic しない

## Alternatives

- 要素が `(K, V)` のタプルならキー関数なしの `into_group_map()`（値側だけが `Vec` に入る）
- キー順で走査したいなら `fold(BTreeMap::new(), |mut m, x| { m.entry(key(&x)).or_insert_with(Vec::new).push(x); m })`
- 件数だけ欲しいなら `counts_by(|x| ...)`（`HashMap<K, usize>`）
- ソート済みで **隣接する** 同キーだけまとめればよいなら `chunk_by(|x| ...)`（遅延。stdlib の `slice::chunk_by` は 2 要素の述語）

## Pitfalls

- 返り値は `HashMap` なので、キーを出現順や昇順で並べたければ `keys()` を `sorted()` するか `BTreeMap` に集め直す。es-toolkit の `groupBy` は整数風キーが昇順、Python の `map_reduce` は初出順
- itertools の `chunk_by`（旧 `group_by`）は Python の `itertools.groupby` と同じで連続する要素しかまとめない。ソートしていない入力に使うと同じキーが何度も現れる
- `f64` は `Hash` / `Eq` でないのでキーにできない。`to_bits()` や整数への丸めで正規化する

## Test

`tests/collection_group_by.rs`
