---
id: map-key-by
lang: python
title: キー関数で要素をキー引きできる辞書にする
tags: [索引化, 辞書化, ルックアップ, 一意キー, key-by, index-by, lookup, dict-comprehension]
lib: stdlib
fn: dict comprehension
since: "3.7"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーから要素を引ける辞書を作る。ID による参照テーブル作成や、リストの線形探索を繰り返す処理の置き換えに使う。

## Signature

```python
{key(x): x for x in iterable}
```

## Usage

```python
users = [{"id": "u1", "name": "A"}, {"id": "u2", "name": "B"}]
by_id = {u["id"]: u for u in users}
by_id["u2"]["name"]
# => 'B'
dup = [{"id": "x", "v": 1}, {"id": "y", "v": 9}, {"id": "x", "v": 2}]
{d["id"]: d for d in dup}
# => {'x': {'id': 'x', 'v': 2}, 'y': {'id': 'y', 'v': 9}}（重複キーは最後が残る）
```

## Contract

- 即時評価。キー式は各要素につきちょうど 1 回、先頭から順に評価される
- 同じキーが複数回出たら **最後** の要素が残る。返り値でのそのキーの位置は最初に出現した場所
- 入力を変更しない。返り値は新しい `dict` で、値は同じ参照
- キーは hashable なら何でもよく、型はそのまま（文字列化しない）。`1` と `1.0` と `True` は同じキー、`1` と `'1'` は別キー
- 順序は元の出現順（キーの初出順）。挿入順の保持は Python 3.7 以降の言語仕様
- 空のイテラブルなら `{}`
- キーが hashable でなければ `TypeError`

## Alternatives

- `dict(zip(keys, xs))` や `dict((key(x), x) for x in xs)` でも同じ辞書ができる
- **最初** の要素を残したいなら `d = {}` に `d.setdefault(key(x), x)` するループ。`{key(x): x for x in reversed(xs)}` でも最初が残るが、キーの順序は最後の出現順になる
- 同じキーの要素を全部残すなら `defaultdict(list)`（カード map-group-to-map）、件数だけなら `Counter`（カード map-count-by）
- 値も変換するなら `{key(x): value(x) for x in xs}`（カード object-map-values）

## Pitfalls

- 重複キーは黙って上書きされる。es-toolkit の `keyBy` と同じ「最後が残る」規則。重複を検出したいなら `len(result) == len(xs)` を確認する
- es-toolkit の `keyBy` はキーを文字列化し整数風キーを昇順先頭に並べるが、Python は型も挿入順もそのまま
- 存在しないキーは `KeyError`。`by_id.get(k)` か `by_id.get(k, default)` で受ける
- `1` と `1.0` と `True` は同じキーにまとまる（`{1: "a", True: "b"}` は `{1: "b"}`）

## Test

`examples/map-key-by_test.py`
