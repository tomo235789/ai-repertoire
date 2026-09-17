---
id: object-deep-merge
lang: python
title: 2 つのオブジェクトを再帰的にマージした新しいオブジェクトを作る
tags: [深いマージ, 再帰マージ, 設定の上書き, deep-merge, merge, defaults, override]
lib: mergedeep
fn: mergedeep.merge
since: "1.3"
verified: 2026-09-17
preserves_order: true
status: public
---

ネストした辞書を再帰的に重ね合わせる。デフォルト設定にユーザー設定を上書きするときに使う。第 1 引数が更新されるので、入力を守るには空の辞書を先頭に渡す。

## Signature

```python
merge(destination: MutableMapping, *sources: Mapping, strategy: Strategy = Strategy.REPLACE) -> MutableMapping
```

## Usage

```python
from mergedeep import merge

defaults = {"retry": 3, "log": {"level": "info", "file": "app.log"}}
overrides = {"log": {"level": "debug"}}
merge({}, defaults, overrides)
# => {'retry': 3, 'log': {'level': 'debug', 'file': 'app.log'}}
```

## Contract

- 第 1 引数 `destination` を **破壊的に更新し、それ自身を返す**。入力を変えたくなければ `merge({}, a, b)` のように空の辞書を先頭に渡す。`sources` は変更しない
- `sources` は左から順に適用され、同じキーは後のものが勝つ
- 両方の値が `Mapping` なら再帰的にマージする。既定の `Strategy.REPLACE` ではそれ以外（リスト、スカラーなど）は後の値で丸ごと置き換える。リストは連結しない
- `sources` から新しく取り込まれる値は `deepcopy` されて入る。ただし `destination` が既に `sources` と同じオブジェクトを参照している場合はその参照が残るので、「返り値と `sources` が参照を共有しない」保証は新規に取り込まれた値に限る
- `sources` の値が `None` でも上書きする
- 返り値のキー順は `destination` の順の後に、`sources` で新たに現れたキーがその順で並ぶ
- `strategy=Strategy.ADDITIVE` では同じキーの `list` / `tuple` / `set` を連結する。スカラーは置き換える
- `strategy=Strategy.TYPESAFE_REPLACE` / `TYPESAFE_ADDITIVE` では、再帰マージされない値（両方が `Mapping` ではない場合）の型が異なると `TypeError` を投げる。`dict` と `defaultdict` のように両方 `Mapping` なら具象型が違っても再帰マージされる。既定の `REPLACE` は例外を投げない

## Alternatives

- 1 段階だけでよいなら stdlib の `{**a, **b}` または `a | b`（3.9+）。ネストした辞書は後の値で丸ごと置き換わる
- リストや集合を連結したいなら `merge({}, a, b, strategy=Strategy.ADDITIVE)`
- 同じキーに違う型が来たら失敗させたいなら `Strategy.TYPESAFE_REPLACE`

## Pitfalls

- `merge(defaults, overrides)` と書くと `defaults` が書き換わる。TypeScript 版（es-toolkit の `toMerged`）は非破壊。破壊的な `merge` に相当する
- 配列の扱いが違う。es-toolkit の `toMerged` はインデックスごとに上書き（`[1, 2, 3]` と `[9]` は `[9, 2, 3]`）だが、mergedeep の `REPLACE` は `[9]` に丸ごと置き換え、`ADDITIVE` は `[1, 2, 3, 9]` に連結する
- es-toolkit は `source` の `undefined` を無視するが、mergedeep は `None` で上書きする。「未指定」を表したいならキー自体を入れない
- `Strategy.TYPESAFE` は `TYPESAFE_REPLACE` の別名（`==` では等しくないが挙動は同じ）

## Test

`examples/object-deep-merge_test.py`
