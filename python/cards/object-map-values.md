---
id: object-map-values
lang: python
title: オブジェクトの各値を変換して同じキーの新しいオブジェクトを作る
tags: [値の変換, 辞書の変換, 辞書のmap, map-values, transform, dictionary, mapping]
lib: stdlib
fn: dict comprehension
since: "3.7"
verified: 2026-09-17
preserves_order: true
status: public
---

キーはそのままに、各値だけを関数で変換した新しい辞書を作る。`dict[str, X]` を `dict[str, Y]` に変換するときに使う。

## Signature

```python
{k: f(v) for k, v in d.items()}
```

## Usage

```python
scores = {"alice": [80, 90], "bob": [70]}
{k: len(v) for k, v in scores.items()}
# => {'alice': 2, 'bob': 1}
```

## Contract

- キーの順序を保持する。返り値のキーは入力と同じ
- 入力辞書を変更しない。返り値は新しい `dict`。`f` が返した値がそのまま入る（入力の値を返せば同じ参照）
- `f` は純粋関数であること。各キーにつきちょうど 1 回、挿入順に呼ばれる
- 空の辞書を渡すと `{}` を返す
- 内包表記自身は例外を投げないが、`f` が投げた例外は捕捉されずそのまま伝播する

## Alternatives

- キーも変えるなら `{g(k): f(v) for k, v in d.items()}`。キーが衝突すると後勝ちになる
- キーと値の両方を使うなら `{k: f(k, v) for k, v in d.items()}`
- リストの各要素を変換するなら `[f(x) for x in xs]`（辞書内包表記ではない）

## Pitfalls

- TypeScript 版（es-toolkit の `mapValues`）と同じ意味論
- `dict(map(lambda kv: (kv[0], f(kv[1])), d.items()))` でも同じだが読みにくい。内包表記を使う
- `d.items()` を走査中に `d` を変更すると `RuntimeError` になる。`f` の中で入力辞書を書き換えない

## Test

`examples/object-map-values_test.py`
