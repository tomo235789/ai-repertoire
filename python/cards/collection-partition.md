---
id: collection-partition
lang: python
title: 条件で配列を 2 つに振り分ける
tags: [振り分け, 分割, 二分, partition, split, separate, filter]
lib: more-itertools
fn: more_itertools.partition
since: "8.0"
verified: 2026-09-17
preserves_order: true
status: public
---

述語の真偽で要素を 2 つのグループに分ける。有効・無効の振り分けや成功・失敗の仕分けに使う。

## Signature

```python
more_itertools.partition(pred, iterable)
```

## Usage

```python
from more_itertools import partition

odds, evens = partition(lambda x: x % 2 == 0, [1, 2, 3, 4, 5])
list(odds), list(evens)
# => ([1, 3, 5], [2, 4])
```

## Contract

- 順序を保持する。両方とも元の並び順のまま
- 入力を変更しない。返り値の要素は同じ参照
- 返り値は `(偽の要素, 真の要素)` の 2 つのジェネレータの組。**偽が先**
- 遅延評価。どちらかのジェネレータから取り出すたびに入力を読み進め、相手側の要素は内部のキューに溜まる。片方を読み切ると入力全体が消費される。各ジェネレータは 1 回しか走査できない
- `pred` は純粋関数であること。どちらから取り出しても、各要素につきちょうど 1 回、先頭から順に呼ばれる
- 戻り値は truthy / falsy で判定する。`0` や `''` は偽側に入る。`pred=None` なら `bool` が使われる
- 空のイテラブルを渡すと両方とも空
- 自身は例外を投げない（`pred` が投げた例外はそのまま伝わる）

## Alternatives

- 依存を増やせない場合は内包表記 2 回 `[x for x in xs if p(x)]` と `[x for x in xs if not p(x)]`（`p` が各要素に 2 回呼ばれる）
- すぐリストで使うなら `false_items, true_items = map(list, partition(pred, xs))`
- 3 つ以上に分けるなら `more_itertools.map_reduce`（collection-group-by）

## Pitfalls

- es-toolkit の `partition` は `[truthy, falsy]` の順で配列を返すが、more-itertools は `(falsy, truthy)` の順でジェネレータを返す。分割代入の順を取り違えない
- ジェネレータなので `len()` は取れず、片方だけを長く読むともう片方のキューにメモリが溜まる
- 入力がイテレータなら、両方を読み終えるまでそのイテレータを他で使わない

## Test

`examples/collection-partition_test.py`
