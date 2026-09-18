---
id: iter-take
lang: python
title: イテレータの先頭から指定個数だけ取り出す
tags: [先頭, 打ち切り, 個数制限, 無限列, take, limit, head, islice]
lib: stdlib
fn: itertools.islice
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

イテレータの先頭 `stop` 個（または `start` 番目から `stop` 番目の手前まで）だけを流すイテレータを返す。無限イテレータやストリームから必要な分だけ取り出すときに使う。

## Signature

```python
itertools.islice(iterable, start, stop[, step])  # islice(iterable, stop) の 2 引数形もある
```

## Usage

```python
from itertools import count, islice

list(islice(count(), 3))
# => [0, 1, 2]
list(islice(count(), 5, 7))
# => [5, 6]（start 番目から stop 番目の手前まで）
list(islice(count(), 0, 10, 3))
# => [0, 3, 6, 9]
list(islice([1, 2], 5))
# => [1, 2]（元が短ければそこで終わる）
```

## Contract

- 遅延評価。`islice` を呼んだ時点では元のイテレータを進めず、`next()` のたびに 1 要素ずつ取り出す。`stop` を超える要素は元から取り出さない（`islice(it, 3)` は元を 3 回しか進めない、`islice(it, 0)` は 1 回も進めない）
- 順序を保持する。元のイテレータが `stop` より短ければあるだけ返して終わる
- `start` を指定すると先頭 `start` 個を読み捨てる。`step` は `start` から数えて `step` 個おきに返す。`stop` に `None` を渡すと最後まで
- 元のイテレータを消費する。読み捨てた要素も取り出した要素も元には戻らない。`islice` を消費し切った後に元の `next()` を呼ぶと続きの要素が返る（元のイテレータは閉じられない）
- 返り値は使い捨てのイテレータ。消費し切った後にもう一度走査すると空になる
- `start` / `stop` が負数または整数でない（`1.5`）と `ValueError`。`step` が `0` 以下でも `ValueError`。いずれも `islice` を呼んだ時点で投げる
- `start >= stop` なら空（`islice(xs, 2, 1)` は `[]`）。空のイテラブルなら空

## Alternatives

- 元がリストならスライス `xs[:n]`（即時、新しいリスト。負数は末尾から数える）
- 条件で打ち切るなら `itertools.takewhile`（カード collection-take-while）
- 先頭 n 個をリストで欲しいだけなら more-itertools の `take(n, iterable)`。先頭 1 個は `next(it, default)` か `more_itertools.first`
- 先頭 n 個を読み捨てて残りを流すなら `islice(it, n, None)`。more-itertools には `consume(it, n)` もある
- 変換・絞り込みは `map` / `filter`（カード iter-lazy-map / iter-lazy-filter）と組み合わせる

## Pitfalls

- 負数は末尾から数えるのではなく `ValueError`。TypeScript の `take` の `RangeError` と同じで、リストのスライスとは別物
- `stop` は含まない。`islice(it, 1, 3)` は添字 1 と 2 の 2 個
- `filter` の後ろに置くこと。`filter(pred, islice(it, 3))` は先頭 3 個から絞るので 3 個未満になる
- 元のイテレータから消費した要素は戻らない。`list(islice(it, 3))` の後に同じ `it` へ `islice(it, 3)` すると 4 個目からになる（分割読みには使えるが、先頭のやり直しはできない）
- TypeScript の `take` は打ち切り時に元のイテレータを `return()` で閉じるが、`islice` は閉じない。ジェネレータの `finally` は走らず、続きから読める

## Test

`examples/iter-take_test.py`
