---
id: collection-group-by
lang: python
title: キー関数で配列をグループ化する
tags: [グループ化, 分類, 集計, group-by, categorize, bucket, map-reduce]
lib: more-itertools
fn: more_itertools.map_reduce
since: "4.2.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、同じキーの要素をリストにまとめた辞書を作る。種別ごとの集計や画面のセクション分けに使う。

## Signature

```python
more_itertools.map_reduce(iterable, keyfunc, valuefunc=None, reducefunc=None)
```

## Usage

```python
from more_itertools import map_reduce

words = ["apple", "bob", "cat", "dove"]
map_reduce(words, keyfunc=len)
# => defaultdict(None, {5: ['apple'], 3: ['bob', 'cat'], 4: ['dove']})
```

## Contract

- 順序を保持する。各グループのリストは元の出現順で、キーもグループの初出順に並ぶ
- 入力を変更しない。返り値は新しい `defaultdict`（`default_factory` は `None` なので未知のキーは `KeyError`）で、要素は同じ参照
- 即時評価。返る時点で入力をすべて読み終えている
- `keyfunc` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーの比較は dict と同じ（ハッシュと `==`）。`1` と `1.0` は同じグループになる
- `valuefunc` を渡すと要素の代わりにその返り値を溜め、`reducefunc` を渡すと各グループのリストをその返り値に置き換える（例: `reducefunc=len` で件数）
- 空のイテラブルを渡すと空の `defaultdict` を返す
- キーがハッシュ不可なら `TypeError` を投げる

## Alternatives

- 依存を増やせない場合は stdlib で `d = defaultdict(list)` に `d[keyfunc(x)].append(x)` するループ
- `itertools.groupby` は **連続した** 要素しかまとめない。使うなら `sorted(xs, key=keyfunc)` を先に通す
- 件数だけなら `collections.Counter(map(keyfunc, xs))`
- 入力を一度に読み切りたくないなら `more_itertools.bucket`

## Pitfalls

- es-toolkit の `groupBy` は数値キーを文字列化して `1` と `'1'` を同じグループにするが、Python では別のキー。逆に `1` と `1.0` と `True` は同じグループになる
- 返り値は `defaultdict` だが `default_factory=None` なので `d[missing]` は `KeyError`。無いキーは `d.get(k, [])` で読む
- `itertools.groupby` と名前が似ているが意味が違う。ソート無しで `groupby` を使うと同じキーが何度も現れる

## Test

`examples/collection-group-by_test.py`
