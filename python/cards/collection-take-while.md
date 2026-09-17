---
id: collection-take-while
lang: python
title: 条件を満たす間だけ先頭から要素を取り出す
tags: [先頭から取り出す, 前置部分列, 打ち切り, take-while, prefix, until, drop-while]
lib: stdlib
fn: itertools.takewhile
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

先頭から述語が真である間だけ要素を返し、最初に偽になった時点で打ち切る。ソート済み列から閾値未満の部分を取るときなどに使う。

## Signature

```python
itertools.takewhile(predicate, iterable, /)
```

## Usage

```python
from itertools import takewhile

list(takewhile(lambda x: x < 3, [1, 2, 3, 4, 1]))
# => [1, 2]
```

## Contract

- 順序を保持する。返り値は入力の先頭部分（前置部分列）
- 入力を変更しない。返り値の要素は同じ参照
- 遅延評価。返り値はイテレータで、取り出した分だけ入力を読み進める。1 回しか走査できない
- `predicate` は純粋関数であること。先頭から順に、最初に偽を返した要素まで呼ばれ、それ以降の要素には呼ばれない
- 戻り値は truthy / falsy で判定する。最初に偽になった要素は結果に含まないが、入力からは **消費されている**
- すべての要素で真なら全要素を返し、先頭で偽なら何も返さない
- 空のイテラブルを渡すと何も返さない
- 自身は例外を投げない（`predicate` が投げた例外はそのまま伝わる）

## Alternatives

- 先頭の条件を満たす部分を **捨てて** 残りが欲しいなら `itertools.dropwhile`。同じリストに両方を使えば連結が元に戻る
- 打ち切った要素を失いたくないなら `more_itertools.before_and_after(predicate, it)`（真の部分と残り全部の 2 つを返す）
- 位置に関係なく条件を満たす要素を集めるなら `filter`
- 先頭から個数で取るなら `itertools.islice(it, n)`

## Pitfalls

- イテレータを渡すと、最初に偽を返した要素は結果にも残りのイテレータにも含まれず失われる。残りを使いたいなら `before_and_after`
- `filter` ではない。途中で 1 つでも偽があれば、その後に真の要素があっても取り出さない
- es-toolkit の `takeWhile` と同じ意味論だが、Python は遅延評価で返り値はイテレータ。`len()` や添字は使えない

## Test

`examples/collection-take-while_test.py`
