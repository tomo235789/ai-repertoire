---
id: map-count-by
lang: python
title: キー関数で要素の出現回数を数える
tags: [集計, 件数, 出現回数, ヒストグラム, count-by, Counter, tally, frequency]
lib: stdlib
fn: collections.Counter
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーごとの出現回数を数えた `Counter`（`dict` のサブクラス）を作る。カテゴリ別の件数表示やヒストグラム作成に使う。

## Signature

```python
collections.Counter([iterable-or-mapping])
```

## Usage

```python
from collections import Counter

counts = Counter(len(w) for w in ["apple", "bob", "cat", "dove"])
counts
# => Counter({3: 2, 5: 1, 4: 1})
counts.most_common(1)
# => [(3, 2)]
counts[99]
# => 0（無いキーは 0。挿入もされない）
```

## Contract

- 即時評価。イテラブルを読み切り、各要素の出現回数を数える。キー関数は `Counter(key(x) for x in xs)` のようにジェネレータ式で与える
- 順序を保持する。キーはそのキーが最初に現れた順。`most_common(n)` は回数の多い順で、同数は初出順
- 入力を変更しない。返り値は新しい `Counter`
- キーは hashable なら何でもよい。同一性は `dict` と同じで `1` と `1.0` と `True` は同じキー、`1` と `'1'` は別キー。hashable でなければ `TypeError`
- 無いキーを `c[k]` で読むと `0` を返す。`KeyError` にならず挿入もされないので `k in c` は `False` のまま
- 空のイテラブルなら空の `Counter`。`most_common()` は `[]`
- `c.update(iterable)` は加算、`c.subtract(iterable)` は減算で、どちらも `c` を書き換え 0 や負の値も残す。`c1 + c2` / `c1 - c2` / `c1 & c2`（最小）/ `c1 | c2`（最大）は新しい `Counter` を返し、**0 以下のキーを落とす**
- `c.total()`（3.10 以降）は合計で `sum(c.values())` と同じ

## Alternatives

- 要素そのものを束ねたいなら `defaultdict(list)`（カード map-group-to-map）、キーが一意なら辞書内包表記（カード map-key-by）
- `more_itertools.map_reduce(xs, keyfunc, reducefunc=len)`（カード collection-group-by）でも同じ辞書ができる
- 通常の `dict` で欲しければ `dict(Counter(...))`
- 最頻 1 つは `c.most_common(1)[0]` か `max(c, key=c.get)`。件数順に並べ替えたいだけなら `sorted(c.items(), key=lambda kv: -kv[1])`

## Pitfalls

- es-toolkit の `countBy` はキーを文字列化する（`1` と `'1'` が同じ）が、`Counter` は型を保つ。逆に `1` と `1.0` と `True` はまとまる
- `c[k]` が `0` を返すので、キーの有無は `k in c` や `len(c)` で判定する。`c[k] += 1` は無いキーにもそのまま使える
- 演算子 `+` / `-` は 0 以下を落とす。`c - other` で 0 になったキーは消える。負の値を保ちたいなら `subtract`
- `most_common()` の同数は初出順。es-toolkit のように整数風キーが昇順先頭に並ぶことはない
- `Counter` は `dict` なので `json.dumps` できるが、キーは文字列化される

## Test

`examples/map-count-by_test.py`
