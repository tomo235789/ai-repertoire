---
id: object-pick
lang: python
title: オブジェクトから指定したキーだけを取り出す
tags: [抽出, キー選択, 部分辞書, pick, select-keys, subset, projection]
lib: stdlib
fn: dict comprehension
since: "3.7"
verified: 2026-09-17
preserves_order: true
status: public
---

辞書から必要なキーだけを持つ新しい辞書を作る。API レスポンスの整形や、機密フィールドを含まない DTO の作成に使う。

## Signature

```python
{k: d[k] for k in keys if k in d}
```

## Usage

```python
user = {"id": 1, "name": "a", "password": "x"}
keys = ["id", "name", "missing"]
{k: user[k] for k in keys if k in user}
# => {'id': 1, 'name': 'a'}
```

## Contract

- 入力辞書を変更しない。返り値は新しい `dict`（値は浅いコピー。ネストした辞書やリストは同じ参照）
- 存在しないキーは `if k in d` で無視され、返り値にそのキーは作られない。値が `None` のキーは `None` のまま含まれる
- 返り値のキーは `keys` の並び順（元の辞書の順ではない）。`keys` に重複があっても 1 つにまとまる
- `keys` が空なら `{}` を返す
- `keys` にハッシュ化できない値（リストなど）があると `in` の判定で `TypeError` を投げる。それ以外で例外は投げない

## Alternatives

- 存在しないキーを黙って無視せず失敗させたいなら `{k: d[k] for k in keys}`（`KeyError`）
- 値だけをタプルで取り出すなら `operator.itemgetter("id", "name")(d)`。存在しないキーは `KeyError` になる
- 除外する側を列挙したいなら object-omit

## Pitfalls

- `{k: d.get(k) for k in keys}` と書くと、存在しないキーが値 `None` で含まれてしまう。TypeScript 版（es-toolkit の `pick`）と同じく「無視」にするには `if k in d` が要る
- es-toolkit の `pick` は整数風のキー（`'1'` など）が昇順で先頭に並ぶが、Python の `dict` は `keys` の順のまま
- `keys` の要素がそのまま返り値のキーになる。`d` のキーが `1` で `keys` が `[True]` のときは `{True: ...}` になる（`1 == True` で一致する）

## Test

`examples/object-pick_test.py`
