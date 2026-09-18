---
id: set-difference
lang: python
title: 2 つの集合の差集合を作る
tags: [差集合, 集合演算, 除外, 共通部分, difference, set-operations, exclude, subset]
lib: stdlib
fn: set.difference
since: "3.0"
verified: 2026-09-17
status: public
---

自分の要素のうち引数に含まれないものだけを持つ新しい `set` を返す。「追加された ID」「未処理の項目」のような 2 集合の差を求めるときに使う。

## Signature

```python
set.difference(*others)  # 演算子形 set - other - ... は set / frozenset 同士のみ
```

## Usage

```python
a = {1, 2, 3, 4}
b = {2, 4, 5}
a - b                      # => {1, 3}（a にあって b に無いもの）
b - a                      # => {5}
a ^ b                      # => {1, 3, 5}（どちらか一方にだけあるもの）
a & b                      # => {2, 4}
{1, 2} <= a                # => True（部分集合）
a.difference([2, 4], [1])  # => {3}（メソッドはイテラブルを複数受け取れる）
a                          # => {1, 2, 3, 4}（元の set は変わらない）
```

## Contract

- 即時評価。`a` も引数も変更せず、新しい `set` を返す
- 要素の順序は不定。順序が要るなら `sorted()` する
- `a - b` / `a ^ b` / `a & b` / `a <= b` は `set` / `frozenset` 同士のみ。リストを相手にすると `TypeError`（`dict.keys()` の view は可）
- `a.difference(*others)` / `a.intersection(*others)` は任意のイテラブルを複数受け取れる。`a.symmetric_difference(other)` は 1 つだけ。`a.issubset(other)` / `a.issuperset(other)` / `a.isdisjoint(other)` もイテラブル可
- 返り値の型は左辺に合わせる。`frozenset - set` は `frozenset`、`set - frozenset` は `set`
- 要素の同一性はハッシュと `==`。`{1} - {1.0}` は空、`{1, 2} - {True}` は `{2}`
- `a` が空、または `b` が `a` を含むなら空。`b` が空なら `a` のコピー
- `<` / `>` は真部分集合（等しいと `False`）、`<=` / `>=` は等しくても `True`。空集合はどの集合の部分集合でもある
- `a -= b` / `difference_update` / `intersection_update` / `symmetric_difference_update` は破壊的で `a` 自身を書き換える
- 要素が hashable でなければ `TypeError`

## Alternatives

- リストの差（`xs` にあって `ys` に無い要素、順序と重複を保つ）は `excluded = set(ys)` を作ってから `[x for x in xs if x not in excluded]`
- `dict` のキー同士の差は `d1.keys() - d2.keys()`（`set` が返る）
- 和集合は `|` / `union`（カード set-union）
- 述語や変換関数で同一性を決めたいなら `{key(x) for x in xs} - {key(y) for y in ys}` のように先にキーへ変換する

## Pitfalls

- `a - [1]` は `TypeError`。リストは `a.difference([1])` か `a - {1}`
- `a - b` と `b - a` は別物。対称な差は `a ^ b`
- `a -= b` は `a` を書き換える。TypeScript の `difference` は非破壊のみだが、Python には破壊的な演算子とメソッドがある
- `symmetric_difference` は引数 1 つだけ。複数なら `a ^ b ^ c`
- TypeScript の `difference` は `this` の順序を保つが、Python の `set` に順序は無い

## Test

`examples/set-difference_test.py`
