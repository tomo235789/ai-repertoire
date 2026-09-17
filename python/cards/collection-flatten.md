---
id: collection-flatten
lang: python
title: ネストした配列を指定の深さまで平坦化する
tags: [平坦化, 展開, 連結, flatten, flat, concat, chain]
lib: stdlib
fn: itertools.chain.from_iterable
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

イテラブルのイテラブルを 1 段開いて 1 本のイテレータにする。ページごとに取得した結果の連結などに使う。

## Signature

```python
itertools.chain.from_iterable(iterable, /)
```

## Usage

```python
from itertools import chain

list(chain.from_iterable([[1, 2], [3], [4, [5]]]))
# => [1, 2, 3, 4, [5]]  1 段だけ開く
```

## Contract

- 順序を保持する。外側の並び順も内側の並び順も保つ
- 入力を変更しない。返り値の要素は同じ参照（開かれずに残る内側の配列も同じ参照）
- 遅延評価。返り値はイテレータで、取り出した分だけ外側・内側を読み進める。1 回しか走査できない
- 開くのは 1 段だけ。要素がさらにイテラブルでもそのまま返す
- 内側はイテラブルなら何でもよく、リスト・タプル・集合・文字列・`range` が混在してもよい
- 空のイテラブル、または空のイテラブルだけを含むイテラブルを渡すと何も返さない
- 内側の要素がイテラブルでなければ、その要素に達した時点で `TypeError` を投げる

## Alternatives

- リストがすぐ欲しいなら内包表記 `[x for inner in xs for x in inner]`
- 深さを問わず全部開くなら `more_itertools.collapse(xs)`。`levels=1` で 1 段だけにでき、文字列・バイト列は開かない
- 各要素を変換しながら 1 段開くなら `chain.from_iterable(map(f, xs))`
- 決まった数のイテラブルを連結するだけなら `chain(a, b)`

## Pitfalls

- 文字列もイテラブルなので文字に分解される（`['ab', 'cd']` → `['a', 'b', 'c', 'd']`）。文字列を要素のまま残したいなら `collapse(xs, levels=1)`
- es-toolkit の `flatten` は `depth` を取り、配列でない要素（文字列など）は展開しない。同じ挙動に近いのは `collapse(xs, levels=depth)`
- `chain(*xs)` と結果は同じだが、`*xs` は先に全部展開するので外側が無限イテレータのときは使えない

## Test

`examples/collection-flatten_test.py`
