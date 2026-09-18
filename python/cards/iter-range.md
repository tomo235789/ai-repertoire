---
id: iter-range
lang: python
title: 等差数列の配列を作る
tags: [連番, 等差数列, 範囲, 数列生成, range, sequence, arithmetic, numbers]
lib: stdlib
fn: range
since: "3.0"
verified: 2026-09-17
preserves_order: true
status: public
---

`start` から `stop` の手前まで `step` 刻みの整数列を表す不変シーケンスを作る。ループの回数指定やページ番号の生成、テストデータ作成に使う。

## Signature

```python
range(start, stop, step=1)  # range(stop) は range(0, stop) と同じ
```

## Usage

```python
list(range(4))          # => [0, 1, 2, 3]
list(range(1, 4))       # => [1, 2, 3]
list(range(0, 20, 5))   # => [0, 5, 10, 15]
list(range(0, -4, -1))  # => [0, -1, -2, -3]
list(range(5, 1))       # => []（step 1 で届かない）
r = range(0, 20, 5)
len(r), r[-1], 10 in r  # => (4, 15, True)
list(reversed(r))       # => [15, 10, 5, 0]
```

## Contract

- 遅延評価。`range` オブジェクトは要素を持たず、添字アクセスや走査のたびに計算する。`range(10**18)` でもメモリは一定で、`10**17 in range(10**18)` は即座に返る
- 順序を保持する不変シーケンス。`start` 以上 `stop` 未満、`step` 刻みの昇順（負の `step` なら降順）
- 引数 1 つなら `range(stop)` = `range(0, stop)`。`step` 省略は `1`
- `step` が正で `start >= stop`、または `step` が負で `start <= stop` なら空。`range(0)` や `range(-3)` も空
- 何度でも走査できる。`len()`、添字（負も可）、`in`、`index()`、`count()`、スライス（結果も `range`）、`reversed()` が使える
- 引数は整数のみ。小数を渡すと `TypeError`、`step` が `0` なら `ValueError`、範囲外の添字は `IndexError`、`index()` に無い値は `ValueError`
- 同じ列を表す `range` は `==` で等しい（`range(0, 3) == range(3)`、`range(0) == range(5, 1)`）。リストとは等しくない

## Alternatives

- 小数刻みは `[i / 10 for i in range(0, 5)]` のように整数で作ってから割る。等間隔の小数列は `numpy.arange` / `numpy.linspace`
- 無限の連番は `itertools.count(start, step)` と `itertools.islice`（カード iter-take）
- 添字と要素を一緒に回すなら `range(len(xs))` ではなく `enumerate(xs)`
- 逆順は `range(stop - 1, -1, -1)` より `reversed(range(stop))` が読みやすい

## Pitfalls

- es-toolkit の `range` と違いリストではない。`append` や `+` での連結はできず、リストが要るなら `list(range(n))`
- `stop` は含まない。`1` から `10` までなら `range(1, 11)`
- 小数の `step` や `stop` は `TypeError`（es-toolkit は `Error`）。`0.1` 刻みは整数で作ってから割る
- `start > stop` で `step` を省略すると空。lodash / `es-toolkit/compat` の `range` は自動で降順になるので移植時に注意。降順は `step` に負数を明示する
- `1.0 in range(3)` は `True` になる（`==` で比較される）。O(1) で判定できるのは整数のとき

## Test

`examples/iter-range_test.py`
