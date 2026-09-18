---
id: iter-lazy-filter
lang: python
title: イテレータの要素を遅延で絞り込む
tags: [遅延評価, 絞り込み, フィルタ, イテレータ, lazy, filter, predicate, filterfalse]
lib: stdlib
fn: filter
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

述語が真を返した要素だけを 1 つずつ返すイテレータを作る。要素は取り出されるたびに判定されるので、無限イテレータや巨大なストリームにも使える。

## Signature

```python
filter(function, iterable)
```

## Usage

```python
from itertools import count, filterfalse, islice

list(islice(filter(lambda n: n % 3 == 0, count()), 3))
# => [0, 3, 6]（無限イテレータでも必要な分しか判定されない）
list(filter(None, [0, 1, "", "a", None]))
# => [1, 'a']（None を渡すと要素自身の真偽値で絞る）
list(filterfalse(lambda n: n % 2, [1, 2, 3, 4]))
# => [2, 4]（述語が偽の要素だけ残す）
```

## Contract

- 遅延評価。`filter` を呼んだ時点では `function` は 1 回も呼ばれず、`next()` のたびに真を返す要素が見つかるまで元のイテレータを進める
- 順序を保持する。`function` は元の順に、読み進めた要素につきちょうど 1 回呼ばれ、要素は同じ参照のまま流れる
- `function` の返り値は truthy 判定。`0` / `''` / `None` / 空リストを返した要素は落ちる
- `function` に `None` を渡すと要素自身の真偽値で判定する（`filter(bool, xs)` と同じ）
- 元のイテレータを 1 回だけ走査する。返り値は使い捨てで、消費し切った後にもう一度走査すると空になる
- 空のイテラブルからは空のイテレータが返る（`list()` にすると `[]`）
- `function` が `None` でも呼び出し可能でもない場合、`filter` を呼んだ時点では例外にならず最初の `next()` で `TypeError`。第 2 引数がイテラブルでなければ呼んだ時点で `TypeError`

## Alternatives

- 結果を即座にリストで欲しく、式で書けるなら内包表記 `[x for x in xs if cond(x)]`
- 述語が偽の要素を残すなら `itertools.filterfalse(function, iterable)`（`None` を渡すと falsy な要素だけ残る）
- 条件が偽になった時点で打ち切る（絞り込みではなく先頭区間）なら `itertools.takewhile`（カード collection-take-while）
- 変換は `map`（カード iter-lazy-map）、先頭 n 個は `itertools.islice`（カード iter-take）
- 真偽の列で選ぶなら `itertools.compress(data, selectors)`

## Pitfalls

- 返り値はリストではない。件数や添字が要るなら `list()` する
- 全要素が偽の無限イテレータに `filter` すると `next()` が返ってこない。無限ソースでは `islice` と組み合わせる
- TypeScript の `Iterator.prototype.filter` と違い、述語にインデックスは渡らない。元の位置が要るなら `filter(lambda t: cond(t[1]), enumerate(xs))`
- 述語が不正でも `filter(...)` の時点では気づけない。TypeScript は呼んだ時点で `TypeError` だが、Python は最初の `next()` まで遅れる
- truthy 判定なので `str.find` のように「見つからないと `-1`、先頭なら `0`」を返す関数を述語にすると意図と逆になる。`bool` を返す関数にする

## Test

`examples/iter-lazy-filter_test.py`
