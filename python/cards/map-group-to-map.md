---
id: map-group-to-map
lang: python
title: キー関数で要素をグループ化して Map にする
tags: [グループ化, 分類, 挿入順, 辞書, group-by, defaultdict, bucket, categorize]
lib: stdlib
fn: collections.defaultdict
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、同じキーの要素をリストにまとめた辞書を `defaultdict(list)` で作る。依存を増やさずにグループ化したいときや、キーにタプルや数値をそのまま使いたいときに使う。

## Signature

```python
d = defaultdict(list)
for x in iterable: d[key(x)].append(x)
```

## Usage

```python
from collections import defaultdict

words = ["apple", "bob", "cat", "dove"]
groups = defaultdict(list)
for w in words:
    groups[len(w)].append(w)
dict(groups)
# => {5: ['apple'], 3: ['bob', 'cat'], 4: ['dove']}
list(groups)
# => [5, 3, 4]（キーが最初に現れた順）
```

## Contract

- 順序を保持する。キーはそのキーが最初に現れた順、各グループのリストは元の出現順
- 即時評価。ループが終わった時点で入力をすべて読み終えている。`key` は各要素につきちょうど 1 回、先頭から順に呼ばれる
- 入力を変更しない。返り値は新しい `defaultdict`（`dict` のサブクラス）で、要素は同じ参照
- キーは hashable なら何でもよい（数値、文字列、タプル、`None`、`frozenset`）。同一性は `dict` と同じハッシュと `==` で、`1` と `1.0` と `True` は同じグループ、`1` と `'1'` は別グループ
- リストや辞書など hashable でないキーは `TypeError`
- 空のイテラブルなら空の `defaultdict`。`dict(d)` で通常の辞書に戻せ、`==` は `dict` と同じ内容なら等しい
- `d[missing]` は `[]` を返すと同時にそのキーを **挿入する**。`d.get(missing)` は `None` を返し挿入しない

## Alternatives

- 1 行で書きたいなら more-itertools の `map_reduce(xs, keyfunc)`（カード collection-group-by。`valuefunc` / `reducefunc` で値の変換・集約もできる）
- `itertools.groupby` は **連続した** 要素しかまとめない。使うなら `sorted(xs, key=key)` を先に通す
- 件数だけなら `collections.Counter`（カード map-count-by）、キーが一意で 1 要素ずつ引くなら辞書内包表記（カード map-key-by）
- 入力を一度に読み切りたくないなら `more_itertools.bucket`
- `defaultdict` を使わないなら `d.setdefault(key(x), []).append(x)`（毎回空リストを作るぶん無駄がある）

## Pitfalls

- `defaultdict` は **読むだけでキーを作る**。存在確認は `k in d` か `d.get(k, [])` で行い、外へ返す前に `dict(d)` にしておくと事故が減る
- TypeScript の `Map.groupBy` はキーの同一性が参照（SameValueZero）だが、Python はハッシュと `==`。内容が同じタプルは同じグループになり、`1` と `1.0` もまとまる
- `json.dumps` するとキーは文字列化される（`{5: [...]}` は `{"5": [...]}`）
- `itertools.groupby` と混同しない。ソート無しで使うと同じキーが何度も現れる

## Test

`examples/map-group-to-map_test.py`
