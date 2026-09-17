---
id: collection-sort-by
lang: python
title: 複数のキーで配列を昇順に並べ替える
tags: [並べ替え, ソート, 整列, sort, sort-by, order-by, stable-sort]
lib: stdlib
fn: sorted
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

キー関数の返り値で要素を昇順に並べ替えた新しいリストを作る。複数キーはタプルを返す。

## Signature

```python
sorted(iterable, /, *, key=None, reverse=False)
```

## Usage

```python
users = [{"name": "b", "age": 30}, {"name": "a", "age": 30}, {"name": "c", "age": 20}]
sorted(users, key=lambda u: (u["age"], u["name"]))
# => [{'name': 'c', 'age': 20}, {'name': 'a', 'age': 30}, {'name': 'b', 'age': 30}]
```

## Contract

- 安定ソート。キーが等しい要素は元の相対順を保つ（`reverse=True` でも保つ）
- 入力を変更しない。返り値は新しいリスト（要素は同じ参照）。入力はイテレータでもよい
- 即時評価。返る時点で入力をすべて読み終えている
- `key` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる（比較のたびではない）
- 複数キーはタプルを返す。左から順に比較し、前が等しいときだけ次で比較する
- `reverse=True` は全キーをまとめて降順にする
- 空のイテラブルを渡すと `[]` を返す
- キー同士が `<` で比較できなければ `TypeError` を投げる（`None` と数値、数値と文字列の混在など）

## Alternatives

- その場で並べ替えてよければ `list.sort(key=..., reverse=...)`（返り値は `None`）
- キーの取り出しは `operator.itemgetter("age", "name")` / `operator.attrgetter("age")` でも書ける
- キーごとに昇順・降順を変えたいなら数値キーを符号反転するか、安定性を利用して後ろのキーから順に複数回 `sorted` する
- 最小・最大の 1 件だけなら `min` / `max` に同じ `key=`

## Pitfalls

- es-toolkit の `sortBy` は `null` / `undefined` を末尾に置くが、Python は `None` が混ざると `TypeError`。末尾に置くなら `key=lambda x: (x is None, x)` のようにタプルで先に振り分ける
- `float('nan')` は比較結果が定まらず、並びが保証されない。事前に除く
- 文字列はコードポイント順で、大文字が小文字より前に来る。大小を無視するなら `key=str.casefold`
- `list.sort()` は `None` を返すので `xs = xs.sort()` としない。新しいリストが欲しいときは `sorted`

## Test

`examples/collection-sort-by_test.py`
