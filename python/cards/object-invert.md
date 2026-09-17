---
id: object-invert
lang: python
title: オブジェクトのキーと値を入れ替える
tags: [逆引き, キーと値の交換, 逆マッピング, invert, reverse-map, swap-keys, lookup]
lib: stdlib
fn: dict comprehension
since: "3.7"
verified: 2026-09-17
preserves_order: true
status: public
---

キーと値を入れ替えた新しい辞書を作る。コード → 名前の対応表から名前 → コードの逆引き表を作るときに使う。

## Signature

```python
{v: k for k, v in d.items()}
```

## Usage

```python
code_to_name = {1: "red", 2: "blue"}
{v: k for k, v in code_to_name.items()}
# => {'red': 1, 'blue': 2}
```

## Contract

- 入力辞書を変更しない。返り値は新しい `dict`
- 返り値のキーは元の値、返り値の値は元のキー。型はそのまま（文字列化しない）
- 順序は元の辞書の挿入順
- 値が重複した場合は **最後** に処理されたキーが残る。返り値でのそのキーの位置は最初に出現した場所
- 空の辞書を渡すと `{}` を返す
- 値にハッシュ化できないもの（リスト、辞書など）があると `TypeError` を投げる。`None` はキーにできる

## Alternatives

- 重複する値をまとめたい（`{1: ['a', 'b']}`）なら `collections.defaultdict(list)` に `append` する
- 値がハッシュ化できないなら、キーにできる形（タプルや `json.dumps` の文字列）に変換してから逆引き表を作る

## Pitfalls

- TypeScript 版（es-toolkit の `invert`）と同じで最後が残る。ただし es-toolkit は元のキーを文字列化し（`1` は `'1'`）、整数風のキーを昇順で先頭に並べる。Python は型も挿入順もそのまま
- 値が重複しないことを前提にしている。重複を検出したいなら `len(inverted) == len(d)` を確認する
- `1` と `1.0` と `True` は同じキーとして扱われる（`{1: "a", True: "b"}` は `{1: "b"}`）

## Test

`examples/object-invert_test.py`
