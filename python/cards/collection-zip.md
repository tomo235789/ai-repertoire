---
id: collection-zip
lang: python
title: 複数の配列を要素ごとに組にする
tags: [組にする, 対応付け, 並行走査, zip, pair, tuple, transpose]
lib: stdlib
fn: zip
since: "3.10"
verified: 2026-09-17
preserves_order: true
status: public
---

複数のイテラブルを同じ位置ごとにタプルにまとめる。ヘッダー行と値の対応付けや 2 列の並行走査に使う。

## Signature

```python
zip(*iterables, strict=False)
```

## Usage

```python
list(zip([1, 2, 3], ["a", "b", "c"]))
# => [(1, 'a'), (2, 'b'), (3, 'c')]

list(zip([1, 2, 3], ["a", "b"]))
# => [(1, 'a'), (2, 'b')]  最短に合わせて打ち切る
```

## Contract

- 順序を保持する。i 番目のタプルは各イテラブルの i 番目の要素からなる
- 入力を変更しない。各タプルは新しく作られ、要素は同じ参照
- 遅延評価。返り値はイテレータで、タプル 1 つ分ずつ各入力を読み進める。1 回しか走査できない
- 長さは **最も短い** 入力に合わせて打ち切る。ただし尽きた入力より前の引数からは 1 要素余分に消費されている
- `strict=True` のとき長さが揃っていなければ、不一致が判明した時点で `ValueError` を投げる
- 引数は可変長で、タプルの長さは引数の数。引数なし、またはいずれかが空なら何も返さない

## Alternatives

- 最も長い入力に合わせ、足りない位置を埋めるなら `itertools.zip_longest(*its, fillvalue=None)`
- 組にした後で加工するなら `map(f, a, b)`（`f(x, y)` が位置ごとに呼ばれる）
- 逆操作（タプルの列を列の組に戻す）は `zip(*pairs)`
- 添字と組にするなら `enumerate(xs)`

## Pitfalls

- es-toolkit の `zip` は **最も長い** 配列に合わせて `undefined` で埋めるが、Python の `zip` は最も短い入力で打ち切る。es-toolkit 相当は `zip_longest`
- 長さの不一致は黙って切り捨てられる。取り違えを検出したいなら `strict=True` を付ける
- イテレータを渡すと、短い入力が尽きた時点でそれより前の引数から 1 要素余分に消費されている（`zip(it, [1])` は `it` の 2 番目まで読む）
- 返り値はイテレータ。`len()` や添字は使えず、2 回目の走査は空になる

## Test

`examples/collection-zip_test.py`
