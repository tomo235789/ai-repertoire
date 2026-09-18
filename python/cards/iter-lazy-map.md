---
id: iter-lazy-map
lang: python
title: イテレータの各要素を遅延で変換する
tags: [遅延評価, 変換, イテレータ, lazy, map, transform, iterator]
lib: stdlib
fn: map
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

イテラブルの各要素に関数を適用した値を 1 つずつ返すイテレータを作る。無限イテレータや巨大なストリームを、全体をメモリに載せずに変換するときに使う。

## Signature

```python
map(function, iterable, *iterables)
```

## Usage

```python
from itertools import count, islice

squares = map(lambda n: n * n, count())
list(islice(squares, 3))
# => [0, 1, 4]（無限イテレータでも先頭 3 個だけ計算される）
list(map(pow, [2, 3], [3, 2]))
# => [8, 9]（複数のイテラブルは位置ごとの要素が引数になる）
```

## Contract

- 遅延評価。`map` を呼んだ時点では `function` は 1 回も呼ばれず、`next()` で要素が取り出されるたびに 1 要素ずつ変換される
- 順序を保持する。`function` は元の順に、取り出された要素につきちょうど 1 回呼ばれる
- 入力を変更しない。返り値は新しい `map` オブジェクト（イテレータ。`iter(m) is m`）で、`len()` や添字は使えない
- 元のイテレータを 1 回だけ走査する。返り値は使い捨てで、`list()` などで消費し切った後にもう一度走査すると空になる
- 複数のイテラブルを渡すと位置ごとに `function(a, b, ...)` が呼ばれ、**最も短い** 入力で打ち切る。尽きた入力より前の引数からは 1 要素余分に消費されている
- 空のイテラブルからは空のイテレータが返る（`list()` にすると `[]`）
- `function` が呼び出し可能でなくても `map` を呼んだ時点では例外にならず、最初の `next()` で `TypeError` を投げる。イテラブルを 1 つも渡さない、またはイテラブルでないものを渡すと呼んだ時点で `TypeError`

## Alternatives

- 結果を即座にリストで欲しく、式で書けるなら内包表記 `[f(x) for x in xs]`。`lambda` を書くより読みやすい
- 遅延のまま式で書くならジェネレータ式 `(f(x) for x in xs)`。`map` は既存の関数をそのまま渡すとき（`map(str, xs)`、`map(str.strip, lines)`）に向く
- 絞り込みは `filter`（カード iter-lazy-filter）、先頭 n 個は `itertools.islice`（カード iter-take）、リストにするのは `list`（カード iter-to-array）
- 変換後をさらに平坦化するなら `itertools.chain.from_iterable(map(f, xs))`
- 長さの不一致を検出したいなら Python 3.14 以降の `map(f, a, b, strict=True)`（`zip` と同じ規則で `ValueError`）

## Pitfalls

- 返り値はリストではない。`len()` や添字は使えず、2 回目の走査は空になる。何度も使うなら `list(map(...))` で確定させる
- TypeScript の `Iterator.prototype.map` と違い、コールバックにインデックスは渡らない。位置が要るなら `(f(i, x) for i, x in enumerate(xs))`
- コールバックが不正でも `map(...)` の時点では気づけない。TypeScript の `map` は呼んだ時点で `TypeError` だが、Python は最初の `next()` まで遅れる
- 複数イテラブルで長さが違うと黙って短い方に合わせる。TypeScript の Iterator Helper は複数イテラブルを受け取らない
- 副作用目的で `list(map(f, xs))` と書かない。消費されるまで何も起きないので、副作用はふつうの `for` 文で書く

## Test

`examples/iter-lazy-map_test.py`
