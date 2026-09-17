---
id: collection-dedup-by-key
lang: python
title: キー関数で配列の重複を除去する
tags: [重複除去, ユニーク, 一意化, dedupe, uniq, distinct, unique-by]
lib: more-itertools
fn: more_itertools.unique_everseen
since: "11.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーが同じ要素を 1 つに絞る。ID を持つ辞書のリストの重複除去に使う。

## Signature

```python
more_itertools.unique_everseen(iterable, key=None)
```

## Usage

```python
from more_itertools import unique_everseen

users = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}, {"id": 1, "name": "c"}]
list(unique_everseen(users, key=lambda u: u["id"]))
# => [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}]
```

## Contract

- 順序を保持する。同じキーの要素は **最初に出現したもの** を残す
- 入力を変更しない。返り値の要素は同じ参照
- 遅延評価。返り値はジェネレータで、取り出した分だけ入力を読み進める。1 回しか走査できない
- `key` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- `key` を省略すると要素そのものがキーになる
- キーの比較は `set` と同じ（ハッシュと `==`）。`1`・`1.0`・`True` は同じキー。`float('nan')` は `nan == nan` が `False` でも、同じオブジェクトなら `set` の同一性判定で重複扱いになり、別オブジェクト同士は別キーになる
- 空のイテラブルを渡すと何も返さない
- キー（`key` 省略時は要素）がハッシュ不可なら、その要素に達した時点で `TypeError` を投げる

## Alternatives

- 要素そのものがキーで順序が不要なら `set(xs)`。順序も要るなら `list(dict.fromkeys(xs))`
- 連続する重複だけをまとめればよい（ソート済み）なら `unique_justseen(xs, key=...)`
- ハッシュ不可な要素は `key=tuple` や `key=lambda d: frozenset(d.items())` で正規化する。順序を捨ててよければ `more_itertools.unique`（ソートして等値比較するのでハッシュ不要）

## Pitfalls

- `{key(x): x for x in xs}.values()` は **最後** の要素を残すので意味論が逆
- 複合キーはタプルにする（`key=lambda u: (u["a"], u["b"])`）。es-toolkit と違いオブジェクトが参照で比較されることはなく、`==` とハッシュで比較される
- es-toolkit の `uniqBy` は `NaN` 同士を等しいとみなすが、Python では別オブジェクトの `nan` は別キーになる
- 11.0 より前はハッシュ不可なキーで線形探索にフォールバックしていたが、11.0 以降は `TypeError`

## Test

`examples/collection-dedup-by-key_test.py`
