---
id: iter-to-array
lang: python
title: イテレータを配列に変換する
tags: [リスト化, 実体化, 消費, イテレータ, to-list, collect, materialize, list]
lib: stdlib
fn: list
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

イテラブルを最後まで走査し、取り出した要素を新しいリストにして返す。`map` / `filter` / `islice` のチェーンの終端で使う。

## Signature

```python
list(iterable)
```

## Usage

```python
list(map(str, range(3)))
# => ['0', '1', '2']
it = iter([1, 2, 3])
next(it)
list(it)
# => [2, 3]（残りだけ。it はこれで空になる）
tuple(x * 10 for x in [1, 2])
# => (10, 20)
```

## Contract

- 即時評価。呼んだ時点でイテラブルを終端まで走査し、新しい `list` を返す
- 順序を保持する。要素は同じ参照のまま入る
- イテレータを消費する。既に `next()` で進めた分は含まれず、`list()` の後はイテレータが空になり、もう一度 `list()` すると `[]` を返す
- 終端まで進めるので、ジェネレータなら `finally` が走る。`return` した値は捨てられ、リストに含まれない
- リストを渡すと浅いコピー（`is` で別物、要素は同じ参照）。`dict` はキーのリスト、文字列は 1 文字ずつのリストになる
- 空のイテラブル、または引数なしなら `[]`
- イテラブルでないものを渡すと `TypeError`

## Alternatives

- 変更不可で欲しいなら `tuple(iterable)`、並べ替えつつ確定するなら `sorted(iterable, key=...)`（カード collection-sort-by）、重複除去なら `set(iterable)`（順序は失われる）
- 要素を変換しながら確定するなら内包表記 `[f(x) for x in it]`。`[*it]` でも `list(it)` と同じ
- 無限イテレータは `itertools.islice`（カード iter-take）で区切ってから `list()` する
- 既存のリストに追記するなら `xs.extend(iterable)`
- `dict` の値や項目は `list(d.values())` / `list(d.items())`

## Pitfalls

- 無限イテレータ（`itertools.count()` など）に直接 `list()` すると止まらない
- イテレータは `list()` で消費される。同じ結果を 2 度使うなら変数に受けてから使う
- `list` は組み込みの名前なので変数名や引数名に使わない（ruff の `A001` / `A002`）。`xs` や `items` にする
- TypeScript の `toArray()` はイテレータ自身のメソッドで配列や `Set` には無いが、Python の `list()` は組み込み関数でどんなイテラブルにも使える
- チェーンの途中で `list()` すると以降はリスト操作になり遅延評価の利点が消える。終端で 1 回だけ呼ぶ

## Test

`examples/iter-to-array_test.py`
