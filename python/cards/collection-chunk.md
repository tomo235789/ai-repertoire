---
id: collection-chunk
lang: python
title: 配列を固定長の小配列に分割する
tags: [分割, チャンク, バッチ, chunk, split, batch, batched]
lib: stdlib
fn: itertools.batched
since: "3.12"
verified: 2026-09-17
preserves_order: true
status: public
---

イテラブルを `n` 個ずつのタプルに切り分ける。API のバッチ送信やページ分割で使う。

## Signature

```python
itertools.batched(iterable, n, *, strict=False)  # strict は 3.13 以降
```

## Usage

```python
from itertools import batched

list(batched([1, 2, 3, 4, 5], 2))
# => [(1, 2), (3, 4), (5,)]
```

## Contract

- 順序を保持する。各タプルの中も元の並び順のまま
- 入力を変更しない。各バッチは新しいタプルで、要素は同じ参照
- 遅延評価。返り値はイテレータで、バッチ 1 つ分だけ入力を読み進める。1 回しか走査できない
- 割り切れない場合、最後のタプルは `n` 未満になる。切り捨てない
- `strict=True`（Python 3.13 以降）のとき最後のタプルが `n` 未満なら `ValueError` を投げる。3.12 では `strict` 引数自体が無く `TypeError` になる
- 空のイテラブルを渡すと何も返さない（`list()` にすると `[]`）
- `n` が 1 未満なら `ValueError`、整数でなければ `TypeError` を投げる

## Alternatives

- 3.11 以前は more-itertools の `chunked(iterable, n)`（各バッチがリスト）
- 各バッチをリストで欲しければ `[list(b) for b in batched(xs, n)]`
- 重なる窓が欲しいなら `more_itertools.windowed`（collection-sliding-window）

## Pitfalls

- 返り値はリストではなくイテレータ。`len()` や添字は使えず、2 回目の走査は空になる。何度も使うなら `list()` で確定させる
- 各バッチはリストではなくタプル。es-toolkit の `chunk` は配列の配列を返す
- es-toolkit の `chunk` は不正な `size` をすべて `Error` にするが、`batched` は `n < 1` で `ValueError`、小数で `TypeError` と型が分かれる
- 文字列を渡すと 1 文字ずつのタプルになる。文字列に戻すなら `''.join(b)`

## Test

`examples/collection-chunk_test.py`
