---
id: number-sum-by
lang: python
title: 配列の各要素から取り出した数値を合計する
tags: [合計, 集計, 合算, sum, sum-by, total, aggregate]
lib: stdlib
fn: sum
since: "3.12"
verified: 2026-09-17
status: public
---

各要素から数値を取り出して合計する。オブジェクト配列の数量や金額の集計に使う。ジェネレータ式を渡せば中間リストを作らない。

## Signature

```python
sum(iterable, /, start=0)
```

## Usage

```python
items = [{"name": "a", "qty": 2}, {"name": "b", "qty": 3}]
sum(item["qty"] for item in items)
# => 5
```

## Contract

- 入力を変更しない
- 取り出し関数（ジェネレータ式の本体）は各要素につきちょうど 1 回、先頭から順に評価される
- 空なら `start` を返す。既定は `0`（`int`）
- 型変換はしない。要素に `str` や `None` があると `TypeError` を投げる。`start` に `str` を渡しても `TypeError`
- `float` の合計は 3.12 以降のほとんどのビルド（ドキュメントの表現では "most builds"）で補正付き加算になり `sum([0.1] * 10)` は `1.0`。ただし厳密に丸められる保証は無い
- 要素に `NaN` があれば `NaN`。`inf` と `-inf` を両方含むと `NaN`
- `bool` は `int` として合計される（`sum([True, True])` は `2`）。`int` と `float` が混在すると `float`

## Alternatives

- `float` を厳密に丸めて合計したいなら `math.fsum(key(x) for x in xs)`（常に `float` を返す）
- `Decimal` の合計は `sum(...)` でそのまま動く（`0 + Decimal` は `Decimal`）。`float` と混ぜると `TypeError`
- 平均は number-mean（`statistics.fmean`）
- 文字列の連結は `"".join(...)`、リストの連結は `itertools.chain.from_iterable(...)`。`sum` は数値専用

## Pitfalls

- TypeScript 版（es-toolkit の `sumBy`）は取り出した値が `undefined` なら `NaN`、文字列なら連結になるが、Python は `TypeError` で止まる
- キーが欠けている要素があるなら `item.get("qty", 0)` で補う。`item["qty"]` は `KeyError`
- 3.11 以前の `sum` は `float` を素朴に加算するので `sum([0.1] * 10)` が `0.9999999999999999` になる
- 金額など誤差を許せない値は整数（最小単位）か `Decimal` で合計する

## Test

`examples/number-sum-by_test.py`
