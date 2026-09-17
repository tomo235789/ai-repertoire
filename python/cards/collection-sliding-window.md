---
id: collection-sliding-window
lang: python
title: 配列をスライディングウィンドウで走査する
tags: [スライディングウィンドウ, 移動窓, 移動平均, sliding-window, windowed, rolling, pairwise]
lib: more-itertools
fn: more_itertools.windowed
since: "11.0"
verified: 2026-09-17
preserves_order: true
status: public
---

幅 `n` の窓を `step` ずつずらしながらタプルで取り出す。移動平均や隣接要素の比較に使う。

## Signature

```python
more_itertools.windowed(seq, n, fillvalue=None, step=1)
```

## Usage

```python
from more_itertools import windowed

list(windowed([1, 2, 3, 4, 5], 3))
# => [(1, 2, 3), (2, 3, 4), (3, 4, 5)]

list(windowed([1, 2, 3, 4, 5], 3, step=2))
# => [(1, 2, 3), (3, 4, 5)]
```

## Contract

- 順序を保持する。窓は先頭から `step` 刻みの開始位置で並び、窓の中も元の並び順
- 入力を変更しない。各窓は新しいタプルで、要素は同じ参照
- 遅延評価。返り値はジェネレータで、窓 1 つ分ずつ入力を読み進める。1 回しか走査できない
- `step` の既定値は `1`。`step > n` なら窓の間の要素は飛ばされる
- 末尾で窓に収まりきらない要素があれば、その要素を含む最後の窓を `fillvalue`（既定 `None`）で **埋めて** 出力する（`step > n` で窓の間に落ちた要素は別で、これは飛ばされる）。前の窓に含まれた要素しか残っていなければ、埋めた窓は出力しない
- 入力長が `n` 未満なら `fillvalue` で埋めた窓を 1 つだけ返す
- 空のイテラブルを渡すと何も返さない
- `n` が 1 未満、または `step` が 1 未満なら `ValueError` を投げる

## Alternatives

- 埋めずに `n` 個そろった窓だけ欲しいなら `more_itertools.sliding_window(iterable, n)`（`step` 無し。入力長が `n` 未満なら空）
- `n == 2` なら stdlib の `itertools.pairwise`（3.10+）
- 重ならない分割は `itertools.batched`（collection-chunk）。`windowed(xs, n, step=n)` は末尾を `fillvalue` で埋める点が違う

## Pitfalls

- es-toolkit の `windowed` は既定で `size` に満たない末尾の窓を **捨てる** が、more-itertools は `fillvalue` で **埋める**。捨てたいなら `sliding_window`、短い窓（`partialWindows: true` 相当）が欲しいなら番兵を `fillvalue` にして各窓から除く
- `fillvalue` の既定は `None` なので、要素に `None` が含まれると埋めた値と区別できない。`fillvalue=object()` のような番兵を使う
- 引数名は `seq` だが任意のイテラブル（ジェネレータ、無限イテレータ）を受け取る
- 11.0 より前は `n=0` で例外を投げなかった。`n < 1` の `ValueError` に頼るなら 11.0 以上を要求する

## Test

`examples/collection-sliding-window_test.py`
