---
id: collection-dedup-by-key
lang: rust
title: キー関数で配列の重複を除去する
tags: [重複除去, ユニーク, 一意化, dedupe, uniq, distinct, unique-by]
lib: itertools
fn: Itertools::unique_by
since: "0.10"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーが同じ要素を 1 つに絞る。ID を持つ構造体の `Vec` の重複除去に使う。

## Signature

```rust
fn unique_by<V, F>(self, f: F) -> UniqueBy<Self, V, F> where V: Eq + Hash, F: FnMut(&Self::Item) -> V
```

## Usage

```rust
use itertools::Itertools;

let users = vec![(1, "a"), (2, "b"), (1, "c")];
let uniq: Vec<&(i32, &str)> = users.iter().unique_by(|u| u.0).collect();
// => [(1, "a"), (2, "b")]
```

## Contract

- 順序を保持する。同じキーの要素は **最初に出現したもの** を残す
- 入力を変更しない。`iter()` で呼べば要素は元への参照、`into_iter()` で呼べば所有権ごと移る
- 遅延評価。返り値はイテレータで、取り出した分だけ入力を読み進める。見たキーは内部の `HashSet` に溜まる
- `f` は各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーの型は `Eq + Hash`。比較は `HashSet` と同じ（`==` とハッシュ）
- 空の入力を渡すと何も返さない（`collect` すると `[]`）
- panic しない

## Alternatives

- 要素そのものがキー（`Eq + Hash`）なら `unique()`
- ソート済みで **隣接する** 重複だけまとめればよいなら `dedup_by(|a, b| ...)` / `dedup_by_key(...)`、その場で縮めるなら stdlib の `Vec::dedup_by_key`
- 順序が不要なら `HashSet` に `collect`、キー順でよければ `BTreeMap<K, T>` に `entry().or_insert()` で先勝ち

## Pitfalls

- `dedup` 系（itertools の `dedup_by` / stdlib の `slice::dedup_by_key`）は隣接する重複しか消さない。`[1, 2, 1]` はそのまま。Python の `unique_justseen` と同じで、全体から消すのは `unique_by`
- `f64` は `Hash` / `Eq` でないのでキーにできない。`to_bits()` か整数への丸めでキーにする。`to_bits()` はビット表現そのものなので `0.0` と `-0.0`、ビットの違う `NaN` は別キーになる
- 複合キーはタプル `|u| (u.a, u.b)` にする。es-toolkit の `uniqBy` と違い参照比較ではなく値比較なので `String` も安全
- `HashMap` に `insert` で集めると **最後** の要素が残り意味論が逆。Python の `{key(x): x}.values()` と同じ罠

## Test

`tests/collection_dedup_by_key.rs`
