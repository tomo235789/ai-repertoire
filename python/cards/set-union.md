---
id: set-union
lang: python
title: 2 つの集合の和集合を作る
tags: [和集合, 集合演算, 結合, 重複除去, union, set-operations, merge, dedupe]
lib: stdlib
fn: set.union
since: "3.0"
verified: 2026-09-17
status: public
---

自分と引数の両方の要素を含む新しい `set` を返す。タグや ID の集合を重複なく合わせるときに使う。

## Signature

```python
set.union(*others)  # 演算子形 set | other | ... は set / frozenset 同士のみ
```

## Usage

```python
a = {3, 1, 2}
b = {2, 4, 1}
a | b
# => {1, 2, 3, 4}
a.union([4, 5], "x")
# => {1, 2, 3, 4, 5, 'x'}（メソッドは任意のイテラブルを複数受け取れる）
a
# => {1, 2, 3}（元の set は変わらない）
```

## Contract

- 即時評価。`a` も引数も変更せず、新しい `set` を返す。`a.union()`（引数なし）でもコピーが返る
- 要素の順序は不定。小さい整数の `set` が昇順に見えるのは実装上の偶然で、順序に依存してはいけない。順序が要るなら `sorted()` する
- `a | b` は `set` / `frozenset` 同士のみ。リストやイテレータや `dict` を右辺にすると `TypeError`（`dict.keys()` の view は可）
- `a.union(*others)` は任意のイテラブル（リスト、`range`、ジェネレータ、文字列、`dict`（キー））を複数受け取れる
- 返り値の型は左辺（メソッドなら `self`）に合わせる。`frozenset | set` は `frozenset`、`set | frozenset` は `set`。`set` のサブクラスで呼んでも返り値は `set`
- 要素の同一性はハッシュと `==`。`{1} | {1.0}` は `{1}`、`{0} | {False}` は `{0}`
- 空同士なら空の `set`。片方が空なら他方のコピー
- 要素が hashable でなければ `TypeError`、イテラブルでないものを渡しても `TypeError`
- `a |= b` と `a.update(*others)` は破壊的で `a` 自身に要素を追加する（`update` は任意のイテラブル可）

## Alternatives

- リストの和集合（重複除去済みで順序保持）が欲しいなら `more_itertools.unique_everseen(chain(xs, ys))`（カード collection-dedup-by-key）
- 複数の `set` をまとめるなら `set().union(*sets)` または `functools.reduce(set.union, sets, set())`
- 共通部分は `&` / `intersection`、差は `-` / `difference`、対称差は `^` / `symmetric_difference`（カード set-difference）
- 変更不可の集合が欲しければ `frozenset`（辞書のキーや `set` の要素にできる）

## Pitfalls

- `a | [1, 2]` は `TypeError`。リストは `a.union([1, 2])` か `a | {1, 2}` にする。TypeScript の `Set.prototype.union` も配列を受け付けないが、Python はメソッド側が任意のイテラブルを許す
- `a.union("ab")` は文字列を 1 文字ずつ要素にする。文字列 1 つを足したいなら `a | {"ab"}`
- TypeScript の `union` は `this` の要素が先に並ぶ順序保持だが、Python の `set` に順序は無い。`a | b == b | a`
- `a |= b` と `a.update(b)` は `a` を書き換える。共有している `set` に使うと他の参照からも見える

## Test

`examples/set-union_test.py`
